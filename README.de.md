# toABify 🍞

**[English](README.md) | Deutsch**

Eine Home Assistant-Integration, die schöne Toast-Benachrichtigungen auf Ihrer Oberfläche anzeigt, basierend auf [Toastify-JS](https://apvarun.github.io/toastify-js/).

> **Basierend auf HA-Toastify von TidjyDev (MIT)**. toABify ist kein offizieller Fork: Es teilt die gleiche interne Architektur (Identifikatoren `toastify_event`, `toastify/subscribe`, `/toastify_lib`), ist aber ein eigenständiges Projekt. **Installieren Sie toABify nicht parallel zu HA-Toastify** — die internen Identifikatoren würden Konflikte verursachen.

## ✨ Funktionen
- **HACS-kompatibel**: Einfache Installation und Updates.
- **Anpassbar**: Farbe, Dauer, Position, Schließschaltfläche, Icons/Avatare.
- **Dynamischer Kontrast**: Text wechselt automatisch zwischen Schwarz und Weiß für optimale Lesbarkeit.
- **Intelligente Sichtbarkeit**: Benachrichtigungen nur auf dem Dashboard oder in der gesamten Home Assistant-Oberfläche anzeigen (Einstellungen, Logs, Historie, etc.).
- **Interaktive Aktionen**: Klicken Sie auf einen Toast, um eine URL zu öffnen oder **einen Home Assistant-Dienst aufzurufen** (z. B. Licht ausschalten, zu einem Dashboard navigieren).
- **Nativer Notify-Service**: Vollständig kompatibel mit dem integrierten Benachrichtigungssystem von Home Assistant.

![toABify Vorschau](images/screenshot.jpg)

## 📦 Installation

### 1. Über HACS (Empfohlen)
1. Öffnen Sie **HACS** in Ihrer Home Assistant-Instanz.
2. Klicken Sie auf die drei Punkte oben rechts → **Benutzerdefinierte Repositorys**.
3. Fügen Sie diese Repository-URL hinzu: `https://github.com/arboeh/toABify`.
4. Wählen Sie die Kategorie **Integration** und klicken Sie auf **Hinzufügen**.
5. Suchen Sie nach "toABify" und installieren Sie es.
6. **Starten Sie Home Assistant neu.**

### 2. Konfiguration
Fügen Sie Folgendes zu Ihrer `configuration.yaml` hinzu, um den Benachrichtigungsdienst zu registrieren:

```yaml
# configuration.yaml: Benachrichtigungsdienst deklarieren
notify:
  - platform: toabify
    name: toabify
```

## 🛠️ Dienstparameter (`data:`)

| Parameter | Beschreibung | Standard |
| :--- | :--- | :--- |
| `message` | Anzuzeigender Text der Benachrichtigung. | *(erforderlich)* |
| `color` | Farbschema (`success`, `info`, `warning`, `error`) oder Hex-Code (`#FFFFFF`). | `info` |
| `duration` | Dauer in ms (`3000` = 3s). Verwenden Sie `-1` für einen dauerhaften Toast. `0` fällt auf `5000` zurück. | `5000` |
| `position` | Horizontale Ausrichtung: `left`, `center` oder `right`. | `right` |
| `gravity` | Vertikale Ausrichtung: `top` oder `bottom`. | `top` |
| `close` | Schließschaltfläche anzeigen (`true`/`false`). | `false` |
| `icon` | Bild-URL oder Avatar (z. B. `/local/avatar.png`) oder MDI-Icon. | *(leer)* |
| `oldestFirst` | Stapelreihenfolge für Benachrichtigungen. | `true` |
| `visibility` | `dashboard` (Lovelace nur) oder `all` (überall in HA). | `dashboard` |
| `onClick` | Klick-Aktion: HA-Dienstaufruf-Objekt (`action`, `action_data`, `label`, `feedback`) oder URL/Pfad-String (z. B. `/lovelace/0`). | *(keine)* |
| `callback` | Aktion beim Schließen: HA-Dienstaufruf-Objekt (`action`, `action_data`) oder URL/Pfad-String (z. B. `/lovelace/0`). | *(keine)* |
| `action_data` | Daten für HA-Dienstaufrufe. Wird in `onClick` oder `callback` verwendet. | *(dict)* |
| `button_label` | Beschriftung der onClick-Schaltfläche. | `VOIR` |

> **Hinweis**: `visibility`, `action_data` und `button_label` sind toABify-spezifisch. Alle anderen Parameter finden Sie in der Upstream-Toastify-JS-Dokumentation: https://github.com/apvarun/toastify-js

> **Technischer Hinweis**: `button_label` wird an das Frontend gesendet, aber Toastify-JS v1.12.0 zeigt es nicht an (die Engine verwendet stattdessen `onClick.label`). Ebenfalls hat `oldestFirst` keine sichtbare Wirkung, da der Standardwert der Bibliothek bereits `true` ist.

## 💡 YAML-Beispiele

### Erfolgs-Benachrichtigung (Grün mit Gradient)
Perfekt, um erfolgreich abgeschlossene Automatisierungen zu bestätigen.
```yaml
service: notify.toabify
data:
  message: "Alarm erfolgreich aktiviert"
  data:
    color: "success"
    position: "center"
    duration: 5000
```

### Voll-HA-Warnung (Rot mit Schließbutton)
Ideal für Fehler oder Sicherheitswarnungen, die sofortige Aufmerksamkeit erfordern.
Sichtbar selbst in den Einstellungsmenüs.
```yaml
service: notify.toabify
data:
  message: "⚠️ Wasserschaden im Küchenbereich erkannt!"
  data:
    color: "#ff5f6d"
    close: true
    duration: -1
    gravity: "bottom"
    visibility: "all"
```

### Benachrichtigung mit Avatar-Icon
Wissen, wer oder was das Ereignis ausgelöst hat.
```yaml
service: notify.toabify
data:
  message: "Alex ist nach Hause gekommen"
  data:
    icon: "/local/img/alex_avatar.png"
    color: "#2196F3"
    duration: 6000
```

### Dienstaufruf beim Klick (Tor schließen)
Klicken Sie auf eine Benachrichtigung, um eine physische Aktion auszulösen.
```yaml
service: notify.toabify
data:
  message: "Das Tor wurde offengelassen! Klick zum Schließen."
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

### Navigations-Link (Kameras öffnen)
Leiten Sie den Benutzer bei einem Ereignis zu einer spezifischen Lovelace-Ansicht weiter.
```yaml
service: notify.toabify
data:
  message: "🚨 Bewegung im Garten erkannt"
  data:
    color: "error"
    onClick: "/lovelace-mobile/cameras"
    icon: "/local/img/cam_icon.png"
    visibility: "all"
    duration: 8000
```

---

Basierend auf [HA-Toastify](https://github.com/TidjyDev/HA-Toastify) von TidjyDev (MIT).
Verwendet [Toastify-JS](https://github.com/apvarun/toastify-js) von apvarun (MIT).
Erstellt mit ❤️ für die Home Assistant-Community.
