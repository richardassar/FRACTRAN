"""The gallery: famous FRACTRAN programs, run on the native core.

Verified pieces run to a checked result; the pieces still blocked on external
data fidelity are reported honestly rather than faked.
"""

from fractran import gallery as G
from fractran import native
from fractran import programs as P
from fractran.core import program, run, fraction


def hdr(t):
    print("\n" + "=" * 66 + f"\n{t}\n" + "=" * 66)


# 1. PRIMEGAME — fully verified, on the native core -----------------------
hdr("PRIMEGAME  (verified)")
r = native.run(P.PRIMEGAME, {2: 1}, "vector", watch_pow2=15, max_steps=50_000_000)
print(f"  first 15 primes: {r['emitted']}")
print(f"  {r['steps']:,} steps at {r['rate']:,.0f} steps/s")
assert r["emitted"] == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
print("  OK")


# 2. Lomont's self-interpreter: encoder verified, interpreter partial ------
hdr("LOMONT self-interpreter  (encoder verified; run partial)")
enc = G.encode_program([fraction(21, 3), fraction(4, 17)])
print(f"  encode({{21/3, 4/17}}) = {enc}   (Lomont's published value 284533968840)")
assert enc == 284533968840
print(f"  interpreter: {len(G.LOMONT)} fractions, 32 primes — matches the source")

ADD = program("3/2")
start = G.encode_input(ADD, 6)  # run ADD on object n=6 (direct result: 9)
r = native.run(G.LOMONT, start, "vector", read=[7, 3], max_steps=1_000_000, timeout=60)
print(f"  run ADD(n=6) through CLF-INTERPRET: {r['steps']:,} steps, status={r['status']}")
print(f"    object state read from 7 = {r['read'].get(7)} (halt marker 3 = {r['read'].get(3)})")
print("    -> completes the base-11 DECODE phase but does not enter object simulation;")
print("       Lomont's post gives no worked trace and calls the program unoptimized,")
print("       so the full run recipe is underspecified. Encoder + fractions are solid.")


# 3. PIGAME — transcribed, execution-blocked by sheer slowness -------------
hdr("PIGAME  (transcribed; validation pending)")
print(f"  {len(G.PIGAME)} fractions; from 2^n*89 it should halt at 2^(nth pi digit).")
r = native.run(G.PIGAME, G.pigame_input(0), "vector", read=[2], max_steps=100_000_000)
print(f"  n=0 after {r['steps']:,} steps: still running (status={r['status']}) — a single")
print("  digit needs >10^9 steps, and sources disagree on a few fractions, so this")
print("  list is not yet execution-verified. Kept explicitly as unverified.")

print("\nGallery status: PRIMEGAME verified; Lomont encoder verified; PIGAME pending.")
