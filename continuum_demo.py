"""The continuum / fluid limit: evolve a density over a box and watch it transport
at the height-drift rate the spectral module predicts."""

import numpy as np

from fractran import continuum as C
from fractran import spectral as S
from fractran.core import program


def show(title, prog, bounds, steps):
    states, hist, heights = C.evolve(prog, bounds, steps=steps)
    print(f"\n=== {title} ===")
    print(f"  box states: {len(states)}   mass conserved: {hist[0].sum():.4f} -> {hist[-1].sum():.4f}")
    print(f"  mean height <log n>:  {heights[0]:.3f} -> {heights[-1]:.3f}  "
          f"over {steps} steps")
    print(f"  per-move height drift (spectral): {S.height_drift(prog):+.3f}")
    final = hist[-1]
    top = np.argsort(final)[::-1][:4]
    print(f"  final mass concentrates at: {[(states[i], round(float(final[i]), 3)) for i in top if final[i] > 1e-3]}")


# {1/2,1/3}: negative drift -> the density drains to the sink n=1
show("{1/2, 1/3}  (drains to 1)", program("1/2 1/3"), {2: 5, 3: 5}, steps=80)

# {2/3,3/2}: zero drift -> the density redistributes but the mean height is stable
show("{2/3, 3/2}  (zero drift: height-stable)", program("2/3 3/2"), {2: 3, 3: 3}, steps=60)
