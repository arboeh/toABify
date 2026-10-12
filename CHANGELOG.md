# Changelog

All notable changes to the toABify project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.4] - 2026-10-12

### Summary

UI accuracy release: the developer-tools form for `notify.toabify` no longer
advertises `title` and `target`, which Home Assistant's generic legacy notify
schema adds but this integration never reads. Existing calls stay valid; the
visible changes are that `button_label` now renders as the button label, hex
and null inputs that the documentation already promised are accepted, and hex
colors reach the frontend in their expanded form.

### Changed

- **`notify.py`**: `ToastifyNotificationService.async_register_services` now calls
  `super().async_register_services()` and then replaces the generic core service
  description via `async_set_service_schema`, so the developer tools only list the
  supported fields `message` and `data`. The core registration failure still
  propagates; a failure of the cosmetic description override is logged only, so a
  registered service is never broken by its UI description.
- **`const.py`**: Added `NOTIFY_SERVICE_NAME`, `NOTIFY_SERVICE_DESCRIPTION` and
  `NOTIFY_SERVICE_FIELDS` describing the notify service.
- **`notify.py`**: `async_send_message` docstring documents that `title` and
  `target` are accepted by the core schema but deliberately ignored.
- **`notify.py`**: Inlined the private helpers `_expand_hex_color`,
  `_drop_none_values` and `_sanitize_label` into their single call sites, and
  replaced the shortened service/field text in `const.py` — the runtime behavior
  is unchanged.
- **`notify.py`**: `BaseNotificationService` is imported from
  `homeassistant.components.notify.legacy`, the schema result is `cast` to a
  typed dict, and `_handle_callback` is only called for dict callbacks, so
  Pylance/pyright reports no errors in the platform.
- **`notify.py`**: `color` now accepts hex codes (`#RGB`, `#RRGGBB`, `#RRGGBBAA`) in
  addition to the six theme names. The frontend engine already resolved hex values,
  but the server-side schema rejected them, so the documented hex examples failed.
- **`notify.py`**: Optional `data:` keys that are explicitly passed as `null` are now
  treated as "not provided" instead of failing validation — YAML and template based
  callers may emit every optional key as null.
- **`notify.py`**: A `#RGB` color is expanded to `#RRGGBB` before it reaches the
  frontend, because the engine derives the label contrast from the first six
  characters only.
- **`notify.py`**: `button_label` is copied into `onClick.label` (server-side)
  unless `onClick.label` is set, because the frontend engine reads the button
  label from `onClick.label` only and otherwise falls back to its own `CLOSE`.
- **Security**: button label is HTML-escaped and limited to 200 characters
  because the frontend engine renders it via `innerHTML`. A non-string label
  (`onClick: {label: 5}`) is rejected with a service validation error instead
  of crashing, and over-long labels are truncated, never rejected.
- **`README.md` / `README.de.md`**: Rewritten to match the verified behavior of
  `notify.toabify`; the removed claims are documented in "Removed".
- **`DEVELOPMENT.md`**: Documented the core-schema origin of `title`/`target`, and
  corrected the outdated statements about `config_flow.py` and
  `configuration.yaml` setup.
- **`manifest.json`**: Version bumped to `2.0.4`.
- `requirements_test.txt`: pin `pytest-homeassistant-custom-component` so the CI test job installs on Python 3.12.
- **CI**: Vitest and Playwright jobs (`js_tests`, `e2e_tests`) in `ci.yml`;
  `package-lock.json` is now tracked and installed via `npm ci`. Dependabot
  covers `npm` as well.

### Removed

- **`custom_components/toabify/services.yaml`**: Dead code. Home Assistant's legacy
  notify layer reads `notify/services.yaml`, not the platform's own file, so this
  file was never loaded. Its field documentation now lives in `const.py`, the user
  documentation in `README.md` / `README.de.md`.
- **`README.md` / `README.de.md`**: Removed the string form of `onClick`
  (`onClick: "/lovelace/0"`), which Home Assistant rejects with
  `expected dict at 'onClick'`, and the `action_data` top-level parameter, which
  is only valid inside `onClick` / `callback`. Both files now also document that
  `gravity: center` is accepted but renders at the top, and that
  `duration: 0` falls back to `5000` in the frontend
  (`d.duration || 5000`) while a server-side callback still never runs for a
  duration of `0` or less.

### Added

- E2E tests (Playwright, Chromium) for the frontend engine.
- **`tests/test_notify.py`**: `test_async_register_services_overrides_description`
  verifies that the service registration is preserved and the overridden schema
  contains only `message` and `data`.
- **`tests/test_readme_examples.py`**: Parses every ```yaml``` block in both
  READMEs and validates the ones calling `notify.toabify` (``action:`` and
  ``service:`` form) against the notify data schema, so a documented example can
  no longer advertise a call Home Assistant rejects. Also rejects options placed
  on the payload level instead of in the nested ``data:``.

## [2.0.3] - 2026-10-11

### Summary

Maintenance release: removed dead code, improved test coverage, increased pytest timeout, and critical bugfixes for notify service registration.

### Bugfixes

- **`__init__.py`**: `async_setup_entry` now calls `discovery.async_load_platform` to register the `notify` platform. Without this call, the `notify.toabify` service was not registered in Home Assistant.
- **`__init__.py`**: `async_unload_entry` now removes the notify service via `hass.services.async_remove("notify", DOMAIN)`.
- **`notify.py`**: Restored `async_get_service` — required by Home Assistant's notify platform to instantiate the service.
- **`manifest.json`**: Fixed `codeowner` → `codeowners` (plural); added `config_flow: true`; added `notify` to `after_dependencies`.
- **`strings.json`**: Removed invalid `configuration` key (caused hassfest validation error).

### Changed

- **`__init__.py`**: Removed `CONFIG_SCHEMA` and `async_setup` — dead YAML compatibility code, since the integration uses config-entry setup exclusively.
- **`notify.py`**: Simplified action validation — `action or ""` replaced by direct `str` type check.
- **`tests/conftest.py`**: Added Windows no-op for `pytest_socket.disable_socket`.
- **`requirements_test.txt`**: Added `pytest-timeout`.
- **`pyproject.toml`**: Configured 600-second global test timeout.
- **`manifest.json`**: Version bumped to `2.0.3`.

### Added

- **`tests/test_init.py`**: Tests `test_no_yaml_setup_dead_code` and `test_setup_entry_loads_notify_platform` for dead code verification and platform registration.
- **`tests/test_notify.py`**: Tests `test_async_get_service_returns_service` and `test_non_string_action_no_crash` for edge-case coverage.

## [2.0.2] - 2026-10-11

### Summary

Code simplification release: refactored toast_engine.js for better maintainability, extracted helper functions, removed redundancies, and updated vendor hash.

### Changed

- **`toast_engine.js`**: Simplified code structure:
  - Extracted CSS/JS loading into reusable `loadResource` helper function
  - Simplified `getContrastColor` function by removing intermediate variable
  - Removed duplicate fontSize assignment in button creation
  - Removed commented-out avatar line in Toastify configuration
  - Maintained all existing functionality
- **`scripts/vendor_hashes.txt`**: Updated SHA-256 hash for toast_engine.js

## [2.0.1] - 2026-10-11

### Summary

Small maintenance release: code simplification in `notify.py`, default button
label changed from `VOIR` to `CLOSE` across all docs and tests, and version
bump for the toABify repository.

### Changed

- **`notify.py`**: Simplified `startswith` check using tuple syntax:
  `callback_data.startswith(("/", "http"))` replaces the `or` chain.
- **`notify.py`**: Extracted server-side callback logic into private method
  `_handle_callback` — reduced from 4 levels of nesting to 1, improves separation
  of concerns.
- **`const.py`**: `DEFAULT_BUTTON_LABEL` changed from `"VOIR"` to `"CLOSE"`
  (consistent across code, tests, and documentation).
- **`manifest.json`**: Version bumped to `2.0.1`.
- **`toast_engine.js`**: All French comments and UI text translated to English
  (themes, error messages, button labels, console logs).
- **`scripts/vendor_hashes.txt`**: Updated SHA-256 hash for `toast_engine.js`.

## [2.0.0] - 2026-10-11

### Summary

First standalone release under the **toABify** name. This refactoring modernizes the
codebase for HACS compliance, converts the notify platform to async, centralizes
constants in `const.py`, adds characterization tests, and locks vendored files
with SHA-256 verification.

### Changed

- **Domain rename**: `toastify` -> `toabify` in all new code.
- **Directory structure**: `custom_components/toastify/` -> `custom_components/toabify/`.
- **`__init__.py`**: async_setup uses `const.py` for all protocol identifiers;
  static path fixed to `custom_components/toabify/dist`.
- **`notify.py`**: `get_service` (sync) -> `async_get_service` (async);
  `send_message` (sync) -> `async_send_message` (async);
  removed `run_callback_threadsafe`; uses `const.py` defaults.
- **`notify.py`**: `action.split(".", 1)` -> `action.split(".")` — restores original
  1:1 behavior; actions with more than one dot raise `ValueError`.
- **import cleanup**: `from __future__ import annotations` added to all Python modules.

### Added

- `const.py` — centralized constants.
- `THIRD_PARTY_NOTICES.md` — Toastify-JS v1.12.0 licensing.
- `scripts/check_version.py` — version consistency validation.
- `scripts/verify_vendor.py` — SHA-256 integrity check for vendored files.
- `tests/conftest.py`, `tests/test_init.py`, `tests/test_notify.py` — characterization tests.
- `.gitattributes` — CRLF control for vendored dist files.
- `.editorconfig` — consistent editor settings.
- `pyproject.toml`, `requirements_test.txt`, `requirements_dev.txt` — tooling.
- `.pre-commit-config.yaml` — linting and formatting hooks (excludes `dist/`).
- CI workflows for linting, testing, HACS validation, and Hassfest.
- `SECURITY.md` — security policy with vulnerability reporting guidance.
- `README.de.md` — German translation of the README.
- `.github/dependabot.yml` — dependency update automation for pip and GitHub Actions.
- `pull_request_template.md` — PR checklist template.

### Security

- Vendored files in `dist/` are now pinned with SHA-256 hashes and verified by
  `verify_vendor.py`.
- `.gitattributes` and `.pre-commit-config.yaml` exclude `dist/` from line-ending
  and trailing-whitespace fixes to prevent corruption.

### Known Deviations (not changed)

- `duration` default: event shows `5000` ms, server-side timer defaults to `3000` ms.
- `button_label` is sent to the frontend but the Toastify-JS engine does not display it.
- `oldestFirst` is sent but Toastify-JS v1.12.0 has `defaults.oldestFirst = true`
  (no visible effect).
- `innerHTML` is used for toast content in `toast_engine.js` (XSS risk if untrusted
  input is passed). The vendored Toastify-JS library uses `escapeMarkup` by default.
- `action.split(".")` in `notify.py` splits on every `.` (not just the first).
  Actions with more than one dot raise a `ValueError`.

## [1.0.0] - Prior release

Initial release by TidjyDev / HA-Toastify.
