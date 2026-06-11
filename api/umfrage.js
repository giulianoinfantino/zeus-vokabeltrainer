// Nimmt Demo-Feedback entgegen und legt es als JSON im Blob-Speicher ab
import { put } from '@vercel/blob';

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ ok: false });

  const b = req.body || {};
  const sterne = Number(b.sterne);
  if (!(sterne >= 1 && sterne <= 5)) {
    return res.status(400).json({ ok: false, fehler: 'sterne (1–5) erforderlich' });
  }
  const s = (v, n) => (typeof v === 'string' ? v.slice(0, n) : '');

  const eintrag = {
    eingegangen: new Date().toISOString(),
    sterne,
    gefallen: Array.isArray(b.gefallen) ? b.gefallen.slice(0, 10).map(x => s(x, 60)) : [],
    verbessern: s(b.verbessern, 2000),
    kontext: s(b.kontext, 60),
    zahlung: s(b.zahlung, 80),
    email: s(b.email, 200),
    gelernt: Number(b.gelernt) || 0,
    streak: Number(b.streak) || 0,
    level: Number(b.level) || 0,
    ua: s(req.headers['user-agent'] || '', 300)
  };

  const name = `umfragen/${Date.now()}-${Math.random().toString(36).slice(2, 8)}.json`;
  await put(name, JSON.stringify(eintrag, null, 2), {
    access: 'public',
    contentType: 'application/json'
  });

  return res.status(200).json({ ok: true });
}
