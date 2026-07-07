"""Graph-Fourier / spectral analysis of FRACTRAN systems: the harmonic data of
the move set (dispersion, drift, Newton polytope) and the numerical spectrum of a
finite reachability box (zero modes = conserved quantities, unit-circle eigs =
cycles)."""

import numpy as np

from fractran import spectral as S
from fractran.core import program


def harmonic(title, prog):
    primes, D = S.moves(prog)
    _, d = S.drift(prog)
    _, verts = S.newton_polytope(prog)
    lo, hi = S.symbol_stats(prog)
    print(f"\n=== {title} ===")
    print(f"  primes {primes}   move vectors (num-den):")
    for row in D:
        print(f"      {row.astype(int).tolist()}")
    print(f"  drift  sum_i delta_i = {d.astype(int).tolist()}   "
          f"height drift <drift,log p> = {S.height_drift(prog):+.4f}")
    print(f"  Newton polytope vertices = {[v.astype(int).tolist() for v in verts]}")
    print(f"  |lambda(theta)| over the dual torus in [{lo:.3f}, {hi:.3f}]")


def spectrum(title, prog, bounds):
    r = S.region_spectrum(prog, bounds)
    print(f"\n=== {title}   box {bounds} ===")
    print(f"  states={r['states']}  zero modes (conserved-quantity components)={r['zero_modes']}"
          f"  spectral gap={r['spectral_gap']:.4f}")
    print(f"  adjacency spectral radius={r['adjacency_spectral_radius']:.3f}  "
          f"unit-circle eigenvalue args (k/L) = {r['unit_circle']}")
    print(f"  sinks (normal forms) = {r['sinks']}")


print("# HARMONIC DATA OF THE MOVES (the bulk / Pontryagin side) -------------")
harmonic("{1/2, 1/3}  (pure decrements: net drift down)", program("1/2 1/3"))
harmonic("{2/3, 3/2}  (balanced: zero drift, conserves v2+v3)", program("2/3 3/2"))
harmonic("{3/2, 5/2}  (growth: net drift up)", program("3/2 5/2"))

print("\n# GRAPH-FOURIER SPECTRUM OF THE MULTIWAY BOX --------------------------")
spectrum("{1/2, 1/3}  (drains, acyclic)", program("1/2 1/3"), {2: 3, 3: 2})
spectrum("{2/3, 3/2}  (conserved v2+v3 -> cyclic level sets)", program("2/3 3/2"), {2: 3, 3: 3})

# check: zero modes should equal the number of connected components (level sets)
r = S.region_spectrum(program("2/3 3/2"), {2: 3, 3: 3})
print(f"\n{{2/3,3/2}}: {r['zero_modes']} zero modes = {r['zero_modes']} conserved-quantity "
      f"level sets in the box (v2+v3 = const).")
