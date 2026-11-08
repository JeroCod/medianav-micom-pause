#!/usr/bin/env python3
"""Patch de dboot.exe (dBoot 1.5, MediaNav Evolution, MIPS WinCE 6) — lot 1, 2026-11-05.
Usage : python3 -I patch_dboot.py <dboot.exe d'origine> <sortie>
Chaque zone modifiee est verifiee octet par octet contre l'original attendu (sinon arret).
 1. Bouton en bas a droite : un APPUI dans x>=560, y>=360 lance dmenu (= bascule WinCE).
    Le glisse horizontal d'origine reste actif en secours.
 2. Libelle dessine en bas a droite (x 600-790, y 446-470) : "[  Windows CE  ]".
 3. Fenetre d'acces : 5 s -> 10 s.
"""
import hashlib, sys

SRC_SHA = "0a33028b2ad849be21e6c97716e7166ab0c24ff919321eb7497c7d9643517538"  # sha256 de l'original (dboot15/dboot.exe)
TEXT_V, TEXT_F = 0x11000, 0x400     # .text : vaddr -> offset fichier
RDATA_V, RDATA_F = 0x12000, 0x1400  # .rdata

REG = {"zero": 0, "at": 1, "v0": 2, "v1": 3, "a0": 4, "a1": 5, "a2": 6, "a3": 7,
       "t0": 8, "t1": 9, "t2": 10, "t3": 11, "t4": 12}
I_OPS = {"addiu": 0x09, "slti": 0x0a, "andi": 0x0c}

def asm(addr, line):
    """Encodeur MIPS32 minimal (petit-boutiste) pour les seules formes utilisees ici.
    Verifie : les instructions d'origine reencodees doivent egaler les octets du fichier,
    et la sortie est relue par un desassembleur independant (radare2/capstone)."""
    m, _, rest = line.partition(" ")
    ar = [x.strip() for x in rest.split(",")] if rest else []
    r = lambda x: REG[x]
    n = lambda x: int(x, 0)
    if m == "nop":
        w = 0
    elif m in I_OPS:                       # addiu/slti/andi rt, rs, imm
        w = I_OPS[m] << 26 | r(ar[1]) << 21 | r(ar[0]) << 16 | (n(ar[2]) & 0xFFFF)
    elif m == "lui":
        w = 0x0F << 26 | r(ar[0]) << 16 | (n(ar[1]) & 0xFFFF)
    elif m == "sw":                        # sw rt, off(base)
        o, base = ar[1].rstrip(")").split("(")
        w = 0x2B << 26 | r(base) << 21 | r(ar[0]) << 16 | (n(o) & 0xFFFF)
    elif m == "bnez":                      # bne rs, zero, cible
        off = (n(ar[1]) - (addr + 4)) >> 2
        assert -0x8000 <= off < 0x8000
        w = 0x05 << 26 | r(ar[0]) << 21 | (off & 0xFFFF)
    elif m == "srl":                       # srl rd, rt, sa
        w = r(ar[1]) << 16 | r(ar[0]) << 11 | n(ar[2]) << 6 | 0x02
    elif m == "j":
        t = n(ar[0])
        assert t >> 28 == (addr + 4) >> 28
        w = 0x02 << 26 | (t >> 2) & 0x3FFFFFF
    else:
        raise ValueError(line)
    return w.to_bytes(4, "little")

def off(v):
    return v - TEXT_V + TEXT_F if v < RDATA_V else v - RDATA_V + RDATA_F

def main(src, dst):
    d = bytearray(open(src, "rb").read())
    h = hashlib.sha256(d).hexdigest()
    assert h.startswith(SRC_SHA), f"original inattendu : {h}"
    patches = []  # (vaddr, attendu, nouveau)

    def ins(addr, old_asm, new_asm):
        patches.append((addr, asm(addr, old_asm), asm(addr, new_asm)))

    # --- 1. WM_LBUTTONDOWN -> code ajoute en zone libre 0x11f00
    ins(0x11444, "addiu t3, zero, 1", "j 0x11f00")
    ins(0x11448, "lui t2, 1", "nop")
    cave = ["andi t0, a3, 0xffff",   # x
            "lui t2, 1",
            "addiu t3, zero, 1",
            "sw t3, 0x30b4(t2)",     # drapeau glisse = 1 (comportement d'origine)
            "sw t0, 0x30ac(t2)",     # x de depart (comportement d'origine)
            "slti t1, t0, 0x230",
            "bnez t1, 0x114c0",      # x < 560 -> sortie normale
            "srl t3, a3, 16",        # (delai) y
            "slti t1, t3, 0x168",
            "bnez t1, 0x114c0",      # y < 360 -> sortie normale
            "lui t4, 1",             # (delai) base utilisee par le code de bascule
            "j 0x11498",             # bascule : lance dmenu.exe puis quitte
            "nop"]
    for i, line in enumerate(cave):
        a = 0x11f00 + 4 * i
        patches.append((a, b"\0\0\0\0", asm(a, line)))
    # --- 2. Rectangle du libelle (SetRect gauche, haut, droite ; bas inchange 470)
    ins(0x11534, "addiu a1, zero, 0x14", "addiu a1, zero, 0x258")
    ins(0x11530, "addiu a2, zero, 0x1c2", "addiu a2, zero, 0x1be")
    ins(0x1152c, "addiu a3, zero, 0xc8", "addiu a3, zero, 0x316")
    old_s, new_s = "DBOOT 1.5 - 2016", "[  Windows CE  ]"
    assert len(old_s) == len(new_s) == 16
    patches.append((0x12284, old_s.encode("utf-16-le"), new_s.encode("utf-16-le")))
    # --- 3. Minuteur 5 s -> 10 s
    ins(0x116a0, "addiu a2, zero, 0x1388", "addiu a2, zero, 0x2710")

    for v, old, new in patches:
        o = off(v)
        assert bytes(d[o:o + len(old)]) == old, f"octets inattendus a {hex(v)}"
        d[o:o + len(new)] = new
    assert len(d) == 7680
    open(dst, "wb").write(d)
    print(f"{len(patches)} zones modifiees -> {dst}")
    print("sha256", hashlib.sha256(d).hexdigest())

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
