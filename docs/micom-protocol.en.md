[Français](micom-protocol.md) · **English**

# MICOM protocol and keep-alive signal

The MICOM is the unit's micro-controller. The MediaNav application talks to it over a
serial link (UART, `COM2`). It handles power, the physical buttons, the anti-theft…
and above all a **watchdog**: if it does not receive a periodic keep-alive signal, it
assumes the main system has crashed and **reboots the unit** (observed: ~2 min 20
under Windows CE, when nothing is talking to it anymore).

## Frame format

```
AA  [mgr << 4 | group]  cmd  length  [data...]  XOR
```

- `AA`: start byte.
- `mgr`/`group`: sender and group identifier.
- `cmd`: command.
- `length`: number of data bytes.
- `XOR`: checksum (exclusive-or of the preceding bytes).

Keep-alive frame example: `AA 11 FF 00 44`.

## The sequence that pauses the watchdog

This is exactly what the "UpgradeManager" and the MICOM manager send at normal
startup:

1. **Open**: command `0xFD` with no data.
2. **Open (continued)**: command `0x07` with data `0x01`.
3. **Keep-alive**: command `0xFF`, repeated **every second**.

As long as the `0xFF` signal arrives at a regular interval, the watchdog stays paused
and the unit does not reboot. `build_micomm_pause.py` produces a Windows CE executable
that opens `COM2`, plays the open sequence, then loops on the keep-alive once per
second.

## Diagnostic log

`micomm_pause.exe` writes a 180-byte binary summary (rewritten every second) to the
USB stick, which `decode_micomm_pause.py` interprets:

| Offset | Field |
|---|---|
| 0 | `KDG1` signature |
| 4 | iteration count (≈ seconds of signal) |
| 8 | `COM2` opened (`1` = OK) |
| 12 / 16 / 20 | reply-wait code after `FD` / `07` / `FF` (`0` = reply received, `0x102` = nothing) |
| 24 / 28 / 32 | bytes received after `FD` / `07` / last `FF` |
| 36 / 84 / 132 | up to 48 reply bytes received (`FD` / `07` / `FF`) |

In practice, the MICOM returns one acknowledgement byte per command, which confirms
the link is established and the watchdog is paused.

## Built-in safety

The built executable **cannot reboot the device**: the `SetSystemPowerState` import is
reassigned to `Sleep`. It only talks to the MICOM over the serial port.
