"""Spectral / graph-Fourier analysis of FRACTRAN systems.

States form the abelian group (+)_p Z and the fractions are translations by the
move vectors delta_i = num - den. So the Cayley-graph Fourier transform is the
Pontryagin transform: characters chi_theta(e) = exp(2*pi*i*<theta,e>) diagonalize
the (bulk) dynamics, with Fourier symbol / dispersion

    lambda(theta) = sum_i exp(2*pi*i*<theta, delta_i>),

a Laurent polynomial in z_p = exp(2*pi*i*theta_p). See explorations.md, Sec. 4.

Two kinds of computation:
  * exact bulk/harmonic data of the move set (no boundary): `moves`, `dispersion`,
    `drift`, `diffusion`, `newton_polytope`, `symbol_stats`.
  * the numerical graph spectrum of a finite reachability box (the multiway graph):
    `region_spectrum` -- zero modes = conserved-quantity level sets, unit-circle
    adjacency eigenvalues = cyclic components.
"""

from __future__ import annotations

import itertools

import numpy as np

from .reachability import as_int, region_graph


def moves(prog):
    """Return (primes, D) with D[i] = num - den, the move vector of fraction i."""
    primes = sorted({p for f in prog for p in set(f.num_f) | set(f.den_f)})
    idx = {p: i for i, p in enumerate(primes)}
    D = np.zeros((len(prog), len(primes)))
    for r, f in enumerate(prog):
        for p, e in f.den_f.items():
            D[r, idx[p]] -= e
        for p, e in f.num_f.items():
            D[r, idx[p]] += e
    return primes, D


def dispersion(prog):
    """Return (primes, lambda) where lambda(theta) is the Fourier symbol."""
    primes, D = moves(prog)

    def lam(theta):
        return complex(np.sum(np.exp(2j * np.pi * (D @ np.asarray(theta, float)))))

    return primes, lam


def drift(prog):
    """Sum of the moves -- the first-order (low-frequency) drift vector.

    Its pairing with (log p) is the mean height drift of the continuum limit.
    """
    primes, D = moves(prog)
    return primes, D.sum(axis=0)


def diffusion(prog):
    """Second-moment tensor sum_i delta_i delta_i^T (the low-frequency diffusion)."""
    primes, D = moves(prog)
    return primes, D.T @ D


def height_drift(prog):
    """<sum_i delta_i, (log p)_p> -- the scalar mean drift of log n."""
    primes, d = drift(prog)
    return float(np.dot(d, np.log(primes)))


def newton_polytope(prog):
    """Vertices of the Newton polytope of the symbol (convex hull of the moves)."""
    primes, D = moves(prog)
    pts = np.unique(D, axis=0)
    if pts.shape[0] > pts.shape[1] >= 1:
        try:
            from scipy.spatial import ConvexHull

            hull = ConvexHull(pts)
            return primes, pts[hull.vertices]
        except Exception:
            pass
    return primes, pts


def symbol_stats(prog, samples=32):
    """Min/max modulus of lambda over the dual torus (spectral range of the bulk)."""
    primes, lam = dispersion(prog)
    P = len(primes)
    grid = np.linspace(0.0, 1.0, samples, endpoint=False)
    if P <= 3:
        vals = [abs(lam(t)) for t in itertools.product(grid, repeat=P)]
    else:
        rng = np.random.default_rng(0)
        vals = [abs(lam(rng.random(P))) for _ in range(4000)]
    return float(min(vals)), float(max(vals))


def region_spectrum(prog, bounds, tol=1e-8):
    """Graph-Fourier spectrum of a finite reachability box.

    Returns: states; zero_modes (symmetric-Laplacian kernel dim = connected
    components = conserved-quantity level sets); spectral_gap; the directed
    adjacency spectral radius; and unit_circle (arguments/2pi of modulus-1
    adjacency eigenvalues -- the cyclic components, a length-L cycle giving k/L).
    """
    g = region_graph(prog, bounds)
    nodes = g["nodes"]
    n = len(nodes)
    idx = {k: i for i, k in enumerate(nodes)}
    A = np.zeros((n, n))
    for k, outs in g["edges"].items():
        for nk in outs:
            A[idx[k], idx[nk]] += 1.0

    As = ((A + A.T) > 0).astype(float)  # undirected skeleton
    Ls = np.diag(As.sum(1)) - As
    lap = np.sort(np.linalg.eigvalsh(Ls))
    zero_modes = int(np.sum(lap < tol))
    gap = float(lap[zero_modes]) if n > zero_modes else 0.0

    adj = np.linalg.eigvals(A)
    circle = adj[np.abs(np.abs(adj) - 1.0) < 1e-6]
    args = sorted({round(float(np.angle(z) / (2 * np.pi)) % 1.0, 4) for z in circle})
    return {
        "states": n,
        "zero_modes": zero_modes,
        "spectral_gap": gap,
        "adjacency_spectral_radius": float(np.max(np.abs(adj))) if n else 0.0,
        "unit_circle": args,
        "sinks": sorted(as_int(k) for k in g["sinks"]),
    }
