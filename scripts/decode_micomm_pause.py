#!/usr/bin/env python3
"""Décode le journal de 180 octets écrit par micomm_pause.exe (\\MD\\micompause.log).
Usage : python3 -I decode_micomm_pause.py micompause.log"""
import struct, sys
d = open(sys.argv[1], "rb").read()
assert d[:4] == b"KDG1", f"en-tête inattendu : {d[:4]!r}"
it, op, rfd, r07, rff, cfd, c07, cff = struct.unpack_from("<8I", d, 4)
w = lambda r: {0: "réponse reçue (fil de lecture terminé)", 0x102: "rien reçu (attente 500 ms écoulée)"}.get(r, hex(r))
print(f"itérations (secondes de signal) : {it}  → durée ≈ {it} s")
print(f"ouverture COM2 : {'OK' if op == 1 else 'ÉCHEC (' + str(op) + ')'}")
for nom, r, c, off in (("FD", rfd, cfd, 36), ("07 01", r07, c07, 84), ("FF (dernier)", rff, cff, 132)):
    n = min(c, 48) if c < 0x10000 else 0
    print(f"{nom:13} : attente = {w(r)} ; octets reçus = {c} ; données = {d[off:off+n].hex(' ') or '-'}")
