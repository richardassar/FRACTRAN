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


def plot_reachability(prog, start, outfile, max_states=400, title=None, style=None):
    style = style or STYLE
    fg = style.title_color
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
    fig, ax = plt.subplots(figsize=(1.2 + span * 1.1, 1.2 + span * 1.1),
                           facecolor=_facecolor(style))
    ax.set_facecolor(_facecolor(style))

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
                        arrowprops=dict(arrowstyle="-|>", color=fg, alpha=0.55, lw=1.3,
                                        shrinkA=14, shrinkB=14,
                                        connectionstyle=f"arc3,rad={curve}"), zorder=1)

    colors = ["#59a14f" if k == start_key else "#e15759" if k in sinks else "#4e79a7"
              for k in nodes]
    ax.scatter(xs, ys, s=780, c=colors, edgecolors=_facecolor(style), linewidths=1.5, zorder=3)
    for k in nodes:
        ax.text(pos[k][0], pos[k][1], str(as_int(k)), ha="center", va="center",
                color="white", fontsize=9, fontweight="bold", zorder=4)

    ax.set_xlabel(xlabel, color=fg)
    ax.set_ylabel(ylabel, color=fg)
    ax.tick_params(colors=fg)
    ax.set_title(title or f"reachability graph  ({len(nodes)} states"
                 + ("" if not r["truncated"] else ", truncated") + ")", color=fg)
    ax.margins(0.15)
    ax.set_aspect("equal") if len(primes) <= 2 else None
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("bottom", "left"):
        ax.spines[s].set_color(fg)
    fig.tight_layout()
    fig.savefig(outfile, dpi=style.dpi, bbox_inches="tight", facecolor=_facecolor(style),
                transparent=style.bg is None)
    plt.close(fig)
    return outfile, len(nodes), sorted(as_int(k) for k in sinks)


from dataclasses import dataclass, field  # noqa: E402


@dataclass
class Style:
    """One place for the look of every graph image; tweaks propagate to all."""
    bg: str = "#0a0d12"
    node_size: float = 9.0
    node_cmap: str = "turbo"       # bright across its whole range
    node_floor: float = 0.10       # skip the darkest 10% of the node cmap
    node_alpha: float = 0.8        # slightly translucent vertices
    node_edge_lw: float = 0.0
    edge_cmap: str = "hsv"         # saturated / no dark colours, keyed by fraction
    edge_lw: float = 0.7
    edge_alpha: float = 0.85
    tail_dim: float = 0.55         # brightness of the direction "tail" (1 = no dim)
    title_color: str = "#e6edf3"
    dpi: int = 150
    figsize: float = 14.0


STYLE = Style()  # the default (dark) theme

#: ready-made themes; pass one as ``style=`` to any plot function, or build your own
#: ``Style(...)``. ``bg=None`` renders on a transparent background.
THEMES = {
    "dark": STYLE,
    "light": Style(bg="#f6f3ec", node_floor=0.05, edge_alpha=0.9, tail_dim=0.62,
                   title_color="#1b1b1b", node_edge_lw=0.0),
    "paper": Style(bg="#faf7ef", node_cmap="plasma", node_floor=0.04, edge_cmap="hsv",
                   edge_alpha=0.9, tail_dim=0.62, title_color="#241f18"),
    "transparent": Style(bg=None),
}


def _facecolor(style):
    return style.bg if style.bg else "none"


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


def _sparse_lap(nodes, efrac):
    import numpy as np
    import scipy.sparse as sp
    nodes = list(nodes)
    idx = {k: i for i, k in enumerate(nodes)}
    n = len(nodes)
    rows, cols = [], []
    for a, b in efrac:
        if a in idx and b in idx:
            rows += [idx[a], idx[b]]
            cols += [idx[b], idx[a]]
    A = ((sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)) > 0).astype(float)
         if rows else sp.csr_matrix((n, n)))
    deg = np.asarray(A.sum(1)).ravel()
    L = sp.diags(deg) - A
    return idx, n, A, deg, L


def laplacian_harmonic(nodes, efrac, k):
    """The k-th graph-Fourier mode (Laplacian eigenvector; k=1 is Fiedler).
    Higher k = higher graph frequency = finer structure (the Pontryagin modes)."""
    import numpy as np
    from scipy.sparse.linalg import eigsh
    idx, n, A, deg, L = _sparse_lap(nodes, efrac)
    if n < k + 2:
        return [0.0] * n
    try:
        vals, vecs = eigsh(L, k=k + 1, which="SA", tol=1e-3, maxiter=8000)
        v = vecs[:, np.argsort(vals)[k]]
    except Exception:
        v = np.zeros(n)
    return [float(v[idx[nd]]) for nd in nodes]


def chebyshev_response(nodes, efrac, sources, order=12):
    """Chebyshev-polynomial graph filter T_order(scaled L) applied to a delta at
    the source -- the GSP spectral-filter/wavelet, localized ~order hops out."""
    import numpy as np
    import scipy.sparse as sp
    from scipy.sparse.linalg import eigsh
    idx, n, A, deg, L = _sparse_lap(nodes, efrac)
    if n < 3:
        return [0.0] * n
    try:
        lmax = float(eigsh(L, k=1, which="LM", tol=1e-2, maxiter=3000)[0])
    except Exception:
        lmax = 2.0 * (deg.max() if n else 1)
    Ls = (2.0 / max(lmax, 1e-6)) * L - sp.identity(n)
    x0 = np.zeros(n)
    for s in sources:
        if s in idx:
            x0[idx[s]] = 1.0
    if x0.sum() == 0:
        x0[0] = 1.0
    tprev, tcur = x0, Ls @ x0
    for _ in range(order - 1):
        tprev, tcur = tcur, 2 * (Ls @ tcur) - tprev
    return [float(tcur[idx[nd]]) for nd in nodes]


def markov_mode(nodes, efrac):
    """The slow random-walk (Markov) mode: 2nd eigenvector of the transition
    operator -- the walk's reaction coordinate (Fiedler for the random walk)."""
    import numpy as np
    import scipy.sparse as sp
    from scipy.sparse.linalg import eigsh
    idx, n, A, deg, L = _sparse_lap(nodes, efrac)
    if n < 3:
        return [0.0] * n
    d = deg.copy(); d[d == 0] = 1.0
    Dm12 = sp.diags(1.0 / np.sqrt(d))
    Lsym = sp.identity(n) - Dm12 @ A @ Dm12
    try:
        vals, vecs = eigsh(Lsym, k=2, which="SA", tol=1e-3, maxiter=8000)
        rw = (1.0 / np.sqrt(d)) * vecs[:, np.argsort(vals)[1]]
    except Exception:
        rw = np.zeros(n)
    return [float(rw[idx[nd]]) for nd in nodes]


def stationary_dist(nodes, efrac):
    """Stationary distribution of the random walk (reversible: pi ~ degree)."""
    idx, n, A, deg, L = _sparse_lap(nodes, efrac)
    tot = deg.sum() or 1.0
    return [float(deg[idx[nd]] / tot) for nd in nodes]


def heat_kernel(nodes, efrac, sources, t=5.0):
    """Heat diffused from the source, exp(-tL) delta (log-scaled for visibility)."""
    import numpy as np
    from scipy.sparse.linalg import expm_multiply
    idx, n, A, deg, L = _sparse_lap(nodes, efrac)
    x0 = np.zeros(n)
    for s in sources:
        if s in idx:
            x0[idx[s]] = 1.0
    if x0.sum() == 0 and n:
        x0[0] = 1.0
    try:
        h = np.log10(np.maximum(expm_multiply(-t * L, x0), 1e-12))
    except Exception:
        h = np.zeros(n)
    return [float(h[idx[nd]]) for nd in nodes]


def graph_wavelet(nodes, efrac, sources, t1=1.0, t2=4.0):
    """A spectral graph wavelet from the source: (e^{-t1 L} - e^{-t2 L}) delta -- a
    difference-of-heat-kernels band-pass, localized and signed (SGWT flavour).
    Vary (t1, t2) for the scale."""
    import numpy as np
    from scipy.sparse.linalg import expm_multiply
    idx, n, A, deg, L = _sparse_lap(nodes, efrac)
    x0 = np.zeros(n)
    for s in sources:
        if s in idx:
            x0[idx[s]] = 1.0
    if x0.sum() == 0 and n:
        x0[0] = 1.0
    try:
        w = expm_multiply(-t1 * L, x0) - expm_multiply(-t2 * L, x0)
    except Exception:
        w = np.zeros(n)
    return [float(w[idx[nd]]) for nd in nodes]


def commute_resistance(nodes, efrac, sources, modes=12):
    """Effective resistance / commute distance from the source, as a truncated
    spectral sum R_i = sum_{k>=1} (u_k(s) - u_k(i))^2 / lambda_k over the low
    graph-Fourier modes -- the commute-time embedding coordinate to the source."""
    import numpy as np
    from scipy.sparse.linalg import eigsh
    idx, n, A, deg, L = _sparse_lap(nodes, efrac)
    if n < 4:
        return [0.0] * n
    modes = min(modes, n - 2)
    try:
        vals, vecs = eigsh(L, k=modes + 1, which="SA", tol=1e-3, maxiter=8000)
    except Exception:
        return [0.0] * n
    s = idx.get(sources[0], 0) if sources else 0
    R = np.zeros(n)
    for j in range(len(vals)):
        if vals[j] > 1e-8:
            R += (vecs[s, j] - vecs[:, j]) ** 2 / vals[j]
    return [float(R[idx[nd]]) for nd in nodes]


#: node-colouring fields available to ``node_field`` / ``plot_multiway`` / gallery
NODE_FIELDS = ("depth", "logn", "fiedler", "harmonic2", "harmonic3",
               "chebyshev", "wavelet", "markov", "stationary", "heat", "commute")


def node_field(nodes, efrac, sources, field):
    """Dispatch a node-colouring field name to its values (spectral or structural)."""
    if field == "depth":
        return node_depths(nodes, efrac, sources)
    if field == "logn":
        return logn_values(nodes)
    if field == "fiedler":
        return laplacian_harmonic(nodes, efrac, 1)
    if field.startswith("harmonic"):
        return laplacian_harmonic(nodes, efrac, int(field[len("harmonic"):]))
    if field == "chebyshev":
        return chebyshev_response(nodes, efrac, sources)
    if field == "wavelet":
        return graph_wavelet(nodes, efrac, sources)
    if field == "commute":
        return commute_resistance(nodes, efrac, sources)
    if field == "markov":
        return markov_mode(nodes, efrac)
    if field == "stationary":
        return stationary_dist(nodes, efrac)
    if field == "heat":
        return heat_kernel(nodes, efrac, sources)
    raise ValueError(f"unknown node field {field!r}")


def plot_spectral_gallery(prog, start, outfile, fields, max_states=1000, cols=4, style=STYLE):
    """Same program lattice, painted by each spectral/structural field -- build the
    multiway graph and layout once, colour many ways."""
    import math

    import numpy as np

    nodes, efrac, sources = build_multiway(prog, start, max_states)
    nodes = list(nodes)
    pos = graph_layout(nodes, efrac)
    rows = math.ceil(len(fields) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 5.0, rows * 5.0), facecolor=_facecolor(style))
    axes = np.atleast_1d(axes).flat
    for ax, field in zip(axes, fields):
        draw_graph(ax, nodes, efrac, pos, node_field(nodes, efrac, sources, field), len(prog), style)
        ax.set_title(field, color=style.title_color, fontsize=13)
    for ax in list(axes)[len(fields):]:
        ax.set_facecolor(style.bg)
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(outfile, dpi=style.dpi, facecolor=_facecolor(style), bbox_inches="tight", pad_inches=0.2, transparent=style.bg is None)
    plt.close(fig)
    return outfile


def graph_layout(nodes, efrac, seed=1, iterations=80):
    import networkx as nx
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(efrac.keys())
    return nx.spring_layout(G, seed=seed, iterations=iterations,
                            k=1.4 / max(1, len(nodes) ** 0.5))


def draw_graph(ax, nodes, efrac, pos, values, nfrac, style=STYLE, fade_steps=8):
    """Shared renderer. Each directed edge is drawn in its fraction's colour as a
    smooth brightness fade from a dim tail (source) to a bright head (target), so
    direction reads without arrowheads; nodes are coloured by `values` through the
    node colormap. Opacity is baked into the RGBA (edge/node alpha channels) so
    ``Style.edge_alpha`` / ``Style.node_alpha`` apply exactly."""
    import numpy as np
    from matplotlib.collections import LineCollection

    nodes = list(nodes)
    ax.set_facecolor(_facecolor(style))

    ekeys = [(a, b, fi) for (a, b), fi in efrac.items() if a in pos and b in pos]
    if ekeys:
        A = np.array([pos[a] for a, b, fi in ekeys])                         # (E,2) sources
        B = np.array([pos[b] for a, b, fi in ekeys])                         # (E,2) targets
        base = plt.get_cmap(style.edge_cmap)(
            [(fi % max(1, nfrac) + 0.5) / max(1, nfrac) for a, b, fi in ekeys])  # (E,4)
        t = np.linspace(0.0, 1.0, fade_steps)
        pts = A[:, None, :] * (1 - t)[None, :, None] + B[:, None, :] * t[None, :, None]  # (E,S,2)
        segs = np.stack([pts[:, :-1], pts[:, 1:]], axis=2).reshape(-1, 2, 2)
        bright = style.tail_dim + (1 - style.tail_dim) * ((t[:-1] + t[1:]) / 2)  # per sub-segment
        cols = np.repeat(base[:, None, :], fade_steps - 1, axis=1)           # (E,S-1,4)
        cols[..., :3] *= bright[None, :, None]
        cols[..., 3] = style.edge_alpha
        ax.add_collection(LineCollection(segs, colors=cols.reshape(-1, 4),
                                         linewidths=style.edge_lw, zorder=1))

    v = np.array(values, float)
    vn = (style.node_floor + (1 - style.node_floor) * (v - v.min()) / (v.max() - v.min())
          if v.size and v.max() > v.min() else np.full(len(nodes), 0.6))
    ncol = plt.get_cmap(style.node_cmap)(vn)
    ncol[:, 3] = style.node_alpha                                            # bake node opacity
    ax.scatter([pos[k][0] for k in nodes], [pos[k][1] for k in nodes],
               c=ncol, s=style.node_size, edgecolors="none", zorder=3)
    ax.set_axis_off()
    ax.margins(0.03)


def plot_multiway(prog, starts, outfile, max_states=1000, node_by="depth",
                  style=STYLE, title=None):
    """Render the multiway graph. `node_by` in {"depth","logn","fiedler"} chooses
    the node colouring (fiedler = the graph-Fourier / Pontryagin spectral mode)."""
    nodes, efrac, sources = build_multiway(prog, starts, max_states)
    nodes = list(nodes)
    pos = graph_layout(nodes, efrac)
    values = node_field(nodes, efrac, sources, node_by)

    fig, ax = plt.subplots(figsize=(style.figsize, style.figsize), facecolor=_facecolor(style))
    draw_graph(ax, nodes, efrac, pos, values, len(prog), style)
    if title:
        ax.set_title(title, color=style.title_color, fontsize=15)
    fig.savefig(outfile, dpi=style.dpi, facecolor=_facecolor(style), bbox_inches="tight",
                pad_inches=0.12, transparent=style.bg is None)
    plt.close(fig)
    return outfile, len(nodes), len(efrac)


def _layered_layout(G, sources):
    """Top-down flowchart layout: y = -(BFS depth from source), x spread per layer."""
    from collections import deque
    depth = {}
    q = deque()
    for s in sources:
        if s in G:
            depth[s] = 0
            q.append(s)
    UG = G.to_undirected()
    while q:
        u = q.popleft()
        for v in UG[u]:
            if v not in depth:
                depth[v] = depth[u] + 1
                q.append(v)
    layers = {}
    for k in G.nodes:
        layers.setdefault(depth.get(k, 0), []).append(k)
    pos = {}
    for d, ks in layers.items():
        m = len(ks)
        for i, k in enumerate(sorted(ks, key=lambda z: as_int(z))):
            pos[k] = ((i - (m - 1) / 2) * 1.6, -float(d))
    return pos


def plot_diffusion_gallery(prog, start, outfile, kind="heat", values=None,
                           max_states=1000, cols=4, style=STYLE):
    """Same program lattice, a diffusion field swept over a parameter (build the
    multiway graph and layout once). ``kind='heat'`` paints the heat kernel
    exp(-tL)delta from the source at each time ``t`` in ``values`` (watch it spread);
    ``kind='wavelet'`` paints the spectral graph wavelet at each ``(t1, t2)`` scale."""
    import math

    import numpy as np

    if values is None:
        values = ([0.5, 1, 2, 4, 8, 16, 32, 64] if kind == "heat"
                  else [(0.5, 2), (1, 4), (2, 8), (4, 16), (8, 32), (16, 64)])
    nodes, efrac, sources = build_multiway(prog, start, max_states)
    nodes = list(nodes)
    pos = graph_layout(nodes, efrac)
    rows = math.ceil(len(values) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 5.0, rows * 5.0), facecolor=_facecolor(style))
    axes = np.atleast_1d(axes).flat
    for ax, v in zip(axes, values):
        if kind == "heat":
            vals = heat_kernel(nodes, efrac, sources, t=v)
            ttl = f"heat  t={v}"
        else:
            vals = graph_wavelet(nodes, efrac, sources, t1=v[0], t2=v[1])
            ttl = f"wavelet  t={v[0]}–{v[1]}"
        draw_graph(ax, nodes, efrac, pos, vals, len(prog), style)
        ax.set_title(ttl, color=style.title_color, fontsize=13)
    for ax in list(axes)[len(values):]:
        ax.set_facecolor(_facecolor(style))
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(outfile, dpi=style.dpi, facecolor=_facecolor(style), bbox_inches="tight",
                pad_inches=0.2, transparent=style.bg is None)
    plt.close(fig)
    return outfile


def plot_conway(prog, start, outfile, control_primes=None, style=None, title=None,
                show_ops=True, rankdir="TB"):
    """Conway's flowchart, to his own 1987 Sec.7 convention, rendered with graphviz.
    One node per program *line* (control state, labelled by its control prime); each
    fraction is a directed edge to the line it jumps to, labelled with the fraction
    (and its register ``-dec``/``+inc`` effect). The number of arrowheads = that
    fraction's PRIORITY at the node (single = tried first, double = next); a line
    that jumps to itself is a self-loop; a stub arrow in marks the start line and a
    stub out marks a line that can stop. Control states are recovered from the raw
    fraction list by the decompiler, so this is the finite ("collapsed") register
    machine, independent of the input value. Cleanest on compiled / one-hot programs;
    hand-golfed lists decompile only heuristically. Needs graphviz + pydot."""
    import pydot

    from .core import factorize
    from .decompile import classify, cfg

    style = style or THEMES["paper"]
    fg = style.title_color
    bg = style.bg or "transparent"
    node_fc = "none" if style.bg is None else "#ffffff"   # unfilled on transparent
    if control_primes is None:
        control_primes = classify(prog, start)["controls"]
    Sctrl = set(control_primes)

    edges, statenodes = [], set()
    for cur, es in cfg(prog, control_primes).items():
        if cur is None:
            continue
        for prio, e in enumerate(es):          # per-node order == FRACTRAN priority
            statenodes.add(cur)
            if e["next"] is not None:
                statenodes.add(e["next"])
            edges.append((cur, e["next"], prio, e["fr"], e["dec"], e["inc"]))
    start_state = factorize(start) if isinstance(start, int) else dict(start)
    start_ctrl = next((p for p in start_state if p in Sctrl), None)

    def opstr(dec, inc):
        s = ""
        if dec:
            s += "-" + ",".join(str(p) for p in sorted(dec))
        if inc:
            s += ("  " if s else "") + "+" + ",".join(str(p) for p in sorted(inc))
        return s

    g = pydot.Dot("conway", graph_type="digraph", rankdir=rankdir, bgcolor=bg,
                  dpi=str(style.dpi), splines="true", nodesep="0.45", ranksep="0.65",
                  fontname="Helvetica", fontcolor=fg, fontsize="18",
                  label=(title or ""), labelloc="t")
    g.set_node_defaults(shape="circle", style="filled", fillcolor=node_fc, color=fg,
                        penwidth="1.6", fontname="Helvetica", fontcolor=fg, fontsize="15",
                        width="0.55", fixedsize="true")
    g.set_edge_defaults(color=fg, fontname="Helvetica", fontcolor=fg, fontsize="11",
                        penwidth="1.3", arrowsize="1.0")

    for n in sorted(statenodes):
        g.add_node(pydot.Node(str(n)))
    if start_ctrl is not None:                                  # start stub
        g.add_node(pydot.Node("__start", style="invis", width="0", height="0", label=""))
        g.add_edge(pydot.Edge("__start", str(start_ctrl)))

    heads = ["normal", "normalnormal", "normalnormalnormal", "normalnormalnormalnormal"]
    for i, (s, d, prio, fr, dec, inc) in enumerate(edges):
        lab = f"{fr.num}/{fr.den}"
        if show_ops:
            op = opstr(dec, inc)
            if op:
                lab += "\n" + op
        head = heads[min(prio, len(heads) - 1)]             # arrowheads = priority
        if d is None:                                           # stop stub
            stop = f"__stop{i}"
            g.add_node(pydot.Node(stop, style="invis", width="0", height="0", label=""))
            g.add_edge(pydot.Edge(str(s), stop, label=lab, arrowhead=head))
        else:
            g.add_edge(pydot.Edge(str(s), str(d), label=lab, arrowhead=head))
    g.write_png(outfile)
    return outfile, len(statenodes), len(edges)


def plot_multiway_montage(specs, outfile, max_states=220, cols=3, node_by="depth", style=STYLE):
    """Grid of MULTIWAY graphs (one panel per (title, program, start-or-[starts]))
    drawn through the shared Style / draw_graph, nodes coloured by ``node_by``."""
    import math

    import numpy as np

    rows = math.ceil(len(specs) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4.4, rows * 4.4), facecolor=_facecolor(style))
    axes = np.atleast_1d(axes).flat
    for ax, (title, prog, starts) in zip(axes, specs):
        nodes, efrac, sources = build_multiway(prog, starts, max_states)
        nodes = list(nodes)
        pos = graph_layout(nodes, efrac)
        draw_graph(ax, nodes, efrac, pos, node_field(nodes, efrac, sources, node_by), len(prog), style)
        ax.set_title(f"{title}  ({len(nodes)})", color=style.title_color, fontsize=10)
    for ax in list(axes)[len(specs):]:
        ax.set_facecolor(style.bg)
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(outfile, dpi=style.dpi, facecolor=_facecolor(style), bbox_inches="tight", pad_inches=0.2, transparent=style.bg is None)
    plt.close(fig)
    return outfile


def collatz_map(n):
    return n // 2 if n % 2 == 0 else 3 * n + 1


def plot_collatz_coral(N=2000, highlights=(27,), outfile="collatz.png", style=None,
                       even_c="#4cc3ff", odd_c="#ff5d7a", hi_c="#ffd23f",
                       step=1.0, title=None):
    """The Collatz 'coral': overlay the trajectories of every start in 1..N under
    the Collatz map (which the FRACTRAN `collatz` program computes step for step);
    they all flow to 1 and merge into a tree, laid out by a parity turn (halving =
    small turn one way, 3n+1 = larger turn the other). Highlighted starts are the
    individual executions drawn bright over the coral. Background/dpi come from the
    shared Style; the parity colours stay meaningful."""
    from collections import deque

    import numpy as np
    from matplotlib.collections import LineCollection

    style = style or STYLE
    bg = _facecolor(style)

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
        ax.set_title(title, color=style.title_color, fontsize=13)
    fig.savefig(outfile, dpi=style.dpi, bbox_inches="tight", facecolor=bg, pad_inches=0.1,
                transparent=style.bg is None)
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
                 node_by="logn", style=STYLE, title=None):
    """Draw a reachability graph as a styled network through the shared Style /
    draw_graph. For squarefree starts the reachable set is a Boolean/divisor
    lattice (a hypercube). ``layout`` in {"kamada","spring","spectral"};
    ``node_by`` is any field from ``NODE_FIELDS``."""
    import networkx as nx

    nodes, efrac, sources = build_multiway(prog, start, max_states)
    nodes = list(nodes)
    if layout in ("kamada", "spectral"):
        G = nx.Graph()
        G.add_nodes_from(nodes)
        G.add_edges_from(efrac.keys())
        pos = (nx.kamada_kawai_layout(G) if layout == "kamada" else nx.spectral_layout(G))
    else:
        pos = graph_layout(nodes, efrac)

    fig, ax = plt.subplots(figsize=(style.figsize, style.figsize), facecolor=_facecolor(style))
    draw_graph(ax, nodes, efrac, pos, node_field(nodes, efrac, sources, node_by), len(prog), style)
    if title:
        ax.set_title(title, color=style.title_color, fontsize=14)
    fig.savefig(outfile, dpi=style.dpi, facecolor=_facecolor(style), bbox_inches="tight", pad_inches=0.15, transparent=style.bg is None)
    plt.close(fig)
    return outfile, len(nodes), len(efrac)


def plot_spacetime(prog, start, steps, outfile, cmap="magma", title=None, style=None):
    """Heatmap of the prime-exponent vector over a run: the FRACTRAN space-time
    diagram (rows = primes/registers, columns = steps, colour = exponent).
    Background/dpi come from the shared Style."""
    import numpy as np

    from .core import factorize, run_iter

    style = style or STYLE
    fg = style.title_color
    state = factorize(start) if isinstance(start, int) else dict(start)
    history = [dict(state)]
    for i, (_, s) in enumerate(run_iter(prog, state)):
        history.append(dict(s))
        if i + 1 >= steps:
            break
    primes = sorted({p for h in history for p in h})
    M = np.array([[h.get(p, 0) for p in primes] for h in history], float).T

    fig, ax = plt.subplots(figsize=(min(14, 2 + len(history) / 90), 1 + len(primes) * 0.32),
                           facecolor=_facecolor(style))
    ax.set_facecolor(_facecolor(style))
    im = ax.imshow(M, aspect="auto", cmap=cmap, origin="lower", interpolation="nearest")
    ax.set_yticks(range(len(primes)))
    ax.set_yticklabels(primes, fontsize=7)
    ax.set_xlabel("step", color=fg)
    ax.set_ylabel("prime (register)", color=fg)
    ax.tick_params(colors=fg)
    ax.set_title(title or f"space-time of the prime exponents ({len(history)} steps)", color=fg)
    cb = fig.colorbar(im, ax=ax, label="exponent", fraction=0.025)
    cb.ax.yaxis.set_tick_params(color=fg)
    cb.ax.yaxis.label.set_color(fg)
    plt.setp(cb.ax.get_yticklabels(), color=fg)
    fig.tight_layout()
    fig.savefig(outfile, dpi=style.dpi, bbox_inches="tight", facecolor=_facecolor(style),
                transparent=style.bg is None)
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
