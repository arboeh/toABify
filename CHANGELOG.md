# Changelog

All notable changes to the toABify project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-10-11

### Summary

First standalone release under the **toABify** name. This refactoring modernizes the
codebase for HACS compliance, converts the notify platform to async, centralizes
constants in `const.py`, adds characterization tests, and locks vendored files
with SHA-256 verification.

### Changed

- **Domain rename**: `toastify` → `toabify` in all new code.
- **Directory structure**: `custom_components/toastify/` → `custom_components/toabify/`.
- **`__init__.py`**: async_setup uses `const.py` for all protocol identifiers;
  static path fixed to `custom_components/toabify/dist`.
- **`notify.py`**: `get_service` (sync) → `async_get_service` (async);
  `send_message` (sync) → `async_send_message` (async);
  removed `run_callback_threadsafe`; uses `const.py` defaults.
- **`notify.py`**: `action.split(".", 1)` → `action.split(".")` — restores original
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
- Configuration is YAML-only; no `config_flow.py`.

## [1.0.0] - Prior release

Initial release by TidjyDev / HA-Toastify.
