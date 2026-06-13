#!/usr/bin/env python3
"""A/B-Test: ElevenLabs v3 mit INLINE-IPA vs. Azure-Phoneme / aktueller turbo-Cache.

Frage: Liefert eleven_v3 die ElevenLabs-Klangqualität UND die phonemische
Kontrolle (Betonung ˈ, Länge ː), die turbo_v2_5 ignoriert?

v3-Trick: IPA wird NICHT per <phoneme>-SSML übergeben (das kann nur Flash v2,
und nur Englisch), sondern direkt im Text in Schrägstriche gesetzt:
    /basiˈleu̯s/
v3 unterstützt das nativ über 70+ Sprachen (~80–90 % konsistent). Da jedes Wort
genau 1× in den Blob-Cache vertont wird, ist die Nicht-Determiniertheit
unkritisch: einmal anhören, die schlechten 10–20 % neu erzeugen.

Die IPA kommt aus grc_ipa.py (derzeit ERASMISCH — bewusst noch nicht auf
Schulaussprache umgestellt; erst hören, ob v3 überhaupt taugt).

Key aus ~/.config/zeus/elevenlabs.key (wie gen_audio.py).

Start:
  python3 eleven_v3_test.py            # 10 Probewörter → ~/Desktop/zeus_v3_test
  python3 eleven_v3_test.py "ἀρετή" …  # eigene Wörter
"""
import json
import subprocess
import sys
from pathlib import Path

from grc_ipa import grc_to_ipa

KEY_DATEI = Path.home() / ".config/zeus/elevenlabs.key"
VOICE_ID = "MTTjXkEpZepLTqO0xH0f"   # Marlena — gleiche Stimme wie gen_audio.py
MODELL = "eleven_v3"


def ipa_text(griechisch_chunk: str) -> str:
    """Chunk → Sprechtext für v3: jedes Wort als /IPA/ (Betonung/Länge inklusive)."""
    teile = []
    for w in griechisch_chunk.split():
        ipa = grc_to_ipa(w)
        teile.append(f"/{ipa}/" if ipa else w)
    return " ".join(teile)


def v3_mp3(griechisch_chunk: str, key: str) -> bytes:
    text = ipa_text(griechisch_chunk)
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
           f"?output_format=mp3_44100_128")
    body = json.dumps({
        "text": text,
        "model_id": MODELL,
        # kein language_code: v3 erkennt die Sprache selbst; IPA ist sprachneutral
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    })
    r = subprocess.run(
        ["curl", "-sf", "-X", "POST", url,
         "-H", f"xi-api-key: {key}",
         "-H", "Content-Type: application/json",
         "-d", body],
        capture_output=True)
    if r.returncode != 0 or (r.stdout[:2] not in (b"ID", b"\xff\xfb")
                             and b"detail" in r.stdout[:300]):
        raise RuntimeError(f"v3-Fehler (rc={r.returncode}): "
                           f"{r.stderr[:200]!r} body={r.stdout[:300]!r}")
    return r.stdout


if __name__ == "__main__":
    proben = ["ἄνθρωπος", "ἀρετή", "βασιλεύς", "εἰρήνη", "καλός",
              "παιδεία", "σοφία", "θεός", "ἡ γλῶσσα", "χαῖρε"]
    woerter = sys.argv[1:] or proben
    if not KEY_DATEI.exists():
        sys.exit(f"Key fehlt: {KEY_DATEI}")
    key = KEY_DATEI.read_text().strip()
    out = Path.home() / "Desktop/zeus_v3_test"
    out.mkdir(parents=True, exist_ok=True)
    for g in woerter:
        name = "".join(c for c in g if c.isalnum())[:16] or "wort"
        try:
            (out / f"{name}.mp3").write_bytes(v3_mp3(g, key))
            print(f"{g:16} {ipa_text(g):24} → {name}.mp3 ✓")
        except Exception as e:
            print(f"{g:16} FEHLER: {e}")
    print("Dateien in", out)
