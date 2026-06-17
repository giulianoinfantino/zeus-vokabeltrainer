#!/usr/bin/env python3
"""Altgriechisch (polyton) → IPA, deutsche Schulaussprache, mit Betonung & Länge.

Liefert IPA-Strings für SSML <phoneme alphabet="ipa" ph="…"> (Azure/Google TTS):
- Betonung (ˈ) exakt auf der Silbe des griechischen Akzents (Akut/Gravis/Zirkumflex)
- Länge (ː) auf η, ω, ου und zirkumflektierten Vokalen
- Schul-Segmente: θ=t, φ=f, χ=ç/x, ζ=dz, υ=y, ει/αι=aɪ, ευ/οι=ɔʏ, αυ=aʊ, ου=uː
- IPA_OVERRIDE: Hand-Korrekturen (v.a. Vokallänge), die nicht aus der Schreibung
  ableitbar sind. Schlüssel = NFC-Wortform. Mit api/grc_ipa.js synchron halten.

Bewusst NICHT rekonstruiert (keine Aspiraten) — Projektnorm „wie an Schulen gelehrt".
"""
import unicodedata

AKUT, GRAVIS, ZIRK = "́", "̀", "͂"
ASPER, LENIS, IOTA, TREMA = "̔", "̓", "ͅ", "̈"
AKZENTE = {AKUT, GRAVIS, ZIRK}

VOKALE = set("αεηιουω")

# Einzelkonsonanten → IPA (Schulaussprache)
KONS = {
    "β": "b", "γ": "ɡ", "δ": "d", "ζ": "dz", "θ": "t", "κ": "k", "λ": "l",
    "μ": "m", "ν": "n", "ξ": "ks", "π": "p", "ρ": "r", "σ": "s", "ς": "s",
    "τ": "t", "φ": "f", "ψ": "ps",
}

# Diphthonge → (IPA, lang?). DEUTSCHE SCHULAUSSPRACHE: germanisierte Diphthonge
# (ει/αι=[aɪ] „ei", ευ/οι=[ɔʏ] „eu", αυ=[aʊ] „au", ου=[uː]) — passend zum App-
# Versprechen „wie an Schulen gelehrt" und deckungsgleich mit gen_audio.py.
# BEWUSST NICHT erasmisch-gleitend ([ei̯]/[eu̯]); zugleich vermeidet das den
# Gleitlaut-Diakritik ̯ (U+032F), die eleven_v3 uneinheitlich liest.
DIPHTHONG = {
    "αι": ("aɪ", False), "ει": ("aɪ", False), "οι": ("ɔɪ", False),
    "υι": ("yi", False), "αυ": ("aʊ", False), "ευ": ("ɔɪ", False),
    "ηυ": ("ɛːɪ", True), "ου": ("uː", True),
}
# Hinweis: ευ/οι = [ɔɪ] (nicht [ɔʏ]) — [ɔɪ̯] ist gängige IPA für dt. „eu/äu" UND
# eleven_v3 realisiert den ɪ-Gleitlaut zuverlässig, während ʏ zu flachem [ɔ]
# kollabiert (per Allosaurus-Phonerkennung gemessen, 06/2026).
# Einzelvokale → (IPA-kurz, IPA-lang)
VOKAL = {
    "α": ("a", "aː"), "ε": ("ɛ", "ɛː"), "η": ("ɛː", "ɛː"), "ι": ("i", "iː"),
    "ο": ("ɔ", "oː"), "υ": ("y", "yː"), "ω": ("oː", "oː"),
}
FRONT = set("εηιυ")   # für χ → ç (Ich-Laut) nach/vor vorderem Vokal


def _zerlege(wort):
    """NFD → Liste von (basis, set(marks))."""
    out = []
    for ch in unicodedata.normalize("NFD", wort):
        if unicodedata.combining(ch):
            if out:
                out[-1][1].add(ch)
        else:
            out.append([ch.lower(), set()])
    return out


def _nuklei(buchst):
    """Gruppiert zu Silbenkernen: [(start, end, marks, lang, akzent)]."""
    nuk = []
    i = 0
    while i < len(buchst):
        b, m = buchst[i]
        if b in VOKALE:
            # Diphthong? nächster ist ι/υ ohne Trema, aktueller Teil eines Diphthongs
            paar = None
            if i + 1 < len(buchst):
                b2, m2 = buchst[i + 1]
                if (b + b2) in DIPHTHONG and TREMA not in m2:
                    paar = b + b2
            if paar:
                m_all = m | buchst[i + 1][1]
                lang = DIPHTHONG[paar][1] or ZIRK in m_all
                nuk.append((i, i + 2, m_all, lang, bool(m_all & AKZENTE)))
                i += 2
            else:
                lang = (b in "ηω") or (ZIRK in m) or (IOTA in m)
                nuk.append((i, i + 1, m, lang, bool(m & AKZENTE)))
                i += 1
        else:
            i += 1
    return nuk


def _kons_ipa(buchst, i, folgevokal):
    """Konsonant an Position i → IPA (mit γ-Nasal, χ-Allophon, σ→z prävokalisch)."""
    b = buchst[i][0]
    if b == "γ" and i + 1 < len(buchst) and buchst[i + 1][0] in "γκχξ":
        return "ŋ"
    if b == "χ":
        return "ç" if (folgevokal in FRONT) else "x"
    if b in ("σ", "ς"):
        return "s"                      # σ im Erasmischen IMMER stimmlos [s] (nie [z])
    if b == "ρ" and ASPER in buchst[i][1]:
        return "r"
    return KONS.get(b, "")


IPA_OVERRIDE = {
    "πράττω": "ˈpraːttoː",   # Wurzel-langes α (πρᾱγ-/πρᾱκ-)
}


def grc_to_ipa(wort):
    """Ein griechisches Wort → IPA mit ˈ (Betonung) und ː (Länge)."""
    ov = IPA_OVERRIDE.get(unicodedata.normalize("NFC", wort))
    if ov is not None:
        return ov
    buchst = _zerlege(wort)
    if not buchst:
        return ""
    nuk = _nuklei(buchst)
    if not nuk:
        return ""
    # betonte Silbe = Kern mit Akzentmark (sonst keiner)
    stress_kern = next((k for k, n in enumerate(nuk) if n[4]), None)
    nuk_start = {n[0] for n in nuk}      # Positionen, an denen ein Kern beginnt

    # Anlaut-h bei Spiritus asper auf dem ersten Vokal
    teile = []
    erstes_v = buchst[nuk[0][0]]
    h_prefix = ASPER in erstes_v[1] or (len(erstes_v[1] & {ASPER}) > 0)
    # (asper kann auf 2. Diphthong-Buchstaben liegen → schon in marks gemerged? nein,
    #  asper steht auf dem ersten Vokal; bei Diphthong auf dem zweiten — prüfe beide)
    for a, b in (nuk[0][0], nuk[0][1] - 1), :
        pass

    # IPA pro Buchstabe aufbauen; ˈ vor den Onset-Konsonanten der betonten Silbe
    out = []
    kern_index = -1
    i = 0
    # Vorab: für jeden Kern-Start die Onset-Konsonanten (zwischen vorigem Kernende und hier)
    while i < len(buchst):
        b, m = buchst[i]
        if i in nuk_start:
            kern_index += 1
            kern = nuk[kern_index]
            # Onset: Konsonanten direkt vor diesem Kern (ab letztem ausgegebenen Vokalende)
            # ˈ einfügen vor Onset, falls dies die betonte Silbe ist
            if kern_index == stress_kern:
                # finde Onset-Länge: Konsonanten unmittelbar vor i
                j = len(out)
                # ˈ vor den zuletzt angehängten Onset-Konsonanten dieser Silbe:
                # wir haben Onset-Konsonanten schon ausgegeben → ˈ dort einsetzen
                # Stattdessen: ˈ jetzt direkt vor den Nukleus, hinter evtl. Onset.
                pass
            # Nukleus-IPA
            kurz_lang = 1 if kern[3] else 0
            seg = buchst[kern[0]:kern[1]]
            if kern[1] - kern[0] == 2:
                ipa = DIPHTHONG[seg[0][0] + seg[1][0]][0]
            else:
                ipa = VOKAL[seg[0][0]][kurz_lang]
                if IOTA in kern[2] and "ː" not in ipa:
                    ipa += "ː"
            out.append(("V", ipa, kern_index))
            i = kern[1]
        else:
            fv = buchst[i + 1][0] if i + 1 < len(buchst) else ""
            ci = _kons_ipa(buchst, i, fv)
            if ci:
                out.append(("C", ci, None))
            i += 1

    # h-Prefix (Spiritus asper) — prüfe Marks beider ersten Vokalbuchstaben
    asper = False
    for p in range(nuk[0][0], nuk[0][1]):
        if ASPER in buchst[p][1]:
            asper = True
    # ˈ-Platzierung: vor die Onset-Konsonanten der betonten Silbe
    res = ""
    if asper:
        res += "h"
    # finde Index in out, wo betonter Nukleus liegt
    v_positions = [idx for idx, t in enumerate(out) if t[0] == "V"]
    if stress_kern is not None and stress_kern < len(v_positions):
        vpos = v_positions[stress_kern]
        # Onset = unmittelbar vorausgehende C-Gruppe
        onset = vpos
        while onset - 1 >= 0 and out[onset - 1][0] == "C":
            onset -= 1
        # Onset-Regel: einzelner Konsonant = Onset; bei Cluster nur Stop+Liquid
        # (z.B. ɡl, xr, tr, pr) gemeinsam zur betonten Silbe, sonst ˈ vor letztem C.
        LIQ = {"l", "r"}
        if vpos - onset > 1:
            if vpos - onset == 2 and out[vpos - 1][1] in LIQ and out[vpos - 2][1] not in LIQ:
                onset = vpos - 2          # Stop+Liquid zusammen
            else:
                onset = vpos - 1
        for idx, t in enumerate(out):
            if idx == onset:
                res += "ˈ"
            res += t[1]
    else:
        res += "".join(t[1] for t in out)
    return res


def grc_to_ipa_parts(wort):
    """Ein Wort → (vor, betont, nach) als IPA-Teilstrings.

    Die betonte Silbe (Onset-Konsonanten + Akzent-Nukleus) wird separiert,
    damit sie per SSML <prosody> angehoben werden kann (Azure ignoriert ˈ).
    Rückgabe ohne ˈ/Längenverlust; ː bleibt erhalten.
    """
    buchst = _zerlege(wort)
    if not buchst:
        return ("", "", "")
    nuk = _nuklei(buchst)
    if not nuk:
        return ("", "", "")
    stress_kern = next((k for k, n in enumerate(nuk) if n[4]), None)
    nuk_start = {n[0] for n in nuk}

    # Liste aus ("V"/"C", ipa) wie in grc_to_ipa, plus h-Prefix
    asper = any(ASPER in buchst[p][1] for p in range(nuk[0][0], nuk[0][1]))
    out = []
    kern_index = -1
    i = 0
    while i < len(buchst):
        b, m = buchst[i]
        if i in nuk_start:
            kern_index += 1
            kern = nuk[kern_index]
            seg = buchst[kern[0]:kern[1]]
            if kern[1] - kern[0] == 2:
                ipa = DIPHTHONG[seg[0][0] + seg[1][0]][0]
            else:
                ipa = VOKAL[seg[0][0]][1 if kern[3] else 0]
                if IOTA in kern[2] and "ː" not in ipa:
                    ipa += "ː"
            out.append(("V", ipa, kern_index))
            i = kern[1]
        else:
            fv = buchst[i + 1][0] if i + 1 < len(buchst) else ""
            ci = _kons_ipa(buchst, i, fv)
            if ci:
                out.append(("C", ci, None))
            i += 1

    v_positions = [idx for idx, t in enumerate(out) if t[0] == "V"]
    if stress_kern is None or stress_kern >= len(v_positions):
        joined = ("h" if asper else "") + "".join(t[1] for t in out)
        return (joined, "", "")

    vpos = v_positions[stress_kern]
    onset = vpos
    while onset - 1 >= 0 and out[onset - 1][0] == "C":
        onset -= 1
    LIQ = {"l", "r"}
    if vpos - onset > 1:
        if vpos - onset == 2 and out[vpos - 1][1] in LIQ and out[vpos - 2][1] not in LIQ:
            onset = vpos - 2
        else:
            onset = vpos - 1
    vor = ("h" if asper else "") + "".join(t[1] for t in out[:onset])
    betont = "".join(t[1] for t in out[onset:vpos + 1])
    nach = "".join(t[1] for t in out[vpos + 1:])
    return (vor, betont, nach)


def chunk_to_ipa(chunk):
    """Mehrwort-Chunk → Liste von IPA-Strings (pro Wort, mit ˈ — für Referenz)."""
    return [grc_to_ipa(w) for w in chunk.split() if w]


def chunk_to_parts(chunk):
    """Mehrwort-Chunk → Liste von (vor, betont, nach) pro Wort."""
    return [grc_to_ipa_parts(w) for w in chunk.split() if w]


if __name__ == "__main__":
    import sys
    proben = ["ἄνθρωπος", "ἀρετή", "βασιλεύς", "εἰρήνη", "καλός",
              "παιδεία", "σοφία", "θεός", "ὁ θεός", "τοῦ θεοῦ",
              "ἡ γλῶσσα", "φέρω", "ἡ χείρ", "χαῖρε", "ἀγαθός",
              "ἡ ψυχή", "ὁ χρόνος", "ἡ ἡμέρα", "πόλεμος"]
    for g in (sys.argv[1:] or proben):
        print(f"{g:16} → {' '.join(chunk_to_ipa(g))}")
