# Changelog

## 0.1.0 – 2026-11-10

First public version.

- Config flow with API key and Technical Device ID, checked against the CASO cloud
- Sensors: current and target temperature for the top and bottom zone, last report time
- Binary sensors: zone switched on
- Lights: top, bottom and both zones (zone 0/1/2 of the SetLight call)
- Re-authentication and reconfigure flow to replace the API key
- Option: polling interval 5–60 minutes (default 5)
- Last state is kept for up to two failed polls
- Translations: English, German, Ukrainian
