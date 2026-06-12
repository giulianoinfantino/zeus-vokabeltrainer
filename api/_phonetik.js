// Aussprache-Pipeline (deutsche Schulaussprache, erasmisch) — JS-Port der in
// gen_audio.py per STT validierten Regeln. Eingabe ist die wissenschaftliche
// Umschrift (z.B. "ho theós", "tou theoú"), wie sie die Vision-API liefert.

// Deutsch-phonetischer Sprechtext. Reihenfolge wichtig.
const ERSETZUNGEN = [
  // Iota subscriptum: stumm
  ['āi', 'ah'], ['ái', 'ah'], ['ēi', 'äh'], ['êi', 'äh'], ['ōi', 'oh'], ['ôi', 'oh'],
  // Hiatus ε+ου / α+ου (θεοῦ, λαοῦ): Bindestrich verhindert falschen dt. Diphthong
  ['eoû', 'e-uh'], ['eoú', 'e-ú'], ['eou', 'e-u'],
  ['aoû', 'a-uh'], ['aoú', 'a-ú'], ['aou', 'a-u'],
  // ου = langes u
  ['ou', 'u'], ['oú', 'ú'], ['oû', 'uh'],
  // Akzente auf Diphthongen zerbrechen die TTS-Aussprache
  ['aí', 'ai'], ['aî', 'ai'], ['eí', 'ei'], ['eî', 'ei'], ['oí', 'oi'], ['oî', 'oi'],
  ['aú', 'au'], ['aû', 'au'], ['eú', 'eu'], ['eû', 'eu'],
  // ei/eu/oi/ai/au bleiben stehen → deutsche Diphthonge (Schulaussprache)
  ['rh', 'r'],
  ['th', 't'],                              // θ = [t]
  ['ph', 'f'],                              // φ = [f]
  // χ bleibt „ch" — deutsches ch
  ['ṓ', 'óh'], ['ō', 'oh'], ['ô', 'oh'],
  ['î', 'ih'], ['ī', 'ih'],
  ['ḗ', 'äh'], ['ē', 'äh'], ['ê', 'äh'],   // η = [ɛː]
  ['â', 'ah'], ['ā', 'ah'],
  ['ŷ', 'ü'], ['ý', 'ü'], ['y', 'ü'],      // υ = ü
];

const UEBERSCHREIBUNGEN = {
  'eimí': ['eimii', 'de'],
  'allá': ['allah', 'de'],
  'oú': ['ου.', 'el'],
  'tí?': ['τι', 'el'],
};

export function sprechtext(umschrift) {
  const u = UEBERSCHREIBUNGEN[umschrift];
  if (u) return u;
  let t = umschrift.normalize('NFC');
  for (const [alt, neu] of ERSETZUNGEN) t = t.split(alt).join(neu);
  t = t.replace(/(^| )s(?=[tp])/g, '$1ß');          // anlautendes st/sp → ß…
  t = t.replace(/äh(?=$| )/g, 'ä');                 // auslautendes äh → ä
  return [t.replace(/[?;·]/g, '').trim(), 'de'];
}

// ── Wortinitiales χ ──
// Deutsche TTS liest anlautendes „ch" als [ʃ]. χ-anlautende Wörter werden
// phonetisch-neugriechisch geschrieben und mit language_code "el" vertont
// (dort ist χ immer [x]/[ç]); Artikel davor bleiben deutsch.
// υ→ι und ευ→[ev] sind Klang-Näherungen, aber χ bleibt korrekt [x]
// (STT-verifiziert). b/d/g/h bleiben unmappbar → Latein-Rest-Check → null.
const NG_REGELN = [
  ['ch', 'χ'], ['th', 'τ'], ['ph', 'φ'], ['ps', 'ψ'], ['rh', 'ρ'], ['z', 'τσ'],
  ['aí', 'άι'], ['aî', 'άι'], ['ai', 'αϊ'],
  ['eí', 'άι'], ['eî', 'άι'], ['ei', 'αϊ'],
  ['oí', 'όι'], ['oî', 'όι'], ['oi', 'οϊ'],
  ['aú', 'άου'], ['aû', 'άου'], ['au', 'αου'],
  ['eú', 'εύ'], ['eû', 'εύ'], ['eu', 'ευ'],
  ['oú', 'ού'], ['oû', 'ού'], ['ou', 'ου'],
  ['ḗ', 'έ'], ['ē', 'ε'], ['ê', 'έ'],
  ['ṓ', 'ώ'], ['ō', 'ω'], ['ô', 'ώ'],
  ['â', 'ά'], ['ā', 'α'], ['î', 'ί'], ['ī', 'ι'],
  ['ý', 'ί'], ['ŷ', 'ί'], ['y', 'ι'],
  ['á', 'ά'], ['a', 'α'], ['é', 'έ'], ['e', 'ε'],
  ['í', 'ί'], ['i', 'ι'], ['ó', 'ό'], ['o', 'ο'], ['ú', 'ού'], ['u', 'ου'],
  ['k', 'κ'], ['l', 'λ'], ['m', 'μ'], ['n', 'ν'], ['p', 'π'],
  ['r', 'ρ'], ['s', 'σ'], ['t', 'τ'], ['x', 'ξ'], ['f', 'φ'],
];

function nachNeugriechisch(wort) {
  let w = wort.normalize('NFC');
  for (const [alt, neu] of NG_REGELN) w = w.split(alt).join(neu);
  if ([...w].some(c => c.charCodeAt(0) < 0x370 && c !== ' ' && c !== '-')) return null;
  if (w.endsWith('σ')) w = w.slice(0, -1) + 'ς';
  if (![...'άέίόύώ'].some(c => w.includes(c))) {
    if (w.includes('αϊ')) w = w.replace('αϊ', 'άι');
    else if (w.includes('οϊ')) w = w.replace('οϊ', 'όι');
    else {
      const akzent = { α: 'ά', ε: 'έ', ι: 'ί', ο: 'ό', υ: 'ύ', ω: 'ώ' };
      for (const v of 'αειουω') {
        if (w.includes(v)) { w = w.replace(v, akzent[v]); break; }
      }
    }
  }
  return w;
}

// Umschrift-Chunk → [[Teiltext, Sprachcode], …] für die TTS-Synthese
export function chunkTeile(umschriftChunk) {
  const u = UEBERSCHREIBUNGEN[umschriftChunk];
  if (u) return [u];
  const teile = [];
  for (const wort of umschriftChunk.normalize('NFC').split(/\s+/)) {
    if (!wort) continue;
    let sp = sprechtext(wort)[0];
    if (wort.toLowerCase().startsWith('ch')) {
      const ng = nachNeugriechisch(wort);
      if (ng) { teile.push([ng, 'el']); continue; }
      sp = 'k' + sp.slice(2);  // ü/ευ nicht schreibbar → dt. [k] wie Chor
    }
    if (teile.length && teile[teile.length - 1][1] === 'de')
      teile[teile.length - 1][0] += ' ' + sp;
    else
      teile.push([sp, 'de']);
  }
  return teile;
}

// Cache-Schlüssel: Typografie raus, Aussprache-Relevantes bleibt
export function normChunk(chunk) {
  return chunk.normalize('NFC').toLowerCase()
    .replace(/[,;.·?!"'()\[\]]/g, '').replace(/\s+/g, ' ').trim();
}
