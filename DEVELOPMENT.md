# Development Guide

This guide covers everything needed to develop, test, and release **toABify**.
User-facing documentation lives in [README.md](README.md).

---

## 1. Project Layout

```
toABify/
├── .github/
│   └── workflows/           # CI/CD: lint, test, HACS, release
├── custom_components/
│   └── toabify/             # HACS delivers only this directory
│       ├── __init__.py      # async_setup, WebSocket command, static path, JS injection
│       ├── const.py         # All constants (protocol IDs + defaults)
│       ├── notify.py        # async_send_message implementation
│       ├── manifest.json    # Integration manifest (domain: "toabify")
│       ├── hacs.json        # HACS integration settings
│       ├── brand/
│       │   └── icon.png     # HACS/Brand favicon
│       └── dist/            # Vendored Toastify-JS 1.12.0 + local toast_engine.js
│           ├── toastify.js
│           ├── toastify.css
│           └── toast_engine.js
├── scripts/
│   ├── check_version.py     # Validate manifest ↔ CHANGELOG version match
│   ├── verify_vendor.py     # SHA-256 integrity check for dist/ files
│   └── vendor_hashes.txt    # Baseline hashes for vendored files
├── tests/
│   ├── conftest.py          # enable_custom_integrations fixture
│   ├── test_init.py         # Tests for async_setup (static path, WS, JS injection)
│   └── test_notify.py       # Tests for async_send_message (defaults, callbacks)
├── .editorconfig            # Editor settings
├── .gitattributes           # Line-ending control (dist/ excluded)
├── .pre-commit-config.yaml  # Ruff, formatting, trailing-whitespace, etc.
├── CHANGELOG.md             # Semantic versioning changelog
├── CONTRIBUTING.md          # Points to this file
├── MANIFEST.in              # Python package manifest (if needed)
├── pyproject.toml           # Ruff, pytest, Python project config
├── requirements_dev.txt     # Development dependencies
├── requirements_test.txt    # Test dependencies (pytest, HA test fixtures)
├── THIRD_PARTY_NOTICES.md   # Toastify-JS v1.12.0 licensing
└── README.md                # User-facing documentation

> **Note**: HACS installs only `custom_components/toabify/`. Development files
> (tests, scripts, CI configs) are repo-only and not delivered to end users.
```

---

## 2. Architecture

The data flow for a notification:

1. User calls `notify.toabify` service → `notify.py` `async_send_message`
2. Service fires `toastify_event` on the Home Assistant event bus
3. `websocket_subscribe_toast` forwards the event to subscribed browser WebSocket clients
4. `dist/toast_engine.js` (IIFE) receives the event and calls Toastify-JS to render the toast

**Why `toastify_*` identifiers are kept**: The event name (`toastify_event`),
WebSocket type (`toastify/subscribe`), and URL path (`/toastify_lib`) are
hardcoded in `dist/toast_engine.js`. Changing them would break existing
installations without a coordinated JS update. They are intentionally
**not** renamed during the `toastify` → `toabify` refactoring (see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the "Known Deviations"
section below).

---

## 3. Setup (Windows 11 / PowerShell)

```powershell
py -3 -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
. .\.venv\Scripts\Activate.ps1
pip install -r requirements_dev.txt
pre-commit install
```

> **Windows note**: `pytest-homeassistant-custom-component` may not install
> cleanly on Windows due to native HA dependencies. If that happens, `ruff check .`
> and `ruff format --check .` remain available for local validation. Tests run
> in CI on Linux.

---

## 4. Commands

| Action | Command |
|---|---|
| Lint (check) | `ruff check .` |
| Lint (fix) | `ruff check . --fix` |
| Format (check) | `ruff format --check .` |
| Format (apply) | `ruff format .` |
| Tests | `pytest` |
| Version consistency | `python scripts\check_version.py` |
| Vendor integrity | `python scripts\verify_vendor.py` |
| Pre-commit (all hooks) | `pre-commit run --all-files` |
| Activate venv | `. .\.venv\Scripts\Activate.ps1` |

---

## 5. Pre-commit Hooks

The following hooks are configured in `.pre-commit-config.yaml`:

| Hook | Purpose | Excludes `dist/`? |
|---|---|---|
| `ruff` | Linting + import sorting | Yes |
| `ruff-format` | Code formatting | Yes |
| `trailing-whitespace` | Strip trailing whitespace | Yes |
| `end-of-file-fixer` | Ensure newlines at EOF | Yes |
| `mixed-line-ending` | Consistent line endings | Yes |
| `check-yaml` | YAML validation | No (no YAML in dist) |

> `pytest` is **not** run as a pre-commit hook; it runs exclusively in CI
> (GitHub Actions) because the HA test fixture requires a full event loop
> and socket support not available in a pre-commit environment on Windows.

---

## 6. Vendored Code (`dist/`)

The `custom_components/toabify/dist/` directory contains three files:

| File | Origin | License |
|---|---|---|
| `toastify.js` | Toastify-JS v1.12.0 | MIT |
| `toastify.css` | Toastify-JS v1.12.0 | MIT |
| `toast_engine.js` | toABify (local) | MIT (project license) |

**Do not edit, reformat, or run any hooks on these files.** They must remain
byte-identical to the upstream Toastify-JS release or the local engine
implementation.

- `.gitattributes` sets `-text` for `dist/**` to prevent line-ending conversion.
- `.pre-commit-config.yaml` excludes `dist/` from all formatters and fixers.
- `scripts/vendor_hashes.txt` stores SHA-256 hashes for each file.
- `scripts/verify_vendor.py` validates all files against the baseline.

**Update process** (when upgrading Toastify-JS or modifying the engine):

1. Replace the file(s) in `dist/`.
2. Update `THIRD_PARTY_NOTICES.md` if the upstream version/license changed.
3. Run `python scripts\verify_vendor.py` — update `vendor_hashes.txt` with
   new hashes if the check fails:
   ```powershell
   Get-FileHash -Algorithm SHA256 custom_components\toabify\dist\*.js, custom_components\toabify\dist\*.css
   ```
4. Manually test in Home Assistant: verify toasts render, `onClick` works,
   and `visibility: all` toasts appear outside the dashboard.

---

## 7. Naming Conventions

| Context | Convention | Example |
|---|---|---|
| Python variables/functions | `snake_case` | `async_send_message` |
| Python constants | `UPPER_SNAKE_CASE` | `DEFAULT_DURATION_EVENT` |
| Python classes | `PascalCase` | `ToastifyNotificationService` |

**Exceptions** — these are external API contracts and must **not** be renamed:

| Identifier | Context | Why unchanged |
|---|---|---|
| `oldestFirst` | HA event data | Toastify-JS config key |
| `onClick` | HA event data | Toastify-JS config key |
| `action_data` | HA event data | YAML-friendly key used in user configs |
| `button_label` | HA event data | Frontend config key |
| `toastify_event` | Event bus | Hardcoded in `toast_engine.js` |
| `toastify/subscribe` | WebSocket type | Hardcoded in `toast_engine.js` |
| `toastify_lib` | URL path | Hardcoded in `toast_engine.js` |

---

## 8. Testing

Tests use `pytest` with `pytest-homeassistant-custom-component`, which provides
a `hass` fixture that spins up a minimal Home Assistant instance.

### Test Structure

- **`tests/conftest.py`**: Defines `enable_custom_integrations` fixture that
  clears the `DATA_CUSTOM_COMPONENTS` cache so the test integration is
  reloadable across tests.
- **`tests/test_init.py`**: Characterization tests for `async_setup`:
  - Static path registration at `/toastify_lib`
  - WebSocket command registration (`toastify/subscribe`)
  - JS injection (`/toastify_lib/toast_engine.js`)
- **`tests/test_notify.py`**: Characterization tests for `async_send_message`:
  - Default values for all event data fields
  - Empty message handling
  - Icon/avatar fallback logic
  - Callback as string URL (with/without `/` or `http` prefix)
  - Callback as dict (service call + timer)
  - Default timer duration (3000 ms when `duration` unset)
  - No timer when `duration <= 0` or negative

### What's NOT Tested

- The JavaScript engine (`dist/toast_engine.js`) — it's an IIFE with no
  unit test harness. Manual browser testing is the validation path.
- Integration with a live Home Assistant instance — tests use mocks.

### Manual Test in Browser

After deploying changes, verify in a browser:

1. Send a simple toast:
   ```yaml
   service: notify.toabify
   data:
     message: "Test toast"
   ```
2. Send a toast with `onClick` service call.
3. Send a toast with `visibility: all` — verify it appears in Settings, logs, etc.

---

## 9. Manual Test in Home Assistant

1. Copy the `toabify` folder to your HA config:
   ```
   config/custom_components/toabify/
   ```
2. Add to `configuration.yaml`:
   ```yaml
   notify:
     - platform: toabify
       name: toabify
   ```
3. Restart Home Assistant.
4. Call the service:
   ```yaml
   service: notify.toabify
   data:
     message: "Hello from toABify!"
     data:
       color: "success"
       duration: 5000
   ```
5. Expected result: A green toast appears in the top-right corner of the
   Lovelace dashboard for 5 seconds.

---

## 10. Release Process

1. Bump the version in `custom_components/toabify/manifest.json`.
2. Add a new section to `CHANGELOG.md` under the new version.
3. Run `python scripts\check_version.py` to validate consistency.
4. Commit and push to a feature branch.
5. Open a Pull Request — CI must pass (lint, tests, HACS, Hassfest).
6. After merge, create a git tag: `git tag v1.2.3 && git push --tags`.
7. The **Release** workflow creates a GitHub Release automatically.
8. Install in HACS and verify toasts appear in the browser.

---

## 11. CI Overview

| Workflow | File | Trigger | Purpose |
|---|---|---|---|
| CI | `.github/workflows/ci.yml` | `push`, `pull_request` | Lint + tests + Hassfest |
| HACS | `.github/workflows/hacs.yml` | `push` | Validate HACS repository structure |
| Release | `.github/workflows/release.yml` | `push: tags` | Create GitHub Release from tag |

---

## 12. Known Deviations (Not Changed in This Refactoring)

1. **`duration` dual defaults**: Event data `duration` defaults to `5000` ms
   (for display), but the server-side callback timer defaults to `3000` ms.
   When `duration` is explicit, both use the same value.

2. **`button_label` is sent but not displayed**: The `button_label` value is
   included in the event payload but the Toastify-JS engine (v1.12.0) does
   not use it to render a button. The engine uses `onClick.label` instead.

3. **`oldestFirst` has no visible effect**: Toastify-JS v1.12.0 sets
   `defaults.oldestFirst = true`, so the flag is a no-op.

4. **`innerHTML` for content**: Toast content is rendered via `innerHTML`
   in `toast_engine.js`, which poses an XSS risk if untrusted user input
   is passed. This is inherent to the vendored library and not changed.

5. **`action.split(".")`**: In `notify.py`, the callback action is split on
   the first `.` only (`split(".", 1)`). Service names cannot contain dots,
   so this is correct.

6. **YAML-only configuration**: There is no `config_flow.py`; the service is
   configured via `configuration.yaml` only.

---

## 13. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| HACS: "Repository structure ... not compliant" | Folder name or path wrong | Ensure `custom_components/toabify/` exists at repo root |
| Hassfest error on `manifest.json` | Missing required keys or wrong order | Check `manifest.json` against [HA schema](https://developers.home-assistant.io/docs/core/integration/manifest/) |
| Toast does not appear | `visibility: dashboard` but URL is not Lovelace | Set `visibility: all` or fix your dashboard URL |
| Toast does not appear | Browser cache stale | Hard-refresh (Ctrl+Shift+R) |
| Toast does not appear | Engine not loaded | Check browser console for `TOASTIFY` log message |
| Test fails on Windows | `pytest_socket` blocks event loop | Run tests in CI (Linux) or use `ruff` for local checks only |
