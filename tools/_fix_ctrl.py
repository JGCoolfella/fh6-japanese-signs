"""One-off: replace raw control bytes inside the tool sources with \\xNN escapes."""
import glob
import os

here = os.path.dirname(os.path.abspath(__file__))
for p in glob.glob(os.path.join(here, "*.py")):
    if p.endswith("_fix_ctrl.py"):
        continue
    data = open(p, "rb").read()
    out = bytearray()
    n = 0
    for ch in data:
        if ch < 32 and ch not in (9, 10, 13):
            out += b"\\x" + ("%02x" % ch).encode()
            n += 1
        else:
            out.append(ch)
    if n:
        open(p, "wb").write(bytes(out))
        print(os.path.basename(p), "fixed", n)
