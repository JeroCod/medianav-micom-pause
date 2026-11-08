"""Encodeur MIPS32 minimal (petit-boutiste) pour les patchs MediaNav. Formes limitées et vérifiées
par relecture radare2/capstone après chaque construction."""
REG = {"zero": 0, "at": 1, "v0": 2, "v1": 3, "a0": 4, "a1": 5, "a2": 6, "a3": 7,
       "t0": 8, "t1": 9, "t2": 10, "t3": 11, "t4": 12, "s0": 16, "s1": 17, "s2": 18, "s3": 19, "sp": 29, "ra": 31}
I_OPS = {"addiu": 0x09, "slti": 0x0a, "andi": 0x0c, "ori": 0x0d}

def asm(addr, line):
    m, _, rest = line.partition(" ")
    ar = [x.strip() for x in rest.split(",")] if rest else []
    r = lambda x: REG[x]
    n = lambda x: int(x, 0)
    def br(target):
        off = (n(target) - (addr + 4)) >> 2
        assert -0x8000 <= off < 0x8000
        return off & 0xFFFF
    if m == "nop":
        w = 0
    elif m in I_OPS:
        w = I_OPS[m] << 26 | r(ar[1]) << 21 | r(ar[0]) << 16 | (n(ar[2]) & 0xFFFF)
    elif m == "lui":
        w = 0x0F << 26 | r(ar[0]) << 16 | (n(ar[1]) & 0xFFFF)
    elif m in ("sw", "lw", "sb"):
        o, base = ar[1].rstrip(")").split("(")
        w = {"sw": 0x2B, "lw": 0x23, "sb": 0x28}[m] << 26 | r(base) << 21 | r(ar[0]) << 16 | (n(o) & 0xFFFF)
    elif m == "beq":                       # beq rs, rt, cible
        w = 0x04 << 26 | r(ar[0]) << 21 | r(ar[1]) << 16 | br(ar[2])
    elif m == "bnez":
        w = 0x05 << 26 | r(ar[0]) << 21 | br(ar[1])
    elif m == "beqz":
        w = 0x04 << 26 | r(ar[0]) << 21 | br(ar[1])
    elif m == "b":
        w = 0x04 << 26 | br(ar[0])
    elif m == "srl":
        w = r(ar[1]) << 16 | r(ar[0]) << 11 | n(ar[2]) << 6 | 0x02
    elif m == "move":                      # addu rd, rs, zero
        w = r(ar[1]) << 21 | r(ar[0]) << 11 | 0x21
    elif m in ("j", "jal"):
        t = n(ar[0])
        assert t >> 28 == (addr + 4) >> 28
        w = (0x02 if m == "j" else 0x03) << 26 | (t >> 2) & 0x3FFFFFF
    elif m == "jalr":
        w = r(ar[0]) << 21 | 31 << 11 | 0x09
    elif m == "jr":
        w = r(ar[0]) << 21 | 0x08
    else:
        raise ValueError(line)
    return w.to_bytes(4, "little")
