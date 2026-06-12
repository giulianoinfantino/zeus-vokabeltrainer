#!/usr/bin/env python3
"""Audio-Generierung für den Zeus-Vokabeltrainer — deutsche Schulaussprache (erasmisch).

Pipeline pro Vokabel:
  griechisch ("ὁ θεός, τοῦ θεοῦ" / "ἀγαθός, -ή, -όν")
    → Chunks an den Kommata, Kurz-Endungen werden expandiert (ἀγαθή, ἀγαθόν)
    → deterministische Transliteration (ho theós, tou theoú)
    → deutsch-phonetischer Sprechtext (Schulaussprache, s.u.)
    → eine m4a-Datei pro Chunk (ElevenLabs, sonst macOS `say`)

Aussprache-Schema: DEUTSCHE SCHULAUSSPRACHE (Nutzerentscheidung 06/2026, löst
die "strenge Rekonstruktion" ab — passend zum App-Versprechen "wie an Schulen
und Universitäten gelehrt"):
  η=[ɛː] ä   ει=dt. „ei"   ευ=dt. „eu"   οι=dt. „oi"   ου=[uː]
  θ=[t]      φ=[f]         χ=dt. „ch"    ζ=[ts]        υ=[yː] ü
Iota subscriptum wird nicht gesprochen.

Der ElevenLabs-Key wird aus ~/.config/zeus/elevenlabs.key gelesen.
Das Feld "sprich" (kompletter Sprechtext) bleibt für den speechSynthesis-
Fallback der App erhalten; "audio" = Lemma-Chunk, "flexAudio" = weitere Chunks.

Start:
  python3 gen_audio.py --pruefen            # nur Transliteration validieren
  python3 gen_audio.py --neu [datei ...]    # alles neu vertonen (Regeln geändert!)
  python3 gen_audio.py [datei ...]          # nur fehlende Dateien ergänzen
"""
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

KEY_DATEI = Path.home() / ".config/zeus/elevenlabs.key"
VOICE_ID = "MTTjXkEpZepLTqO0xH0f"  # Marlena — deutsche Muttersprachlerin
MODELL = "eleven_turbo_v2_5"        # unterstützt language_code-Erzwingung
SAY_STIMME = "Sandy (German (Germany))"
SAY_RATE = 160

# ───────────────────────── Transliteration (Griechisch → Latein) ─────────────────────────
# Kombinierende Zeichen nach NFD-Zerlegung
M_LENIS, M_ASPER = "̓", "̔"
M_AKUT, M_GRAVIS, M_ZIRK = "́", "̀", "͂"
M_IOTA, M_TREMA, M_MAKRON, M_BREVE = "ͅ", "̈", "̄", "̆"

BASIS = {"α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "ē",
         "θ": "th", "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "x",
         "ο": "o", "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y",
         "φ": "ph", "χ": "ch", "ψ": "ps", "ω": "ō"}
VOKALE = "αεηιουω"

def _zerlege(wort: str):
    """NFD-Wort → Liste (Basisbuchstabe, Menge der Diakritika)."""
    out = []
    for ch in unicodedata.normalize("NFD", wort):
        if ch in BASIS or ch.lower() in BASIS:
            out.append([ch.lower(), set(), ch.isupper()])
        elif out and unicodedata.combining(ch):
            out[-1][1].add(ch)
    return out

def translit_wort(wort: str) -> str:
    buchst = _zerlege(wort)
    if not buchst:
        return ""
    lat, asper = [], False
    for i, (b, marks, gross) in enumerate(buchst):
        if M_ASPER in marks:
            asper = True
        # γ-Nasal: γ vor γ/κ/χ/ξ → n
        if b == "γ" and i + 1 < len(buchst) and buchst[i + 1][0] in "γκχξ":
            lat.append("n")
            continue
        # υ als zweiter Diphthong-Bestandteil → u (außer bei Trema)
        if (b == "υ" and i > 0 and buchst[i - 1][0] in "αεηο"
                and M_TREMA not in marks and M_IOTA not in buchst[i - 1][1]):
            kern = "u"
        else:
            kern = BASIS[b]
        # Akzente auf den (letzten) lateinischen Vokal setzen
        if M_AKUT in marks:
            kern = unicodedata.normalize("NFC", kern[:-1] + kern[-1].replace("ē", "e").replace("ō", "o") + M_AKUT) \
                   if kern[-1] in "ēō" else unicodedata.normalize("NFC", kern + M_AKUT)
            if b == "η": kern = "ḗ"
            if b == "ω": kern = "ṓ"
        elif M_ZIRK in marks:
            basisvokal = {"ē": "e", "ō": "o"}.get(kern, kern)
            kern = unicodedata.normalize("NFC", basisvokal + "̂")  # â ê î ô û ŷ
        # Iota subscriptum anhängen (ᾳ→āi, ᾴ→ái, ῷ→ôi …)
        if M_IOTA in marks:
            if M_AKUT not in marks and M_ZIRK not in marks and b == "α":
                kern = "ā"
            kern += "i"
        lat.append(kern)
    s = "".join(lat)
    if asper:
        s = ("rh" + s[1:]) if s.startswith("r") else ("h" + s)
    if buchst[0][2]:
        s = s[0].upper() + s[1:]
    return unicodedata.normalize("NFC", s)

def translit(text: str) -> str:
    return " ".join(filter(None, (translit_wort(w) for w in text.split())))

# ───────────────────────── Endungs-Expansion (ἀγαθός, -ή → ἀγαθή) ─────────────────────────
# (Kopf-Endungen, mögliche Kurzformen, Anzahl zu ersetzender Zeichen)
EXPANSION = [
    (("ος", "ός"), {"ή", "ά", "όν", "ον", "η", "α", "ο", "ό"}, 2),
    (("ων",), {"ον"}, 2),
    (("οι",), {"αι", "α"}, 2),
    (("ης", "ής"), {"ες", "ές", "ητος"}, 2),
    (("ύς", "υς"), {"εῖα", "εια", "ύ", "υ"}, 2),
    (("οῦς", "ους"), {"ῆ", "οῦν", "ουν"}, 3),
    (("οῦ",), {"ῆς", "οῦ"}, 2),
    (("ις",), {"ιος"}, 2),
]

def expandiere(kopfwort: str, endung: str) -> str | None:
    e = unicodedata.normalize("NFC", endung.lstrip("-–").strip().rstrip(";,."))
    k = unicodedata.normalize("NFC", kopfwort)
    for kopf_enden, formen, n in EXPANSION:
        if e in formen and k.endswith(kopf_enden):
            return k[:-n] + e
    return None

def chunks_von(griechisch: str) -> list[str]:
    """Vokabeleintrag → vollständige Sprech-Chunks (Kurz-Endungen expandiert)."""
    teile = [t.strip() for t in griechisch.split(",") if t.strip()]
    if not teile:
        return []
    kopf = teile[0].replace("(ν)", "")
    kopfwort = kopf.split()[-1]
    out = [kopf]
    for t in teile[1:]:
        t = t.replace("(ν)", "")
        if t.startswith(("-", "–")):
            voll = expandiere(kopfwort, t)
            if voll is None:
                print(f"  ⚠ Endung nicht expandierbar: {griechisch!r} → {t!r}")
                continue
            out.append(voll)
        else:
            out.append(t)
    return out

# ───────────────────────── Sprechtext (Schulaussprache, dt. Orthographie) ─────────────────────────
# Reihenfolge wichtig: Iota-subscriptum- und ου-Regeln vor den Einzelzeichen.
ERSETZUNGEN = [
    # Iota subscriptum: stumm
    ("āi", "ah"), ("ái", "ah"), ("ēi", "äh"), ("êi", "äh"), ("ōi", "oh"), ("ôi", "oh"),
    # Hiatus ε+ου / α+ου (θεοῦ, λαοῦ): Bindestrich verhindert falschen
    # deutschen Diphthong („teuh" → [tɔʏ] statt [te-uː])
    ("eoû", "e-uh"), ("eoú", "e-ú"), ("eou", "e-u"),
    ("aoû", "a-uh"), ("aoú", "a-ú"), ("aou", "a-u"),
    # ου = langes u
    ("ou", "u"), ("oú", "ú"), ("oû", "uh"),
    # Akzente auf Diphthongen zerbrechen die TTS-Aussprache (verifiziert):
    ("aí", "ai"), ("aî", "ai"), ("eí", "ei"), ("eî", "ei"), ("oí", "oi"), ("oî", "oi"),
    ("aú", "au"), ("aû", "au"), ("eú", "eu"), ("eû", "eu"),
    # ei/eu/oi/ai/au bleiben stehen → deutsche Diphthonge (Schulaussprache)
    ("rh", "r"),
    ("th", "t"),                                # θ = [t]
    ("ph", "f"),                                # φ = [f]   (Schulaussprache)
    # χ bleibt „ch" — deutsches ch              (Schulaussprache)
    ("ṓ", "óh"), ("ō", "oh"), ("ô", "oh"),     # ω lang
    ("î", "ih"), ("ī", "ih"),
    ("ḗ", "äh"), ("ē", "äh"), ("ê", "äh"),     # η = [ɛː]
    ("â", "ah"), ("ā", "ah"),
    ("ŷ", "ü"), ("ý", "ü"), ("y", "ü"),        # υ = ü
]

# Handkorrekturen, wo die automatische Regel nicht reicht.
# Wert: Sprechtext oder (Sprechtext, Sprachcode). Bei οὔ und τί deckt sich die
# neugriechische Aussprache mit der Schulaussprache — diese laufen über "el".
UEBERSCHREIBUNGEN = {
    "eimí": "eimii",          # Endbetonung erzwingen
    "allá": "allah",
    "oú": ("ου.", "el"),
    "tí?": ("τι", "el"),
}

# ── Wortinitiales χ ──
# Deutsche TTS liest anlautendes „ch" als [ʃ] („chaire" → „Schere", per STT
# verifiziert). Lösung: χ-anlautende Wörter werden phonetisch-neugriechisch
# geschrieben und mit language_code "el" vertont — dort ist χ immer [x]/[ç]
# (STT-verifiziert: „χάιρε" → [ˈxaire]). Artikel davor bleiben deutsch; die
# MP3-Teile werden zu einer Datei verbunden.
# Nur b/d/g/h sind neugriechisch nicht schreibbar (gefangen vom Latein-Rest-Check).
# υ→ι und ευ→[ev] sind Klang-Näherungen, aber χ bleibt korrekt [x] (Nutzerwunsch:
# χ ist „ch", nicht [k]) — STT-verifiziert: χορέβω→„Χορεύω", χρισός→„Χρυσός".
NG_REGELN = [
    # Digraphen zuerst
    ("ch", "χ"), ("th", "τ"), ("ph", "φ"), ("ps", "ψ"), ("rh", "ρ"), ("z", "τσ"),
    # Diphthonge (Schulaussprache → neugriechische Schreibung mit gleichem Klang)
    ("aí", "άι"), ("aî", "άι"), ("ai", "αϊ"),
    ("eí", "άι"), ("eî", "άι"), ("ei", "αϊ"),
    ("oí", "όι"), ("oî", "όι"), ("oi", "οϊ"),
    ("aú", "άου"), ("aû", "άου"), ("au", "αου"),
    ("eú", "εύ"), ("eû", "εύ"), ("eu", "ευ"),     # ευ → MG [ev/ef] (Näherung)
    ("oú", "ού"), ("oû", "ού"), ("ou", "ου"),
    # lange Vokale (Akzent bleibt erhalten!)
    ("ḗ", "έ"), ("ē", "ε"), ("ê", "έ"),
    ("ṓ", "ώ"), ("ō", "ω"), ("ô", "ώ"),
    ("â", "ά"), ("ā", "α"), ("î", "ί"), ("ī", "ι"),
    ("ý", "ί"), ("ŷ", "ί"), ("y", "ι"),           # υ → MG [i] (Näherung)
    # kurze Vokale
    ("á", "ά"), ("a", "α"), ("é", "έ"), ("e", "ε"),
    ("í", "ί"), ("i", "ι"), ("ó", "ό"), ("o", "ο"), ("ú", "ού"), ("u", "ου"),
    # Konsonanten
    ("k", "κ"), ("l", "λ"), ("m", "μ"), ("n", "ν"), ("p", "π"),
    ("r", "ρ"), ("s", "σ"), ("t", "τ"), ("x", "ξ"), ("f", "φ"),
]

def nach_neugriechisch(umschrift_wort: str) -> str | None:
    """Translit-Wort (mit Akzenten) → phonetisches Neugriechisch, sonst None."""
    w = unicodedata.normalize("NFC", umschrift_wort)
    for alt, neu in NG_REGELN:
        w = w.replace(alt, neu)
    if any(ord(c) < 0x370 and c not in " -" for c in w):
        return None              # unmappbarer Rest (b/d/g/h) → lieber Fallback
    if w.endswith("σ"):
        w = w[:-1] + "ς"
    # Neugriechisch braucht einen geschriebenen Akzent — sonst rät die TTS
    if not any(c in w for c in "άέίόύώ"):
        if "αϊ" in w:
            w = w.replace("αϊ", "άι", 1)
        elif "οϊ" in w:
            w = w.replace("οϊ", "όι", 1)
        else:
            for v in "αειουω":
                if v in w:
                    w = w.replace(v, {"α": "ά", "ε": "έ", "ι": "ί",
                                      "ο": "ό", "υ": "ύ", "ω": "ώ"}[v], 1)
                    break
    return w

def teile_fuer_chunk(chunk: str) -> tuple[list[tuple[str, str]], str]:
    """Griechischer Chunk → ([(Teiltext, Sprachcode)], deutscher Sprechtext).

    χ-anlautende Wörter laufen neugriechisch (echtes [x]/[ç]), der Rest
    deutsch; zusammenhängende deutsche Wörter bleiben ein TTS-Aufruf."""
    teile, sprich = [], []
    for w in chunk.split():
        um = translit_wort(w)
        sp = sprechtext(um)[0]
        if um.lower().startswith("ch"):
            ng = nach_neugriechisch(um)
            if ng:
                teile.append((ng, "el"))
                sprich.append(sp)
                continue
            # nicht schreibbar (ü/ευ): deutsches [k] — wie in Chor/Christus
            sp = "k" + sp[2:]
        sprich.append(sp)
        if teile and teile[-1][1] == "de":
            teile[-1] = (teile[-1][0] + " " + sp, "de")
        else:
            teile.append((sp, "de"))
    return teile, " ".join(sprich)

def sprechtext(umschrift: str) -> tuple[str, str]:
    u = UEBERSCHREIBUNGEN.get(umschrift)
    if u is not None:
        return u if isinstance(u, tuple) else (u, "de")
    t = unicodedata.normalize("NFC", umschrift)
    for alt, neu in ERSETZUNGEN:
        t = t.replace(alt, neu)
    # Anlautendes st/sp: ß erzwingt messbar sauberes [s] statt „scht/schp"
    t = re.sub(r"(^|(?<= ))s(?=[tp])", "ß", t)
    # Auslautendes „äh" wird verschluckt → schlichtes „ä" (verifiziert)
    t = re.sub(r"äh($|(?= ))", "ä", t)
    return re.sub(r"[?;·]", "", t).strip(), "de"

# ───────────────────────── TTS-Erzeugung ─────────────────────────
def elevenlabs_mp3(text: str, key: str, lang: str = "de") -> bytes:
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
           f"?output_format=mp3_44100_128")
    body = json.dumps({
        "text": text,
        "model_id": MODELL,
        "language_code": lang,
        "voice_settings": {"stability": 0.85, "similarity_boost": 0.75,
                           "speed": 0.9},
    })
    # curl statt urllib: das python.org-Python hat keine CA-Zertifikate.
    r = subprocess.run(
        ["curl", "-sf", "-X", "POST", url,
         "-H", f"xi-api-key: {key}",
         "-H", "Content-Type: application/json",
         "-d", body],
        check=True, capture_output=True)
    if r.stdout[:2] not in (b"ID", b"\xff\xfb") and b"detail" in r.stdout[:200]:
        raise RuntimeError(f"ElevenLabs-Fehler: {r.stdout[:200]!r}")
    return r.stdout

_TEIL_CACHE: dict[tuple[str, str], bytes] = {}   # Artikel u.ä. nur einmal vertonen

def _teil_mp3(text: str, lang: str, key: str) -> bytes:
    k = (text, lang)
    if k not in _TEIL_CACHE:
        _TEIL_CACHE[k] = elevenlabs_mp3(text, key, lang)
    return _TEIL_CACHE[k]

def erzeuge_m4a(teile: list[tuple[str, str]], ziel: Path, key: str | None) -> str:
    ziel.parent.mkdir(parents=True, exist_ok=True)
    if key:
        mp3 = b"".join(_teil_mp3(t, l, key) for t, l in teile)
        with tempfile.NamedTemporaryFile(suffix=".mp3") as tmp:
            tmp.write(mp3)
            tmp.flush()
            subprocess.run(
                ["afconvert", "-f", "m4af", "-d", "aac", tmp.name, str(ziel)],
                check=True, capture_output=True)
        return "elevenlabs"
    text = " ".join(t for t, _ in teile)
    stimme = "Melina" if teile and teile[0][1] == "el" else SAY_STIMME
    subprocess.run(
        ["say", "-v", stimme, "-r", str(SAY_RATE),
         "-o", str(ziel), "--data-format=aac@44100", text],
        check=True)
    return "say"

def flex_pfad(audio_pfad: str, k: int) -> str:
    return audio_pfad.replace(".m4a", f"_f{k}.m4a")

def vokabel_vertonen(v, audio_pfad: str, basis: Path, key, neu: bool) -> str:
    chunks = chunks_von(v["griechisch"])
    if not chunks:
        return "leer"
    texte = []   # ([(text, lang), ...], ziel-pfad)
    sprich_teile = []
    for k, chunk in enumerate(chunks):
        um = translit(chunk)
        # Überschreibungen greifen auf der Umschrift (z.B. "eimí", "tí?")
        schluessel = um if um in UEBERSCHREIBUNGEN else \
                     (v["umschrift"] if k == 0 and v.get("umschrift") in UEBERSCHREIBUNGEN else None)
        if schluessel is not None:
            text, lang = sprechtext(schluessel)
            teile, sprich = [(text, lang)], text
        elif any(translit_wort(w).lower().startswith("ch") for w in chunk.split()):
            teile, sprich = teile_fuer_chunk(chunk)
        else:
            text, _ = sprechtext(um)
            teile, sprich = [(text, "de")], text
        sprich_teile.append(sprich)
        pfad = audio_pfad if k == 0 else flex_pfad(audio_pfad, k)
        texte.append((teile, pfad))

    v["sprich"] = ", ".join(sprich_teile)
    v["audio"] = audio_pfad
    if len(texte) > 1:
        v["flexAudio"] = [t[1] for t in texte[1:]]
    else:
        v.pop("flexAudio", None)

    stati = []
    for teile, pfad in texte:
        ziel = basis / pfad
        if not neu and ziel.exists() and ziel.stat().st_size > 500:
            stati.append("übersprungen")
            continue
        try:
            stati.append(erzeuge_m4a(teile, ziel, key))
        except Exception as e:
            ziel.unlink(missing_ok=True)
            stati.append(f"FEHLER: {e}")
    if any(s.startswith("FEHLER") for s in stati):
        # kaputte Vokabel → Fallback-TTS in der App, nächster Lauf versucht es erneut
        v.pop("audio", None)
        v.pop("flexAudio", None)
        return next(s for s in stati if s.startswith("FEHLER"))
    if all(s == "übersprungen" for s in stati):
        return "übersprungen"
    return f"{sum(1 for s in stati if s != 'übersprungen')} Chunks"

def generiere(lektion_pfad: Path, key: str | None, neu: bool) -> None:
    daten = json.loads(lektion_pfad.read_text(encoding="utf-8"))
    basis = lektion_pfad.parent.parent  # Projektwurzel (data/ liegt darunter)

    def lauf(vokabeln, pfad_fn):
        with ThreadPoolExecutor(max_workers=3) as pool:
            jobs = {pool.submit(vokabel_vertonen, v, pfad_fn(i, v), basis, key, neu): v
                    for i, v in enumerate(vokabeln)}
            for job, v in jobs.items():
                q = job.result()
                if q != "übersprungen":
                    print(f"    {v['griechisch'][:30]:<32} → „{v['sprich']}“ ({q})", flush=True)

    if "lektionen" in daten:           # Paketformat (Grundwortschatz)
        pid = daten["id"]
        for j, lek in enumerate(daten["lektionen"]):
            print(f"  [{lek['titel']}]")
            lauf(lek["vokabeln"],
                 lambda i, v, j=j: v.get("audio") or f"data/audio/{pid}_{j:02d}_{i:02d}.m4a")
            # nach jeder Lektion sichern → Lauf ist jederzeit abbrechbar
            lektion_pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return
    lauf(daten["vokabeln"], lambda i, v: v.get("audio") or f"data/audio/l1_{i:02d}.m4a")
    lektion_pfad.write_text(
        json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

# ───────────────────────── Validierung ─────────────────────────
ARTIKEL = {"ὁ", "ἡ", "τό", "τὸ", "οἱ", "αἱ", "τά", "τὰ"}

def pruefe(pfade: list[Path]) -> None:
    """Transliterator gegen alle vorhandenen Umschriften validieren."""
    ok = falsch = 0
    for p in pfade:
        daten = json.loads(p.read_text(encoding="utf-8"))
        leks = daten["lektionen"] if "lektionen" in daten else [daten]
        for lek in leks:
            for v in lek["vokabeln"]:
                chunks = chunks_von(v["griechisch"])
                if not chunks:
                    continue
                woerter = [w for w in chunks[0].split() if w not in ARTIKEL]
                meine = translit(" ".join(woerter))
                soll = unicodedata.normalize("NFC", v.get("umschrift", ""))
                if meine == soll:
                    ok += 1
                else:
                    falsch += 1
                    print(f"  ✗ {v['griechisch'][:28]:<30} soll={soll!r:<22} ist={meine!r}")
    print(f"\n{ok} korrekt, {falsch} abweichend ({100*ok/max(ok+falsch,1):.1f} %)")

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pfade = [Path(p) for p in args] or sorted(
        (Path(__file__).parent / "app/data").glob("*.json"))
    pfade = [p for p in pfade if p.name != "index.json"]
    if "--pruefen" in sys.argv:
        pruefe(pfade)
        sys.exit(0)
    key = KEY_DATEI.read_text().strip() if KEY_DATEI.exists() else None
    if not key:
        print(f"Hinweis: {KEY_DATEI} fehlt — nutze macOS-Stimme als Fallback.")
    neu = "--neu" in sys.argv
    for p in pfade:
        print(p.name)
        generiere(p, key, neu)
