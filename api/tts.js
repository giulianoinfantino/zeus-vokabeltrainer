// Vertonung eigener Vokabeln: Umschrift-Chunks → ElevenLabs (Marlena, gleiche
// Stimme wie die eingebauten Aufnahmen) → globaler Blob-Cache. Jeder Chunk
// wird genau einmal überhaupt vertont — danach Cache-Treffer für alle Nutzer.
import crypto from 'node:crypto';
import { put, list } from '@vercel/blob';
import { chunkTeileV3, normChunk } from './_phonetik.js';
import { zutrittErlaubt } from './_auth.js';

const VOICE_ID = 'MTTjXkEpZepLTqO0xH0f';   // Marlena
const MODELL = 'eleven_turbo_v2_5';         // χ-Pfad (Neugriechisch+el)
const MODELL_V3 = 'eleven_v3';              // Normalpfad: Inline-IPA /…/
const V3_SEED = 42;                         // fester Seed → konstante Stimme (gemessen)
const CACHE_VER = 'v3b';                    // Bump invalidiert alte Aufnahmen (neue v3-Settings)
const MAX_CHUNKS = 8;                       // pro Vokabel mehr als genug
const MAX_ZEICHEN = 60;                     // pro Chunk
const TAGES_LIMIT = 3000;                   // neue Vertonungen pro Tag (global)

async function elevenlabsMp3(text, lang) {
  const body = lang === 'v3'
    ? { text, model_id: MODELL_V3, seed: V3_SEED, voice_settings: { stability: 0.5, similarity_boost: 1.0 } }
    : { text, model_id: MODELL, language_code: lang,
        voice_settings: { stability: 0.85, similarity_boost: 0.75, speed: 0.9 } };
  const r = await fetch(
    `https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}?output_format=mp3_44100_128`,
    {
      method: 'POST',
      headers: { 'xi-api-key': process.env.ELEVENLABS_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  if (!r.ok) throw new Error(`ElevenLabs ${r.status}: ${(await r.text()).slice(0, 150)}`);
  return Buffer.from(await r.arrayBuffer());
}

async function blobUrl(pfad) {
  const { blobs } = await list({ prefix: pfad, limit: 1 });
  return blobs.length ? blobs[0].url : null;
}

async function tagesZaehler(delta) {
  const tag = new Date().toISOString().slice(0, 10);
  const pfad = `tts/limit-${tag}.txt`;
  let stand = 0;
  const url = await blobUrl(pfad);
  if (url) {
    try { stand = parseInt(await (await fetch(url, { cache: 'no-store' })).text(), 10) || 0; } catch {}
  }
  if (delta) {
    await put(pfad, String(stand + delta), {
      access: 'public', addRandomSuffix: false, contentType: 'text/plain',
      allowOverwrite: true, cacheControlMaxAge: 0,
    });
  }
  return stand;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Nur POST erlaubt' });
  for (const env of ['ELEVENLABS_API_KEY', 'BLOB_READ_WRITE_TOKEN']) {
    if (!process.env[env]) return res.status(500).json({ error: env + ' ist nicht konfiguriert' });
  }
  // Zutritt: Login-Cookie (Web) oder App-Token (iOS-App)
  if (!zutrittErlaubt(req))
    return res.status(401).json({ error: 'Nicht angemeldet' });

  let { chunks } = req.body || {};
  if (!Array.isArray(chunks) || !chunks.length)
    return res.status(400).json({ error: 'chunks fehlt' });
  // Chunks: { g: Griechisch, u: Umschrift }. String-Fallback für ältere Clients.
  chunks = chunks.slice(0, MAX_CHUNKS).map(c => {
    const o = (c && typeof c === 'object') ? c : { u: String(c) };
    return { g: String(o.g || '').slice(0, MAX_ZEICHEN), u: String(o.u || '').slice(0, MAX_ZEICHEN) };
  });

  try {
    const urls = [];
    let neuErzeugt = 0;
    for (const { g, u } of chunks) {
      const norm = normChunk(u || g);
      if (!norm) { urls.push(null); continue; }
      const hash = crypto.createHash('sha1').update(`${CACHE_VER}|${norm}`).digest('hex').slice(0, 24);
      const pfad = `tts/${hash}.mp3`;

      let url = await blobUrl(pfad);
      if (!url) {
        if (await tagesZaehler(0) >= TAGES_LIMIT)
          return res.status(429).json({ error: 'Tageskontingent der Vertonung erschöpft — morgen wieder' });
        const teile = chunkTeileV3({ g, u });
        const mp3 = Buffer.concat(await Promise.all(teile.map(([t, l]) => elevenlabsMp3(t, l))));
        ({ url } = await put(pfad, mp3, {
          access: 'public', addRandomSuffix: false, contentType: 'audio/mpeg', allowOverwrite: true,
        }));
        neuErzeugt++;
      }
      urls.push(url);
    }
    if (neuErzeugt) await tagesZaehler(neuErzeugt);
    return res.status(200).json({ urls });
  } catch (e) {
    return res.status(502).json({ error: e.message || 'Vertonung fehlgeschlagen' });
  }
}
