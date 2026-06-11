#!/usr/bin/env python3
"""Zeus – Vokabeltrainer: lokaler Server.

Serviert die statischen Dateien und stellt POST /api/extract bereit,
das Fotos von Lehrbuchseiten per Claude Vision in strukturierte
Vokabellisten umwandelt.

Start:  ANTHROPIC_API_KEY=sk-ant-... python3 server.py
"""
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import anthropic

PORT = 8765

VOKABEL_SCHEMA = {
    "type": "object",
    "properties": {
        "titel": {
            "type": "string",
            "description": "Lektionstitel falls auf der Seite erkennbar, sonst leerer String",
        },
        "vokabeln": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "griechisch": {
                        "type": "string",
                        "description": "Das griechische Wort in polytoner Orthographie (alle Akzente, Spiritus, Iota subscriptum exakt)",
                    },
                    "umschrift": {
                        "type": "string",
                        "description": "Lateinische Transliteration mit Akzent, z.B. 'ánthrōpos'",
                    },
                    "deutsch": {
                        "type": "string",
                        "description": "Deutsche Bedeutung(en), kurz",
                    },
                    "erklaerung": {
                        "type": "string",
                        "description": "Knappe grammatische oder etymologische Anmerkung, falls die Seite eine enthält oder sie didaktisch wichtig ist; sonst leer",
                    },
                },
                "required": ["griechisch", "umschrift", "deutsch", "erklaerung"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["titel", "vokabeln"],
    "additionalProperties": False,
}

PROMPT = (
    "Auf dem Bild ist eine Vokabelseite aus einem Altgriechisch-Lehrbuch. "
    "Extrahiere alle Vokabeleinträge vollständig und in der Reihenfolge der Seite. "
    "Achte penibel auf die polytone Orthographie (Spiritus asper/lenis, Akut, Gravis, "
    "Zirkumflex, Iota subscriptum). Bei Substantiven übernimm Genitiv und Artikel in das "
    "Feld 'griechisch', falls das Lehrbuch sie angibt. Grammatische Hinweise des Lehrbuchs "
    "(Stammformen, Rektion) gehören in 'erklaerung'. Erfinde keine Einträge, die nicht "
    "auf der Seite stehen."
)

client = anthropic.Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None


class Handler(SimpleHTTPRequestHandler):
    def _json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        # Statische Dateien nie cachen — vermeidet die Stale-Version-Probleme
        if self.command == "GET":
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self):
        if self.path != "/api/extract":
            self._json(404, {"error": "Unbekannter Endpunkt"})
            return
        if client is None:
            self._json(503, {
                "error": "ANTHROPIC_API_KEY nicht gesetzt. Server so starten: "
                         "ANTHROPIC_API_KEY=sk-ant-... python3 server.py"
            })
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(length))
            image_b64 = req["image"]
            media_type = req.get("media_type", "image/jpeg")
        except (KeyError, ValueError, json.JSONDecodeError):
            self._json(400, {"error": "Ungültige Anfrage — 'image' (base64) erwartet"})
            return

        try:
            response = client.messages.create(
                model="claude-opus-4-8",
                max_tokens=16000,
                thinking={"type": "adaptive"},
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64,
                            },
                        },
                        {"type": "text", "text": PROMPT},
                    ],
                }],
                output_config={
                    "format": {"type": "json_schema", "schema": VOKABEL_SCHEMA}
                },
            )
            text = next(b.text for b in response.content if b.type == "text")
            self._json(200, json.loads(text))
        except anthropic.AuthenticationError:
            self._json(401, {"error": "API-Key ungültig"})
        except anthropic.RateLimitError:
            self._json(429, {"error": "Rate-Limit erreicht — kurz warten und erneut versuchen"})
        except anthropic.APIStatusError as e:
            self._json(502, {"error": f"API-Fehler {e.status_code}: {e.message}"})
        except Exception as e:
            self._json(500, {"error": str(e)})


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    status = "aktiv" if client else "INAKTIV (ANTHROPIC_API_KEY fehlt)"
    print(f"Zeus-Server: http://localhost:{PORT}  ·  Foto-Import: {status}")
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
