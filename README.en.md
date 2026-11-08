[Français](README.md) · **English**

# MediaNav Evolution — Windows CE tools (dBoot 1.5)

Two small reverse-engineering tools for **MediaNav Evolution** head units
(LG `LAN5xxx`, Windows CE 6.0 on MIPS), fitted to many **Dacia / Renault / Nissan**
vehicles from around 2012-2016.

They solve two problems well known to tinkerers of these units:

1. **Reach the Windows CE desktop** cleanly, through a touch button, instead of the
   finicky swipe on the logo.
2. **Stop the forced reboot** (~2 min 20) that happens as soon as you are under
   Windows CE, because nothing is sending the "keep-alive" signal the
   micro-controller (MICOM) expects anymore.

> ⚠️ **No proprietary binary is included here.** These scripts *patch your own copy*
> of the original files (whose SHA-256 is verified before any modification).
> Reverse engineering for interoperability and personal use. **No warranty** —
> see the Safety section.

## The tools (`scripts/`)

| Script | Role |
|---|---|
| `patch_dboot.py` | Patches `dboot.exe` (dBoot 1.5): adds a touch **"Windows CE" button** in the bottom-right corner and extends the access window from 5 to 10 s. The original swipe stays active as a fallback. |
| `build_micomm_pause.py` | Builds `micomm_pause.exe` from `dmenu.exe`: sends the MICOM the **keep-alive sequence** (open `FD` + `07 01`, then `FF` every second) that **pauses the watchdog**. Run it once under Windows CE. |
| `decode_micomm_pause.py` | Decodes the small diagnostic log (180 bytes) written by `micomm_pause.exe`. |
| `mipsenc.py` | Minimal MIPS32 instruction encoder, used by the build scripts. |

## Requirements

- Python 3 (no external dependencies).
- **Your own original files**, copied from your unit: `dboot.exe` and `dmenu.exe`
  (found in `\Storage Card\System\`).
- A disassembler (radare2 or capstone) is recommended to double-check the output,
  but not required to run.

## Usage

```bash
# 1) Windows CE access button
python3 -I scripts/patch_dboot.py  dboot.exe  dboot_patched.exe

# 2) MICOM keep-alive (anti-reboot)
python3 -I scripts/build_micomm_pause.py  dmenu.exe  micomm_pause.exe

# 3) Read the diagnostic log recovered from the USB stick
python3 -I scripts/decode_micomm_pause.py  micompause.log
```

Each script **verifies the SHA-256** of the original file and checks every modified
region byte by byte: if it does not recognise your binary, it stops without writing
anything. Then copy the produced file onto the unit with the Windows CE file manager
(TTCMD / Total Commander), **keeping the original** so you can roll back.

`micomm_pause.exe` is launched once per Windows CE session; as long as it runs, the
watchdog stays paused. Stop it from the task manager (ITaskMgr). With no USB stick
plugged in, it writes no log but keeps sending the signal.

## How it works

- `docs/dboot-analysis.md` — what dBoot 1.5 does at startup, where the Windows CE
  switch lives, and the patched regions.
- `docs/micom-protocol.md` — the MICOM serial frame format and the keep-alive
  sequence that pauses the watchdog.

(Both reference docs are in French for now; the code and this overview are in English.)

## Safety — read before touching anything

- **Back up the whole unit first** (all `Storage Card` volumes), with checksums.
  A wrong move can wipe everything.
- **Never touch** the vehicle configuration files or the anti-theft file
  (e.g. `Antitheft.cfg`, the vehicle MICOM config): deleting or corrupting them can
  trigger an anti-theft code request on the next boot.
- **Never touch** the kernel images (`NK.BIN`, `NA.BIN`, `NB.BIN`): red zone.
- Work **with the engine running**, without cutting the ignition during a copy.
- Always keep the original of every modified file so you can roll back.

Provided **as is, with no warranty whatsoever**. You are solely responsible for what
you do with your hardware. These tools embed no proprietary code and serve only
interoperability with hardware you own.

## License

Code under the MIT License (see `LICENSE`). Trademarks and binaries mentioned belong
to their respective owners and are not distributed here.
