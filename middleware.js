// Passwortschutz für die App: serverseitig, vor jeder Auslieferung von /app/*
export const config = { matcher: ['/app/:path*', '/app'] };

export default function middleware(req) {
  const pw = process.env.ZEUS_PASSWORT || '';
  const cookie = req.headers.get('cookie') || '';
  const token = btoa(unescape(encodeURIComponent(pw)));
  if (pw && cookie.includes('zeus_zutritt=' + token)) return;
  const url = new URL(req.url);
  return Response.redirect(
    new URL('/login.html?weiter=' + encodeURIComponent(url.pathname + url.search), req.url), 302);
}
