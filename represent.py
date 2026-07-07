"""Measure how compactly a FRACTRAN program can be stored, on the calculator."""
from fractran.calc import build_calculator

calc = build_calculator()
frs = calc.fractions

# (1) naive decimal text "num/den ..."
decimal = " ".join(f"{f.num}/{f.den}" for f in frs)

# (2) factored text "p^e*.../p^e*..."
def fac(d): return "*".join(f"{p}^{e}" for p,e in d.items()) or "1"
factored = " ".join(f"{fac(f.num_f)}/{fac(f.den_f)}" for f in frs)

# (3) index form: relabel primes 0..P-1; store each fraction as
#     den = {idx:exp} and delta = num-den = {idx:Δ}. Count (idx,exp) pairs.
primes = sorted({p for f in frs for p in (set(f.num_f)|set(f.den_f))})
idx = {p:i for i,p in enumerate(primes)}
pairs = 0
maxexp = 0
for f in frs:
    delta = {}
    for p,e in f.den_f.items(): delta[p] = delta.get(p,0)-e
    for p,e in f.num_f.items(): delta[p] = delta.get(p,0)+e
    pairs += len(f.den_f) + sum(1 for v in delta.values() if v)  # den guard + delta
    maxexp = max([maxexp]+[abs(e) for e in list(f.den_f.values())+list(delta.values())])
# 1 byte prime-index (P<256) + 1 byte exponent each
index_bytes = pairs
print(f"program: {len(frs)} fractions, {len(primes)} distinct primes (max exp seen {maxexp})")
print(f"  (1) decimal text     : {len(decimal):6} bytes")
print(f"  (2) factored text    : {len(factored):6} bytes")
print(f"  (3) index+exponent   : {index_bytes:6} bytes  ({pairs} (idx,exp) pairs, 1B+1B each)")
print(f"       prime table cost : 0 (indices ARE the i-th primes)")
print(f"  ratio decimal/index  : {len(decimal)/index_bytes:.1f}x smaller")
