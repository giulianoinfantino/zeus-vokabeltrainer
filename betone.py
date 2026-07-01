#!/usr/bin/env python3
"""Hebt die betonte Silbe jeder Audiodatei lautstärkemäßig an (sanfte Glocke).

eleven_v3 setzt das IPA-Betonungszeichen ˈ kaum als Lautstärke um → der Akzent
klingt zu leise. Darum nachträglich: betonte Silbe lauter mit weicher Cosinus-
Glocke (kein harter Sprung → natürlich). Silbenposition aus grc_ipa (Akzent-
Nukleus), Zeitfenster proportional. Vom Nutzer/Experten als „gut" bestätigt.

Idempotent: jede Datei nur einmal (Marker app/data/audio/.boosted.json). Nach
erneutem Vertonen (gen_audio) sind neue Dateien nicht im Marker → werden beim
nächsten Lauf verstärkt; schon verstärkte werden übersprungen (kein Doppeln).
"""
import json, glob, os, subprocess, tempfile, wave
import numpy as np
import grc_ipa, gen_audio

ROOT = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(ROOT, "app")
MARKER = os.path.join(APP, "data/audio/.boosted.json")
GAIN = 1.5   # ~+3,5 dB Spitze auf der betonten Silbe


def stress(chunk):
    nuk = grc_ipa._nuklei(grc_ipa._zerlege(chunk))
    return next((k for k, n in enumerate(nuk) if n[4]), None), len(nuk)


def boost_file(rel, chunk):
    p = os.path.join(APP, rel)
    if not os.path.exists(p):
        return False
    s, N = stress(chunk)
    if s is None or N == 0:
        return False
    with tempfile.NamedTemporaryFile(suffix=".wav") as w:
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16", p, w.name], check=True, capture_output=True)
        ww = wave.open(w.name, "rb")
        ch, sr = ww.getnchannels(), ww.getframerate()
        a = np.frombuffer(ww.readframes(ww.getnframes()), np.int16).astype(np.float32)
        ww.close()
    mono = a.reshape(-1, ch) if ch > 1 else a.reshape(-1, 1)
    n = mono.shape[0]
    c = (s + 0.5) / N * n
    halb = 0.85 / N * n
    idx = np.arange(n)
    bell = np.cos(np.clip((idx - c) / halb, -1, 1) * np.pi) * 0.5 + 0.5   # weiche Glocke, 0 an den Rändern
    env = (1 + (GAIN - 1) * bell).reshape(-1, 1)
    out = np.clip(mono * env, -32768, 32767).astype(np.int16)
    with tempfile.NamedTemporaryFile(suffix=".wav") as w:
        ww = wave.open(w.name, "wb")
        ww.setnchannels(ch); ww.setsampwidth(2); ww.setframerate(sr)
        ww.writeframes(out.tobytes()); ww.close()
        subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", w.name, p], check=True, capture_output=True)
    return True


def main():
    done = set()
    if os.path.exists(MARKER):
        try:
            done = set(json.load(open(MARKER)))
        except Exception:
            done = set()
    cnt = skip = 0
    for f in sorted(glob.glob(os.path.join(APP, "data/*.json"))):
        if f.endswith("index.json"):
            continue
        d = json.load(open(f, encoding="utf-8"))
        for lek in d.get("lektionen", [d]):
            for v in lek.get("vokabeln", []):
                if not v.get("audio"):
                    continue
                chunks = gen_audio.chunks_von(v["griechisch"])
                files = [v["audio"]] + (v.get("flexAudio") or [])
                for k, rel in enumerate(files):
                    if k >= len(chunks):
                        break
                    if rel in done:
                        skip += 1
                        continue
                    if boost_file(rel, chunks[k]):
                        done.add(rel)
                        cnt += 1
        json.dump(sorted(done), open(MARKER, "w"))
    print(f"verstärkt: {cnt}, übersprungen (schon): {skip}")


if __name__ == "__main__":
    main()
