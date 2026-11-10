# CASO Wine Cooler – Home Assistant integration (unofficial)

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories)
[![Validate](https://github.com/8871988-sketch/CASO-Design-Winecooler-Home-Assistant-Custom-Integration-UnOfficial/actions/workflows/validate.yml/badge.svg)](https://github.com/8871988-sketch/CASO-Design-Winecooler-Home-Assistant-Custom-Integration-UnOfficial/actions/workflows/validate.yml)
![Version](https://img.shields.io/badge/version-0.1.0-blue)
![IoT class](https://img.shields.io/badge/IoT%20class-cloud%20polling-orange)

A custom integration for [Home Assistant](https://www.home-assistant.io/) that connects **CASO Design smart wine coolers with two zones** (the ones you control with the *CASO Control* app) through the official, public **CASO Public Kitchen API**.

> [!IMPORTANT]
> This is a **community project**. It is **not** made, endorsed or supported by CASO Design (Braukmann GmbH). "CASO" and "CASO Design" are trademarks of their respective owner and are used here only to describe which devices the integration works with.

Deutsch: [siehe unten](#deutsch) · Українською: [див. нижче](#українською)

---

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Entities](#entities)
- [Options](#options)
- [Changing the API key](#changing-the-api-key)
- [Examples](#examples)
- [How it works](#how-it-works)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)
- [Privacy and security](#privacy-and-security)
- [Development](#development)
- [License and disclaimer](#license-and-disclaimer)

## Features

- Current temperature of the **top** and **bottom** zone
- Target temperature of both zones (read only, see [Limitations](#limitations))
- Whether each zone is switched on
- Interior **light** per zone, plus one light entity for **both zones**
- Time of the last report of the cooler to the CASO cloud
- Set up in the UI (config flow), no YAML
- Re-authentication and "Reconfigure" to replace the API key without removing the integration
- Adjustable polling interval (5–60 minutes)
- Short cloud outages do not make the entities unavailable immediately
- Translations: English, German, Ukrainian

## Requirements

| What | Details |
|---|---|
| Home Assistant | 2025.2 or newer |
| Device | CASO Design smart wine cooler with **2 zones**, connected to Wi-Fi and registered in the *CASO Control* app |
| CASO account | the same account you use in the app |
| API key | create it at <https://www.casoapp.com/apikey> |
| Device ID | the *Technical Device ID*, shown at <https://www.casoapp.com/devices> |
| Internet | Home Assistant must reach `https://publickitchenapi.casoapp.com` |

Single-zone models are not tested. If you own one, please open an issue with the JSON of the status call (remove your device ID).

## Installation

### HACS (recommended)

1. Open **HACS** in Home Assistant.
2. Menu (⋮) → **Custom repositories**.
3. Repository: `https://github.com/8871988-sketch/CASO-Design-Winecooler-Home-Assistant-Custom-Integration-UnOfficial`, type: **Integration** → **Add**.
4. Search for **CASO Wine Cooler (unofficial)** and click **Download**.
5. **Restart** Home Assistant.

### Manual

1. Download the latest release (or the repository as ZIP).
2. Copy the folder `custom_components/caso` into the `custom_components` folder of your Home Assistant configuration, so that you end up with `/config/custom_components/caso/manifest.json`.
   You can use the *Samba share*, *File editor*, *Studio Code Server* or *Terminal & SSH* add-ons for this.
3. **Restart** Home Assistant.

## Configuration

1. **Settings → Devices & services → Add integration** → search for **CASO Wine Cooler**.
2. Fill in the form:

   | Field | Meaning |
   |---|---|
   | **Name** | Name of the device in Home Assistant, e.g. `Wine Cooler`. Entity IDs are created from it. |
   | **API key** | Your personal key from <https://www.casoapp.com/apikey>. Stored in the Home Assistant configuration entry, never written to YAML. |
   | **Device ID** | The *Technical Device ID* from <https://www.casoapp.com/devices>. |

3. The integration checks the values against the CASO cloud before it saves them. Possible errors:

   | Error | Cause |
   |---|---|
   | *The API key is not accepted* | wrong, revoked or expired key |
   | *The device ID is not known* | typo, or the device belongs to another account |
   | *Cannot reach the CASO cloud* | no internet, DNS or firewall problem, or the CASO service is down |

Each wine cooler is one configuration entry. Add the integration again for a second cooler.

## Entities

With the device name `Wine Cooler` you get (entity IDs depend on your name and language):

| Entity | Type | Description |
|---|---|---|
| `sensor.wine_cooler_top_zone_temperature` | sensor, °C | current temperature, top zone |
| `sensor.wine_cooler_top_zone_target_temperature` | sensor, °C | target temperature, top zone |
| `sensor.wine_cooler_bottom_zone_temperature` | sensor, °C | current temperature, bottom zone |
| `sensor.wine_cooler_bottom_zone_target_temperature` | sensor, °C | target temperature, bottom zone |
| `binary_sensor.wine_cooler_top_zone` | binary sensor (power) | top zone switched on |
| `binary_sensor.wine_cooler_bottom_zone` | binary sensor (power) | bottom zone switched on |
| `light.wine_cooler_top_zone_light` | light (on/off) | interior light, top zone |
| `light.wine_cooler_bottom_zone_light` | light (on/off) | interior light, bottom zone |
| `light.wine_cooler_light` | light (on/off) | both lights together; *on* if at least one is on |
| `sensor.wine_cooler_last_report` | sensor, timestamp (diagnostic) | when the cooler last reported to the CASO cloud |

The API reports whole degrees Celsius.

## Options

**Settings → Devices & services → CASO Wine Cooler → Configure**

| Option | Default | Range | Meaning |
|---|---|---|---|
| Polling interval | 5 min | 5–60 min | how often the status is read from the cloud |

Please do not poll more often: the CASO cloud is designed for low request rates, and the cooler itself only reports every few minutes.

## Changing the API key

If you renew or revoke your key:

- **Settings → Devices & services → CASO Wine Cooler → ⋮ → Reconfigure** and enter the new key, or
- wait: when the cloud rejects the key, Home Assistant shows a *Re-authentication required* notice and asks for the new one.

The device and all entities, history and automations stay as they are.

## Examples

See the [`examples`](examples) folder:

- [`dashboard_card.yaml`](examples/dashboard_card.yaml) – an entities card for both zones
- [`automations.yaml`](examples/automations.yaml) – temperature alarm and light schedule

## How it works

| Call | Endpoint | Used for |
|---|---|---|
| Status | `POST /api/v1.1/Winecooler/Status` with `{"technicalDeviceId": …}` | all sensors, every polling interval |
| Light | `POST /api/v1.1/Winecooler/SetLight` with `{"technicalDeviceId": …, "zone": 0/1/2, "lightOn": true/false}` | light entities (zone 0 = both, 1 = top, 2 = bottom) |

The key is sent in the `x-api-key` header over HTTPS. After switching a light, the new state is shown at once without an extra status call.

File overview:

| File | Purpose |
|---|---|
| `api.py` | small HTTP client for the CASO API, no Home Assistant code |
| `coordinator.py` | polling, keeps the last state during short outages, light commands |
| `config_flow.py` | setup form, re-authentication, reconfigure, options |
| `sensor.py`, `binary_sensor.py`, `light.py` | entities |
| `translations/` | English, German, Ukrainian texts |

## Limitations

- **Target temperature is read only.** The CASO API does not allow changing it; use the buttons on the cooler.
- **Cloud only.** Without internet or when the CASO service is down, no data is available. After two failed polls in a row the entities become *unavailable*.
- **Delay.** Values are as fresh as the cooler's last report to the cloud (see the *Last report* sensor) plus the polling interval.
- **Beeping.** Some models beep when the light is switched remotely. This is done by the device.
- Only two-zone coolers are supported at the moment.

## Troubleshooting

Enable debug logging and reproduce the problem:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.caso: debug
```

Or temporarily: **Developer tools → Actions → `logger.set_level`** with `custom_components.caso: debug`.

When you open an issue, add the Home Assistant version, the integration version and the log lines. **Remove your API key and device ID** before posting.

## Privacy and security

- The API key and device ID are stored only in Home Assistant's configuration entry (`.storage/core.config_entries`). They are part of your Home Assistant backups – keep backups encrypted.
- The integration talks only to `publickitchenapi.casoapp.com` over HTTPS. Nothing is sent anywhere else.
- If a key was ever exposed (for example in a YAML file or a screenshot), revoke it at <https://www.casoapp.com/apikey> and create a new one.

## Development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements_test.txt
pytest -q
```

The tests use a fake CASO cloud (`tests/conftest.py`) and do not need a real device or key. Pull requests are welcome.

## License and disclaimer

[MIT](LICENSE). The software is provided "as is", without warranty of any kind. Use at your own risk.

This project is not affiliated with, authorised, maintained, sponsored or endorsed by CASO Design / Braukmann GmbH. All product and company names are trademarks or registered trademarks of their respective holders; they are used only to identify compatible devices. The integration uses the publicly documented CASO Public Kitchen API with the user's own API key.

---

## Deutsch

Inoffizielle Home-Assistant-Integration für **CASO Design Smart-Weinkühlschränke mit zwei Zonen** über die öffentliche **CASO Public Kitchen API**. Kein offizielles Produkt von CASO Design.

**Installation:** HACS → ⋮ → *Benutzerdefinierte Repositories* → diese Repository-URL, Typ *Integration* → herunterladen → Home Assistant neu starten. Alternativ den Ordner `custom_components/caso` nach `/config/custom_components/` kopieren.

**Einrichtung:** *Einstellungen → Geräte & Dienste → Integration hinzufügen → CASO Wine Cooler*. Benötigt werden der **API-Schlüssel** (<https://www.casoapp.com/apikey>) und die **Geräte-ID / Technical Device ID** (<https://www.casoapp.com/devices>).

**Entitäten:** Ist- und Solltemperatur oben/unten, Zone ein/aus, Licht oben/unten/beide, letzte Meldung. Die Solltemperatur kann über die API **nicht** geändert werden. Abfrageintervall 5–60 Minuten (Standard 5). Neuer API-Schlüssel: *⋮ → Neu konfigurieren*.

## Українською

Неофіційна інтеграція Home Assistant для **винних шаф CASO Design з двома зонами** через публічний **CASO Public Kitchen API**. Не є офіційним продуктом CASO Design.

**Встановлення:** HACS → ⋮ → *Custom repositories* → URL цього репозиторію, тип *Integration* → завантажити → перезапустити Home Assistant. Або скопіювати теку `custom_components/caso` у `/config/custom_components/`.

**Налаштування:** *Налаштування → Пристрої та служби → Додати інтеграцію → CASO Wine Cooler*. Потрібні **API-ключ** (<https://www.casoapp.com/apikey>) і **ID пристрою / Technical Device ID** (<https://www.casoapp.com/devices>).

**Сутності:** поточна й задана температура верх/низ, стан зон, світло верх/низ/обидва, час останнього повідомлення. Задану температуру через API змінити **не можна**. Інтервал опитування 5–60 хвилин (типово 5). Новий API-ключ: *⋮ → Переналаштувати*.
