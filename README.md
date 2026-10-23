# TDS-8 Firmware

Firmware releases for the TDS-8 Digital Scribble Strip. Each TDS-8 unit has 8 OLED displays that show your DAW's track names.

- **Firmware downloads:** see [Releases](https://github.com/m1llipede/TDS-8_Firmware/releases). The current version is v1.0.3.
- **Bridge app** (required, Mac and Windows): [https://tds-8.com](https://tds-8.com). It connects the TDS-8 over USB and can flash firmware for you.

## Which DAW?

| DAW | How |
|---|---|
| Ableton Live | Drag `TDS-8.amxd` from the Bridge download into a track. See [https://tds-8.com](https://tds-8.com). |
| Bitwig Studio | Add the TDS-8 controller script. See [bitwig/](bitwig/). |
| Anything that sends OSC | Send `/trackname <index> <name>` to the Bridge on UDP port 8003. See [bitwig/README.md](bitwig/README.md#how-it-works) for the full message list. |
