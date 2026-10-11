# toABify 🍞

**English | [Deutsch](README.de.md)**

A Home Assistant integration that displays beautiful toast-style notifications on your interface, powered by [Toastify-JS](https://apvarun.github.io/toastify-js/).

> **Based on HA-Toastify by TidjyDev (MIT)**. toABify is not an official fork: it shares the same internal architecture (identifiers `toastify_event`, `toastify/subscribe`, `/toastify_lib`) but is a standalone project. **Do not install toABify alongside HA-Toastify** - the internal identifiers would conflict.

## ✨ Features
- **HACS Ready**: Simple installation and updates.
- **Customizable**: Color, duration, position, close button, icons/avatars.
- **Dynamic Contrast**: Text automatically switches between black and white for optimal readability against any background color.
- **Smart Visibility**: Show notifications only on the dashboard or across all of Home Assistant (settings, logs, history, etc.).
- **Interactive Actions**: Click a toast to open a URL or **call a Home Assistant service** (e.g., turn off a light, navigate to a dashboard).
- **Native Notify Service**: Fully compatible with Home Assistant's built-in notification system.

![toABify Preview](images/screenshot.jpg)

## 📦 Installation

### 1. Via HACS (Recommended)
1. Open **HACS** in your Home Assistant instance.
2. Click the three dots in the top-right corner → **Custom repositories**.
3. Add this repository URL: `https://github.com/arboeh/toABify`.
4. Select the **Integration** category and click **Add**.
5. Search for "toABify" and install it.
6. **Restart Home Assistant.**

### 2. Configuration
Add the following to your `configuration.yaml` to register the notification service:

```yaml
# configuration.yaml: Notification service declaration
notify:
  - platform: toabify
    name: toabify
```

## 🛠️ Service Parameters (`data:`)

| Parameter | Description | Default |
| :--- | :--- | :--- |
| `message` | Text to display in the notification. | *(required)* |
| `color` | Theme (`success`, `info`, `warning`, `error`) or hex code (`#FFFFFF`). | `info` |
| `duration` | Duration in ms (`3000` = 3s). Use `-1` for a persistent toast. `0` falls back to `5000`. | `5000` |
| `position` | Horizontal alignment: `left`, `center`, or `right`. | `right` |
| `gravity` | Vertical alignment: `top` or `bottom`. | `top` |
| `close` | Show a close button (`true` / `false`). | `false` |
| `icon` | Image URL or avatar (e.g., `/local/avatar.png`) or MDI icon. | *(empty)* |
| `oldestFirst` | Stack order for notifications. | `true` |
| `visibility` | `dashboard` (Lovelace only) or `all` (everywhere in HA). | `dashboard` |
| `onClick` | Click action: HA service call object (`action`, `action_data`, `label`, `feedback`) or URL/path string (e.g., `/lovelace/0`). | *(none)* |
| `callback` | Action on toast dismissal: HA service call object (`action`, `action_data`) or URL/path string (e.g., `/lovelace/0`). | *(none)* |
| `action_data` | Data for HA service calls. Used within `onClick` or `callback`. | *(dict)* |
| `button_label` | Label for the onClick button. | `VOIR` |

> **Note**: `visibility`, `action_data`, and `button_label` are toABify-specific. For all other parameters, see the upstream Toastify-JS docs: https://github.com/apvarun/toastify-js

> **Technical note**: `button_label` is sent to the frontend but Toastify-JS v1.12.0 does not display it (the engine uses `onClick.label` instead). Similarly, `oldestFirst` is transmitted but has no visible effect because the library's default is already `true`.

## 💡 YAML Examples

### Success Notification (Green with Gradient)
Perfect for confirming successful automation execution.
```yaml
service: notify.toabify
data:
  message: "Alarm activated successfully"
  data:
    color: "success"
    position: "center"
    duration: 5000
```

### Full-HA Alert (Red with Close Button)
Ideal for errors or security alerts requiring immediate attention.
Visible even in configuration menus.
```yaml
service: notify.toabify
data:
  message: "⚠️ Water leak detected in the kitchen!"
  data:
    color: "#ff5f6d"
    close: true
    duration: -1
    gravity: "bottom"
    visibility: "all"
```

### Notification with Avatar Icon
Know who or what triggered the event.
```yaml
service: notify.toabify
data:
  message: "Alex just arrived home"
  data:
    icon: "/local/img/alex_avatar.png"
    color: "#2196F3"
    duration: 6000
```

### Service Call on Click (Close the Gate)
Click a notification to trigger a physical action.
```yaml
service: notify.toabify
data:
  message: "The gate was left open! Click to close."
  data:
    color: warning
    onClick:
      action: cover.close_cover
      action_data:
        entity_id: cover.gate_main
    visibility: all
    close: true
    duration: -1
```

### Navigation Link (Open Cameras)
Redirect to a specific Lovelace view when an event occurs.
```yaml
service: notify.toabify
data:
  message: "🚨 Motion detected in the garden"
  data:
    color: "error"
    onClick: "/lovelace-mobile/cameras"
    icon: "/local/img/cam_icon.png"
    visibility: "all"
    duration: 8000
```

---

Based on [HA-Toastify](https://github.com/TidjyDev/HA-Toastify) by TidjyDev (MIT).
Uses [Toastify-JS](https://github.com/apvarun/toastify-js) by apvarun (MIT).
