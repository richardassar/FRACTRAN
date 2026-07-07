"""Live FRACTRAN visualizer CLI.

Usage:
    python3 visualize.py primegame            # watch the primes emerge
    python3 visualize.py multiply 3 4         # 2^3 * 3^4 -> 5^12
    python3 visualize.py fib 10               # compiled Fibonacci
    python3 visualize.py factorial 5          # compiled factorial
    python3 visualize.py add 5 3

Options: --stride N (render every Nth step), --delay S (seconds/frame),
--max N (step cap). Set NO_COLOR=1 to disable colour.
"""

from __future__ import annotations

import argparse

from fractran import programs as P
from fractran import viz


def _compiled(make, title, **regs):
    c = make()
    return c.fractions, c.start(**regs), c.names, set(c.label_prime.values()), title


def build(name, nums):
    if name == "primegame":
        return P.PRIMEGAME, {2: 1}, {}, set(), "PRIMEGAME — exponents of the pure powers of two are the primes"
    if name == "multiply":
        a, b = (nums + [3, 4])[:2]
        names = {2: "a", 3: "b", 5: "prod", 7: "s7", 11: "s11", 13: "s13"}
        return P.MULTIPLY, {2: a, 3: b}, names, {11, 13}, f"MULTIPLY — {a} * {b}"
    if name == "add":
        a, b = (nums + [5, 3])[:2]
        return P.ADD, {2: a, 3: b}, {2: "a", 3: "b"}, set(), f"ADD — {a} + {b}"
    if name == "fib":
        n = (nums + [10])[0]
        return _compiled(P.make_fibonacci, f"FIBONACCI — fib({n})", n=n)
    if name == "factorial":
        n = (nums + [5])[0]
        return _compiled(P.make_factorial, f"FACTORIAL — {n}!", n=n)
    raise SystemExit(f"unknown program: {name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("program")
    ap.add_argument("args", nargs="*", type=int)
    ap.add_argument("--stride", type=int, default=None)
    ap.add_argument("--delay", type=float, default=0.06)
    ap.add_argument("--max", type=int, default=1_000_000)
    a = ap.parse_args()

    prog, start, names, controls, title = build(a.program, a.args)
    emit = viz.power_of_two if a.program == "primegame" else None
    stride = a.stride if a.stride is not None else (200 if a.program == "primegame" else 1)

    viz.watch(
        prog, start, names,
        controls=controls, stride=stride, delay=a.delay,
        max_steps=a.max, emit=emit, title=title,
    )


if __name__ == "__main__":
    main()
