# Entwicklungsleitfaden

Dieser Leitfaden deckt alles ab, was für die Entwicklung, das Testen und die Veröffentlichung von **toABify** erforderlich ist.
Dokumentation für Endanwender findet sich in [README.md](README.md).

---

## 1. Projektstruktur

```
toABify/
├── .github/
│   └── workflows/           # CI/CD: Linting, Tests, HACS, Release
├── custom_components/
│   └── toabify/             # HACS installiert nur dieses Verzeichnis
│       ├── __init__.py      # async_setup, WebSocket-Befehl, statischer Pfad, JS-Injektion
│       ├── const.py         # Alle Konstanten (Protokoll-IDs + Standardwerte)
│       ├── notify.py        # async_send_message Implementierung
│       ├── manifest.json    # Integrations-Manifest (Domain: "toabify")
│       ├── brand/
│       │   └── icon.png     # HACS/Brand Favicon
│       └── dist/            # Vendored Toastify-JS 1.12.0 + lokales toast_engine.js
│           ├── toastify.js
│           ├── toastify.css
│           └── toast_engine.js
├── scripts/
│   ├── check_version.py     # Validierung: Manifest ↔ CHANGELOG Versionsabgleich
│   ├── verify_vendor.py     # SHA-256 Integritätsprüfung für dist/ Dateien
│   └── vendor_hashes.txt    # Basis-Hashwerte für vendored Dateien
├── tests/
│   ├── conftest.py          # enable_custom_integrations Fixture
│   ├── test_init.py         # Tests für async_setup (statischer Pfad, WebSocket, JS-Injektion)
│   └── test_notify.py       # Tests für async_send_message (Standardwerte, Callbacks)
├── .editorconfig            # Editor-Einstellungen
├── .gitattributes           # Zeilenenden-Kontrolle (dist/ ausgeschlossen)
├── .pre-commit-config.yaml  # Ruff, Formatierung, Whitespace-Bereinigung, etc.
├── CHANGELOG.md             # Changelog mit semantischer Versionierung
├── CONTRIBUTING.md          # Verweist auf diese Datei
├── hacs.json                # HACS-Integrationseinstellungen (Repository-Root)
├── pyproject.toml           # Ruff, pytest, Python-Projektkonfiguration
├── requirements_dev.txt     # Entwicklungsabhängigkeiten
├── requirements_test.txt    # Test-Abhängigkeiten (pytest, HA-Test-Fixtures)
├── THIRD_PARTY_NOTICES.md   # Toastify-JS v1.12.0 Lizenzierung
└── README.md                # Dokumentation für Endanwender

> **Hinweis**: HACS installiert nur `custom_components/toabify/`. Entwicklungsdateien
> (Tests, Skripte, CI-Konfigurationen) sind repository-intern und werden nicht an Endanwender ausgeliefert.
```

---

## 2. Architektur

Der Datenfluss für eine Benachrichtigung:

1. Benutzer ruft `notify.toabify` Service auf → `notify.py` `async_send_message`
2. Service löst `toastify_event` auf dem Home Assistant Event-Bus aus
3. `websocket_subscribe_toast` leitet das Ereignis an abonnierte Browser-WebSocket-Clients weiter
4. `dist/toast_engine.js` (IIFE) empfängt das Ereignis und ruft Toastify-JS auf, um den Toast zu rendern

**Warum `toastify_*`-Bezeichner beibehalten werden:** Der Ereignisname (`toastify_event`),
der WebSocket-Typ (`toastify/subscribe`) und der URL-Pfad (`/toastify_lib`) sind in
`dist/toast_engine.js` hartcodiert. Eine Änderung würde bestehende Installationen ohne
eine koordinierte JS-Aktualisierung brechen. Sie werden absichtlich **nicht** während des
`toastify` → `toabify` Refactorings umbenannt (siehe
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) und den Abschnitt "Bekannte Abweichungen" unten).

---

## 3. Einrichtung (Windows 11 / PowerShell)

```powershell
py -3 -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
. .\.venv\Scripts\Activate.ps1
pip install -r requirements_dev.txt
pre-commit install
```

> **Windows-Hinweis**: `pytest-homeassistant-custom-component` installiert sich unter Umständen
> nicht sauber auf Windows aufgrund nativer HA-Abhängigkeiten. Falls dies fehlschlägt, bleiben
> `ruff check .` und `ruff format --check .` für lokale Validierungen verfügbar.
> Tests laufen in CI auf Linux.

---

## 4. Befehle

| Aktion | Befehl |
|---|---|
| Linting (prüfen) | `ruff check .` |
| Linting (korrigieren) | `ruff check . --fix` |
| Formatierung (prüfen) | `ruff format --check .` |
| Formatierung (anwenden) | `ruff format .` |
| Tests ausführen | `pytest` |
| Tests ausführen (spezifische Datei) | `pytest tests/test_notify.py` |
| Version-Konsistenz | `python scripts\check_version.py` |
| Vendor-Integrität | `python scripts\verify_vendor.py` |
| Pre-commit (alle Hooks) | `pre-commit run --all-files` |
| Virtuelle Umgebung aktivieren | `. .\.venv\Scripts\Activate.ps1` |

---

## 5. Testsuite manuell ausführen

### Voraussetzungen

Stellen Sie sicher, dass die virtuelle Umgebung eingerichtet und aktiviert ist (siehe Abschnitt 3):

```powershell
. .\.venv\Scripts\Activate.ps1
pip install -r requirements_test.txt
```

### Tests ausführen

Führen Sie die Tests aus, indem Sie in der Projektwurzel `pytest` ausführen:

```powershell
pytest
```

### Tests mit Ausgabe anzeigen

Um detailliertere Ausgaben zu erhalten (inklusive Print-Statement- und Log-Ausgaben):

```powershell
pytest -v --tb=short
```

### Spezifische Test-Datei oder -klasse ausführen

Um nur eine bestimmte Test-Datei oder -Klasse auszuführen:

```powershell
pytest tests/test_notify.py
pytest tests/test_notify.py::test_send_message_defaults
```

### Tests mit Coverage-Bericht (falls installiert)

Falls das `pytest-cov`-Plugin installiert ist:

```powershell
pytest --cov=custom_components/toabify --cov-report=term-missing
```

### Tests in CI

Die Tests werden in GitHub Actions auf Linux ausgeführt (siehe `.github/workflows/ci.yml`).
Auf Windows kann `pytest-homeassistant-custom-component` aufgrund nativer Abhängigkeiten
Probleme verursachen. Verwenden Sie alternativ `ruff check .` für lokale Code-Qualitätsprüfungen.

---

## 6. Pre-commit Hooks

Die folgenden Hooks sind in `.pre-commit-config.yaml` konfiguriert:

| Hook | Zweck | Schließt `dist/` aus? |
|---|---|---|
| `ruff` | Linting + Import-Sortierung | Ja |
| `ruff-format` | Code-Formatierung | Ja |
| `trailing-whitespace` | Abschließende Leerzeichen entfernen | Ja |
| `end-of-file-fixer` | Sicherstellen, dass Dateien mit Newline enden | Ja |
| `check-yaml` | YAML-Validierung | Nein (kein YAML in dist) |
| `check-json` | JSON-Validierung (`.pre-commit-config.yaml`, `hacs.json`) | Nein (kein JSON in dist) |

> `pytest` ist **kein** Pre-commit Hook; es wird ausschließlich in CI
> (GitHub Actions) ausgeführt, da das HA-Test-Fixture einen vollständigen Event-Loop
> und Socket-Unterstützung erfordert, die in einer Pre-commit-Umgebung auf Windows nicht verfügbar sind.

---

## 7. Vendored Code (`dist/`)

Das Verzeichnis `custom_components/toabify/dist/` enthält drei Dateien:

| Datei | Herkunft | Lizenz |
|---|---|---|
| `toastify.js` | Toastify-JS v1.12.0 | MIT |
| `toastify.css` | Toastify-JS v1.12.0 | MIT |
| `toast_engine.js` | toABify (lokal) | MIT (Projeklizenz) |

**Diese Dateien dürfen nicht bearbeitet, formatiert oder mit Hooks verarbeitet werden.** Sie müssen
byte-gleich zum upstream Toastify-JS-Release oder zur lokalen Engine-Implementierung bleiben.

- `.gitattributes` setzt `-text` für `dist/**` zur Prävention von Zeilenenden-Konvertierungen.
- `.pre-commit-config.yaml` schließt `dist/` von allen Formatierern und Korrigierungen aus.
- `scripts/vendor_hashes.txt` speichert SHA-256 Hashwerte für jede Datei.
- `scripts/verify_vendor.py` validiert alle Dateien gegen die Basiswerte.

**Update-Prozess** (bei Upgrade von Toastify-JS oder Modifikation der Engine):

1. Datei(en) in `dist/` ersetzen.
2. Änderung gegenüber upstream verifizieren, bevor Hashwerte aktualisiert werden:
   - Für Toastify-JS-Dateien: `toastify.js` und `toastify.css` von dem
     npm-Paket `toastify-js@1.12.0` herunterladen und SHA-256 vergleichen.
3. `vendor_hashes.txt` **nur** aktualisieren, wenn der Vergleich mit upstream
   die neue Version bestätigt (nicht blind bei einem Mismatch aktualisieren).
4. `THIRD_PARTY_NOTICES.md` aktualisieren, wenn sich die upstream-Version/Lizenz geändert hat.
5. `python scripts\verify_vendor.py` ausführen, um alle Dateien zu validieren.
6. Manuelle Tests in Home Assistant durchführen: Toasts rendern, `onClick` funktioniert,
   und `visibility: all` erscheint in Einstellungen, Logs, etc.

---

## 8. Namenskonventionen

| Kontext | Konvention | Beispiel |
|---|---|---|
| Python-Variablen/Funktionen | `snake_case` | `async_send_message` |
| Python-Konstanten | `UPPER_SNAKE_CASE` | `DEFAULT_DURATION_EVENT` |
| Python-Klassen | `PascalCase` | `ToastifyNotificationService` |

**Ausnahmen** — diese sind externe API-Verträge und dürfen **nicht** umbenannt werden:

| Bezeichner | Kontext | Warum unverändert |
|---|---|---|
| `oldestFirst` | HA-Ereignisdaten | Toastify-JS-Konfig Schlüssel |
| `onClick` | HA-Ereignisdaten | Toastify-JS-Konfig Schlüssel |
| `action_data` | HA-Ereignisdaten | YAML-freundlicher Schlüssel in Benutzer-Konfigurationen |
| `button_label` | HA-Ereignisdaten | Frontend-Konfigurationsschlüssel |
| `toastify_event` | Event-Bus | Hartcodiert in `toast_engine.js` |
| `toastify/subscribe` | WebSocket-Typ | Hartcodiert in `toast_engine.js` |
| `toastify_lib` | URL-Pfad | Hartcodiert in `toast_engine.js` |

---

## 9. Test-Struktur

Tests verwenden `pytest` mit `pytest-homeassistant-custom-component`, welches ein
`hass`-Fixture bereitstellt, das eine minimale Home Assistant-Instanz startet.

### Test-Dateien

- **`tests/conftest.py`**: Definiert das `enable_custom_integrations` Fixture, das den
  `DATA_CUSTOM_COMPONENTS` Cache leert, damit die Test-Integration über Tests hinweg neu geladen werden kann.
- **`tests/test_init.py`**: Charakterisierungstests für `async_setup`:
  - Statischer Pfad `/toastify_lib` zeigt auf das vendored dist-Verzeichnis
  - WebSocket-Befehl `toastify/subscribe`
  - JS-Injektion (`/toastify_lib/toast_engine.js`)
- **`tests/test_notify.py`**: Charakterisierungstests für `async_send_message`:
  - Standardwerte für alle Ereignisdatenfelder
  - Leere Nachricht-Behandlung
  - Icon/Avatar Fallback-Logik
  - Callback als String-URL (mit/ohne `/` oder `http` Präfix)
  - Callback als Dict (Service-Aufruf + Timer)
  - Standard-Timer-Dauer (3000 ms wenn `duration` nicht gesetzt)
  - Kein Timer wenn `duration <= 0` oder negativ

### Was NICHT getestet wird

- Die JavaScript-Engine (`dist/toast_engine.js`) — sie ist ein IIFE ohne
  Test-Framework. Manuelle Browser-Tests sind der Validierungspfad.
- Integration mit einer Live-Home-Assistant-Instanz — Tests verwenden Mocks.

### Manuelle Tests im Browser

Nach dem Deployen von Änderungen im Browser verifizieren:

1. Einfachen Toast senden:
   ```yaml
   service: notify.toabify
   data:
     message: "Test toast"
   ```
2. Toast mit `onClick` Service-Aufruf senden.
3. Toast mit `visibility: all` senden — verifiziert, dass er in Einstellungen, Logs, etc. erscheint.

---

## 10. Manuelle Tests in Home Assistant

1. Kopieren Sie den `toabify`-Ordner in die HA-Konfiguration:
   ```
   config/custom_components/toabify/
   ```
2. Fügen Sie zu `configuration.yaml` hinzu:
   ```yaml
   notify:
     - platform: toabify
       name: toabify
   ```
3. Home Assistant neu starten.
4. Service aufrufen:
   ```yaml
   service: notify.toabify
   data:
     message: "Hallo von toABify!"
     data:
       color: "success"
       duration: 5000
   ```
5. Erwartetes Ergebnis: Ein grüner Toast erscheint in der rechten oberen Ecke
   des Lovelace-Dashboards für 5 Sekunden.

---

## 11. Veröffentlichungsprozess

1. Version in `custom_components/toabify/manifest.json` erhöhen.
2. Einen neuen Abschnitt zu `CHANGELOG.md` unter der neuen Version hinzufügen.
3. `python scripts\check_version.py` ausführen, um Konsistenz zu validieren.
4. Auf einen Feature-Branch committen und pushen.
5. Stellen Sie sicher, dass CI besteht (Linting, Tests, HACS, Hassfest).
6. Lokal in `main` zusammenführen **ohne** Pull Request:
   ```powershell
   git checkout main
   git merge --no-ff chore/refactor_hacs_structure
   git tag v2.0.0
   git push origin main --tags
   ```
7. Der **Release**-Workflow erstellt automatisch eine GitHub-Release.
8. In HACS installieren und verifizieren, dass Toasts im Browser erscheinen.

---

## 12. CI-Übersicht

| Workflow | Datei | Trigger | Zweck |
|---|---|---|---|
| CI | `.github/workflows/ci.yml` | `push`, `pull_request` | Linting + Tests + Hassfest |
| HACS | `.github/workflows/hacs.yml` | `push` | Validierung der HACS-Repositorystruktur |
| Release | `.github/workflows/release.yml` | `push: tags` | GitHub-Release aus Tag erstellen |

---

## 13. Bekannte Abweichungen (Nicht geändert in diesem Refactoring)

1. **`duration` doppelte Standardwerte**: Ereignisdaten-`duration` standardisiert auf `5000` ms
   (für die Anzeige), aber der serverseitige Callback-Timer standardisiert auf `3000` ms.
   Wenn `duration` explizit gesetzt ist, verwenden beide dens gleiche Wert.

2. **`button_label` wird gesendet, aber nicht angezeigt**: Der `button_label`-Wert ist im
   Ereignis-Payload enthalten, aber die Toastify-JS-Engine (v1.12.0) verwendet ihn nicht
   zur Schaltflächen-Rendierung. Die Engine verwendet stattdessen `onClick.label`.

3. **`oldestFirst` hat keine sichtbare Wirkung**: Toastify-JS v1.12.0 setzt
   `defaults.oldestFirst = true`, sodass das Flag ein No-Op ist.

4. **`innerHTML` für Inhalte**: Toast-Inhalte werden über `innerHTML` in
   `toast_engine.js` gerendert (spezifisch `btn.innerHTML` mit `onClick.label`),
   was ein XSS-Risiko darstellt, wenn unvertrauene Benutzereingaben übergeben werden.
   Die vendored Toastify-JS-Bibliothek verwendet standardmäßig `escapeMarkup`;
   nur die lokale Engine umgeht dies.

5. **`action.split(".")`**: In `notify.py` wird die Callback-Aktion bei
   jedem `.` getrennt (`split(".")`). Aktionen mit mehr als einem Punkt
   (z.B. `"light.turn_on.foo"`) lösen einen `ValueError` aus. Dienst-Namen können
   keine Punkte enthalten, daher ist dies das ursprüngliche 1:1-Verhalten —
   nicht geändert.

6. **YAML-konfiguration**: Es gibt keine `config_flow.py`; der Dienst wird
   ausschließlich über `configuration.yaml` konfiguriert.

---

## 14. Fehlerbehebung

| Symptom | Ursache | Lösung |
|---|---|---|
| HACS: "Repository structure ... is not compliant" | Ordnername oder Pfad falsch | Stellen Sie sicher, dass `custom_components/toabify/` im Repository-Root existiert |
| Hassfest-Fehler in `manifest.json` | Fehlende erforderliche Schlüssel oder falsche Reihenfolge | Prüfen Sie `manifest.json` gegen [HA-Schema](https://developers.home-assistant.io/docs/core/integration/manifest/) |
| Toast wird nicht angezeigt | `visibility: dashboard`, aber URL ist kein Lovelace | Setzen Sie `visibility: all` oder korrigieren Sie Ihre Dashboard-URL |
| Toast wird nicht angezeigt | Browser-Cache veraltet | Hard-Refresh (Strg+Shift+R) |
| Toast wird nicht angezeigt | Engine nicht geladen | Konsolen der Entwicklungsumgebung auf `TOASTIFY` Log-Nachricht prüfen |
| Test schlägt auf Windows fehl | `pytest_socket` blockiert Event-Loop | Tests in CI (Linux) ausführen oder `ruff` für lokale Code-Qualitätsprüfungen verwenden |
