# TDS-8 in Bitwig Studio

The TDS-8 works in Bitwig Studio as it is. You don't need new firmware or a different Bridge. Bitwig only needs one small controller script, in this folder, that sends your track names to the TDS-8 Bridge app.

What you get:

- Each TDS-8 display shows the name of a Bitwig track, in order. The first unit shows tracks 1 to 8, the second 9 to 16, and so on up to 32 tracks across 4 units.
- Rename a track in Bitwig and its display changes right away.
- The track you select in Bitwig is highlighted on the TDS-8.
- The Bridge's **Refresh** button re-pulls every name from Bitwig.

## Setup

1. **Install the TDS-8 Bridge** from [https://tds-8.com](https://tds-8.com) and plug in your TDS-8 with a USB **data** cable. A charge-only cable powers the unit, but the Bridge can't see it.
2. **Copy `TDS-8.control.js`** from this folder into Bitwig's controller scripts folder:
   - Windows: `Documents\Bitwig Studio\Controller Scripts\`
   - macOS: `~/Documents/Bitwig Studio/Controller Scripts/`
3. **Start the Bridge** before or after Bitwig; the order doesn't matter.
4. In Bitwig, open **Settings > Controllers**, click **Add Controller**, choose **PlayOptix**, then **TDS-8**. There are no MIDI ports to pick.

That's it. The TDS-8 displays fill in with your track names within a second.

You don't need the Ableton Max for Live device (`TDS-8.amxd`) for Bitwig. Ignore it.

## Settings

The controller's settings in Bitwig hold three values. You only change them if you changed the OSC ports in the Bridge:

| Setting | Default | What it is |
|---|---|---|
| Bridge address | `127.0.0.1` | The computer running the Bridge. Leave as is when Bitwig and the Bridge run on the same machine. |
| Bridge listen port | `8003` | Where the script sends track names. Must match the Bridge's OSC listen port. |
| Script listen port | `8001` | Where the Bridge sends Refresh requests. Must match the port the Bridge sends to. |

After changing a setting, turn the controller off and on in Settings > Controllers so it reconnects.

## Troubleshooting

- **Displays stay blank:** check that the Bridge shows the TDS-8 as connected. If it doesn't, try a different USB cable first.
- **Names show, but Refresh does nothing:** something else is using UDP port 8001. Usually that's Ableton with the TDS-8 Max for Live device open at the same time. Close it, or change the script listen port and the Bridge to match.
- **Only the first 32 tracks show.** The TDS-8 supports up to 4 units of 8 displays.
- **Script messages:** Bitwig shows them in its Controller Script Console. Look for lines starting with `TDS-8:`.

## How it works

The Bridge accepts plain OSC over UDP, so any DAW or tool that can send OSC can drive the TDS-8. This script is one example. The messages:

**To the Bridge** (UDP `127.0.0.1:8003`):

| Address | Arguments | Effect |
|---|---|---|
| `/trackname` | `<index 0-31>` `<name>` | Shows `name` on display `index`. Display 0 is unit 1's first screen; display 8 is unit 2's first screen. |
| `/activetrack` | `<index 0-31>` | Highlights that display as the selected track. |
| `/hi` | none | Heartbeat. Shows the DAW as connected in the Bridge. |

**From the Bridge** (UDP port `8001`):

| Address | Arguments | Expected reply |
|---|---|---|
| `/request-trackname` | `<index>` | A `/trackname` for that index |
| `/reannounce` | none | Resend every name |
| `/hello` | none | `/hi` |

Integer or float indexes both work, and names may contain quotes.

To use the TDS-8 with another DAW, send `/trackname` and `/activetrack` to port 8003 from that DAW's OSC or scripting features. Reaper, TouchOSC and Max all can.

## Controlling Bitwig itself with OSC

The TDS-8 is a display: it shows Bitwig's state and doesn't send commands back. If you also want to control Bitwig over OSC (transport, mixer, devices), use a separate OSC extension such as DrivenByMoss. It runs alongside this script. Just keep its ports clear of 8001 and 8003.
