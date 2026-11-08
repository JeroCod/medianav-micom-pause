#!/usr/bin/env python3
"""Construit micomm_pause.exe à partir de dmenu.exe (dBoot 1.5, MediaNav Evolution, MIPS WinCE 6).
Usage : python3 -I build_micomm_pause.py <dmenu.exe d'origine> <sortie micomm_pause.exe>

But : sous Windows CE (branche StartWinCE de dBoot), ni UpgradeManager ni MicomManager ne tournent,
donc plus personne n'envoie le « signal de vie » au micro-contrôleur (MICOM) sur COM2, et son chien
de garde redémarre l'appareil au bout d'environ 2 min 20. micomm_pause rejoue exactement ce signal :
séquence d'ouverture d'UpgradeManager (cmd 0xFD sans donnée, puis cmd 0x07 donnée 0x01), puis la trame
de vie (cmd 0xFF) chaque seconde. Tant qu'il tourne, le chien de garde reste désactivé.

Trames MICOM (UART COM2) : AA [mgr<<4 | groupe] cmd longueur [données] XOR. Signal de vie = AA 11 FF 00 44.

Journal (diagnostic) : écrit un résumé binaire de 180 octets dans \\MD\\micompause.log (\\MD = la clé USB),
réécrit chaque seconde ; décodeur : decode_micomm_pause.py. En l'absence de clé, l'écriture échoue
silencieusement et le signal continue d'être envoyé.
  0 'KDG1' | 4 itérations | 8 ouverture COM2 (1 = ok) | 12/16/20 retour d'attente FD/07/FF (0 = réponse
  reçue, 0x102 = rien) | 24/28/32 octets reçus après FD/07/dernier FF | 36/84/132 : 48 octets reçus.

Sécurité : l'import SetSystemPowerState (ordinal 1582) est réaffecté à Sleep (496) → ce programme ne
peut pas redémarrer l'appareil ; il ne fait que parler au MICOM sur le port série.

AUCUN binaire n'est inclus dans ce dépôt : fournissez votre propre dmenu.exe d'origine (sa somme SHA-256
est vérifiée ci-dessous). Reverse engineering à fin d'interopérabilité / usage personnel, sans garantie.
"""
import hashlib, os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mipsenc import asm

SRC_SHA = "9026cfcf3c19814b3a7b81fd323d9939a91ba76518602a65cb1d36d2aaa46ced"
TEXT_V, TEXT_F, RDATA_V, RDATA_F = 0x11000, 0x400, 0x13000, 0x1C00
MAIN, MAIN_MAX = 0x1175C, 0x11A90           # ancien FUN_1175c (820 octets) réutilisé
PATH_V = 0x132E8                             # ancienne chaîne \Storage Card3\StartWinCE (inutilisée)
IMP = lambda a: ["lui t0, 1", f"lw t0, {a:#x}(t0)", "jalr t0", "nop"]
CREATEFILE, WRITEFILE, CLOSEHANDLE, SLEEP, MEMCPY = 0x4024, 0x4030, 0x4018, 0x4048, 0x4068

def send(cmd, ln, data_on_stack, rslot, cslot, rxoff):
    c = ["move a0, s0", "addiu a1, zero, 1", f"addiu a2, zero, {cmd:#x}", f"addiu a3, zero, {ln}"]
    if data_on_stack:
        c += ["addiu t0, sp, 0x200", "jal 0x1141c", "sw t0, 0x10(sp)"]
    else:
        c += ["jal 0x1141c", "sw zero, 0x10(sp)"]
    c += [f"sw v0, {rslot}(s1)", "lw t0, 0x11c(s0)", f"sw t0, {cslot}(s1)",
          f"addiu a0, s1, {rxoff}", "addiu a1, s0, 0x19", "jal MEMCPY48", "nop"]
    return c

CODE = ([
    "addiu sp, sp, -0x300", "sw ra, 0x2fc(sp)", "sw s0, 0x2f0(sp)", "sw s1, 0x2f4(sp)", "sw s2, 0x2f8(sp)",
    "addiu s0, sp, 0x20", "addiu s1, sp, 0x140",
    "lui t0, 0x3147", "ori t0, t0, 0x444b", "sw t0, 0(s1)", "sw zero, 4(s1)",
    "sw zero, 12(s1)", "sw zero, 16(s1)", "sw zero, 20(s1)", "sw zero, 24(s1)", "sw zero, 28(s1)", "sw zero, 32(s1)",
    "jal 0x11000", "move a0, s0",
    "jal 0x11020", "move a0, s0",
    "sw v0, 8(s1)",
    "jal WRITELOG", "nop",
    "lw t0, 8(s1)", "beqz t0, END", "nop",
] + send(0xFD, 0, False, 12, 24, 36)
  + ["addiu t0, zero, 1", "sb t0, 0x200(sp)"]
  + send(0x07, 1, True, 16, 28, 84)
  + ["jal WRITELOG", "nop"]
  + ["LOOP: nop"] + send(0xFF, 0, False, 20, 32, 132)
  + ["lw t0, 4(s1)", "addiu t0, t0, 1", "sw t0, 4(s1)", "jal WRITELOG", "nop",
     "lui t0, 1", f"lw t0, {SLEEP:#x}(t0)", "jalr t0", "addiu a0, zero, 0x3e8",
     "b LOOP", "nop",
     "END: lw s2, 0x2f8(sp)", "lw s1, 0x2f4(sp)", "lw s0, 0x2f0(sp)", "lw ra, 0x2fc(sp)",
     "move v0, zero", "jr ra", "addiu sp, sp, 0x300",
     # memcpy(a0, a1, 48) en appel terminal
     "MEMCPY48: lui t0, 1", f"lw t0, {MEMCPY:#x}(t0)", "jr t0", "addiu a2, zero, 48",
     # WRITELOG : CreateFileW(\MD\micompause.log, GENERIC_WRITE, 0, NULL, OPEN_ALWAYS, NORMAL, NULL) ; WriteFile 180 ; CloseHandle
     "WRITELOG: addiu sp, sp, -0x30", "sw ra, 0x2c(sp)", "sw s3, 0x28(sp)",
     "lui a0, 1", f"addiu a0, a0, {PATH_V & 0xFFFF:#x}", "lui a1, 0x4000", "move a2, zero", "move a3, zero",
     "addiu t0, zero, 4", "sw t0, 0x10(sp)", "addiu t0, zero, 0x80", "sw t0, 0x14(sp)", "sw zero, 0x18(sp)"]
  + IMP(CREATEFILE)
  + ["move s3, v0", "addiu t0, zero, -1", "beq s3, t0, WLEND", "nop",
     "move a0, s3", "move a1, s1", "addiu a2, zero, 180", "addiu a3, sp, 0x20", "sw zero, 0x10(sp)"]
  + IMP(WRITEFILE)
  + ["move a0, s3"] + IMP(CLOSEHANDLE)
  + ["WLEND: lw s3, 0x28(sp)", "lw ra, 0x2c(sp)", "jr ra", "addiu sp, sp, 0x30"])

def main(src, dst):
    d = bytearray(open(src, "rb").read())
    assert hashlib.sha256(d).hexdigest() == SRC_SHA, "dmenu.exe inattendu"
    old, new = struct.pack("<I", 0x80000000 | 1582), struct.pack("<I", 0x80000000 | 496)
    hits = [i for i in range(len(d) - 3) if d[i:i + 4] == old]
    assert hits == [0x2104, 0x2248], hits
    for i in hits:
        d[i:i + 4] = new
    # chemin du journal
    po = PATH_V - RDATA_V + RDATA_F
    old_s = "\\Storage Card3\\StartWinCE".encode("utf-16-le") + b"\0\0"
    assert d[po:po + len(old_s)] == old_s
    new_s = "\\MD\\micompause.log".encode("utf-16-le") + b"\0\0"
    assert len(new_s) <= len(old_s)
    d[po:po + len(old_s)] = new_s + b"\0" * (len(old_s) - len(new_s))
    # code
    labels, lines = {}, []
    for i, l in enumerate(CODE):
        m = re.match(r"^([A-Z0-9_]+):\s*(.*)$", l)
        if m:
            labels[m.group(1)] = MAIN + 4 * i
            l = m.group(2)
        lines.append(l)
    assert MAIN + 4 * len(lines) <= MAIN_MAX, "code trop long"
    o = MAIN - TEXT_V + TEXT_F
    assert d[o:o + 4] == asm(MAIN, "addiu sp, sp, -0x58")
    for i, l in enumerate(lines):
        l = re.sub(r"\b([A-Z][A-Z0-9_]+)\b", lambda mm: hex(labels[mm.group(1)]) if mm.group(1) in labels else mm.group(1), l)
        d[o + 4 * i:o + 4 * i + 4] = asm(MAIN + 4 * i, l)
    open(dst, "wb").write(d)
    print(f"micomm_pause.exe : {len(lines)} instructions, labels { {k: hex(v) for k, v in labels.items()} }")
    print("sha256", hashlib.sha256(d).hexdigest())

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
