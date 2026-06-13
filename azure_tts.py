#!/usr/bin/env python3
"""Azure Neural TTS mit IPA-Phonemen — präzise Betonung & Vokallänge.

Warum Azure statt ElevenLabs: ElevenLabs (turbo_v2_5) ignoriert <phoneme>-Tags
(empirisch verifiziert → Stille). Azure de-DE Neural-Stimmen unterstützen
<phoneme alphabet="ipa" ph="…"> zuverlässig — damit kommt die griechische
Betonung (ˈ) und Länge (ː) aus grc_ipa.py exakt in die Audioausgabe.

Key/Region aus ~/.config/zeus/azure.key  (zwei Zeilen: KEY, dann REGION),
oder Umgebungsvariablen AZURE_TTS_KEY / AZURE_TTS_REGION.

Start:
  python3 azure_tts.py            # erzeugt Testwörter nach ~/Desktop/zeus_azure_test
  python3 azure_tts.py "ἀρετή" …  # eigene Wörter
"""
import os
import subprocess
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

from grc_ipa import chunk_to_ipa, chunk_to_parts

KEY_DATEI = Path.home() / ".config/zeus/azure.key"
# de-DE-SeraphinaMultilingualNeural: flachste Deklination → klarste Endbetonung
# (gemessen vs. Katja/Amala/Louisa). Multilingual stimmt auch für gr. Laute.
VOICE = "de-DE-SeraphinaMultilingualNeural"
OUTFMT = "audio-24khz-48kbitrate-mono-mp3"


def _key_region():
    k = os.environ.get("AZURE_TTS_KEY")
    r = os.environ.get("AZURE_TTS_REGION")
    if k and r:
        return k, r
    if KEY_DATEI.exists():
        zeilen = [z.strip() for z in KEY_DATEI.read_text().splitlines() if z.strip()]
        if len(zeilen) >= 2:
            return zeilen[0], zeilen[1]
    raise RuntimeError(f"Azure-Key fehlt: {KEY_DATEI} (Zeile 1 KEY, Zeile 2 REGION) "
                       "oder AZURE_TTS_KEY/AZURE_TTS_REGION setzen.")


def _ph(ipa):
    return f'<phoneme alphabet="ipa" ph="{escape(ipa)}">·</phoneme>' if ipa else ""

def wort_ssml(wort):
    """Ein Wort → SSML: Segmente+Länge per <phoneme>; Betonung erzwungen, da Azure
    das IPA-ˈ ignoriert — betonte Silbe anheben (Konfig A). Unbetonte bleiben in
    normaler Lautstärke (sauberer als Absenken; Betonung trotzdem hörbar)."""
    vor, betont, nach = next(iter(chunk_to_parts(wort)), ("", "", ""))
    if not betont:                       # kein Akzent (Proklitika o.ä.)
        return _ph(vor) or escape(wort)
    return (_ph(vor)
            + f'<prosody pitch="high" volume="loud" rate="slow">{_ph(betont)}</prosody>'
            + _ph(nach))

def ssml_fuer_chunk(griechisch_chunk, voice=VOICE):
    """Griechischer Chunk → SSML mit korrekter Betonung (prosody) & Länge (IPA)."""
    inhalt = " ".join(wort_ssml(w) for w in griechisch_chunk.split() if w)
    return (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            f'xml:lang="de-DE"><voice name="{voice}">{inhalt}</voice></speak>')


def azure_mp3(griechisch_chunk, key=None, region=None, voice=VOICE):
    if key is None or region is None:
        key, region = _key_region()
    ssml = ssml_fuer_chunk(griechisch_chunk, voice)
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    r = subprocess.run(
        ["curl", "-sf", "-X", "POST", url,
         "-H", f"Ocp-Apim-Subscription-Key: {key}",
         "-H", "Content-Type: application/ssml+xml",
         "-H", f"X-Microsoft-OutputFormat: {OUTFMT}",
         "-H", "User-Agent: zeus-vokabeltrainer",
         "--data-binary", ssml.encode("utf-8")],
        capture_output=True)
    if r.returncode != 0 or len(r.stdout) < 800:
        raise RuntimeError(f"Azure-Fehler (rc={r.returncode}): {r.stderr[:200]!r} body={r.stdout[:200]!r}")
    return r.stdout


def erzeuge_m4a(griechisch_chunk, ziel: Path, key=None, region=None):
    """Chunk → m4a (für die App), via Azure-MP3 + afconvert."""
    mp3 = azure_mp3(griechisch_chunk, key, region)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".mp3") as tmp:
        tmp.write(mp3); tmp.flush()
        subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", tmp.name, str(ziel)],
                       check=True, capture_output=True)


if __name__ == "__main__":
    import sys
    proben = ["ἄνθρωπος", "ἀρετή", "βασιλεύς", "εἰρήνη", "καλός",
              "παιδεία", "σοφία", "θεός", "ἡ γλῶσσα", "χαῖρε"]
    woerter = sys.argv[1:] or proben
    out = Path.home() / "Desktop/zeus_azure_test"; out.mkdir(parents=True, exist_ok=True)
    key, region = _key_region()
    for g in woerter:
        ipa = " ".join(chunk_to_ipa(g))
        name = "".join(c for c in g if c.isalnum())[:16] or "wort"
        try:
            (out / f"{name}.mp3").write_bytes(azure_mp3(g, key, region))
            print(f"{g:16} [{ipa}]  → {name}.mp3 ✓")
        except Exception as e:
            print(f"{g:16} FEHLER: {e}")
    print("Dateien in", out)
