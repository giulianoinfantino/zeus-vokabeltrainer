#!/usr/bin/env python3
"""Erasmische Audio-Generierung für den Zeus-Vokabeltrainer.

Erzeugt aus der Umschrift jeder Vokabel einen deutsch-phonetischen
Sprechtext (erasmische Schulaussprache) und generiert damit die
m4a-Dateien — bevorzugt über ElevenLabs, sonst über die macOS-
Sprachsynthese (`say`) als Offline-Fallback.

Der ElevenLabs-Key wird aus ~/.config/zeus/elevenlabs.key gelesen
(bewusst außerhalb des App-Ordners: der lokale Server liefert alle
Dateien im Projektordner aus). Audio wird einmalig generiert und als
Datei abgelegt — es entstehen keine laufenden Kosten.

Der Sprechtext wird zusätzlich als Feld "sprich" in die Lektions-JSON
geschrieben, damit der speechSynthesis-Fallback der App denselben Text
mit einer deutschen Stimme sprechen kann.

Start:  python3 gen_audio.py [data/lektionN.json ...]
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

KEY_DATEI = Path.home() / ".config/zeus/elevenlabs.key"
VOICE_ID = "MTTjXkEpZepLTqO0xH0f"  # Marlena — deutsche Muttersprachlerin (Library, Starter-Plan nötig)
MODELL = "eleven_turbo_v2_5"        # unterstützt language_code-Erzwingung
SAY_STIMME = "Sandy (German (Germany))"
SAY_RATE = 160

# Erasmische Schulaussprache, in deutscher Orthographie ausgedrückt.
# Reihenfolge wichtig: Digraphen vor Einzelzeichen.
ERSETZUNGEN = [
    ("ou", "u"), ("oú", "ú"), ("oû", "uh"),   # ου = langes u
    # Akzente auf Diphthongen zerbrechen die TTS-Aussprache (verifiziert):
    ("aí", "ai"), ("eí", "ei"), ("oí", "oi"), ("aú", "au"), ("eú", "eu"),
    ("rh", "r"),
    ("th", "t"),                                # θ = t (Schulaussprache)
    ("ph", "f"),                                # φ = f
    ("ō", "oh"), ("ē", "eh"), ("ī", "ih"),     # Längen ausschreiben
    ("y", "ü"), ("ý", "ü"),                    # υ = ü (Akzent stört die TTS)
]

# Handkorrekturen, wo die automatische Regel nicht reicht.
# Wert: Sprechtext oder (Sprechtext, Sprachcode). Per STT-Rücktranskription
# verifiziert: "chaire" wird als "Schere" gesprochen, "uh"/"tih" werden
# missdeutet. Bei οὔ und τί deckt sich die neugriechische Aussprache mit
# der erasmischen — diese werden daher griechisch generiert.
UEBERSCHREIBUNGEN = {
    "eimí": "eimii",          # Endbetonung erzwingen (Standard wäre EI-mi)
    "chaíre": "kaire",
    "naí": "nai",
    "allá": "allah",
    "oú": ("ου.", "el"),
    "eû ge": "eu geh",
    "tí?": ("τι", "el"),
}


def sprechtext(umschrift: str) -> tuple[str, str]:
    u = UEBERSCHREIBUNGEN.get(umschrift)
    if u is not None:
        return u if isinstance(u, tuple) else (u, "de")
    t = umschrift
    for alt, neu in ERSETZUNGEN:
        t = t.replace(alt, neu)
    # Anlautendes ch wird von deutscher TTS als „sch" gesprochen → k
    # (Erasmus-Kompromiss, verifiziert: „cheir" → „Scheier", „kaire" ✓)
    t = re.sub(r"(^|(?<= ))ch", "k", t)
    # Anlautendes st/sp: ß erzwingt messbar sauberes [s] statt „scht/schp"
    t = re.sub(r"(^|(?<= ))s(?=[tp])", "ß", t)
    return re.sub(r"[?;·]", "", t).strip(), "de"


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


def erzeuge_m4a(text: str, lang: str, ziel: Path, key: str | None) -> str:
    ziel.parent.mkdir(parents=True, exist_ok=True)
    if key:
        mp3 = elevenlabs_mp3(text, key, lang)
        with tempfile.NamedTemporaryFile(suffix=".mp3") as tmp:
            tmp.write(mp3)
            tmp.flush()
            subprocess.run(
                ["afconvert", "-f", "m4af", "-d", "aac", tmp.name, str(ziel)],
                check=True, capture_output=True)
        return "elevenlabs"
    stimme = "Melina" if lang == "el" else SAY_STIMME
    subprocess.run(
        ["say", "-v", stimme, "-r", str(SAY_RATE),
         "-o", str(ziel), "--data-format=aac@44100", text],
        check=True)
    return "say"


def vokabel_vertonen(v, audio_pfad: str, basis: Path, key) -> str:
    text, lang = sprechtext(v["umschrift"])
    v["sprich"] = text
    v["audio"] = audio_pfad
    ziel = basis / audio_pfad
    if ziel.exists() and ziel.stat().st_size > 500:
        return "übersprungen"
    try:
        return erzeuge_m4a(text, lang, ziel, key)
    except Exception as e:
        v.pop("audio", None)   # kaputter Eintrag → Fallback-TTS, nächster Lauf versucht es erneut
        ziel.unlink(missing_ok=True)
        return f"FEHLER: {e}"


def generiere(lektion_pfad: Path, key: str | None) -> None:
    daten = json.loads(lektion_pfad.read_text(encoding="utf-8"))
    basis = lektion_pfad.parent.parent  # Projektwurzel (data/ liegt darunter)
    if "lektionen" in daten:           # Paketformat (Grundwortschatz)
        pid = daten["id"]
        for j, lek in enumerate(daten["lektionen"]):
            print(f"  [{lek['titel']}]")
            for i, v in enumerate(lek["vokabeln"]):
                pfad = v.get("audio") or f"data/audio/{pid}_{j:02d}_{i:02d}.m4a"
                q = vokabel_vertonen(v, pfad, basis, key)
                if q != "übersprungen":
                    print(f"    {v['griechisch'][:24]:<26} → „{v['sprich']}“ ({q})", flush=True)
            # nach jeder Lektion sichern → Lauf ist jederzeit abbrechbar
            lektion_pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return
    for i, v in enumerate(daten["vokabeln"]):
        pfad = v.get("audio") or f"data/audio/l1_{i:02d}.m4a"
        q = vokabel_vertonen(v, pfad, basis, key)
        if q != "übersprungen":
            print(f"  {v['griechisch'][:24]:<26} → „{v['sprich']}“ ({q})", flush=True)
    lektion_pfad.write_text(
        json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    key = KEY_DATEI.read_text().strip() if KEY_DATEI.exists() else None
    if not key:
        print(f"Hinweis: {KEY_DATEI} fehlt — nutze macOS-Stimme als Fallback.")
    pfade = [Path(p) for p in sys.argv[1:]] or sorted(
        (Path(__file__).parent / "data").glob("lektion*.json")
    )
    for p in pfade:
        print(p.name)
        generiere(p, key)
