"""Order-free (nondeterministic) evolution of FRACTRAN states.

Deterministic FRACTRAN fires the FIRST applicable fraction. Drop that priority
and fire ANY applicable fraction: the fractions become a set of commuting lattice
moves, and a start state unfolds into a reachability GRAPH — bundles of paths
that bifurcate (a state with several applicable moves) and, where the moves are
independent, reconverge (concurrency diamonds). This is the underlying vector
addition system / Petri net (see theory.md, Sec. 5).

Two kinds of branching:
  * concurrency  - independent moves (after firing one, the other still applies);
    order is irrelevant and the paths reconverge into a diamond. Locally
    confluent.
  * conflict     - moves competing for the same factor: firing one disables the
    other, so the paths diverge for good. Genuine bifurcation.

For a conflict-free program the reachable set is a distributive lattice
(a product of chains / a grid): e.g. {1/2, 1/3} from 2^a * 3^b is the grid
[0,a] x [0,b], ordered by divisibility.
"""

from __future__ import annotations

from collections import deque
from itertools import product

from .core import factorize, run, to_int


def _applies(state, den_f):
    return all(state.get(p, 0) >= e for p, e in den_f.items())


def _apply(state, fr):
    ns = dict(state)
    for p, e in fr.den_f.items():
        v = ns[p] - e
        if v:
            ns[p] = v
        else:
            del ns[p]
    for p, e in fr.num_f.items():
        ns[p] = ns.get(p, 0) + e
    return ns


def _key(s):
    return tuple(sorted(s.items()))


def reachable(prog, start, max_states=20000):
    """BFS the nondeterministic reachability graph from ``start``.

    Returns dict with ``seen`` (key -> state), ``graph`` (key -> list of
    (fraction_index, next_key)), and ``truncated`` (hit max_states).
    """
    s0 = factorize(start) if isinstance(start, int) else dict(start)
    seen = {_key(s0): s0}
    graph = {}
    q = deque([s0])
    truncated = False
    while q:
        s = q.popleft()
        k = _key(s)
        succ = []
        for i, fr in enumerate(prog):
            if _applies(s, fr.den_f):
                ns = _apply(s, fr)
                nk = _key(ns)
                succ.append((i, nk))
                if nk not in seen:
                    if len(seen) >= max_states:
                        truncated = True
                        continue
                    seen[nk] = ns
                    q.append(ns)
        graph[k] = succ
    return {"seen": seen, "graph": graph, "truncated": truncated}


def independent(prog, state, i, j):
    """Do moves i and j commute at ``state`` (each still applies after the other)?

    The resulting states coincide automatically (vector additions commute); the
    only question is whether firing one starves the other of a needed factor.
    """
    si = _apply(state, prog[i])
    sj = _apply(state, prog[j])
    return _applies(si, prog[j].den_f) and _applies(sj, prog[i].den_f)


def analyze(prog, r):
    seen, graph = r["seen"], r["graph"]
    terminals = [k for k, v in graph.items() if not v]
    conc = conf = 0
    for k, v in graph.items():
        outs = sorted({nk for _, nk in v})
        if len(outs) < 2:
            continue
        idxs = [i for i, _ in v]
        pairs = [(a, b) for a in idxs for b in idxs if a < b]
        if all(independent(prog, seen[k], a, b) for a, b in pairs):
            conc += 1
        else:
            conf += 1
    return {
        "states": len(seen),
        "edges": sum(len(v) for v in graph.values()),
        "terminals": terminals,
        "concurrency_branches": conc,
        "conflict_branches": conf,
        "confluent": len(terminals) == 1 and not r["truncated"],
        "truncated": r["truncated"],
    }


def as_int(key):
    n = 1
    for p, e in key:
        n *= p**e
    return n


# --- confluence and normal forms -----------------------------------------

def confluent(prog) -> bool:
    """Structurally confluent? Sufficient test: denominators pairwise disjoint.

    If no two fractions share a denominator prime, firing one can never starve
    another of a needed factor, so every branch is a concurrency diamond (local
    confluence). Combined with termination this means every state has a UNIQUE
    normal form, independent of evaluation order — so you can compute it by any
    single reduction, no graph search needed.
    """
    dens = [set(f.den_f) for f in prog]
    return all(not (dens[a] & dens[b])
               for a in range(len(dens)) for b in range(a + 1, len(dens)))


def normal_form(prog, start, max_steps=1_000_000):
    """Reduce ``start`` to a halting state by one (deterministic) reduction.

    For a ``confluent`` program this is THE unique normal form, order-independent.
    For pure-decrement moves it is simply ``start`` with the removed primes
    projected away. Returns ``(n, halted)``.
    """
    state, _steps, status = run(prog, start, max_steps=max_steps)
    return to_int(state), status == "halt"


# --- whole-region ("all states at once") evolution -----------------------

def region_states(bounds):
    """Every state with exponent of ``p`` in ``[0, bounds[p]]`` for each prime p."""
    primes = sorted(bounds)
    for exps in product(*[range(bounds[p] + 1) for p in primes]):
        yield {p: e for p, e in zip(primes, exps) if e}


def region_graph(prog, bounds):
    """Transition graph over a bounded box of *all* states.

    Returns ``nodes``, within-box ``edges`` (key -> [key]), ``exits`` (key ->
    number of moves that leave the box), and ``sinks`` (keys where no fraction
    applies — true normal forms).
    """
    inbox = {_key(s): s for s in region_states(bounds)}
    edges = {k: [] for k in inbox}
    exits, sinks = {}, []
    for k, s in inbox.items():
        applicable = 0
        for fr in prog:
            if _applies(s, fr.den_f):
                applicable += 1
                nk = _key(_apply(s, fr))
                if nk in inbox:
                    edges[k].append(nk)
                else:
                    exits[k] = exits.get(k, 0) + 1
        if applicable == 0:
            sinks.append(k)
    return {"nodes": list(inbox), "edges": edges, "exits": exits, "sinks": sinks}


def sccs(edges):
    """Strongly connected components (iterative Kosaraju)."""
    visited, order = set(), []
    for root in edges:
        if root in visited:
            continue
        stack = [(root, iter(edges[root]))]
        visited.add(root)
        while stack:
            node, it = stack[-1]
            for nxt in it:
                if nxt not in visited:
                    visited.add(nxt)
                    stack.append((nxt, iter(edges.get(nxt, ()))))
                    break
            else:
                order.append(node)
                stack.pop()
    rev = {k: [] for k in edges}
    for k, vs in edges.items():
        for v in vs:
            rev.setdefault(v, []).append(k)
    comp, comps = {}, []
    for node in reversed(order):
        if node in comp:
            continue
        group, stack = [], [node]
        comp[node] = len(comps)
        while stack:
            u = stack.pop()
            group.append(u)
            for w in rev.get(u, ()):
                if w not in comp:
                    comp[w] = len(comps)
                    stack.append(w)
        comps.append(group)
    return comps


def analyze_region(prog, bounds):
    """Global flow of a finite box: normal-form sinks and cyclic components."""
    g = region_graph(prog, bounds)
    cyclic = []
    for c in sccs(g["edges"]):
        if len(c) > 1 or (c and c[0] in g["edges"].get(c[0], ())):
            cyclic.append(sorted(as_int(k) for k in c))
    return {
        "states": len(g["nodes"]),
        "sinks": sorted(as_int(k) for k in g["sinks"]),
        "cyclic_components": sorted(cyclic),
        "boundary_states": len(g["exits"]),
    }


def render_grid(seen, p, q):
    """ASCII grid of a reachable set over exactly two primes p, q (rows = q)."""
    pts = {(s.get(p, 0), s.get(q, 0)) for s in seen.values()}
    if any(set(s) - {p, q} for s in seen.values()):
        return "(states use primes beyond the two given)"
    mp = max(i for i, _ in pts)
    mq = max(j for _, j in pts)
    lines = []
    for j in range(mq, -1, -1):
        lines.append("".join("#" if (i, j) in pts else "." for i in range(mp + 1)))
    return "\n".join(lines)
