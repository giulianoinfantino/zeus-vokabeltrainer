# Zeus — Business-Plan

*Stand: Juni 2026 · Arbeitsdokument*

## 1. Produkt heute

Zeus ist ein Altgriechisch-Vokabeltrainer als PWA: 1640 kuratierte Vokabeln in
82 thematischen Lektionen (Grund- und Aufbauwortschatz), jede Vokabel vertont
(1652 Audiodateien, ElevenLabs), Spaced Repetition mit fünf Lernstufen,
Gamification (Drachmen, 12 Athen-Bauwerke, Streak-Katastrophen, Combo-Klang),
Foto-Import für eigene Lehrbuchseiten, offline-fähig, deutschsprachig.

**Alleinstellungsmerkmale (USP):**
1. **Vertonung** — kein anderer deutschsprachiger Altgriechisch-Trainer hat
   durchgängig vertonte Vokabeln. Audio ist das stärkste Argument.
2. **Kuratierter Wortschatz** mit Erklärungen, Stammformen, Umschrift und
   Sprechhilfe — kein nacktes Karteikarten-Deck wie bei Anki/Quizlet.
3. **Gamification, die zur Zielgruppe passt** (Athen aufbauen, Zeus zürnt) —
   thematisch stimmig statt generischer Punkte.
4. **Deutschsprachig** — der englische Markt (Biblical-Greek-Apps) bedient
   den DACH-Schulmarkt nicht.

## 2. Markt (DACH)

| Segment | Größe (Schätzung) | Zahlungsbereitschaft | Erreichbarkeit |
|---|---|---|---|
| Schüler mit Altgriechisch (humanist. Gymnasien DE/AT/CH) | ~13–15 Tsd. | niedrig (Eltern zahlen) | über Lehrkräfte |
| Graecum-Kandidaten an Unis (Theologie, Klass. Phil., Philosophie, Alte Geschichte) | ~5–10 Tsd./Jahr | **hoch** (Prüfungsdruck, 1–2 Semester Zeitfenster) | direkt (SEO, Sprachkurse) |
| Selbstlerner / Liebhaber (Homer, NT-Griechisch, Philosophie) | klein, aber stetig | mittel | SEO, YouTube, Podcasts |
| Institutionen (Schulen, Sprachenzentren, Seminare) | wenige hundert Einrichtungen | mittel, aber wiederkehrend | Verbände, Direktansprache |

**Ehrliche Einordnung:** Das ist ein Nischenmarkt. Realistisch sind hunderte
bis niedrige tausende zahlende Nutzer — ein solides Nebeneinkommen
(grob 5–30 Tsd. €/Jahr bei gutem Lauf), kein Startup-Markt. Dafür ist die
Konkurrenz fast null und die Zielgruppe loyal und gut vernetzt.

**Wettbewerb:**
- *Anki/Quizlet*: gratis, aber unkuratiert, ohne Audio, hässlich. Zeus gewinnt über Qualität und Null-Einrichtungsaufwand.
- *phase6*: stark im Schulmarkt über Lehrbuch-Lizenzen (Kantharos, Hellas), aber Altgriechisch ist dort Randthema und unvertont.
- *Navigium, eVokabel*: Latein-fokussiert.
- *Englische Biblical-Greek-Apps* (ParseGreek u. a.): falsche Sprache, falsche Aussprachekonvention für den deutschen Markt.

## 3. Zielgruppen-Strategie: Wer zuerst?

**Priorität 1 — Graecum-Kandidaten (B2C).** Bester Kunde: akuter Bedarf,
eigene Kaufentscheidung, kurzes Zeitfenster (= Einmalkauf statt Abo-Hürde),
direkt erreichbar über Suchbegriffe wie „Graecum lernen", „Altgriechisch
Vokabeln App", „Kantharos Vokabeln". Hier entsteht der erste Umsatz und der
Beweis, dass jemand zahlt.

**Priorität 2 — Lehrkräfte als Multiplikatoren (B2B2C).** Altgriechisch-
Lehrkräfte sind eine kleine, extrem gut vernetzte Community (Deutscher
Altphilologenverband, Forum Classicum, Fachtagungen). Eine Lehrkraft bringt
eine ganze Klasse. Kostenloser Lehrer-Account + Klassenlizenz.

**Priorität 3 — Institutionen (Lizenzen).** Sprachenzentren und Theologische
Fakultäten, die Graecum-Kurse anbieten, sowie Schulen. **Wichtig:** Der
Einkauf läuft praktisch nie über die Uni-Bibliothek (die lizenziert
Datenbanken, keine Lerntools), sondern über das **Sprachenzentrum, das
Institut oder den Lehrstuhl** — kleinere Budgets, aber kurze Wege: eine
E-Mail an den Graecum-Dozenten genügt oft. Kirchliche Träger
(Sprachsemester der Landeskirchen, kirchliche Hochschulen) sind ein
zweiter Weg.

## 4. Preismodell

| Angebot | Preis | Begründung |
|---|---|---|
| **Frei-Stufe** | 0 € | 1–2 Lektionsgruppen + Demo-Audio. Senkt die Hürde, füttert Mundpropaganda. |
| **Zeus Vollzugang (Einmalkauf)** | 29–39 € einmalig | Graecum ist ein 6–18-Monats-Projekt; Einmalkauf konvertiert in dieser Zielgruppe besser als Abo. „Weniger als ein Repetitorium-Nachmittag." |
| Alternativ: Abo | 4,99 €/Monat · 29 €/Jahr | nur falls Einmalkauf + laufende Kosten (Server, Audio) nicht tragen |
| **Klassenlizenz Schule** | 99–149 €/Jahr (bis 35 Schüler) | aus dem Fachschafts- oder Fördervereinsbudget bezahlbar, keine Ausschreibung nötig |
| **Kurslizenz Uni/Sprachenzentrum** | 3–5 €/Student/Semester oder 300–800 €/Jahr flat | Dozent verteilt Codes; Abrechnung pro Kurs ist anschlussfähig an Semesterlogik |

Lehrkräfte und Dozenten: immer **kostenloser Vollzugang**. Sie sind
Vertriebskanal, nicht Kunde.

## 5. Was vor dem ersten verkauften Euro passieren muss

Derzeit ist Zeus ein privates Projekt mit einem geteilten Passwort. Verkaufbar
wird es erst mit:

1. **Accounts + Sync.** Lernstand liegt heute im localStorage — Gerätewechsel
   = Totalverlust. Für zahlende Kunden inakzeptabel; für Klassenlizenzen
   braucht es ohnehin Nutzerverwaltung. (Vercel + kleine DB reicht.)
2. **Zahlungsabwicklung.** Stripe (Web) und/oder App-Store-Wrapper. Für
   Schüler-Markt ist die App-Store-Präsenz fast Pflicht, kostet aber 15–30 %
   Provision — Web-Kauf als Primärweg, Store als Schaufenster.
3. **Rechtliches.** Impressum, Datenschutzerklärung, AGB, Widerruf;
   Gewerbeanmeldung (Kleinunternehmerregelung reicht anfangs). Für Schulen
   ist **DSGVO die erste Einkaufsfrage**: AV-Vertrag anbieten, Datensparsamkeit
   betonen (Zeus braucht fast keine personenbezogenen Daten — das ist ein
   Verkaufsargument, prominent ausspielen).
4. **Lizenz-Klärung Audio.** ElevenLabs-Tarif auf kommerzielle Nutzung prüfen
   (bezahlte Pläne erlauben sie, Free-Tier nicht).
5. **Urheberrecht Wortschatz.** Klären, dass die gw_-Listen eine eigene
   Kuratierung sind und nicht 1:1 einem verlegten Grundwortschatz (Klett,
   Buchner) folgen. Falls doch: umstellen oder lizenzieren — *vor* dem Launch.
6. **Fachlicher Expertencheck** (steht ohnehin aus): Aussprache- und
   Vokabel-Qualität von Gräzisten absegnen lassen. Das Ergebnis ist zugleich
   Marketing („geprüft von …") und Absicherung der zentralen Werbeaussage
   „wissenschaftlich rekonstruierte Aussprache". *Achtung:* Landing-Page
   verspricht „rekonstruiertes klassisches Attisch", die Audios sind nach
   bisherigem Stand eher erasmisch — das muss vor dem Launch konsistent sein,
   sonst zerlegt die Fach-Community genau das stärkste Verkaufsargument.

## 6. Vertriebskanäle konkret

**SEO/Content (wichtigster B2C-Kanal, 0 € Budget):**
- Landing-Pages je Suchintention: „Graecum vorbereiten", „Altgriechisch
  Vokabeln lernen", „Kantharos/Hellas Vokabeltrainer", „rekonstruierte
  Aussprache Altgriechisch".
- Die Audio-Demo ist der Conversion-Hebel: niemand sonst kann „so klang
  χαῖρε wirklich" vorspielen.
- Kostenlose Häppchen, die geteilt werden: „Die 100 häufigsten griechischen
  Vokabeln — vertont" als frei zugängliche Seite.

**Community/Multiplikatoren:**
- Deutscher Altphilologenverband (DAV): Landestagungen, Forum Classicum
  (Rezension anregen), Newsletter.
- Fachschaften Klassische Philologie + Theologie: Aushang/Insta zu
  Semesterbeginn, wenn Graecum-Kurse starten (= saisonales Marketing:
  April und Oktober).
- Graecum-Dozenten direkt anschreiben (es gibt nur ein paar Dutzend
  relevante Sprachenzentren in DACH — das ist in zwei Wochen abtelefonierbar).
- Reddit/Discord (r/AncientGreek, Latin-/Greek-Lern-Discords), YouTube-Kanäle
  zu Altgriechisch (polýMATHY u. ä. für die rekonstruierte Aussprache-Szene).

**Schulen:**
- Über begeisterte Lehrkräfte, nie über „die Schule" abstrakt. Erst 3–5
  Pilot-Klassen gratis, Feedback einarbeiten, Zitate sammeln, dann
  Klassenlizenz mit den Testimonials verkaufen.
- Bundeswettbewerb Fremdsprachen / Certamina als Sponsoring-Mini-Budget
  (Preis: Jahreslizenzen) — günstige, glaubwürdige Sichtbarkeit.

**Unis/Institutionen:**
- Direktvertrieb per E-Mail an Sprachenzentren und Theologische Fakultäten
  mit Kurslizenz-Angebot und DSGVO-Mappe.
- Referenz-Logik: eine erste Uni als zitierbare Referenz ist mehr wert als
  Rabatt — notfalls Jahr 1 gratis gegen Testimonial und Feedback.

## 7. Roadmap

**Phase 0 — Verkaufsreife (1–3 Monate):**
Accounts/Sync, Stripe, Rechtstexte, Audio-Lizenz, Wortschatz-Provenienz,
Expertencheck, Aussprache-Claim konsistent machen.

**Phase 1 — Beta & Beweis (parallel/danach, 2–3 Monate):**
2–3 Graecum-Kurse und 2–3 Schulklassen als Gratis-Piloten. Ziel: Testimonials,
Retention-Daten, Preisvalidierung. Erst danach öffentlicher Launch.

**Phase 2 — B2C-Launch (zum Semesterstart Oktober 2026):**
Einmalkauf 29–39 €, Frei-Stufe, SEO-Seiten live, Posts in Communities,
Dozenten-Mailing. Ziel Jahr 1: 200–500 zahlende Nutzer (≈ 6–18 Tsd. €).

**Phase 3 — Lizenzen (ab 2027):**
Klassen- und Kurslizenzen mit den Pilot-Referenzen. Ziel: 10–20 Institutionen
(≈ 3–15 Tsd. €/Jahr wiederkehrend).

**Optionale Erweiterungen mit echtem Markt-Hebel (erst nach Phase 2):**
- **Koine/NT-Griechisch-Modul** — verdoppelt den Theologie-Markt und öffnet
  kirchliche Kanäle.
- **Lehrbuch-Anbindung** (Kantharos-/Hellas-Lektionsreihenfolge als Filter
  über den bestehenden Wortschatz — *nicht* deren Listen kopieren) — das
  Killer-Feature für Schulklassen.
- Englische Oberfläche → internationaler Markt (Reconstructed-Pronunciation-
  Community ist global und unterversorgt).

## 8. Risiken

| Risiko | Einschätzung | Gegenmaßnahme |
|---|---|---|
| Markt zu klein / schrumpft | real (Griechisch-Schülerzahlen sinken) | Koine-Modul + englischer Markt als Erweiterung; Kostenbasis nahe null halten |
| Urheberrecht Wortschatzlisten | klärungsbedürftig | vor Launch prüfen (Punkt 5.5) |
| Aussprache-Claim hält Fachprüfung nicht stand | mittel | Expertencheck vor Launch; Claim ggf. präzisieren |
| Abo-Müdigkeit der Zielgruppe | hoch | Einmalkauf als Primärmodell |
| App-Store-Provision frisst Marge | sicher | Web-Kauf primär, Store als Marketing |
| Einzelperson-Projekt (Bus-Faktor) | strukturell | einfache Architektur beibehalten, keine Feature-Inflation |

## 9. Nächste drei Schritte

1. Provenienz der Vokabellisten + ElevenLabs-Kommerzlizenz klären (Blocker für alles Weitere).
2. Expertencheck organisieren und Aussprache-Claim festzurren.
3. Zwei Graecum-Dozenten für einen Gratis-Piloten ab Wintersemester 2026/27 gewinnen — deren Antwort validiert den ganzen Plan, bevor in Accounts/Payment investiert wird.
