# Third-Party Notices

This document lists third-party code and projects that **toABify** is based on.

---

## HA-Toastify (TidjyDev)

toABify is **based on** [HA-Toastify](https://github.com/TidjyDev/HA-Toastify) by
TidjyDev (MIT). The original project architecture — WebSocket subscription,
static path serving, notify platform, and event names (`toastify_event`,
`toastify/subscribe`, `/toastify_lib`) — is preserved verbatim to maintain
compatibility. toABify is not a fork; it is an independent evolution under the
same MIT license.

| Field | Value |
|---|---|
| **Name** | HA-Toastify |
| **Author** | TidjyDev |
| **License** | MIT |
| **Source** | <https://github.com/TidjyDev/HA-Toastify> |

---

## Toastify-JS v1.12.0

| Field | Value |
|---|---|
| **Name** | Toastify-JS |
| **Version** | 1.12.0 |
| **Author** | Varun A P ([@apvarun](https://github.com/apvarun)) |
| **License** | [MIT](https://opensource.org/licenses/MIT) |
| **Source** | <https://github.com/apvarun/toastify-js> |
| **Files** | `custom_components/toabify/dist/toastify.js`, `custom_components/toabify/dist/toastify.css` |

### MIT License

Copyright (c) 2018 Varun A P

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Local additions

| File | Description |
|---|---|
| `custom_components/toabify/dist/toast_engine.js` | toABify-specific engine that listens for `toastify_event` events on the HA WebSocket and renders Toastify-JS instances. |
