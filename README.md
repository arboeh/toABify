<img src="images/heading.svg" alt="huABus" height="40"/>

**English | [Deutsch](README.de.md)**

A Home Assistant integration that displays beautiful toast-style notifications on your interface, powered by [Toastify-JS](https://apvarun.github.io/toastify-js/).

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-41BDF5?logo=home-assistant)](https://www.home-assistant.io/)
[![release](https://img.shields.io/github/v/release/arboeh/toABify?display_name=tag)](https://github.com/arboeh/toABify/releases/latest)
[![CI](https://github.com/arboeh/toABify/actions/workflows/ci.yml/badge.svg)](https://github.com/arboeh/toABify/actions)
[![Security](https://img.shields.io/badge/Security-Policy-blue?logo=github)](https://github.com/arboeh/toABify/blob/main/SECURITY.md)
[![maintained](https://img.shields.io/maintained/yes/2026)](https://github.com/arboeh/toABify/graphs/commit-activity)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/arboeh/toABify/blob/main/LICENSE)

> **Based on HA-Toastify by TidjyDev (MIT)**. toABify is not an official fork: it shares the same internal architecture (identifiers `toastify_event`, `toastify/subscribe`, `/toastify_lib`) but is a standalone project. **Do not install toABify alongside HA-Toastify** - the internal identifiers would conflict.

## ⚡ Quick test

Run this in **Developer tools → Actions** to check that toasts reach your browser:

```yaml
action: notify.toabify
data:
  message: "Hello from toABify"
  data:
    visibility: all
```

> **Use `visibility: all` here.** The default is `dashboard`, so a toast sent from the
> developer tools (page path `/developer-tools/...`) is not shown at all.

![toABify Preview](images/screenshot.jpg)

## Features
- **HACS Ready**: Simple installation and updates.
- **Customizable**: Color (theme or hex), duration, position, close button, icon/avatar.
- **Dynamic Contrast**: Text automatically switches between black and white for optimal readability against any background color.
- **Smart Visibility**: Show notifications only on the dashboard or across all of Home Assistant (settings, logs, history, etc.).
- **Interactive Button**: An optional button that opens a URL or **calls a Home Assistant service** (e.g. turn off a light, navigate to a dashboard).
- **Native Notify Service**: Fully compatible with Home Assistant's built-in notification system.

## Installation

### 1. Via HACS (Recommended)
1. Open **HACS** in your Home Assistant instance.
2. Click the three dots in the top-right corner → **Custom repositories**.
3. Add this repository URL: `https://github.com/arboeh/toABify`.
4. Select the **Integration** category and click **Add**.
5. Search for "toABify" and install it.
6. **Restart Home Assistant.**

### 2. Configuration
After installing via HACS, **no manual configuration** is required.
The integration is set up as a **Config Entry**:

1. Open **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **toABify** and follow the setup wizard.
3. The notification service `notify.toabify` is then available in automations and scripts.

## Service Parameters

`message` is the only required field and sits directly next to `data:`. All options below
go into the nested `data:`:

| Parameter (in `data.data`) | Description | Default |
| :--- | :--- | :--- |
| `color` | Theme (`success`, `info`, `warning`, `error`, `alert`, `default`) or hex color (`#RGB`, `#RRGGBB`, `#RRGGBBAA`). A `#RGB` value is expanded to `#RRGGBB` internally. | `info` |
| `duration` | Duration in ms (`3000` = 3s). `-1` keeps the toast until it is dismissed. `0` falls back to `5000`. | `5000` |
| `position` | Horizontal alignment: `left`, `center`, or `right`. | `right` |
| `gravity` | Vertical alignment: `top` or `bottom`. `center` is accepted but renders at the top. | `top` |
| `close` | Show the close button (`X`) in the toast. | `false` |
| `icon` | Image URL or path (e.g. `/local/avatar.png`) or an MDI icon (e.g. `mdi:bell`). | *(empty)* |
| `avatar` | Fallback for `icon` when `icon` is not set. | *(empty)* |
| `visibility` | `dashboard` (Lovelace only) or `all` (everywhere in HA, including settings and developer tools). | `dashboard` |
| `onClick` | Button configuration. **Object only** - see [Button](#-button-onclick). | *(none)* |
| `button_label` | Fallback label for the button, used when `onClick.label` is not set. Rendered as plain text, max 200 characters. | `CLOSE` |
| `callback` | Action when the toast disappears. String or object - see [Callback](#-callback). | *(none)* |
| `oldestFirst` | Stack order for notifications. No visible effect. | `true` |

## Button (`onClick`)

`onClick` is only accepted as an **object** with these keys:

| Key | Description |
| :--- | :--- |
| `action` | Path (`/...`), URL (`http...`) or a Home Assistant service (`domain.service`). |
| `action_data` | Parameters for the service call (only with `domain.service`). |
| `label` | Button text. |
| `feedback` | Set to `true` to pulse the label and show a checkmark while the action runs. |

Important behavior:

- A button is only rendered when `onClick` is set. `onClick: {}` produces a plain
  **CLOSE** button. `close: true` is a different element (the `X` in the corner).
- Label order: `onClick.label`, then `button_label`, then `CLOSE`.
- An `action` that starts with `/` or `http` opens a **new browser tab**.
- An `action` in the form `domain.service` is called in the frontend with `action_data`.
- Unknown keys (for example `URL`) are ignored and trigger nothing.

```yaml
action: notify.toabify
data:
  message: "The gate was left open! Click to close."
  data:
    color: warning
    visibility: all
    close: true
    duration: -1
    onClick:
      action: cover.close_cover
      action_data:
        entity_id: cover.gate_main
```

## Callback

`callback` reacts when the toast disappears. It has two forms:

**As a string** (`/...` or `http...`): opened in the browser when the toast disappears.
The browser may block this as a popup.

**As an object** (`action`, `action_data`): a **server-side service call** after `duration`
ms - without `duration` after `3000` ms. With `duration` less than or equal to `0` the
callback is never executed.

```yaml
action: notify.toabify
data:
  message: "Backup finished"
  data:
    duration: 2000
    visibility: all
    callback:
      action: persistent_notification.create
      action_data:
        message: "The toABify callback has run."
```

> **Note**: The generic core fields `title` and `target` are accepted by the notify
> service but ignored by toABify.

## YAML Examples (Service Calls)

In automations and scripts, use the service `notify.toabify`:

### Success Notification
Perfect for confirming successful automation execution.
```yaml
action: notify.toabify
data:
  message: "Alarm activated successfully"
  data:
    color: "success"
    duration: 5000
    visibility: all
```

### Full-HA Alert (Red with Close Button)
Ideal for errors or security alerts requiring immediate attention.
Visible even in configuration menus.
```yaml
action: notify.toabify
data:
  message: "⚠️ Water leak detected in the kitchen!"
  data:
    color: "#ff5f6d"
    close: true
    duration: -1
    gravity: "bottom"
    visibility: all
```

### Notification with Avatar Icon
Know who or what triggered the event.
```yaml
action: notify.toabify
data:
  message: "Alex just arrived home"
  data:
    avatar: "/local/img/alex_avatar.png"
    color: "#2196F3"
    duration: 6000
    visibility: all
```

### Notification with an MDI Icon
```yaml
action: notify.toabify
data:
  message: "Front door is still open"
  data:
    icon: "mdi:door-open"
    color: info
    duration: 6000
    visibility: all
```

### Button with a Service Call (Close the Gate)
Click the button to trigger a physical action.
```yaml
action: notify.toabify
data:
  message: "The gate was left open! Click to close."
  data:
    color: warning
    visibility: all
    close: true
    duration: -1
    onClick:
      action: cover.close_cover
      action_data:
        entity_id: cover.gate_main
```

### Button with Navigation (Open Cameras)
Redirect to a specific Lovelace view when an event occurs. **The click opens a new tab.**
```yaml
action: notify.toabify
data:
  message: "🚨 Motion detected in the garden"
  data:
    color: "error"
    duration: 8000
    visibility: all
    onClick:
      action: "/dashboard-home/default_view"
      label: "Open"
```

### Custom Button Label
Instead of the default `CLOSE`, the button shows your label.
```yaml
action: notify.toabify
data:
  message: "New update available"
  data:
    color: info
    visibility: all
    button_label: "Open"
    onClick:
      action: "/dashboard-home/default_view"
```

### Server-Side Callback
The toast calls a service server-side after two seconds.
```yaml
action: notify.toabify
data:
  message: "Backup started"
  data:
    duration: 2000
    visibility: all
    callback:
      action: persistent_notification.create
      action_data:
        message: "The toABify callback has run."
```

## Troubleshooting

- **No toast appears**: set `visibility: all`, force a browser refresh (`Ctrl+Shift+R`) and
  check the browser console for `TOASTIFY` messages.
- **No button appears**: `onClick` is missing. Only `onClick` renders a button,
  `close: true` only renders the `X`.
- **Clicking the button does nothing**: `onClick.action` is missing or misspelled.
  Unknown keys are ignored.

## Security

`message` is rendered as plain text. The button label (`onClick.label`, or
`button_label` when no explicit label is set) is inserted as HTML by the engine,
so the integration escapes it server-side: labels appear as plain text, HTML is
not interpreted, and the label is limited to 200 characters. A non-string label
is rejected with a validation error.

---

Based on [HA-Toastify](https://github.com/TidjyDev/HA-Toastify) by TidjyDev (MIT).
Uses [Toastify-JS](https://github.com/apvarun/toastify-js) by apvarun (MIT).
