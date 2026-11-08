[Français](dboot-analysis.md) · **English**

# dBoot 1.5 — startup sequence and the Windows CE switch

Static analysis of `dboot.exe` and `dmenu.exe` (dBoot 1.5, MediaNav Evolution,
Windows CE 6.0, MIPS little-endian). The addresses below apply to the version whose
SHA-256 is verified in `scripts/patch_dboot.py`.

## What dBoot does at startup

1. Initialises the screen and touch panel, loads the software keyboard.
2. **If `\Storage Card3\StartWinCE` exists**: it deletes that file, (re)creates the
   desktop shortcuts and launches `\Windows\explorer.exe` → **Windows CE desktop**.
3. **Otherwise (normal case)**: it launches the MediaNav application (the
   "UpgradeManager" with its launch argument) → normal head unit.
4. During a short window after the logo, a **gesture** (horizontal swipe on the logo)
   creates `\Storage Card3\StartWinCE` then reboots: on the next boot you therefore
   land on the Windows CE desktop.

`\Storage Card3\` is a small persistent internal storage, empty by default; it is the
"flag" dBoot reads to choose between MediaNav and Windows CE.

## The patch ("button" build)

`patch_dboot.py` applies three changes, each verified byte by byte:

1. **Touch button**: the `WM_LBUTTONDOWN` handler is redirected to a small block
   added in a free area of the `.text` segment. This block reads the touch
   coordinates; if `x ≥ 560` and `y ≥ 360` (bottom-right quarter of an 800×480
   screen), it jumps straight to the original Windows CE switch code. The horizontal
   swipe stays functional as a fallback.
2. **Label**: the text rectangle drawn at the bottom is repositioned and its content
   replaced with `[  Windows CE  ]` (same length as the original string).
3. **Access window**: the display delay goes from 5 s to 10 s.

The patch is reversible: keep the original and put the old `dboot.exe` back to roll
back.

## The forced reboot under Windows CE

Under Windows CE (the `StartWinCE` branch), neither the MediaNav application nor the
MICOM manager is running. But the micro-controller (MICOM) expects a **periodic
keep-alive signal**; without it, its watchdog **reboots the unit after about
2 min 20**. That timer is not in the Windows CE code: it lives in the MICOM firmware,
which we do not modify. The fix is therefore not to disable it but to **send it the
right signal** — see `micom-protocol.en.md` and `build_micomm_pause.py`.

## Zones never to touch

`NK.BIN`, `NA.BIN`, `NB.BIN` (kernel images) and the vehicle configuration /
anti-theft files. A mistake in these places can make the unit unusable or trigger the
anti-theft code request.
