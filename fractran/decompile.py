"""Recover structure from a raw fraction list.

Two tools:

  * ``classify`` runs the machine and watches the trajectory. A prime whose
    exponent ever exceeds 1 is a register/scratch (it *counts*); the primes that
    stay in {0,1} and are mutually exclusive across states are the program
    counter (control) primes. This is data-driven and robust for machines that
    keep a one-hot counter; for hand-golfed programs it is a heuristic.

  * ``cfg`` / ``describe`` reconstruct the control-flow graph given the set of
    control primes: each fraction becomes an edge cur -> next annotated with the
    register decrements (denominator) and increments (numerator).
"""

from __future__ import annotations

from .core import factorize, run_iter


def observe(prog, start, max_steps=50_000):
    """Walk the trajectory, returning ``(max_exp, control_ok, primes)``.

    ``max_exp`` maps prime -> largest exponent seen. ``control_ok`` is True if,
    at every visited state, exactly one candidate control prime is present.
    """
    state = factorize(start) if isinstance(start, int) else dict(start)
    max_exp = {p: e for p, e in state.items()}
    states = [frozenset(state)]
    for i, (_, s) in enumerate(run_iter(prog, state)):
        for p, e in s.items():
            if e > max_exp.get(p, 0):
                max_exp[p] = e
        states.append(frozenset(s))
        if i + 1 >= max_steps:
            break
    controls = {p for p, e in max_exp.items() if e == 1}
    control_ok = all(len(st & controls) == 1 for st in states if st)
    return max_exp, controls, control_ok


def classify(prog, start, max_steps=50_000):
    """Split primes into registers vs control primes by simulation."""
    max_exp, controls, control_ok = observe(prog, start, max_steps)
    registers = {p for p in max_exp if p not in controls}
    return {
        "registers": registers,
        "controls": controls,
        "one_hot": control_ok,
        "max_exp": max_exp,
    }


def cfg(prog, control_primes):
    """Build a control-flow graph keyed by control prime.

    Returns ``nodes``: control_prime -> list of edges, each edge a dict with
    ``index`` (fraction index), ``next`` (control prime or None), ``dec`` and
    ``inc`` (register -> amount).
    """
    S = set(control_primes)
    nodes: dict = {}
    for i, fr in enumerate(prog):
        den_states = [p for p in fr.den_f if p in S]
        num_states = [p for p in fr.num_f if p in S]
        cur = den_states[0] if len(den_states) == 1 else None
        nxt = num_states[0] if len(num_states) == 1 else None
        dec = {p: e for p, e in fr.den_f.items() if p not in S}
        inc = {p: e for p, e in fr.num_f.items() if p not in S}
        nodes.setdefault(cur, []).append(
            {"index": i, "next": nxt, "dec": dec, "inc": inc, "fr": fr}
        )
    return nodes


def describe(prog, control_primes, names=None) -> str:
    """Render the recovered CFG as text."""
    names = dict(names or {})

    def nm(p):
        return names.get(p, f"p{p}") if p is not None else "HALT"

    def regs(d):
        return ", ".join(f"{nm(p)}{'' if e == 1 else '^' + str(e)}" for p, e in sorted(d.items()))

    nodes = cfg(prog, control_primes)
    lines = []
    targets = {e["next"] for edges in nodes.values() for e in edges}
    halts = (targets - set(nodes)) - {None}
    for cur in sorted(nodes, key=lambda p: (p is None, p or 0)):
        lines.append(f"state {nm(cur)}:")
        for e in nodes[cur]:
            ops = []
            if e["dec"]:
                ops.append(f"need/dec[{regs(e['dec'])}]")
            if e["inc"]:
                ops.append(f"inc[{regs(e['inc'])}]")
            op = ("  " + "; ".join(ops)) if ops else ""
            lines.append(f"    [{e['index']:>2}] {e['fr']}  -> {nm(e['next'])}{op}")
    for h in sorted(halts):
        lines.append(f"state {nm(h)}:  (halt)")
    return "\n".join(lines)
