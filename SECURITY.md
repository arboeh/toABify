# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.x.x   | ✅ Yes    |
| < 2.0.0 | ❌ No     |

## Reporting a Vulnerability

Please report security vulnerabilities responsibly:

1. **Do NOT** open a public GitHub issue.
2. Open a private security advisory at https://github.com/arboeh/toABify/security/advisories/new
   or email the maintainer directly.
3. You should receive an acknowledgment within 2 business days.
4. We will investigate and, if confirmed, work on a fix within 30 days.

## Known Security Considerations

- **XSS risk**: The toast `message` is rendered as plain text (Toastify's own
  `escapeMarkup`). Only the button label (`onClick.label`, or `button_label`
  when no explicit label is set) is inserted via `innerHTML` in
  `toast_engine.js`; the integration escapes it server-side, limits it to 200
  characters, and rejects non-string labels, so markup in a label is displayed
  as text and never executes. `dist/` is vendored and unchanged. See the
  "Known Deviations" section in [DEVELOPMENT.md](DEVELOPMENT.md).

- **Callback service calls**: The `callback` action as a dict executes a Home
  Assistant service after the toast duration. Ensure only trusted users can
  invoke the `notify.toabify` service.
