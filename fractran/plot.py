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


from dataclasses import dataclass, field  # noqa: E402


@dataclass
class Style:
    """One place for the look of every graph image; tweaks propagate to all."""
    bg: str = "#0a0d12"
    node_size: float = 11.0
    node_cmap: str = "turbo"       # bright across its whole range
    node_floor: float = 0.10       # skip the darkest 10% of the node cmap
    node_alpha: float = 1.0
    node_edge_lw: float = 0.0
    edge_cmap: str = "hsv"         # saturated / no dark colours, keyed by fraction
    edge_lw: float = 0.7
    edge_alpha: float = 0.85
    tail_dim: float = 0.55         # brightness of the direction "tail" (1 = no dim)
    title_color: str = "#e6edf3"
    dpi: int = 150
    figsize: float = 14.0


STYLE = Style()


def _starts_list(starts):
    return [starts] if isinstance(starts, (int, dict)) else list(starts)


def build_multiway(prog, starts, max_states=1000):
    """Multiway graph: fire every applicable fraction at every integer state,
    iterated from the start(s). Returns (nodes, efrac{(a,b):fraction_index}, sources)."""
    nodes, efrac, sources = set(), {}, []
    for s in _starts_list(starts):
        sources.append(_key(factorize(s) if isinstance(s, int) else dict(s)))
        r = reachable(prog, s, max_states=max_states)
        nodes |= set(r["seen"])
        for k, outs in r["graph"].items():
            for fi, nk in outs:
                efrac[(k, nk)] = fi
    return nodes, efrac, sources


def node_depths(nodes, efrac, sources):
    from collections import deque
    adj = {}
    for a, b in efrac:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    depth = {s: 0 for s in sources if s in nodes}
    q = deque(depth)
    while q:
        u = q.popleft()
        for v in adj.get(u, ()):
            if v not in depth:
                depth[v] = depth[u] + 1
                q.append(v)
    return [depth.get(k, 0) for k in nodes]


def logn_values(nodes):
    import numpy as np
    return [np.log(as_int(k)) if as_int(k) > 1 else 0.0 for k in nodes]


def fiedler_values(nodes, efrac):
    """The Fiedler vector (2nd graph-Fourier mode of the Laplacian) per node -- the
    smallest non-trivial Pontryagin/graph-Fourier frequency, a smooth coordinate."""
    import numpy as np
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla

    nodes = list(nodes)
    idx = {k: i for i, k in enumerate(nodes)}
    n = len(nodes)
    rows, cols = [], []
    for a, b in efrac:
        if a in idx and b in idx:
            rows += [idx[a], idx[b]]
            cols += [idx[b], idx[a]]
    if not rows or n < 3:
        return [0.0] * n
    A = (sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)) > 0).astype(float)
    L = sp.diags(np.asarray(A.sum(1)).ravel()) - A
    try:
        _vals, vecs = spla.eigsh(L, k=min(2, n - 1), which="SA", tol=1e-3, maxiter=5000)
        fv = vecs[:, -1]
    except Exception:
        fv = np.zeros(n)
    return list(fv)


def graph_layout(nodes, efrac, seed=1, iterations=80):
    import networkx as nx
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(efrac.keys())
    return nx.spring_layout(G, seed=seed, iterations=iterations,
                            k=1.4 / max(1, len(nodes) ** 0.5))


def draw_graph(ax, nodes, efrac, pos, values, nfrac, style=STYLE):
    """Shared renderer: fraction-coloured directed edges (dim tail -> bright head)
    and nodes coloured by `values` through the style's node colormap."""
    import numpy as np
    from matplotlib.collections import LineCollection

    nodes = list(nodes)
    ax.set_facecolor(style.bg)
    ecmap = plt.get_cmap(style.edge_cmap)
    segs, cols = [], []
    for (a, b), fi in efrac.items():
        if a in pos and b in pos:
            pa, pb = np.array(pos[a]), np.array(pos[b])
            pm = (pa + pb) / 2
            base = np.array(ecmap((fi % max(1, nfrac) + 0.5) / max(1, nfrac)))
            tail = base.copy()
            tail[:3] *= style.tail_dim
            segs += [[pa, pm], [pm, pb]]
            cols += [tail, base]
    ax.add_collection(LineCollection(segs, colors=cols, linewidths=style.edge_lw,
                                     alpha=style.edge_alpha, zorder=1))
    v = np.array(values, float)
    if v.max() > v.min():
        vn = style.node_floor + (1 - style.node_floor) * (v - v.min()) / (v.max() - v.min())
    else:
        vn = np.full(len(v), 0.6)
    ax.scatter([pos[k][0] for k in nodes], [pos[k][1] for k in nodes],
               c=plt.get_cmap(style.node_cmap)(vn), s=style.node_size, alpha=style.node_alpha,
               edgecolors=style.bg, linewidths=style.node_edge_lw, zorder=3)
    ax.set_axis_off()
    ax.margins(0.03)


def plot_multiway(prog, starts, outfile, max_states=1000, node_by="depth",
                  style=STYLE, title=None):
    """Render the multiway graph. `node_by` in {"depth","logn","fiedler"} chooses
    the node colouring (fiedler = the graph-Fourier / Pontryagin spectral mode)."""
    nodes, efrac, sources = build_multiway(prog, starts, max_states)
    pos = graph_layout(nodes, efrac)
    values = {"depth": lambda: node_depths(nodes, efrac, sources),
              "logn": lambda: logn_values(nodes),
              "fiedler": lambda: fiedler_values(nodes, efrac)}[node_by]()

    fig, ax = plt.subplots(figsize=(style.figsize, style.figsize), facecolor=style.bg)
    draw_graph(ax, nodes, efrac, pos, values, len(prog), style)
    if title:
        ax.set_title(title, color=style.title_color, fontsize=15)
    fig.savefig(outfile, dpi=style.dpi, facecolor=style.bg, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    return outfile, len(nodes), len(efrac)


def plot_multiway_montage(specs, outfile, max_states=220, cols=3, bg="#0d1117"):
    """Grid of MULTIWAY graphs -- every applicable fraction fired at every state
    (integer states only) -- one panel per (title, program, [starts]). The
    nondeterministic reachability graph is drawn grey; the deterministic FRACTRAN
    execution from each start is highlighted in colour. Two-prime programs are
    laid out on the exponent lattice, others by a spring layout.
    """
    import math

    import networkx as nx
    import numpy as np
    from matplotlib import cm
    from matplotlib.collections import LineCollection

    from .core import factorize, run_iter

    rows = math.ceil(len(specs) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4.3, rows * 4.3), facecolor=bg)
    axes = np.atleast_1d(axes).flat

    for ax, (title, prog, starts) in zip(axes, specs):
        ax.set_facecolor(bg)
        G = nx.DiGraph()
        seen = {}
        for s in starts:
            r = reachable(prog, s, max_states=max_states)
            seen.update(r["seen"])
            for k, outs in r["graph"].items():
                G.add_node(k)
                for _, nk in outs:
                    G.add_edge(k, nk)
        primes = sorted({p for st in seen.values() for p in st})
        if len(primes) == 2:
            pos = {k: (seen[k].get(primes[0], 0), seen[k].get(primes[1], 0)) for k in G.nodes}
            ax.set_aspect("equal")
        else:
            pos = nx.spring_layout(G, seed=2, iterations=90)

        segs = [[pos[a], pos[b]] for a, b in G.edges()]
        ax.add_collection(LineCollection(segs, colors="#7c8899",
                                         linewidths=0.5, alpha=0.28, zorder=1))
        ax.scatter([pos[k][0] for k in G.nodes], [pos[k][1] for k in G.nodes],
                   s=14, c="#4e79a7", edgecolors="none", zorder=2)

        cmap = cm.get_cmap("turbo", max(2, len(starts)))
        for j, s in enumerate(starts):
            st = factorize(s) if isinstance(s, int) else dict(s)
            path = [_key(st)]
            work = dict(st)
            for i, (_, cur) in enumerate(run_iter(prog, work)):
                path.append(_key(cur))
                if i > max_states:
                    break
            pts = np.array([pos[k] for k in path if k in pos])
            if len(pts):
                ax.plot(pts[:, 0], pts[:, 1], color=cmap(j), lw=1.7, alpha=0.95, zorder=4)
                ax.scatter([pts[0, 0]], [pts[0, 1]], c=[cmap(j)], s=42,
                           edgecolors="white", linewidths=0.5, zorder=5)
        tag = f"  ({len(G)} states)" if not r["truncated"] else f"  ({len(G)}+ states)"
        ax.set_title(title + tag, color="#e6edf3", fontsize=9)
        ax.set_axis_off()

    for ax in list(axes):
        if not ax.has_data() and not ax.get_title():
            ax.set_visible(False)
    fig.tight_layout()
    fig.savefig(outfile, dpi=140, bbox_inches="tight", facecolor=bg, pad_inches=0.2)
    plt.close(fig)
    return outfile


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
