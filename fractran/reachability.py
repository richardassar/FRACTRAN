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

from .core import factorize


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
