// Foto einer Vokabelseite → Claude Vision → strukturierte Vokabelliste
import Anthropic from '@anthropic-ai/sdk';

const SCHEMA = {
  type: 'object',
  properties: {
    titel: {
      type: 'string',
      description: 'Lektionstitel/-nummer, falls auf der Seite erkennbar (z.B. "Kantharos Lektion 3"), sonst leerer String'
    },
    vokabeln: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          griechisch: { type: 'string', description: 'Griechisches Wort exakt wie gedruckt, polyton (alle Akzente, Spiritus, Iota subscriptum); Substantive mit Artikel, falls angegeben' },
          umschrift: { type: 'string', description: 'Wissenschaftliche lateinische Umschrift der Grundform INKLUSIVE Artikel (ē für η, ō für ω, Spiritus asper als h), z.B. "hē glōssa"' },
          deutsch: { type: 'string', description: 'Deutsche Bedeutung(en)' },
          erklaerung: { type: 'string', description: 'Grammatikangabe oder Zusatzinfo (Genitiv, Stammformen, Hinweise), sonst leerer String' },
          flexion: {
            type: 'array',
            items: { type: 'string' },
            description: 'Umschrift der weiteren auf der Seite angegebenen Formen, jeweils VOLL ausgeschrieben: aus "ὁ θεός, -οῦ" wird ["tou theoú"] (Genitiv mit Artikel), aus "ἀγαθός, -ή, -όν" wird ["agathḗ", "agathón"]. Leer, wenn keine Flexionsangaben auf der Seite stehen.'
          }
        },
        required: ['griechisch', 'umschrift', 'deutsch', 'erklaerung', 'flexion'],
        additionalProperties: false
      }
    }
  },
  required: ['titel', 'vokabeln'],
  additionalProperties: false
};

const AUFTRAG = `Auf dem Bild ist eine Vokabelseite aus einem Altgriechisch-Lehrbuch (oder eine handschriftliche Vokabelliste).
Extrahiere ALLE Vokabeleinträge vollständig und exakt — lass keinen Eintrag aus und erfinde nichts, was nicht auf der Seite steht.
Übernimm die polytone Schreibung buchstabengetreu. Fehlt die Umschrift auf der Seite, erzeuge sie selbst nach wissenschaftlicher Konvention.
Wichtig für umschrift und flexion: abgekürzte Endungen immer zur vollen gesprochenen Form expandieren (aus "-οῦ" wird der volle Genitiv mit Artikel, z.B. "tou theoú") — aber NUR Formen aufnehmen, die auf der Seite tatsächlich angegeben sind.`;

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Nur POST erlaubt' });
  if (!process.env.ANTHROPIC_API_KEY)
    return res.status(500).json({ error: 'ANTHROPIC_API_KEY ist auf dem Server nicht konfiguriert' });

  // Gleicher Zutrittsschutz wie /app/* — sonst könnte jeder auf fremde Kosten scannen
  const pw = process.env.ZEUS_PASSWORT || '';
  const token = Buffer.from(pw, 'utf8').toString('base64');
  if (pw && !(req.headers.cookie || '').includes('zeus_zutritt=' + token))
    return res.status(401).json({ error: 'Nicht angemeldet — bitte zuerst einloggen' });

  const { image, media_type } = req.body || {};
  if (!image) return res.status(400).json({ error: 'Kein Bild übermittelt' });

  const client = new Anthropic();
  try {
    const msg = await client.messages.create({
      model: 'claude-opus-4-8',
      max_tokens: 16000,
      thinking: { type: 'adaptive' },
      output_config: { format: { type: 'json_schema', schema: SCHEMA } },
      messages: [{
        role: 'user',
        content: [
          { type: 'image', source: { type: 'base64', media_type: media_type || 'image/jpeg', data: image } },
          { type: 'text', text: AUFTRAG }
        ]
      }]
    });

    if (msg.stop_reason === 'refusal')
      return res.status(422).json({ error: 'Das Bild konnte nicht verarbeitet werden' });

    const text = msg.content.find(b => b.type === 'text')?.text;
    if (!text) return res.status(502).json({ error: 'Leere Antwort der Vision-API' });

    const data = JSON.parse(text);
    if (!Array.isArray(data.vokabeln) || !data.vokabeln.length)
      return res.status(422).json({ error: 'Keine Vokabeln auf dem Bild erkannt' });

    return res.status(200).json({ titel: data.titel || '', vokabeln: data.vokabeln });
  } catch (e) {
    const status = (e instanceof Anthropic.APIError && e.status) ? e.status : 500;
    return res.status(status).json({ error: e.message || 'Unbekannter Fehler' });
  }
}
