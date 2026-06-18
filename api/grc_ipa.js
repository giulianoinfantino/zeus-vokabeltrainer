// Altgriechisch (polyton) → IPA, deutsche Schulaussprache (erasmisch), mit
// Betonung (ˈ) und Länge (ː). 1:1-JS-Port von grc_ipa.py — bei JEDER Änderung
// BEIDE synchron halten und per `node api/_grc_ipa_test.mjs` gegen Python prüfen.
//
// Liefert IPA-Strings für eleven_v3 Inline-IPA (/…/). Schulaussprache:
// θ=t, φ=f, χ=ç/x, ζ=dz, υ=y; ει/αι=[aɪ], ευ/οι=[ɔɪ], αυ=[aʊ], ου=[uː];
// Spiritus asper = [h]. Diphthonge germanisiert (Wahl A, vgl. grc_ipa.py).
//
// IPA_OVERRIDE: Hand-Korrekturen für Fälle, die der Algorithmus nicht aus der
// Schreibung ableiten kann (v.a. Vokallänge bei α/ι/υ, z.B. wurzel-langes α).
// Schlüssel = NFC-Wortform. BEIDE Dateien (js + py) synchron halten.

const AKUT = '́', GRAVIS = '̀', ZIRK = '͂';
const ASPER = '̔', IOTA = 'ͅ', TREMA = '̈';
const AKZENTE = new Set([AKUT, GRAVIS, ZIRK]);
const VOKALE = new Set('αεηιουω');

const KONS = {
  β: 'b', γ: 'ɡ', δ: 'd', ζ: 'dz', θ: 't', κ: 'k', λ: 'l', μ: 'm', ν: 'n',
  ξ: 'ks', π: 'p', ρ: 'r', σ: 's', ς: 's', τ: 't', φ: 'f', ψ: 'ps',
};
const DIPHTHONG = {
  αι: ['aɪ', false], ει: ['aɪ', false], οι: ['ɔɪ', false], υι: ['yi', false],
  αυ: ['aʊ', false], ευ: ['ɔɪ', false], ηυ: ['ɛːɪ', true], ου: ['uː', true],
};
const VOKAL = {
  α: ['a', 'aː'], ε: ['ɛ', 'ɛː'], η: ['ɛː', 'ɛː'], ι: ['i', 'iː'],
  ο: ['ɔ', 'oː'], υ: ['y', 'yː'], ω: ['oː', 'oː'],
};
const FRONT = new Set('εηιυ');

// Hand-Korrekturen (Vokallänge etc.), die nicht aus der Schreibung ableitbar sind.
const IPA_OVERRIDE = {
  'πράττω': 'ˈpraːttoː',   // Wurzel-langes α (πρᾱγ-/πρᾱκ-)
};

const istKombi = (c) => { const n = c.codePointAt(0); return n >= 0x300 && n <= 0x36f; };
const hatAkzent = (marks) => { for (const a of AKZENTE) if (marks.has(a)) return true; return false; };

// NFD → Liste von [basis, Set(marks)]
function zerlege(wort) {
  const out = [];
  for (const ch of wort.normalize('NFD')) {
    if (istKombi(ch)) { if (out.length) out[out.length - 1][1].add(ch); }
    else out.push([ch.toLowerCase(), new Set()]);
  }
  return out;
}

// Silbenkerne: [start, end, marks, lang, akzent]
function nuklei(b) {
  const nuk = [];
  let i = 0;
  while (i < b.length) {
    const [base, m] = b[i];
    if (VOKALE.has(base)) {
      let paar = null;
      if (i + 1 < b.length) {
        const [b2, m2] = b[i + 1];
        if (DIPHTHONG[base + b2] && !m2.has(TREMA)) paar = base + b2;
      }
      if (paar) {
        const mAll = new Set([...m, ...b[i + 1][1]]);
        const lang = DIPHTHONG[paar][1] || mAll.has(ZIRK);
        nuk.push([i, i + 2, mAll, lang, hatAkzent(mAll)]);
        i += 2;
      } else {
        const lang = 'ηω'.includes(base) || m.has(ZIRK) || m.has(IOTA);
        nuk.push([i, i + 1, m, lang, hatAkzent(m)]);
        i += 1;
      }
    } else i += 1;
  }
  return nuk;
}

function konsIpa(b, i, folgevokal) {
  const base = b[i][0];
  if (base === 'γ' && i + 1 < b.length && 'γκχξ'.includes(b[i + 1][0])) return 'ŋ';
  if (base === 'χ') return FRONT.has(folgevokal) ? 'ç' : 'x';
  if (base === 'σ' || base === 'ς') return 's';
  if (base === 'ρ' && b[i][1].has(ASPER)) return 'r';
  return KONS[base] || '';
}

// Ein griechisches Wort → IPA mit ˈ (Betonung) und ː (Länge).
export function grcToIpa(wort) {
  const ov = IPA_OVERRIDE[wort.normalize('NFC')];
  if (ov !== undefined) return ov;
  const b = zerlege(wort);
  if (!b.length) return '';
  const nuk = nuklei(b);
  if (!nuk.length) return '';
  let stressKern = null;
  for (let k = 0; k < nuk.length; k++) if (nuk[k][4]) { stressKern = k; break; }
  const nukStart = new Set(nuk.map((n) => n[0]));

  const out = []; // ['V'|'C', ipa]
  let kernIndex = -1, i = 0;
  while (i < b.length) {
    if (nukStart.has(i)) {
      kernIndex += 1;
      const kern = nuk[kernIndex];
      const seg = b.slice(kern[0], kern[1]);
      let ipa;
      if (kern[1] - kern[0] === 2) {
        ipa = DIPHTHONG[seg[0][0] + seg[1][0]][0];
      } else {
        ipa = VOKAL[seg[0][0]][kern[3] ? 1 : 0];
        if (kern[2].has(IOTA) && !ipa.includes('ː')) ipa += 'ː';
      }
      out.push(['V', ipa]);
      i = kern[1];
    } else {
      const fv = i + 1 < b.length ? b[i + 1][0] : '';
      const ci = konsIpa(b, i, fv);
      if (ci) out.push(['C', ci]);
      i += 1;
    }
  }

  // Hiatus: Glottisschlag ʔ zwischen zwei direkt aufeinanderfolgenden Vokalen
  // (eleven_v3 verschluckt sonst den ersten/betonten Vokal). Experten-Korrektur.
  // ... aber NICHT nach kurzem ι/υ (Gleitlaut → Artefakt „Heli-a-os") und NICHT nach
  // einem Diphthong (endet auf ɪ/ʊ → trennt schon selbst; ʔ zerstört z.B. βασιλεύω).
  { const GLEIT = new Set(['i', 'iː', 'y', 'yː']); const hi = []; for (let i = 0; i < out.length; i++) { const prev = i ? out[i - 1][1] : ''; if (i > 0 && out[i][0] === 'V' && out[i - 1][0] === 'V' && !GLEIT.has(prev) && !/[ɪʊ]$/.test(prev)) hi.push(['C', 'ʔ']); hi.push(out[i]); } out.length = 0; out.push(...hi); }

  let asper = false;
  for (let p = nuk[0][0]; p < nuk[0][1]; p++) if (b[p][1].has(ASPER)) asper = true;
  let res = asper ? 'h' : '';

  const vPos = [];
  out.forEach((t, idx) => { if (t[0] === 'V') vPos.push(idx); });
  if (stressKern !== null && stressKern < vPos.length) {
    const vpos = vPos[stressKern];
    let onset = vpos;
    while (onset - 1 >= 0 && out[onset - 1][0] === 'C') onset -= 1;
    const LIQ = new Set(['l', 'r']);
    if (vpos - onset > 1) {
      if (vpos - onset === 2 && LIQ.has(out[vpos - 1][1]) && !LIQ.has(out[vpos - 2][1])) onset = vpos - 2;
      else onset = vpos - 1;
    }
    for (let idx = 0; idx < out.length; idx++) {
      if (idx === onset) res += 'ˈ';
      res += out[idx][1];
    }
  } else {
    res += out.map((t) => t[1]).join('');
  }
  return res;
}

// Mehrwort-Chunk → v3-Sprechtext: jedes Wort als /IPA/.
export function ipaChunk(chunk) {
  return chunk.split(/\s+/).filter(Boolean).map((w) => `/${grcToIpa(w)}/`).join(' ');
}
