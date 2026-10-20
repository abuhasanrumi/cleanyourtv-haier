# Themes

A theme is a folder with a `config.json` and, optionally, a `wallpaper.jpg`. Pushing one changes the
launcher's dock, layout and look on the TV without rebuilding the APK: the launcher reads
`config.json` as an overlay over its built-in `config.xml` the next time it starts.
Choices made in Launcher settings take priority until you choose Follow theme. Pushing a theme or
using `tools/theme.sh --reset` also clears those on-TV column and motion choices.

```bash
TV_HOST=192.168.1.50 tools/theme.sh themes/aurora          # push a theme and restart Home
TV_HOST=192.168.1.50 tools/theme.sh --reset                # back to the built-in config.xml
powershell -ExecutionPolicy Bypass -File tools\theme.ps1 -TvHost 192.168.1.50 themes\aurora
```

| Theme | What it does |
|---|---|
| `default/` | The built-in look written out as JSON, as a starting point for your own |
| `aurora/` | A dark aurora wallpaper (teal and violet on navy, darker at the bottom) with a matching background colour |
| `dussehra/` | Festive skin for Dussehra (ends 21 Oct 2026): a marigold toran, a faint gold rangoli, a diya for Wi-Fi, a bell for Inputs, a marigold for Settings and a petal shower |
| `haier-lite/` | Haier fork: the fastest setup for 1 GB sets. No wallpaper, reduced motion, no advanced effects, no module card lookups |
| `haier-cosy-valley/` | Haier fork: a valley with a cottage that follows the day in 16 frames: stars and lit windows at night, a sunrise, a sunny noon, a sunset, blue hour; same speed settings as `haier-lite` |
| `haier-solar/` | Haier fork: the same 16 skies with no scene, plain gradients from night through sunrise, noon and sunset |
| `haier-hearth/` | Haier fork: a low amber fireside glow with drifting embers; same speed settings |
| `haier-tide/` | Haier fork: deep blue swells under a band of moonlight; same speed settings |
| `six-columns/` | Six smaller tiles per row and one grid row visible under the dock |

## Keys

Every key is optional; a missing key keeps the value from `config.xml`, an unknown or wrongly typed key
is ignored, and a file that doesn't parse is ignored as a whole, so a theme can never break Home.

| Key | Type | Meaning |
|---|---|---|
| `dock_apps` | list of package names | The dock row, in order; missing apps are skipped |
| `fill_dock` | bool | Fill the dock slots `dock_apps` leaves free with the first grid apps (true by default); false leaves them empty |
| `hidden_apps` | list of package names | Never shown as tiles |
| `live_tv_package`, `live_tv_action` | string | The Live TV app and, if it has no leanback entry, the action to start it with |
| `source_panel_service`, `source_panel_action` | string | The TV's own source panel, for sets with no TvInputManager |
| `input_action` | string | Action sent with an HDMI/AV row's channel URI when nothing handles the standard `VIEW` (XGIMI: `com.xgimi.action.hdmiPlayer`) |
| `columns` | 1 to 8 | Tiles per row; tiles shrink to fit from 5 up |
| `rows_below_dock` | 0 to 3 | Grid rows left visible under the dock; tiles shrink if the dock, its title and that many rows would not fit the screen height |
| `dock_title` | bool | The focused dock app's name in large type above the dock (`true`); `false` keeps only the glow |
| `dock_row` | bool | The dock as its own row with a band (`true`); `false` makes the dock apps the first tiles of one plain grid |
| `reorder_button` | bool | A reorder button in the top bar (`false` by default); reordering is always in the Settings button's long-press menu |
| `app_library` | bool | An App library pill after the last Home row: every installed app, add one to Home or take it off (`false` by default). The choices stay on the TV when a theme is pushed or reset; see [docs/app-library.md](../docs/app-library.md) |
| `shamsi_date` | bool | Show the Solar Hijri date above the Gregorian one |
| `module_cards` | bool | Look for module cards and ask about them (`true`); `false` turns the feature off |
| `reduced_motion` | bool | Calmer motion for weak GPUs: stiff highlight spring, no tile overshoot, short fades, no entrance replay |
| `vpn_app` | string | App the network pill opens when a VPN is configured; also shows a red "VPN off" badge while no VPN is up |
| `animations` | bool | Basic focus, glass, title and tile entrance motion; true by default |
| `advanced_effects` | bool | Optional lifted tile, icon zoom, smooth ambient colour and app opening effects; false by default |
| `show_home_settings_shortcut` | bool | Keep the optional Default-home tile visible when the TV has a home picker; false by default |
| `show_stats` | bool | One line under the clock with CPU, free memory and free storage. Off unless set |
| `background_color` | `#RRGGBB` | Colour behind everything; black by default |
| `sky_intensity` | 0 to 100 | Time-of-day backdrop: a dark gradient that follows the clock, 0 hides it (default) |
| `wallpaper` | bool | Show `wallpaper.jpg` from the theme folder (`true`), or ignore it (`false`) |
| `sunrise`, `sunset` | `HH:MM` | When the sun rises and sets where the TV is, for time-of-day wallpapers; 06:00 and 18:00 if not set. Times less than six hours apart are ignored |
| `festival` | string | Turns on a festive skin: the network pill becomes a diya whose flame follows the connection, Inputs a temple bell, Settings a marigold, and the first Home of the day gets a petal shower. `dussehra` and `diwali` have built-in greetings |
| `festival_until` | `YYYY-MM-DD` | Last day the festive skin shows; it switches itself off after that. A malformed date turns it off |
| `greeting` | string | Replaces the time-of-day greeting while the festive skin is on |
| `accent_color` | `#RRGGBB` | Colour of the focus glow while the festive skin is on; diya gold if not set |
| `settings_key_keycodes` | list of keycodes | Remote buttons that open Settings, for `HomeKeyService` (TCL Google TV gear: `[83]`) |
| `settings_key_panel` | bool | Those buttons open a small quick settings panel (TV settings, Display, Network, Apps, Launcher settings) instead of the TV's Settings |

## Wallpapers

`wallpaper.jpg` is drawn full screen behind the launcher, centre-cropped. Keep it dark, 1920×1080 and
under about 300 KB: the text, the hero name and the dock band are designed for black, and a 1 GB TV
decodes the picture into memory on every Home start. Pictures larger than the screen are scaled down to
it; a picture that is still over 4K (about 8.4 million pixels) after it is sampled down to the screen is not shown at all, and the plain colour stays.

## Time-of-day wallpapers

A theme can ship sixteen frames, `wallpaper-00.jpg` to `wallpaper-15.jpg`, next to `wallpaper.jpg`, and the
launcher shows the one for the time of day, like a solar dynamic desktop. Most frames sit around sunrise and
sunset, where the sky changes fastest:

| Frame | Shown from |
|---|---|
| `00` | 90 minutes after sunset (night) |
| `01` to `07` | 90 minutes before sunrise, then every 30 minutes; `04` is sunrise |
| `08` | two hours after sunrise (day) |
| `09` to `15` | 90 minutes before sunset, then every 30 minutes; `12` is sunset |

Set `sunrise` and `sunset` for your town in the theme's `config.json`, and change them with the seasons. Only
one frame is decoded at a time, so the memory cost is the same as one wallpaper; the frame changes on the
minute tick while Home is open, or when you come back to Home. A frame that is missing falls back to
`wallpaper.jpg`, which a launcher without this feature shows all day. `tools/theme.sh` pushes the frames and
removes old ones.

## Reduced motion

`"reduced_motion": true` keeps the look but calms the movement: the highlight spring is stiff instead
of bouncing, tiles zoom without overshoot, fades are shorter, and Home does not replay the tile
entrance when you come back to it. Use it on TVs whose GPU cannot keep up; a MediaTek MT5895 on
Android 10 is the known case. The default, `false`, keeps the normal motion.

```json
{ "reduced_motion": true }
```

## Time-of-day backdrop

`"sky_intensity": 60` draws a dark gradient over the wallpaper and behind everything else, that follows the
clock: night blues, a soft blue day, then a warm horizon that peaks just before eight in the evening.
The glow near the bottom edge travels from left to right with the sun. The colours stay dark so the
white clock, the hero name and the dock band keep their contrast. It is drawn as one 480×270 bitmap
and redrawn once a minute, never animated, so even a 1 GB TV has nothing to keep up with. `0` keeps
the plain background; the default is off (the reference launcher looks exactly as before).

```json
{ "sky_intensity": 60 }
```

## The Haier fork's wallpapers

The `haier-*` wallpapers are drawn from code by
[`tools/wallpapers/make_wallpapers.py`](../tools/wallpapers/make_wallpapers.py) (numpy and Pillow, fixed
seeds), so they are original and MIT-licensed like the rest of the repo. Each is 1920×1080 and 25 to 70 KB.
The time-of-day frames follow the shape of macOS's Solar Gradients (most frames around sunrise and sunset)
with their own colours; no Apple image is used.

## Adding a theme

Open a PR with a new folder here, a one-line row in the table above and a screenshot from a real TV
in the PR description. Keep the dock list generic (the big streaming apps) unless the theme is for a
specific TV, and say which TV you tried it on.
