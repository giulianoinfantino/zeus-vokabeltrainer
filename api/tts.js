// Vertonung eigener Vokabeln: Umschrift-Chunks → ElevenLabs (Marlena, gleiche
// Stimme wie die eingebauten Aufnahmen) → globaler Blob-Cache. Jeder Chunk
// wird genau einmal überhaupt vertont — danach Cache-Treffer für alle Nutzer.
import crypto from 'node:crypto';
import { put, list } from '@vercel/blob';
import { chunkTeile, normChunk } from './_phonetik.js';

const VOICE_ID = 'MTTjXkEpZepLTqO0xH0f';   // Marlena
const MODELL = 'eleven_turbo_v2_5';
const MAX_CHUNKS = 8;                       // pro Vokabel mehr als genug
const MAX_ZEICHEN = 60;                     // pro Chunk
const TAGES_LIMIT = 3000;                   // neue Vertonungen pro Tag (global)

async function elevenlabsMp3(text, lang) {
  const r = await fetch(
    `https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}?output_format=mp3_44100_128`,
    {
      method: 'POST',
      headers: { 'xi-api-key': process.env.ELEVENLABS_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text, model_id: MODELL, language_code: lang,
        voice_settings: { stability: 0.85, similarity_boost: 0.75, speed: 0.9 },
      }),
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
  // Gleicher Zutrittsschutz wie /app/*
  const pw = process.env.ZEUS_PASSWORT || '';
  const token = Buffer.from(pw, 'utf8').toString('base64');
  if (pw && !(req.headers.cookie || '').includes('zeus_zutritt=' + token))
    return res.status(401).json({ error: 'Nicht angemeldet — bitte zuerst einloggen' });

  let { chunks } = req.body || {};
  if (!Array.isArray(chunks) || !chunks.length)
    return res.status(400).json({ error: 'chunks fehlt' });
  chunks = chunks.slice(0, MAX_CHUNKS).map(c => String(c).slice(0, MAX_ZEICHEN));

  try {
    const urls = [];
    let neuErzeugt = 0;
    for (const chunk of chunks) {
      const norm = normChunk(chunk);
      if (!norm) { urls.push(null); continue; }
      const hash = crypto.createHash('sha1').update(norm).digest('hex').slice(0, 24);
      const pfad = `tts/${hash}.mp3`;

      let url = await blobUrl(pfad);
      if (!url) {
        if (await tagesZaehler(0) >= TAGES_LIMIT)
          return res.status(429).json({ error: 'Tageskontingent der Vertonung erschöpft — morgen wieder' });
        const teile = chunkTeile(norm);
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
