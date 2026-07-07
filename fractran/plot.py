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


def collatz_map(n):
    return n // 2 if n % 2 == 0 else 3 * n + 1


def plot_collatz_coral(N=2000, highlights=(27,), outfile="collatz.png",
                       bg="#0b0e13", even_c="#4cc3ff", odd_c="#ff5d7a",
                       hi_c="#ffd23f", step=1.0, title=None):
    """The Collatz 'coral': overlay the trajectories of every start in 1..N under
    the Collatz map (which the FRACTRAN `collatz` program computes step for step);
    they all flow to 1 and merge into a tree, laid out by a parity turn (halving =
    small turn one way, 3n+1 = larger turn the other). Highlighted starts are the
    individual executions drawn bright over the coral."""
    from collections import deque

    import numpy as np
    from matplotlib.collections import LineCollection

    edges = set()
    for start in range(1, N + 1):
        x = start
        while x != 1:
            y = collatz_map(x)
            edges.add((x, y))
            x = y
    pred = {}
    for k, m in edges:
        pred.setdefault(m, []).append(k)

    pos = {1: np.zeros(2)}
    ang = {1: 90.0}
    q = deque([1])
    while q:
        n = q.popleft()
        for m in sorted(pred.get(n, [])):
            a = ang[n] + (7.0 if m % 2 == 0 else -20.0)
            ang[m] = a
            pos[m] = pos[n] + step * np.array([np.cos(np.radians(a)), np.sin(np.radians(a))])
            q.append(m)

    segs = [[pos[k], pos[m]] for k, m in edges if k in pos and m in pos]
    cols = [even_c if k % 2 == 0 else odd_c for k, m in edges if k in pos and m in pos]

    fig, ax = plt.subplots(figsize=(11, 11), facecolor=bg)
    ax.set_facecolor(bg)
    ax.add_collection(LineCollection(segs, colors=cols, linewidths=0.6, alpha=0.5))
    for h in highlights:
        pts, x = [], h
        while x != 1 and x in pos:
            pts.append(pos[x])
            x = collatz_map(x)
        pts.append(pos[1])
        pts = np.array(pts)
        ax.plot(pts[:, 0], pts[:, 1], color=hi_c, lw=2.4, alpha=0.95, zorder=5)
        ax.scatter([pts[0, 0]], [pts[0, 1]], c=hi_c, s=40, zorder=6)
    ax.set_axis_off()
    ax.set_aspect("equal")
    ax.autoscale_view()
    if title:
        ax.set_title(title, color="#e6edf3", fontsize=13)
    fig.savefig(outfile, dpi=150, bbox_inches="tight", facecolor=bg, pad_inches=0.1)
    plt.close(fig)
    return outfile, len(pos), len(edges)


def plot_execution(prog, starts, outfile, max_states=4000, layout="spring",
                   bg="#0d1117", title=None):
    """Draw the multiway reachability graph over a set of starts (grey) with each
    deterministic FRACTRAN execution highlighted as a coloured path."""
    import networkx as nx
    import numpy as np
    from matplotlib import cm

    from .core import factorize, run_iter

    if isinstance(starts, int):
        starts = [starts]
    G = nx.DiGraph()
    trajs = []
    for s in starts:
        r = reachable(prog, s, max_states=max_states)
        for k, outs in r["graph"].items():
            G.add_node(k)
            for _, nk in outs:
                G.add_edge(k, nk)
        st = factorize(s) if isinstance(s, int) else dict(s)
        path = [_key(st)]
        for i, (_, cur) in enumerate(run_iter(prog, st)):
            path.append(_key(cur))
            if i > max_states:
                break
        trajs.append(path)

    pos = (nx.kamada_kawai_layout(G.to_undirected()) if layout == "kamada"
           else nx.spring_layout(G, seed=3, iterations=200))
    fig, ax = plt.subplots(figsize=(11, 11), facecolor=bg)
    ax.set_facecolor(bg)
    segs = [[pos[a], pos[b]] for a, b in G.edges()]
    from matplotlib.collections import LineCollection

    ax.add_collection(LineCollection(segs, colors="#8892a0", linewidths=0.5, alpha=0.25))
    colors = cm.get_cmap("turbo", max(2, len(trajs)))
    for j, path in enumerate(trajs):
        pts = np.array([pos[k] for k in path if k in pos])
        ax.plot(pts[:, 0], pts[:, 1], color=colors(j), lw=2.0, alpha=0.9, zorder=4)
        ax.scatter([pts[0, 0]], [pts[0, 1]], c=[colors(j)], s=45, zorder=5)
    ax.set_axis_off()
    ax.autoscale_view()
    if title:
        ax.set_title(title, color="#e6edf3", fontsize=13)
    fig.savefig(outfile, dpi=150, bbox_inches="tight", facecolor=bg, pad_inches=0.15)
    plt.close(fig)
    return outfile, G.number_of_nodes(), len(trajs)


def plot_network(prog, start, outfile, max_states=4000, layout="kamada",
                 cmap="plasma", bg="#0d1117", node_size=70, edge_alpha=0.28,
                 title=None):
    """Draw the reachability graph as a styled network: force/energy layout,
    nodes coloured by log(n), thin translucent edges, no labels. For squarefree
    starts the reachable set is a Boolean/divisor lattice (a hypercube)."""
    import networkx as nx
    import numpy as np

    r = reachable(prog, start, max_states=max_states)
    G = nx.DiGraph()
    G.add_nodes_from(r["seen"])
    for k, outs in r["graph"].items():
        for _, nk in outs:
            G.add_edge(k, nk)
    if layout == "kamada":
        pos = nx.kamada_kawai_layout(G.to_undirected())
    elif layout == "spectral":
        pos = nx.spectral_layout(G.to_undirected())
    else:
        pos = nx.spring_layout(G, seed=3, iterations=250, k=None)

    nodes = list(G.nodes)
    xs = np.array([pos[k][0] for k in nodes])
    ys = np.array([pos[k][1] for k in nodes])
    vals = np.array([np.log(as_int(k)) if as_int(k) > 1 else 0.0 for k in nodes])

    fig, ax = plt.subplots(figsize=(10, 10), facecolor=bg)
    ax.set_facecolor(bg)
    segs = np.array([[pos[a], pos[b]] for a, b in G.edges()])
    from matplotlib.collections import LineCollection

    ax.add_collection(LineCollection(segs, colors="#aab4c4", linewidths=0.7,
                                     alpha=edge_alpha, zorder=1))
    ax.scatter(xs, ys, c=vals, cmap=cmap, s=node_size, edgecolors="white",
               linewidths=0.35, zorder=3)
    ax.set_axis_off()
    ax.margins(0.06)
    ax.autoscale_view()
    if title:
        ax.set_title(title, color="#e6edf3", fontsize=13)
    fig.savefig(outfile, dpi=150, bbox_inches="tight", facecolor=bg, pad_inches=0.15)
    plt.close(fig)
    return outfile, len(nodes), G.number_of_edges()


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
