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

- **XSS risk**: Toast content is rendered via `innerHTML` in `toast_engine.js`.
  Only pass trusted text in the `message` parameter. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
  and the "Known Deviations" section in [DEVELOPMENT.md](DEVELOPMENT.md).

- **Callback service calls**: The `callback` action as a dict executes a Home
  Assistant service after the toast duration. Ensure only trusted users can
  invoke the `notify.toabify` service.
