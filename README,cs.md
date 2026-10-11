# toABify 🍞

**[English](README.md) | [Deutsch](README.de.md) | Čeština**

Integrace pro Home Assistant, která na vašem rozhraní zobrazuje krásná vyskakovací oznámení (toast notifications), poháněná knihovnou [Toastify-JS](https://github.io).

> **Založeno na projektu HA-Toastify od TidjyDev (MIT)**. toABify není oficiální fork: sdílí stejnou interní architekturu (identifikátory `toastify_event`, `toastify/subscribe`, `/toastify_lib`), ale jedná se o samostatný projekt. **Neinstalujte toABify společně s HA-Toastify** – interní identifikátory by byly v konfliktu.

## ✨ Vlastnosti
- **Připraveno pro HACS**: Jednoduchá instalace a aktualizace.
- **Přizpůsobitelné**: Barva, doba trvání, pozice, tlačítko pro zavření, ikony/avatary.
- **Dynamický kontrast**: Text se automaticky přepíná mezi černou a bílou barvou pro optimální čitelnost na jakémkoli pozadí.
- **Chytrá viditelnost**: Zobrazení oznámení pouze na přehledu (dashboardu) nebo napříč celým Home Assistantem (nastavení, logy, historie atd.).
- **Interaktivní akce**: Kliknutím na oznámení můžete otevřít URL adresu nebo **zavolat službu Home Assistanta** (např. zhasnout světlo, přejít na přehled).
- **Nativní oznamovací služba**: Plně kompatibilní s vestavěným systémem oznámení v Home Assistantu.

![toABify Náhled](images/screenshot.jpg)

## 📦 Instalace

### 1. Přes HACS (Doporučeno)
1. Otevřete **HACS** ve vaší instanci Home Assistanta.
2. Klikněte na tři tečky v pravém horním rohu → **Vlastní repozitáře** (Custom repositories).
3. Přidejte URL adresu tohoto repozitáře: `https://github.com`.
4. Vyberte kategorii **Integrace** (Integration) a klikněte na **Přidat** (Add).
5. Vyhledejte "toABify" a nainstalujte jej.
6. **Restartujte Home Assistanta.**

### 2. Konfigurace
Pro registraci oznamovací služby přidejte do svého souboru `configuration.yaml` následující kód:

```yaml
# configuration.yaml: Deklarace oznamovací služby
notify:
  - platform: toabify
    name: toabify
```

## 🛠️ Parametry služby (`data:`)

| Parametr | Popis | Výchozí |
| :--- | :--- | :--- |
| `message` | Text, který se má v oznámení zobrazit. | *(vyžadováno)* |
| `color` | Téma (`success`, `info`, `warning`, `error`) nebo hex kód barvy (`#FFFFFF`). | `info` |
| `duration` | Doba trvání v milisekundách (`3000` = 3s). Použijte `-1` pro trvalé oznámení. `0` se vrátí k hodnotě `5000`. | `5000` |
| `position` | Horizontální zarovnání: `left` (vlevo), `center` (na střed) nebo `right` (vpravo). | `right` |
| `gravity` | Vertikální zarovnání: `top` (nahoře) nebo `bottom` (dole). | `top` |
| `close` | Zobrazit tlačítko pro zavření (`true` / `false`). | `false` |
| `icon` | URL adresa obrázku nebo avataru (např. `/local/avatar.png`) nebo MDI ikona. | *(prázdné)* |
| `oldestFirst` | Pořadí řazení oznámení na sebe. | `true` |
| `visibility` | `dashboard` (pouze Lovelace přehledy) nebo `all` (všude v HA). | `dashboard` |
| `onClick` | Akce při kliknutí: Objekt volání služby HA (`action`, `action_data`, `label`, `feedback`) nebo řetězec URL/cesty (např. `/lovelace/0`). | *(žádná)* |
| `callback` | Akce při zavření oznámení: Objekt volání služby HA (`action`, `action_data`) nebo řetězec URL/cesty (např. `/lovelace/0`). | *(žádná)* |
| `action_data` | Data pro volání služeb HA. Používá se uvnitř `onClick` nebo `callback`. | *(dict)* |
| `button_label` | Štítek (text) pro tlačítko onClick. | `VOIR` |

> **Poznámka**: Parametry `visibility`, `action_data` a `button_label` jsou specifické pro toABify. Všechny ostatní parametry naleznete v dokumentaci upstreamové knihovny Toastify-JS: https://github.com

> **Technická poznámka**: Parametr `button_label` se sice posílá do frontendové části, ale Toastify-JS v1.12.0 ho nezobrazuje (jádro místo toho používá `onClick.label`). Podobně se přenáší i `oldestFirst`, ale nemá žádný viditelný efekt, protože výchozí nastavení knihovny je již nastaveno na `true`.

## 💡 Příklady YAML

### Úspěšné oznámení (Zelené s přechodem)
Ideální pro potvrzení úspěšného spuštění automatizace.
```yaml
service: notify.toabify
data:
  message: "Alarm byl úspěšně aktivován"
  data:
    color: "success"
    position: "center"
    duration: 5000
```

### Upozornění pro celý Home Assistant (Červené s tlačítkem zavřít)
Ideální pro chyby nebo bezpečnostní výstrahy vyžadující okamžitou pozornost.
Viditelné i v nabídkách nastavení.
```yaml
service: notify.toabify
data:
  message: "⚠️ V kuchyni byl detekován únik vody!"
  data:
    color: "#ff5f6d"
    close: true
    duration: -1
    gravity: "bottom"
    visibility: "all"
```

### Oznámení s ikonou avataru
Mějte přehled o tom, kdo nebo co událost spustilo.
```yaml
service: notify.toabify
data:
  message: "Alex právě dorazil domů"
  data:
    icon: "/local/img/alex_avatar.png"
    color: "#2196F3"
    duration: 6000
```

### Volání služby na kliknutí (Zavřít bránu)
Kliknutím na oznámení spustíte fyzickou akci.
```yaml
service: notify.toabify
data:
  message: "Brána zůstala otevřená! Kliknutím ji zavřete."
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

### Navigační odkaz (Otevřít kamery)
Přesměrování na konkrétní zobrazení Lovelace, když nastane událost.
```yaml
service: notify.toabify
data:
  message: "🚨 Na zahradě byl detekován pohyb"
  data:
    color: "error"
    onClick: "/lovelace-mobile/cameras"
    icon: "/local/img/cam_icon.png"
    visibility: "all"
    duration: 8000
```

---

Založeno na projektu [HA-Toastify](https://github.com) od TidjyDev (MIT).
Využívá knihovnu [Toastify-JS](https://github.com) od apvarun (MIT).
