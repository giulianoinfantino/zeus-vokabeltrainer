// Prüft das Passwort und setzt das Zutritts-Cookie (1 Jahr gültig)
export default function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ ok: false });
  const pw = (req.body && req.body.pw) || '';
  if (pw && pw === process.env.ZEUS_PASSWORT) {
    const token = Buffer.from(pw, 'utf8').toString('base64');
    res.setHeader('Set-Cookie',
      `zeus_zutritt=${token}; Path=/; Max-Age=31536000; HttpOnly; Secure; SameSite=Lax`);
    return res.status(200).json({ ok: true });
  }
  return res.status(401).json({ ok: false });
}
