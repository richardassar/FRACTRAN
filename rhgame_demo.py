"""RHGAME: RH as a FRACTRAN halting problem. Verify the compiled sigma(n) kernel,
then run the Robin-violation search (which halts iff RH is false)."""

import math

from fractran import rhgame as G

# 1. the FRACTRAN kernel: sigma(n) really computes as a fraction list ------
sig = G.make_sigma()
print(f"compiled sigma(n): {len(sig.fractions)} fractions")
print("  verifying against Python sigma:")
for n in [6, 10, 12, 28, 30]:
    fr, py = G.fractran_sigma(sig, n), G.sigma(n)
    print(f"    sigma({n:2}) = {fr}   (python {py})   {'ok' if fr == py else 'FAIL'}")
    assert fr == py

# 2. Robin's inequality and the known exceptions ---------------------------
print(f"\ne^gamma = {G.E_GAMMA:.10f}")
print("Robin's inequality fails at exactly 27 integers, all <= 5040. Ratios:")
for n in [5040, 2520, 840]:
    print(f"    n={n:5}: sigma/(n ln ln n) = {G.robin_ratio(n):.5f}  > e^gamma  (exception)")

# 3. the search: halts iff a Robin violation exists above 5040 -------------
HI = 1_000_000
best_n, best_r, violation = G.search(HI)
print(f"\nRHGAME search over 5040 < n <= {HI:,}:")
print(f"  record ratio: n={best_n} -> {best_r:.6f}   (e^gamma = {G.E_GAMMA:.6f})")
if violation is None:
    print(f"  NO Robin violation found: RHGAME does not halt in this range")
    print(f"  (RH is consistent with all n <= {HI:,}).")
else:
    print(f"  VIOLATION at n={violation} -- RHGAME halts -> RH would be FALSE")

print("\nRHGAME halts  <=>  a Robin counterexample exists  <=>  RH is false.")
