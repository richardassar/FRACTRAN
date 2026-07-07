"""The continuum / fluid limit of a FRACTRAN system (explorations.md Sec. 3C).

Instead of a single trajectory, evolve a *density* rho over a bounded box of
states under the moves -- the transport/master equation
``d rho/dt = sum_i (rho . guard along move i - outflow)``. Discretely this is the
random walk on the reachability graph: each state sends its mass, split over its
applicable within-box moves, to the successors; sinks absorb. The mean height
<log n> then drifts at the rate `spectral.height_drift`, and the relaxation rate
is the spectral gap. This closes the discrete -> fluid loop.
"""

from __future__ import annotations

import numpy as np

from .reachability import as_int, region_graph


def transition_matrix(prog, bounds):
    """Row-stochastic random walk on the box: uniform over within-box moves;
    sinks (and boundary mass) absorb. Returns (states, P)."""
    g = region_graph(prog, bounds)
    nodes = g["nodes"]
    n = len(nodes)
    idx = {k: i for i, k in enumerate(nodes)}
    P = np.zeros((n, n))
    for k, outs in g["edges"].items():
        i = idx[k]
        if outs:
            w = 1.0 / len(outs)
            for nk in outs:
                P[i, idx[nk]] += w
        else:
            P[i, i] = 1.0  # sink absorbs
    return [as_int(k) for k in nodes], P


def evolve(prog, bounds, rho0=None, steps=200):
    """Evolve a density for `steps`; return (states, history of rho, mean_height).

    `rho0` is a dict {n: mass} or None (a point mass at the largest state).
    """
    states, P = transition_matrix(prog, bounds)
    index = {s: i for i, s in enumerate(states)}
    rho = np.zeros(len(states))
    if rho0 is None:
        rho[int(np.argmax(states))] = 1.0
    else:
        for s, m in rho0.items():
            rho[index[s]] = m
    logn = np.array([np.log(s) if s > 1 else 0.0 for s in states])
    hist = [rho.copy()]
    heights = [float(rho @ logn)]
    for _ in range(steps):
        rho = rho @ P
        hist.append(rho.copy())
        heights.append(float(rho @ logn))
    return states, np.array(hist), np.array(heights)
