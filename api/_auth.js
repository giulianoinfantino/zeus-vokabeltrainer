// Zutritt für /api: Login-Cookie (Web-PWA) ODER App-Token (native iOS-App).
// Der App-Token steckt im App-Bündel und schützt nur gegen wahllosen Bot-
// Zugriff; die echte Kostenbremse ist das Tageslimit in tts.js.
export function zutrittErlaubt(req) {
  const pw = process.env.ZEUS_PASSWORT || '';
  if (pw) {
    const cookieToken = Buffer.from(pw, 'utf8').toString('base64');
    if ((req.headers.cookie || '').includes('zeus_zutritt=' + cookieToken)) return true;
  }
  const appToken = process.env.ZEUS_APP_TOKEN || '';
  if (appToken && req.headers['x-zeus-app'] === appToken) return true;
  // Wenn weder Passwort noch App-Token serverseitig gesetzt sind: offen lassen
  // (lokale Entwicklung), sonst sperren.
  return !pw && !appToken;
}
