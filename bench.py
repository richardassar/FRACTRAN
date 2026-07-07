"""Acceleration benchmark.

Two kinds of rows:
  * verify — inputs small enough that the reference interpreter finishes; we
    assert the accelerated run matches it on *every* register (exact).
  * scale  — inputs far beyond what raw FRACTRAN could ever churn through; we run
    only the accelerator and check its result against the known function. (The
    register value is stored as a prime *exponent*, so 100! or fib(500) costs
    nothing — no giant integer is ever materialised.)
"""

import math

from fractran import programs as P
from fractran.accel import Accelerator
from fractran.core import run

CAP = 3_000_000


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def regs_only(state, controls):
    return {p: e for p, e in state.items() if p not in controls and e}


def bench(name, compiled, out_reg, want_fn, verify, scale):
    controls = set(compiled.label_prime.values())
    acc = Accelerator(compiled.fractions, controls)
    rp = compiled.reg_prime[out_reg]
    print(f"\n{name}")
    print(f"  {'input':>13} {'raw steps':>13} {'accel ops':>10} {'speedup':>10}   result")

    for args in verify:
        start = compiled.start(**args)
        raw_state, raw_steps, status = run(compiled.fractions, dict(start), max_steps=CAP)
        acc_state, acc_ops = acc.run(dict(start))
        assert status == "halt", f"raw didn't finish {name}{args} under cap"
        assert regs_only(raw_state, controls) == acc_state, f"MISMATCH {name}{args}"
        got, want = acc_state.get(rp, 0), want_fn(**args)
        assert got == want, f"WRONG {name}{args}: {got} != {want}"
        istr = ",".join(f"{k}={v}" for k, v in args.items())
        print(f"  {istr:>13} {raw_steps:>13,} {acc_ops:>10,} {raw_steps / acc_ops:>9,.0f}x   {out_reg}={got}")

    for args in scale:
        acc_state, acc_ops = acc.run(compiled.start(**args))
        got, want = acc_state.get(rp, 0), want_fn(**args)
        assert got == want, f"WRONG {name}{args}: {got} != {want}"
        istr = ",".join(f"{k}={v}" for k, v in args.items())
        shown = got if got < 10**15 else f"{out_reg} has {len(str(got))} digits"
        print(f"  {istr:>13} {'(skipped)':>13} {acc_ops:>10,} {'accel-only':>10}   {out_reg}={shown}")


bench("MULTIPLY  dst = a*b", P.make_multiply(), "dst", lambda a, b: a * b,
      verify=[dict(a=3, b=4), dict(a=40, b=50), dict(a=200, b=200)],
      scale=[dict(a=1000, b=1000), dict(a=100000, b=100000)])

bench("FIBONACCI a = fib(n)", P.make_fibonacci(), "a", fib,
      verify=[dict(n=10), dict(n=20)],
      scale=[dict(n=50), dict(n=100), dict(n=1000)])

bench("FACTORIAL f = n!", P.make_factorial(), "f", lambda n: math.factorial(n),
      verify=[dict(n=5), dict(n=8)],
      scale=[dict(n=20), dict(n=100)])

bench("ADD       dst = a+b", P.make_add(), "dst", lambda a, b: a + b,
      verify=[dict(a=5, b=3), dict(a=100, b=250)], scale=[])

print("\nExact-equivalence checks passed on every 'verify' input;")
print("'scale' results match the reference function.")
