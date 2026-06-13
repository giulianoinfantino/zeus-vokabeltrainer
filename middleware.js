// Passwortschutz für die App: serverseitig, vor jeder Auslieferung von /app/*
export const config = { matcher: ['/app/:path*', '/app'] };

export default function middleware(req) {
  const url = new URL(req.url);
  // /app ohne Slash → /app/ normalisieren: sonst lösen relative Pfade (data/…)
  // gegen / statt /app/ auf und liefern 404 ("The page could not be found").
  if (url.pathname === '/app') {
    url.pathname = '/app/';
    return Response.redirect(url, 308);
  }
  const pw = process.env.ZEUS_PASSWORT || '';
  const cookie = req.headers.get('cookie') || '';
  const token = btoa(unescape(encodeURIComponent(pw)));
  if (pw && cookie.includes('zeus_zutritt=' + token)) return;
  return Response.redirect(
    new URL('/login.html?weiter=' + encodeURIComponent(url.pathname + url.search), req.url), 302);
}
