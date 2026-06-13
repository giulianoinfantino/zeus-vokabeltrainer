# Zeus → App Store (Phase 1: kostenlose App)

Die App ist als native iOS-App vorbereitet (Capacitor-Hülle um die bestehende Web-App).
Code ist fertig; was bleibt, sind Schritte, die nur **du am Mac mit Xcode + Apple-Konto**
machen kannst. Diese Anleitung führt dich durch.

---

## Was schon erledigt ist

- Capacitor eingerichtet, iOS-Xcode-Projekt unter `ios/` generiert.
- Die ganze App (inkl. aller 2685 Audiodateien, ~43 MB) wird **ins App-Bündel gepackt** → läuft offline.
- Web-App ist „native-ready": API-Aufrufe zeigen im App-Kontext absolut auf Vercel und
  authentifizieren per App-Token (`x-zeus-app`) statt Login-Cookie. Passwortsperre entfällt in der App.
- Kamera-/Foto-Berechtigungen in `Info.plist` eingetragen.
- App-Icon (1024×1024) gesetzt.
- Bundle-ID: `online.zeusvokabeltrainer.app`, App-Name: **Zeus**.

## Voraussetzungen

1. **Apple Developer Program** — 99 $/Jahr, anmelden unter https://developer.apple.com/programs/
   (Freischaltung dauert manchmal 1–2 Tage). Ohne das geht keine Store-Veröffentlichung.
2. **Xcode** ist installiert (26.5 ✓).

---

## Schritt für Schritt

### 1. Projekt öffnen
```sh
npm run ios:open      # oder: npx cap open ios
```
Öffnet `ios/App/App.xcodeproj` in Xcode.

> Nach jeder Änderung an `app/` (HTML/JS/Audio): `npm run ios:sync` ausführen, damit das
> Bündel aktualisiert wird.

### 2. Signing einrichten
In Xcode: Projekt **App** anwählen → Tab **Signing & Capabilities**.
- **Team**: dein Apple-Developer-Account auswählen.
- **Bundle Identifier**: `online.zeusvokabeltrainer.app` (oder eigenen wählen — muss
  weltweit eindeutig sein; dann auch in `capacitor.config.json` angleichen).
- „Automatically manage signing" anlassen → Xcode erzeugt das Provisioning-Profil.

### 3. Auf eigenem iPhone testen
- iPhone per Kabel anschließen, oben in Xcode als Ziel wählen.
- ▶︎ (Run). Beim ersten Mal am iPhone unter *Einstellungen → Allgemein → VPN & Geräte­verwaltung*
  dein Entwickler­zertifikat vertrauen.
- Prüfen: Vokabeln lernen, Audio (Marlena-Stimme), Foto-Import einer Vokabelseite,
  eigene Vokabeln werden vertont.

### 4. App Store Connect vorbereiten
Unter https://appstoreconnect.apple.com → **Apps → +** neue App anlegen:
- Plattform iOS, Name „Zeus" (oder „Zeus – Altgriechisch"), Sprache Deutsch, Bundle-ID auswählen.
- **Datenschutzrichtlinie (Pflicht)**: eine URL nötig. Einfachste Lösung: kurze Seite auf
  zeus-vokabeltrainer.online (z.B. `/datenschutz.html`) — Inhalt: keine Tracking-Cookies,
  Fotos werden nur zum Vokabel-Import an die Server geschickt, keine Weitergabe.
- **App-Datenschutz („Privacy Nutrition Labels")**: Kamera/Fotos = „wird genutzt, nicht zum Tracking";
  „Data Not Collected" passt sonst (kein Tracking).
- Alterseinstufung: 4+.
- Screenshots: mind. für 6,7"-iPhone (z.B. iPhone 15 Pro Max) — im Simulator oder am Gerät erstellen.

### 5. Build hochladen
In Xcode: oben Ziel auf **Any iOS Device (arm64)** → Menü **Product → Archive**.
Nach dem Archivieren: **Distribute App → App Store Connect → Upload**.
Der Build erscheint nach einigen Minuten in App Store Connect.

### 6. Zur Prüfung einreichen
In App Store Connect den Build der App-Version zuordnen, Beschreibung/Keywords/Screenshots
ausfüllen, **Submit for Review**. Apple prüft meist in 1–3 Tagen.

---

## Stolperfallen bei der Apple-Prüfung

- **Richtlinie 4.2 („nur eine Website")**: Das größte Risiko bei Web-Wrappern. Zeus hat echte
  App-Funktionen (Offline-Audio, Spaced Repetition, Kamera-Import, Gamification) — in der
  Beschreibung diese **nativen, offline funktionierenden** Eigenschaften betonen. Falls Apple
  doch meckert: im Review-Notes-Feld erklären, dass Inhalte gebündelt und offline nutzbar sind.
- **Login/Demo**: Falls die Prüfer einen Zugang brauchen — die App ist frei, kein Login nötig.
  Das ist gut (keine Demo-Credentials erforderlich).
- **Datenschutz-URL fehlt** → automatische Ablehnung. Vorher anlegen.

---

## Wichtig fürs Backend (schon erledigt, zur Info)

Die App ruft `/api/extract` und `/api/tts` auf Vercel mit dem Header `x-zeus-app: <Token>`.
Der Token (`ZEUS_APP_TOKEN`) ist in Vercel gesetzt und im App-Code hinterlegt. Er schützt nur
gegen wahllosen Bot-Zugriff; die echte Kostenbremse ist das Tageslimit in `tts.js`.

> **Sicherheits-Hinweis:** Der Token steckt im App-Bündel und ist mit Aufwand extrahierbar.
> Für eine kostenlose App mit Tageslimit ist das vertretbar. **Phase 2** (Bezahl-Version)
> sollte ihn durch echte, kaufgebundene Authentifizierung ersetzen (StoreKit-Abo → serverseitige
> Quittungsprüfung → pro-Gerät-Token).

## Phase 2 (später): Bezahlung

Wenn die kostenlose App durch die Prüfung ist und Nutzer da sind:
- **StoreKit-Abo** (5 €/Monat) — Apple nimmt 15 % (Small Business Program, < 1 Mio. $/Jahr).
- App-Store-Regeln verbieten Stripe für digitale Abos; es muss Apples In-App-Kauf sein.
- Server: Kauf-Quittung prüfen, dann erst `/api`-Zugang gewähren.

---

## Befehls-Spickzettel

```sh
npm run ios:sync     # app/ → iOS-Bündel kopieren (nach jeder Web-Änderung)
npm run ios:open     # Projekt in Xcode öffnen
npm run ios:build    # sync + open in einem
```
