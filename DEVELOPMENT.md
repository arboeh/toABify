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
│   ├── test_init.py         # Tests für async_setup_entry / async_unload_entry
│   ├── test_notify.py       # Tests für async_send_message (Standardwerte, Callbacks)
│   ├── e2e/                 # Playwright E2E-Tests (Chromium)
│   │   ├── fixtures.js      # Routing ohne Server, Testseite, open_page/push_toast
│   │   └── toast_engine.spec.js  # E2E-Tests für dist/toast_engine.js (DOM, Popups, Service-Aufrufe)
│   └── js/
│       └── test_toast_engine.test.js  # Vitest-Tests für dist/toast_engine.js (DOM, WebSocket, Toastie-Rendering)
├── .editorconfig            # Editor-Einstellungen
├── .gitattributes           # Zeilenenden-Kontrolle (dist/ ausgeschlossen)
├── .pre-commit-config.yaml  # Ruff, Formatierung, Whitespace-Bereinigung, etc.
├── CHANGELOG.md             # Changelog mit semantischer Versionierung
├── CONTRIBUTING.md          # Verweist auf diese Datei
├── hacs.json                # HACS-Integrationseinstellungen (Repository-Root)
├── pyproject.toml           # Ruff, pytest, Python-Projektkonfiguration
├── package.json             # Vitest (JS-Tests) + Playwright (E2E-Tests) für toast_engine.js
├── playwright.config.js     # Playwright-Konfiguration (testDir: tests/e2e, Chromium)
├── vitest.config.ts         # Vitest-Konfiguration (happy-dom-Umgebung)
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

## 3. Einrichtung (Windows 11 / PowerShell oder Git Bash)

### PowerShell

```powershell
py -3 -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
. .\.venv\Scripts\Activate.ps1
pip install -r requirements_dev.txt
pre-commit install
```

### Git Bash (MINGW64)

```bash
py -3 -m venv .venv
source .venv/Scripts/activate
pip install -r requirements_dev.txt
pre-commit install
```

### Node.js (JS-Tests)

```powershell
npm ci
```

`package-lock.json` ist eingecheckt; `npm ci` installiert exakt die gesperrten
Versionen (CI-tauglich). Nur wenn sich `package.json` ändert, wird das Lockfile
mit `npm install` aktualisiert.

> **Windows-Hinweis**: `pytest-homeassistant-custom-component` installiert sich unter Umständen
> nicht sauber auf Windows aufgrund nativer HA-Abhängigkeiten. Falls dies fehlschlägt, bleiben
> `ruff check .` und `ruff format --check .` für lokale Validierungen verfügbar.
> Tests laufen in CI auf Linux.

---

## 4. Befehle

### PowerShell

| Aktion | Befehl |
|---|---|
| Linting (prüfen) | `ruff check .` |
| Linting (korrigieren) | `ruff check . --fix` |
| Formatierung (prüfen) | `ruff format --check .` |
| Formatierung (anwenden) | `ruff format .` |
| Node-Abhängigkeiten installieren | `npm ci` (nutzt `package-lock.json`) |
| Python-Tests ausführen | `pytest` |
| Python-Tests (spezifische Datei) | `pytest tests/test_notify.py` |
| JS-Tests ausführen | `npx vitest run` |
| JS-Tests (spezifische Datei) | `npx vitest run tests/js/toast_engine.test.js` |
| E2E-Tests ausführen | `npm run test_e2e` |
| E2E-Tests (einmalige Einrichtung) | `npx playwright install chromium` |
| Version-Konsistenz | `python scripts/check_version.py` |
| Vendor-Integrität | `python scripts/verify_vendor.py` |
| Pre-commit (alle Hooks) | `pre-commit run --all-files` |
| Virtuelle Umgebung aktivieren | `. .\.venv\Scripts\Activate.ps1` |

### Git Bash (MINGW64)

| Aktion | Befehl |
|---|---|
| Linting (prüfen) | `ruff check .` |
| Linting (korrigieren) | `ruff check . --fix` |
| Formatierung (prüfen) | `ruff format --check .` |
| Formatierung (anwenden) | `ruff format .` |
| Node-Abhängigkeiten installieren | `npm ci` (nutzt `package-lock.json`) |
| Python-Tests ausführen | `pytest` |
| Python-Tests (spezifische Datei) | `pytest tests/test_notify.py` |
| JS-Tests ausführen | `npx vitest run` |
| JS-Tests (spezifische Datei) | `npx vitest run tests/js/toast_engine.test.js` |
| E2E-Tests ausführen | `npm run test_e2e` |
| E2E-Tests (einmalige Einrichtung) | `npx playwright install chromium` |
| Version-Konsistenz | `python scripts/check_version.py` |
| Vendor-Integrität | `python scripts/verify_vendor.py` |
| Pre-commit (alle Hooks) | `pre-commit run --all-files` |
| Virtuelle Umgebung aktivieren | `source .venv/Scripts/activate` |

---

## 5. Testsuite manuell ausführen

### Voraussetzungen

Stellen Sie sicher, dass die virtuelle Umgebung eingerichtet und aktiviert ist (siehe Abschnitt 3):

```bash
source .venv/Scripts/activate
pip install -r requirements_test.txt
```

> **Windows:** `pytest` läuft unter Windows **nicht** — `homeassistant.runner`
> importiert `fcntl`, das nur unter Python auf Linux existiert; der
> Plugin-Import bricht ab. Lokale Ausführung daher in **WSL2 (Ubuntu)** mit
> Python 3.12 und dem gepinnten `pytest-homeassistant-custom-component` aus
> `requirements_test.txt`:
>
> ```bash
> python3.12 -m venv --without-pip ~/venv-t312
> curl -sS https://bootstrap.pypa.io/get-pip.py | ~/venv-t312/bin/python
> . ~/venv-t312/bin/activate && pip install --index-url https://pypi.org/simple -r requirements_test.txt
> pytest -v
> ```
>
> `python3.12-venv`/`ensurepip` fehlt in manchen WSL-Images (daher
> `--without-pip` + `get-pip.py`, kein Root nötig); der Standard-Index mancher
> Distributionen ist veraltet, deshalb der explizite pypi.org-Index.

### Tests ausführen

Führen Sie die Tests aus, indem Sie in der Projektwurzel `pytest` ausführen:

```bash
pytest
```

### Tests mit Ausgabe anzeigen

Um detailliertere Ausgaben zu erhalten (inklusive Print-Statement- und Log-Ausgaben):

```bash
pytest -v --tb=short
```

### Spezifische Test-Datei oder -klasse ausführen

Um nur eine bestimmte Test-Datei oder -Klasse auszuführen:

```bash
pytest tests/test_notify.py
pytest tests/test_notify.py::test_send_message_defaults
```

### Tests mit Coverage-Bericht (falls installiert)

Falls das `pytest-cov`-Plugin installiert ist:

```bash
pytest --cov=custom_components/toabify --cov-report=term-missing
```

### Tests in CI

Die Tests werden in GitHub Actions auf Linux ausgeführt (siehe `.github/workflows/ci.yml`).
Auf Windows kann `pytest-homeassistant-custom-component` aufgrund nativer Abhängigkeiten
Probleme verursachen. Verwenden Sie alternativ `ruff check .` für lokale Code-Qualitätsprüfungen.
JS-Tests (`npx vitest run`) laufen auf allen Plattformen.

---

## 6. Pre-commit Hooks

Die folgenden Hooks sind in `.pre-commit-config.yaml` konfiguriert:

| Pre-commit Hook | Zweck | Schließt `dist/` aus? |
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
   4. `python scripts/verify_vendor.py` ausführen, um alle Dateien zu validieren.
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
Zusätzlich gibt es JavaScript-Tests mit `vitest` für die Frontend-Engine sowie
E2E-Tests mit `playwright` (Chromium), die die Engine ohne Home Assistant gegen
echtes DOM und echte Popups fahren.

### Test-Dateien

- **`tests/conftest.py`**: Definiert das `enable_custom_integrations` Fixture, das den
  `DATA_CUSTOM_COMPONENTS` Cache leert, damit die Test-Integration über Tests hinweg neu geladen werden kann.
- **`tests/test_init.py`**: Charakterisierungstests für `async_setup_entry` / `async_unload_entry`:
  - Statischer Pfad `/toastify_lib` zeigt auf das vendored dist-Verzeichnis
  - WebSocket-Befehl `toastify/subscribe`
  - JS-Injektion (`/toastify_lib/toast_engine.js`)
  - Koordinator-Instanziierung und State-Tracking
  - `async_unload_entry` ruft `remove_extra_js_url` auf
- **`tests/test_notify.py`**: Charakterisierungstests für `async_send_message`:
  - Standardwerte für alle Ereignisdatenfelder
  - Leere Nachricht-Behandlung
  - Farbvalidierung (Theme-Namen, Hex inkl. `#RGB`-Expansion, ungültige Werte)
  - Explizite `null`-Werte fallen auf die Schema-Defaults zurück
  - Icon/Avatar Fallback-Logik
  - `button_label`-Übernahme in `onClick.label` (auch: eigener `onClick.label` gewinnt)
  - Callback als String-URL (mit/ohne `/` oder `http` Präfix)
  - Callback als Dict (Service-Aufruf + Timer)
  - Standard-Timer-Dauer (3000 ms wenn `duration` nicht gesetzt)
  - Kein Timer wenn `duration <= 0` oder negativ
- **`tests/test_readme_examples.py`**: Schutztests für die Dokumentation:
  - Extrahiert alle ```yaml```-Blöcke aus `README.md` und `README.de.md`
  - Validiert jeden Block mit `action: notify.toabify` gegen `_NOTIFY_DATA_SCHEMA`
    (nach dem Inline-Aussortieren von `null`-Werten), damit die Doku keinen
    Aufruf beschreibt, den Home Assistant ablehnt (Regression: die entfernte
    String-Form von `onClick`)
  - Prüft, dass beide READMEs mindestens ein `notify.toabify`-Beispiel enthalten
  - Synchron, ohne `hass`-Fixture
- **`tests/js/test_toast_engine.test.js`**: Vitest-Tests für `dist/toast_engine.js`:
  - WebSocket-Abonnement mit Typ `toastify/subscribe`
  - CSS/JS-Ressourcen-Ladung (`toastify-css`, `toastify-js`)
  - Keyframe-Animation (`toast-label-pulse`)
  - Toast-Erstellung mit Standardwerten (Dauer, Position, Gravitation)
  - Theme-Farben (`success`, `info`, `warning`, `error`, `default`)
  - Sichtbarkeitsfilterung (`dashboard` vs. `all`)
  - Icon-Rendering (MDI `ha-icon` vs. `img` für URLs)
  - `onClick`-Aktionen (URL-Öffnung und HA-Service-Aufrufe)
  - Custom-Button-Label
- **`tests/e2e/fixtures.js`**: Playwright-Fixture ohne Server:
  - Routet `http://toabify.test/**` auf **Context**-Ebene (bedient auch Popups)
  - Liefert `/toastify_lib/*` direkt aus `dist/`, jeden anderen Pfad als Testseite
  - Testseite mockt das `hass`-Objekt (`subscribeMessage` liefert
    `window.__toast_push`, `callService` zeichnet Aufrufe in
    `window.__service_calls` auf)
  - Helfer `open_page(page, path)` (wartet auf das Engine-Abonnement, Poll-Takt 1 s)
    und `push_toast(page, overrides)` (Server-Defaults plus Overrides)
- **`tests/e2e/toast_engine.spec.js`**: E2E-Tests der **echten Engine** mit dem
  **echten Toastify** im Chromium, ohne Home Assistant. Zweck: Verhalten prüfen,
  das Vitest in `happy-dom` nicht abbildet — berechnete Styles, Klasse
  `toastify-top`/`toastify-bottom`, Popups per `window.open`, Service-Aufrufe
  über den `hass`-Mock, Sichtbarkeit pro `window.location.pathname`. Geprüft
  werden nur DOM, Styles, Popups und Mock-Aufrufe, keine Screenshots:
  - Farb-/Kontrast-Rendering (`success`-Theme, `#ffffff`/`#000000`-Kontrasttext)
  - Button-Logik: kein Button ohne `onClick`, nur X mit `close: true`
  - `onClick: {}` → `CLOSE`, eigenes Label, Pfad-Aktion öffnet neuen Tab,
    `domain.service`-Aktion ruft `hass.callService` auf, unbekannter Key
    (`URL`) tut nichts
  - Label wird als Text gerendert (`a &amp; b &lt;b&gt;x&lt;/b&gt;` ergibt
    wörtlich `a & b <b>x</b>` — klärt die `&Ajax;`-Anomalie)

### Was NICHT getestet wird

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
2. Home Assistant neu starten.
3. Integration über **Einstellungen → Geräte & Dienste → Integration hinzufügen**,
   Suche nach **toABify**, abschließen. Der Config-Flow legt einen Config-Entry
   ohne weitere Optionen an; `configuration.yaml` wird nicht benötigt.
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
3. `python scripts/check_version.py` ausführen, um Konsistenz zu validieren.
4. Auf einen Feature-Branch committen und pushen.
5. Stellen Sie sicher, dass CI besteht (Linting, Tests, HACS, Hassfest).
6. Lokal in `main` zusammenführen **ohne** Pull Request:
   ```bash
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
| CI | `.github/workflows/ci.yml` | `push`, `pull_request` | Linting + Tests (Python, JS, E2E) + Hassfest + Vendor-Check |
| HACS | `.github/workflows/hacs.yml` | `push` | Validierung der HACS-Repositorystruktur |
| Release | `.github/workflows/release.yml` | `push: tags` | GitHub-Release aus Tag erstellen |

Jobs in `ci.yml` (unabhängig voneinander):

| Job | Lauf | Zweck |
|---|---|---|
| `lint` | `ruff check .`, `ruff format --check .` | Code-Qualität |
| `test` | `pytest --cov=custom_components/toabify` | Python-Tests |
| `hassfest` | `home-assistant/actions/hassfest@master` | HA-Repositoryvalidierung |
| `vendor-check` | `python scripts/verify_vendor.py` | `dist/`-Integrität |
| `js_tests` | `npm ci`, `npm test` | Vitest auf `dist/toast_engine.js` |
| `e2e_tests` | `npm ci`, `npx playwright install --with-deps chromium`, `npm run test_e2e` | Playwright-E2E (Chromium); Traces als Artefakt bei Fehlschlag |

---

## 13. Bekannte Abweichungen (Nicht geändert in diesem Refactoring)

1. **`duration` doppelte Standardwerte**: Ereignisdaten-`duration` standardisiert auf `5000` ms
   (für die Anzeige), aber der serverseitige Callback-Timer standardisiert auf `3000` ms.
   Wenn `duration` explizit gesetzt ist, verwenden beide dens gleiche Wert.

2. **`button_label` wird serverseitig nach `onClick.label` übernommen**: Die
   Toastify-JS-Engine (v1.12.0) liest die Schaltflächen-Beschriftung ausschließlich aus
   `onClick.label`; `button_label` kommt in `dist/toast_engine.js` nicht vor. Damit die
   Engine den gewählten Text zeigt, kopiert `_apply_button_label` (in `notify.py`) den
   Wert von `button_label` in `onClick.label`, sofern dort kein eigener Wert gesetzt ist.
   Reihenfolge: `onClick.label`, dann `button_label`, dann das Engine-eigene Fallback
   `CLOSE`. Ein `button_label` ohne `onClick` erzeugt keine Schaltfläche, denn die Engine
   rendert einen Button nur unter `if (d.onClick)`.

3. **`oldestFirst` hat keine sichtbare Wirkung**: Toastify-JS v1.12.0 setzt
   `defaults.oldestFirst = true`, sodass das Flag ein No-Op ist.

4. **`innerHTML` nur für die Button-Beschriftung**: In `toast_engine.js` wird
   ausschließlich die Schaltflächen-Beschriftung über `btn.innerHTML` mit
   `onClick.label` eingesetzt; die `message` selbst escaped Toastify-JS
   (`escapeMarkup`). Da `dist/` nicht geändert werden darf (Vendor-Hashes in
   `scripts/vendor_hashes.txt`), entschärft `notify.py` serverseitig:
   `_apply_button_label` (in `notify.py`) escaped `& < > " '`, kappt die Länge bei
   200 Zeichen (Kappung, keine Ablehnung) und weist Nicht-Strings (nur über
   `onClick.label` erreichbar, da `button_label` schema-validiert ist) mit einem
   `vol.Invalid` zurück, das als `ServiceValidationError` an den Aufrufer geht.
   Der Choke-Point bleibt `_apply_button_label`: sowohl `button_label` als auch
   ein explizites `onClick.label` gehen durch dieselbe Behandlung. Die Engine
   selbst ist unverändert.
   Der Choke-Point bleibt `_apply_button_label`: sowohl `button_label` als auch
   ein explizites `onClick.label` gehen durch dieselbe Behandlung. Die Engine
   selbst ist unverändert.

5. **`action.split(".")`**: In `notify.py` wird die Callback-Aktion bei
   jedem `.` getrennt (`split(".")`). Aktionen mit mehr als einem Punkt
   (z.B. `"light.turn_on.foo"`) lösen einen `ValueError` aus. Dienst-Namen können
   keine Punkte enthalten, daher ist dies das ursprüngliche 1:1-Verhalten —
   nicht geändert.

6. **Einrichtung**: Die Integration verwendet einen Config-Flow (`config_flow.py`).
   Die Einrichtung erfolgt über **Einstellungen → Geräte & Dienste → Integration
   hinzufügen**; `configuration.yaml` wird nicht benötigt.

7. **`title` und `target` in der Service-Beschreibung**: `notify.toabify` ist ein
   Legacy-Notify-Service. Home Assistant registriert ihn mit dem generischen
   `NOTIFY_SERVICE_SCHEMA` (`message`, `title`, `target`, `data`) und beschreibt
   die Felder in der UI aus `homeassistant/components/notify/services.yaml`.
   Beide Felder werden vom Core akzeptiert und von `async_send_message` stillschweigend
   ignoriert. Damit die Entwicklerwerkzeuge keine nicht unterstützten Felder anzeigen,
   überschreibt `ToastifyNotificationService.async_register_services` (erst `super()`,
   dann `async_set_service_schema`) die Core-Beschreibung mit den tatsächlich
   unterstützten Feldern `message` und `data` — definiert in `const.py`
   (`NOTIFY_SERVICE_NAME`, `NOTIFY_SERVICE_DESCRIPTION`, `NOTIFY_SERVICE_FIELDS`).
   Die Laufzeit-Validierung des Core bleibt unverändert: ein Aufruf mit `title`
   oder `target` schlägt nicht fehl. Die frühere `custom_components/toabify/services.yaml`
   war toter Code (der Core liest `notify/services.yaml`, nicht die der Plattform)
   und wurde entfernt.

   **Fehlerbehandlung**: Schlägt `super().async_register_services()` fehl, wird der
   Fehler weitergegeben, denn dann ist gar kein Service registriert. Das Überschreiben
   der Beschreibung ist dagegen rein kosmetisch — der Service funktioniert bereits.
   Ein Fehler dort wird deshalb nur geloggt (`_LOGGER.exception`) und nicht
   weitergereicht, damit ein funktionierender Service nie an seiner UI-Beschreibung
   scheitert.

8. **`onClick` wird nur als Objekt akzeptiert**: Ein String (z. B.
   `onClick: "/lovelace/0"`) wird vom Schema mit `expected dict at 'onClick'`
   abgelehnt. Die Kurzform gilt nur für `callback`. Die String-Kurzform für `onClick`
   ist bewusst nicht ergänzt (Funktionsentscheidung, offen).

9. **Unbekannte Schlüssel in `onClick` werden ignoriert**: Das Schema deklariert
   `onClick` als beliebiges `dict`. Die Engine liest ausschließlich
   `action`, `action_data`, `label` und `feedback`; ein falsch geschriebener Schlüssel
   (z. B. `URL` statt `action`) wird ohne Fehler verworfen. `executeAction` liefert dann
   `false`, und der Toast schließt sich nach der Dauer — von außen sieht es so aus, als
   würde "nichts passieren". Eine Warnung (`_LOGGER.warning`) oder eine Schema-Validierung
   wäre möglich, ist aber bewusst nicht umgesetzt (offen).

10. **`callback` hat zwei Formen**: Als String (`/...` oder `http...`) wird der Wert im
    Browser beim Verschwinden des Toasts geöffnet (`window.open`, Popup-Blocker möglich).
    Als Objekt (`action`, `action_data`) ist es ein **serverseitiger Dienstaufruf** nach
    `duration` ms (ohne `duration` nach `3000` ms). Bei `duration <= 0` wird er nie
    ausgeführt. Beide Formen sind live verifiziert.

11. **`gravity: center` rendert oben**: Das Schema akzeptiert `top`, `bottom` und `center`.
    Die Engine übergibt `gravity` direkt an Toastify-JS (`d.gravity || "top"`), und
    `center` wird von Toastify-JS als `top` behandelt. Der Wert ist daher in den
    READMEs als „akzeptiert, rendert aber oben" dokumentiert, ohne als Empfehlung
    zu gelten.

12. **Hex-Farben**: `color` akzeptiert die sechs Theme-Namen sowie Hex-Farben
    (`#RGB`, `#RRGGBB`, `#RRGGBBAA`). Ein `#RGB`-Wert wird in `_validate_color`
    (in `notify.py`) zu `#RRGGBB` erweitert, weil die Engine die
    Label-Kontrastfarbe nur aus den ersten sechs Zeichen berechnet
    (`getContrastColor`). Die Engine selbst unterstützt Hex bereits
    (`TOAST_THEMES[colorInput] || d.color`), nur das Server-Schema hat es vorher
    abgelehnt.

---

## 14. Fehlerbehebung

| Symptom | Ursache | Lösung |
|---|---|---|
| HACS: "Repository structure ... is not compliant" | Ordnername oder Pfad falsch | Stellen Sie sicher, dass `custom_components/toabify/` im Repository-Root existiert |
| Hassfest-Fehler in `manifest.json` | Fehlende erforderliche Schlüssel oder falsche Reihenfolge | Prüfen Sie `manifest.json` gegen [HA-Schema](https://developers.home-assistant.io/docs/core/integration/manifest/) |
| Toast wird nicht angezeigt | `visibility: dashboard`, aber URL ist kein Lovelace | Setzen Sie `visibility: all` oder korrigieren Sie Ihre Dashboard-URL |
| Toast wird nicht angezeigt | Browser-Cache veraltet | Hard-Refresh (Strg+Shift+R) |
| Toast wird nicht angezeigt | Engine nicht geladen | Konsolen der Entwicklungsumgebung auf `TOASTIFY` Log-Nachricht prüfen |
| Test schlägt auf Windows fehl | `pytest-homeassistant-custom-component` benötigt native Abhängigkeiten (z.B. `pygame`), die auf Windows nicht installierbar sind | Tests in CI (Linux) ausführen oder `ruff check .` / `ruff format --check .` für lokale Code-Qualitätsprüfungen verwenden |
