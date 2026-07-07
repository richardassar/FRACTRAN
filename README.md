# fractran

A complete FRACTRAN toolchain — interpreter, compiler, loop accelerator, native
C++/GMP core, a self-interpreter, and a pile of runnable I/O programs — built up
from Conway's "just multiply fractions."

## What is FRACTRAN?

John Conway's esoteric language. A program is an ordered list of fractions; the
state is a single positive integer `n`. Each step multiplies `n` by the first
fraction that keeps it an integer, halting when none does. It's Turing-complete:
the exponent of prime `p` in `n` is register `p`, and a fraction is a guarded
register update (divisibility is the guard). The whole system is a register /
Minsky machine written multiplicatively.

## Quickstart

```sh
# compiled FRACTRAN programs doing real terminal I/O
python3 demos.py rule30 20        # Rule 30 cellular automaton (the chaotic triangle)
python3 demos.py pyramid 6        # ASCII pyramid
python3 demos.py collatz 27       # Collatz trajectory of 27
python3 demos.py march 30         # animation: a '*' walks across
python3 demos.py gcd 1071 462     # Euclid's algorithm

# a calculator compiled to 188 fractions, reading stdin, writing stdout
printf '0 3 4\n1 6 7\n3 17 5\n' | python3 calc.py    # 7, 42, then 3 and 2

# watch Conway's PRIMEGAME emit primes live, with register bars
python3 visualize.py primegame

# show any program's actual fraction list
python3 demos.py rule30 --show
```

## Tests & demos

```sh
python3 demo.py            # interpreter, streaming I/O, compiler, decompiler
python3 bench.py           # loop accelerator: exact vs reference, big speedups
python3 bootstrap_demo.py  # a FRACTRAN self-interpreter, compiled from the toolchain
python3 io_demo.py         # compiled streaming transducers (doubler, running sum)
python3 calc_demo.py       # calculator vs Python arithmetic
python3 measure_repr.py    # compact binary format + compression study
```

## Native core (optional, fast)

```sh
make -C native             # builds native/fractran_core (needs GMP)
python3 bench_native.py    # ~130x over the pure-Python stepper
```

Two modes: **vector** (int64 prime exponents — the fast path) and **canonical**
(a real GMP integer `n` — the faithful, unbounded oracle).

## Architecture

`fractran/` is a dependency-free Python package. The pipeline is:

> structured front-end → Minsky IR → fraction list → (accelerate / run native)

| module | role |
|---|---|
| `core.py` | exponent-vector interpreter (a step is a guarded vector add) |
| `minsky.py` / `build.py` | Minsky IR + structured front-end that lower to fractions |
| `io.py` | streaming I/O trampoline (READ/WRITE/DONE halt-and-resume) |
| `accel.py` | loop accelerator (collapse constant-effect loops to closed form) |
| `decompile.py` / `viz.py` | recover the control-flow graph; live terminal visualizer |
| `native.py` + `native/` | binding to the C++/GMP core |
| `bootstrap.py` | a FRACTRAN self-interpreter, compiled from this toolchain |
| `calc.py` / `demos.py` | the calculator and the I/O demo gallery |
| `serialize.py` | compact binary representation of programs |

Design notes, the module-by-module tour, the external gallery, and the roadmap
live in **[fractran-overview.md](fractran-overview.md)**. The deep theoretical
landscape — the prime-valuation lattice, p-adic and height dynamics, vector
addition systems, binomial/toric ideals, universality, and where elliptic curves
do and don't enter — is in **[theory.md](theory.md)**, with citations.
