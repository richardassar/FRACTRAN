"""Round-trip check + storage/compression comparison across representations."""
import gzip
from fractran import serialize as S
from fractran import demos as D
from fractran.calc import build_calculator
from fractran.programs import PRIMEGAME
from fractran.gallery import LOMONT

progs = {
    "PRIMEGAME":     PRIMEGAME,
    "calculator":    build_calculator().fractions,
    "rule30 (w=31)": D.make_rule30(31).fractions,
    "LOMONT interp": LOMONT,
}

def gz(b): return len(gzip.compress(b, 9))

hdr = f"{'program':<15}{'fr':>5}{'text':>7}{'txt.gz':>7}{'bin':>7}{'bin.gz':>7}{'col':>7}{'col.gz':>7}"
print(hdr); print("-"*len(hdr))
for name, frs in progs.items():
    assert S.from_bytes(S.to_bytes(frs)) == frs, f"interleaved round-trip failed: {name}"
    assert S.from_bytes_columnar(S.to_bytes_columnar(frs)) == frs, f"columnar round-trip failed: {name}"
    text = " ".join(f"{f.num}/{f.den}" for f in frs).encode()
    b = S.to_bytes(frs); c = S.to_bytes_columnar(frs)
    print(f"{name:<15}{len(frs):>5}{len(text):>7}{gz(text):>7}{len(b):>7}{gz(b):>7}{len(c):>7}{gz(c):>7}")
print("\nall round-trips verified (both formats reconstruct the exact fractions)")
