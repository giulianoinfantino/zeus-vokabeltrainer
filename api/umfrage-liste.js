// Liefert alle Umfrage-Antworten — nur mit gültigem Zutritts-Cookie (wie middleware.js)
import { list } from '@vercel/blob';

function zutrittOk(req) {
  const pw = process.env.ZEUS_PASSWORT || '';
  const cookie = req.headers.cookie || '';
  const token = Buffer.from(pw, 'utf8').toString('base64');
  return Boolean(pw) && cookie.includes('zeus_zutritt=' + token);
}

export default async function handler(req, res) {
  if (!zutrittOk(req)) return res.status(401).json({ ok: false });

  const eintraege = [];
  let cursor;
  do {
    const r = await list({ prefix: 'umfragen/', cursor, limit: 1000 });
    for (const blob of r.blobs) {
      try {
        const inhalt = await (await fetch(blob.url)).json();
        eintraege.push({ pfad: blob.pathname, ...inhalt });
      } catch {
        eintraege.push({ pfad: blob.pathname, fehler: 'nicht lesbar' });
      }
    }
    cursor = r.cursor;
  } while (cursor);

  eintraege.sort((a, b) => (b.eingegangen || '').localeCompare(a.eingegangen || ''));
  return res.status(200).json({ ok: true, anzahl: eintraege.length, eintraege });
}
