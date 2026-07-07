"""Graph-Fourier modes: the dispersion amoeba over the dual torus, and the
Laplacian eigenbasis (graph frequencies + Fiedler vector) of a reachability box."""

import numpy as np

from fractran import spectral as S
from fractran.core import program

# 1. the dispersion |lambda(theta)| over the 2-torus (the amoeba: dark = zero locus)
primes, grid, M = S.dispersion_grid(program("2/3 3/2"), samples=28)
print(f"|lambda(theta)| for {{2/3,3/2}} over primes {primes}  (dark = symbol zero):")
ramp = " .:-=+*#%@"
mx = M.max()
for row in M:
    print("  " + "".join(ramp[int(v / mx * (len(ramp) - 1))] for v in row))

# 2. graph frequencies (Laplacian eigenvalues) of a box
m = S.laplacian_modes(program("2/3 3/2"), {2: 3, 3: 3})
print(f"\ngraph frequencies of {{2/3,3/2}} box (Laplacian eigenvalues):")
print(f"  {np.round(m['vals'], 3).tolist()}")
print(f"  (multiplicity of 0 = {int(np.sum(m['vals'] < 1e-8))} = conserved-quantity components)")

# 3. the Fiedler vector: the lowest nonzero graph-frequency mode -- a smooth
#    gradient across the reachable lattice
states, freq, fied = S.fiedler(program("1/2 1/3"), {2: 3, 3: 2})
print(f"\nFiedler mode of {{1/2,1/3}} box (lowest nonzero frequency {freq:.3f}):")
for i in np.argsort(fied):
    print(f"    state {states[i]:>4}: {fied[i]:+.3f}")
