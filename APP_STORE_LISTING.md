# Zeus → App Store · Einreich-Paket

Stand: alles Code-/Backend-seitige ist fertig. Es bleiben die Xcode- und
App-Store-Connect-Schritte (GUI, nur du am Mac mit deinem Developer-Account).
Die fertigen Texte unten sind zum Kopieren.

---

## A) Fertige Store-Texte (kopieren)

**App-Name** (muss store-weit eindeutig sein — „Zeus" allein ist sicher belegt):
> Zeus – Altgriechisch

**Untertitel** (max. 30 Zeichen):
> Vokabeltrainer mit Vertonung

**Kategorie:** Bildung · **Alterseinstufung:** 4+ · **Sprache:** Deutsch

**Beschreibung:**
```
Zeus ist der Vokabeltrainer für Altgriechisch — mit echter Vertonung, kuratiertem Wortschatz und einem Lernspiel, das motiviert.

• Über 1.600 vertonte Vokabeln in 82 thematischen Lektionen — jede Vokabel gesprochen, vollständig OFFLINE auf dem Gerät.
• Intelligente Wiederholung (Spaced Repetition) mit fünf Lernstufen — du übst genau das, was sitzen muss.
• Eigene Lehrbuchseiten per Foto importieren — die App erkennt die Vokabeln und vertont sie.
• Athen aufbauen: lerne, sammle Drachmen, errichte zwölf Bauwerke — und halte deine Lernsträhne, sonst zürnt Zeus.
• Deutsche Schulaussprache, wie an Schulen und Universitäten gelehrt.
• Kein Konto nötig, kein Tracking, konsequent datensparsam.

Für Graecum-Kandidatinnen und -Kandidaten, Schülerinnen und Schüler am humanistischen Gymnasium und alle, die Homer, Platon oder das Neue Testament im Original lesen wollen.
```

**Werbetext** (optional, max. 170 Zeichen):
> Über 1.600 vertonte Vokabeln, Foto-Import eigener Lektionen und der Aufbau Athens — Altgriechisch lernen, das motiviert.

**Keywords** (max. 100 Zeichen, kommagetrennt, keine Leerzeichen):
> altgriechisch,graecum,vokabeln,griechisch,gymnasium,kantharos,hellas,homer,koine,vokabeltrainer

**URLs:**
- Support-URL: `https://www.zeus-vokabeltrainer.online`
- Marketing-URL: `https://ergon-solutions.net`
- **Datenschutz-URL (Pflicht):** `https://www.zeus-vokabeltrainer.online/datenschutz.html`

**Hinweise für die Prüfung (Review Notes) — wichtig gegen Richtlinie 4.2:**
```
Die App funktioniert vollständig ohne Konto oder Login. Alle Inhalte (über 1.600 Vokabeln inklusive Audio) sind im App-Bündel enthalten und offline nutzbar. Native Zusatzfunktionen: Spaced-Repetition-Lernlogik, Kamera-Import von Vokabelseiten, Gamification. Es handelt sich nicht um eine reine Website-Hülle — die Kernfunktionen laufen offline auf dem Gerät.
```

**App-Datenschutz (Privacy „Nutrition Labels"):**
- **Fotos / Benutzerinhalte** → „Wird erfasst" → Zweck **App-Funktionalität**, **nicht** mit Identität verknüpft, **nicht** für Tracking. (Begründung: Foto-Import schickt das Bild zur Vokabel-Erkennung an den Server, ohne dauerhafte Speicherung.)
- Alles andere: **„Daten werden nicht erfasst"** (kein Konto, kein Analytics, keine Werbung).

---

## B) Schritte am Mac (du)

1. **Projekt öffnen:** `npm run ios:open` (Bündel ist bereits frisch gesynct).
2. **Signing:** Target „App" → *Signing & Capabilities* → dein **Team** wählen.
   Bundle-ID ist `online.zeusvokabeltrainer.app` (muss in deinem Account registrierbar/eindeutig sein). „Automatically manage signing" an.
3. **Auf echtem iPhone testen** (Gerät anschließen, ▶︎): durchprüfen —
   Vokabeln lernen, **Audio abspielen**, **Foto-Import** einer Vokabelseite,
   eigene Vokabeln werden vertont. (Erst-Vertrauen: iPhone → Einstellungen →
   Allgemein → VPN & Geräteverwaltung → dein Zertifikat vertrauen.)
4. **Archivieren:** Ziel oben auf **„Any iOS Device (arm64)"** → Menü
   *Product → Archive*.
5. **Hochladen:** im Organizer *Distribute App → App Store Connect → Upload*.
6. **App Store Connect** (appstoreconnect.apple.com) → *Apps → +*:
   neue App anlegen (iOS, Name „Zeus – Altgriechisch", Deutsch, Bundle-ID, SKU frei).
   Texte oben einfügen, **Screenshots** (mind. 6,7" — iPhone 15/16 Pro Max,
   im Simulator oder am Gerät), Datenschutz-URL, Privacy-Labels (s. o.).
7. **Build zuordnen** (erscheint einige Minuten nach dem Upload) → **Submit for Review**.
   Prüfung dauert meist 1–3 Tage.

## C) Status der Vorbereitung (erledigt)
- ✓ Bundle-ID, App-Name, Kamera-/Foto-Permissions (mit Begründungstexten)
- ✓ Version 1.0 / Build 1
- ✓ iOS-Bündel auf aktuellen Stand gesynct (Code + Offline-Audio)
- ✓ Datenschutz + Impressum live (Ergon Solutions)
- ✓ Backend (`/api/extract`, `/api/tts`) deployt, App-Token-Auth

## D) Vor breitem Marketing noch klären (kein Blocker für die reine Einreichung)
- ElevenLabs-Kommerzlizenz (Audio wird im Bündel verteilt)
- Wortschatz-Provenienz (keine 1:1-Verlagslisten)
- Aussprache-Ohr-Check (χ/Betonung) — Audio ist turbo (bewährt); v3-Migration bleibt dev-only bis bestätigt
