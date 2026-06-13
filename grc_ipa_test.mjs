// Verifiziert den JS-Port api/grc_ipa.js gegen Python-Goldwerte.
// Goldwerte (grc_ipa_fixtures.json) sind aus grc_ipa.py über alle eingebauten
// Vokabeln erzeugt. Bei beabsichtigter Aussprache-Änderung in grc_ipa.py:
//   python3 -c "..."  → grc_ipa_fixtures.json neu erzeugen (siehe Repo-History).
// Lauf:  node grc_ipa_test.mjs
import { grcToIpa } from './api/grc_ipa.js';
import { readFileSync } from 'node:fs';

const pairs = JSON.parse(readFileSync(new URL('./grc_ipa_fixtures.json', import.meta.url), 'utf-8'));
let ok = 0, diff = 0, shown = 0;
for (const [w, py] of pairs) {
  const js = grcToIpa(w);
  if (js === py) ok++;
  else { diff++; if (shown++ < 25) console.error(`✗ ${w}  py=${JSON.stringify(py)}  js=${JSON.stringify(js)}`); }
}
console.log(`${ok} identisch, ${diff} abweichend von ${pairs.length} (${(100 * ok / pairs.length).toFixed(2)}%)`);
process.exit(diff ? 1 : 0);
