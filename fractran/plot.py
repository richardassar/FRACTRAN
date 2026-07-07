"""Draw the reachability graph of a FRACTRAN system to an image file.

The nondeterministic reachability graph (the multiway graph) is rendered with
nodes labelled by their integer state and directed edges for the moves. For a
two-prime program the nodes are laid out on the exponent lattice (v_p, v_q) — the
Hasse diagram of the reachable order — so the grid / lattice structure is visible;
otherwise a spring layout is used. The start node is green, halting states (normal
forms) red.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # headless: write a file, no display needed
import matplotlib.pyplot as plt  # noqa: E402

from .core import factorize  # noqa: E402
from .reachability import _key, as_int, reachable  # noqa: E402


def plot_reachability(prog, start, outfile, max_states=400, title=None):
    r = reachable(prog, start, max_states=max_states)
    seen, graph = r["seen"], r["graph"]
    nodes = list(seen)
    start_key = _key(factorize(start) if isinstance(start, int) else dict(start))
    sinks = {k for k, v in graph.items() if not v}

    primes = sorted({p for s in seen.values() for p in s})
    xlabel = ylabel = ""
    if len(primes) == 2:
        pos = {k: (seen[k].get(primes[0], 0), seen[k].get(primes[1], 0)) for k in nodes}
        xlabel, ylabel = f"$v_{{{primes[0]}}}$", f"$v_{{{primes[1]}}}$"
    elif len(primes) <= 1:
        p = primes[0] if primes else 2
        pos = {k: (seen[k].get(p, 0), 0.0) for k in nodes}
        xlabel = f"$v_{{{p}}}$"
    else:
        import networkx as nx

        G = nx.DiGraph()
        G.add_nodes_from(nodes)
        for k, outs in graph.items():
            for _, nk in outs:
                G.add_edge(k, nk)
        pos = nx.spring_layout(G, seed=1, k=1.2)

    xs = [pos[k][0] for k in nodes]
    ys = [pos[k][1] for k in nodes]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1)
    fig, ax = plt.subplots(figsize=(1.2 + span * 1.1, 1.2 + span * 1.1))

    seen_edges = set()
    for k, outs in graph.items():
        for _, nk in outs:
            if (k, nk) in seen_edges:
                continue
            seen_edges.add((k, nk))
            x0, y0 = pos[k]
            x1, y1 = pos[nk]
            curve = 0.0 if (nk, k) not in {(b, a) for a, b in seen_edges} else 0.12
            ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                        arrowprops=dict(arrowstyle="-|>", color="#9aa4b2", lw=1.3,
                                        shrinkA=14, shrinkB=14,
                                        connectionstyle=f"arc3,rad={curve}"), zorder=1)

    colors = ["#59a14f" if k == start_key else "#e15759" if k in sinks else "#4e79a7"
              for k in nodes]
    ax.scatter(xs, ys, s=780, c=colors, edgecolors="white", linewidths=1.5, zorder=3)
    for k in nodes:
        ax.text(pos[k][0], pos[k][1], str(as_int(k)), ha="center", va="center",
                color="white", fontsize=9, fontweight="bold", zorder=4)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title or f"reachability graph  ({len(nodes)} states"
                 + ("" if not r["truncated"] else ", truncated") + ")")
    ax.margins(0.15)
    ax.set_aspect("equal") if len(primes) <= 2 else None
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(outfile, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return outfile, len(nodes), sorted(as_int(k) for k in sinks)


def plot_spacetime(prog, start, steps, outfile, cmap="magma", title=None):
    """Heatmap of the prime-exponent vector over a run: the FRACTRAN space-time
    diagram (rows = primes/registers, columns = steps, colour = exponent)."""
    import numpy as np

    from .core import factorize, run_iter

    state = factorize(start) if isinstance(start, int) else dict(start)
    history = [dict(state)]
    for i, (_, s) in enumerate(run_iter(prog, state)):
        history.append(dict(s))
        if i + 1 >= steps:
            break
    primes = sorted({p for h in history for p in h})
    M = np.array([[h.get(p, 0) for p in primes] for h in history], float).T

    fig, ax = plt.subplots(figsize=(min(14, 2 + len(history) / 90), 1 + len(primes) * 0.32))
    im = ax.imshow(M, aspect="auto", cmap=cmap, origin="lower", interpolation="nearest")
    ax.set_yticks(range(len(primes)))
    ax.set_yticklabels(primes, fontsize=7)
    ax.set_xlabel("step")
    ax.set_ylabel("prime (register)")
    ax.set_title(title or f"space-time of the prime exponents ({len(history)} steps)")
    fig.colorbar(im, ax=ax, label="exponent", fraction=0.025)
    fig.tight_layout()
    fig.savefig(outfile, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return outfile


def plot_rule30(width=480, gens=260, outfile="rule30.png", ink="#101418",
                paper="#f4f1ea", pad=0.0):
    """Render the Rule 30 space-time triangle (the same CA the FRACTRAN rule30
    program computes) as a crisp raster from a single seed cell."""
    import numpy as np
    from matplotlib.colors import ListedColormap

    row = np.zeros(width, dtype=np.uint8)
    row[width // 2] = 1
    grid = np.zeros((gens, width), dtype=np.uint8)
    for g in range(gens):
        grid[g] = row
        left = np.roll(row, 1)
        left[0] = 0
        right = np.roll(row, -1)
        right[-1] = 0
        row = left ^ (row | right)

    fig, ax = plt.subplots(figsize=(width / 90, gens / 90), dpi=200)
    ax.imshow(grid, cmap=ListedColormap([paper, ink]), interpolation="nearest")
    ax.set_axis_off()
    fig.savefig(outfile, bbox_inches="tight", pad_inches=pad, facecolor=paper)
    plt.close(fig)
    return outfile
