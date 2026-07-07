"""Head-to-head: pure-Python stepper vs the native C++ core (vector & canonical).

Same programs, same results — the point is the constant-factor speedup of native
stepping, and that the GMP canonical mode (authentic big-integer semantics)
agrees with the vector view.
"""

import time

from fractran import native
from fractran import programs as P
from fractran.core import run, run_iter


def py_primegame(limit):
    """Time pure-Python PRIMEGAME and return (primes, steps, seconds)."""
    out, state, steps = [], {2: 1}, 0
    t = time.time()
    for _, s in run_iter(P.PRIMEGAME, state):
        steps += 1
        if len(s) == 1 and 2 in s and s[2] > 1:
            out.append(s[2])
            if len(out) >= limit:
                break
    return out, steps, time.time() - t


def rate(steps, secs):
    return steps / secs if secs else float("inf")


print("PRIMEGAME — first 25 primes")
N = 25
py_primes, py_steps, py_t = py_primegame(N)
vec = native.run(P.PRIMEGAME, {2: 1}, "vector", watch_pow2=N)
can = native.run(P.PRIMEGAME, {2: 1}, "canonical", watch_pow2=N)

assert py_primes == vec["emitted"] == can["emitted"], "prime streams disagree!"
print(f"  all three emit the same {N} primes, ending {py_primes[-3:]}")
print(f"  {'engine':<22}{'steps':>10}{'sec':>9}{'steps/sec':>15}{'vs python':>11}")
print(f"  {'python (vector)':<22}{py_steps:>10,}{py_t:>9.3f}{rate(py_steps, py_t):>15,.0f}{'1x':>11}")
for label, r in [("native vector", vec), ("native canonical (GMP)", can)]:
    sp = rate(r["steps"], r["elapsed"]) / rate(py_steps, py_t)
    print(f"  {label:<22}{r['steps']:>10,}{r['elapsed']:>9.3f}{r['rate']:>15,.0f}{sp:>10,.0f}x")


print("\nMULTIPLY (raw stepping, no acceleration) — 120 * 120")
start = {2: 120, 3: 120}
t = time.time()
st, py_steps, _ = run(P.MULTIPLY, dict(start))
py_t = time.time() - t
vec = native.run(P.MULTIPLY, dict(start), "vector", read=[5])
can = native.run(P.MULTIPLY, dict(start), "canonical", read=[5])
assert st.get(5, 0) == vec["read"][5] == can["read"][5] == 14400, "results disagree!"
print(f"  all three compute 120*120 = {vec['read'][5]}  ({py_steps:,} steps)")
print(f"  python={rate(py_steps, py_t):,.0f}/s   "
      f"native-vector={vec['rate']:,.0f}/s   native-canonical={can['rate']:,.0f}/s")

print("\nAll engines agree; native vector is the fast path, GMP canonical is the oracle.")
