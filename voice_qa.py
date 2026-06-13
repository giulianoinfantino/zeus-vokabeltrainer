#!/usr/bin/env python3
"""QA-Harness für die Sprachausgabe (Ziel: perfekt = konstante Stimme + korrekte
Aussprache). Erzeugt v3-Audio mit den Produktions-Settings, misst:
  • Stimm-Konsistenz: Resemblyzer-Cosine zum Referenz-Centroid (Marlena),
    Stimm-Ausreißer werden mit anderem Seed neu erzeugt (best-of-N).
  • Aussprache: Allosaurus-Phone vs. Ziel-IPA (grobe Editdistanz → flaggt Grobfehler;
    Frikative/χ kann Allosaurus nicht beurteilen → immer für Ohr-Review flaggen).

Lauf IM venv:  ~/greek-app/.venv-allo/bin/python voice_qa.py <lektion.json> [--limit N]
"""
import json, subprocess, sys, re
from pathlib import Path
import numpy as np
import editdistance
from resemblyzer import VoiceEncoder, preprocess_wav
from allosaurus.app import read_recognizer
from grc_ipa import grc_to_ipa

KEY = (Path.home() / ".config/zeus/elevenlabs.key").read_text().strip()
VOICE = "MTTjXkEpZepLTqO0xH0f"
OUT = Path.home() / "Desktop/zeus_qa"; OUT.mkdir(parents=True, exist_ok=True)
SEEDS = [42, 7, 123, 999]      # 42 = Produktion; weitere nur für Ausreißer
VOICE_THRESH = 0.82            # darunter = Stimm-Ausreißer → anderen Seed versuchen
REF_WORDS = ["ἀρετή", "σοφία", "παιδεία", "βασιλεύς", "εἰρήνη", "ἄνθρωπος", "φέρω", "καλός"]

enc = VoiceEncoder("cpu")
phon = read_recognizer()

def synth(ipa_text, seed):
    body = {"text": ipa_text, "model_id": "eleven_v3", "seed": seed,
            "voice_settings": {"stability": 0.5, "similarity_boost": 1.0}}
    r = subprocess.run(["curl", "-sf", "-X", "POST",
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_128",
        "-H", f"xi-api-key: {KEY}", "-H", "Content-Type: application/json", "-d", json.dumps(body)],
        capture_output=True)
    return r.stdout if (r.returncode == 0 and len(r.stdout) >= 800) else None

def to_wav(mp3_bytes, path):
    mp3 = path.with_suffix(".mp3"); mp3.write_bytes(mp3_bytes)
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", "-c", "1", str(mp3), str(path)], capture_output=True)

def emb(wav):
    return enc.embed_utterance(preprocess_wav(Path(wav)))

def pron_score(wav, expected_ipa):
    got = phon.recognize(str(wav)).replace(" ", "")
    exp = re.sub(r"[ˈ/ː ]", "", expected_ipa)
    if not exp:
        return 1.0, got
    return max(0.0, 1 - editdistance.eval(got, exp) / max(len(exp), 1)), got

def safe(s):
    return "".join(c for c in s if c.isalnum())[:14] or "x"

def build_reference():
    embs, sims = [], []
    for w in REF_WORDS:
        b = synth(f"/{grc_to_ipa(w)}/", 42)
        if b:
            p = OUT / f"ref_{safe(w)}.wav"; to_wav(b, p); embs.append(emb(p))
    ref = np.mean(embs, axis=0); ref /= np.linalg.norm(ref)
    sims = [float(np.dot(e, ref)) for e in embs]
    print(f"Referenz-Centroid aus {len(embs)} Wörtern · Selbst-Ähnlichkeit "
          f"min={min(sims):.3f} mittel={np.mean(sims):.3f}")
    return ref

def qa_word(greek, ref):
    chunk = greek.split(",")[0].strip()                    # Grundform-Chunk
    ipa = " ".join(f"/{grc_to_ipa(w)}/" for w in chunk.split())
    exp = " ".join(grc_to_ipa(w) for w in chunk.split())
    best = None
    for seed in SEEDS:
        b = synth(ipa, seed)
        if not b:
            continue
        p = OUT / f"{safe(chunk)}_{seed}.wav"; to_wav(b, p)
        vs = float(np.dot(emb(p), ref))
        if best is None or vs > best[1]:
            best = (seed, vs, p)
        if vs >= VOICE_THRESH:
            break
    if best is None:
        return {"chunk": chunk, "flag": ["synth-fehler"]}
    seed, vs, p = best
    ps, got = pron_score(p, exp)
    flag = []
    if vs < VOICE_THRESH: flag.append("Stimme")
    # Allosaurus kann Aussprache NICHT benoten (Referenz-Korrektwörter: P~0.28 = reines
    # Erkenner-Rauschen). Nur Grobausfall: leere/sehr kurze Phonfolge = Stille/Abbruch.
    if len(got) < max(3, int(0.4 * len(re.sub(r"[ˈ/ː ]", "", exp)))): flag.append("stumm?")
    if "χ" in chunk or "Χ" in chunk: flag.append("χ")
    return {"chunk": chunk, "ipa": exp, "voice": round(vs, 3), "seed": seed,
            "pron": round(ps, 3), "allo": got, "flag": flag, "audio": p.with_suffix(".mp3").name}

if __name__ == "__main__":
    path = Path(sys.argv[1])
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 9999
    data = json.loads(path.read_text())
    leks = data.get("lektionen", [data])
    vocab = [v for lek in leks for v in lek.get("vokabeln", [])][:limit]
    ref = build_reference()
    print(f"QA über {len(vocab)} Wörter (Grundform-Chunk):\n")
    results = []
    for v in vocab:
        r = qa_word(v["griechisch"], ref); results.append(r)
        print(f"  {r['chunk'][:22]:<24} V={r.get('voice','?'):<6} P={r.get('pron','?'):<6} "
              f"seed={r.get('seed','?'):<4} [{','.join(r.get('flag', [])) or 'ok'}]")
    flagged = [r for r in results if r.get("flag")]
    (OUT / "qa_report.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    # Ohr-Review-Seite: Geflaggtes zuerst, jedes Wort mit Player + Ziel-IPA.
    rows = sorted(results, key=lambda r: (not r.get("flag"), r.get("chunk", "")))
    items = "\n".join(
        f'<li class="{"flag" if r.get("flag") else ""}">'
        f'<audio controls preload=none src="{r.get("audio","")}"></audio>'
        f'<span class=g>{r.get("chunk","")}</span><span class=i>/{r.get("ipa","")}/</span>'
        f'<span class=m>V={r.get("voice","?")} seed={r.get("seed","?")} {" ".join(r.get("flag",[]))}</span></li>'
        for r in rows)
    html = ("<!doctype html><meta charset=utf-8><title>Zeus Audio-Review</title><style>"
            "body{font-family:sans-serif;background:#0a0d15;color:#edf0f7;max-width:780px;margin:24px auto;padding:0 16px}"
            "h1{font-size:18px}ul{padding:0}li{list-style:none;display:flex;align-items:center;gap:12px;padding:8px;border-bottom:1px solid #242e47}"
            "li.flag{background:#2a1a1a}.g{font-size:20px;min-width:130px}.i{color:#8b94ab;min-width:150px;font-size:13px}"
            ".m{color:#e3b64f;font-size:12px;margin-left:auto}audio{height:34px}</style>"
            f"<h1>Audio-Review · {len(flagged)} geflaggt / {len(results)} · rot = prüfen</h1><ul>{items}</ul>")
    review_name = f"review_{path.stem}.html"
    (OUT / review_name).write_text(html)
    print(f"\n{len(flagged)}/{len(results)} geflaggt. Ohr-Review-Seite: open {OUT/review_name}")
