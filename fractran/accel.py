"""Acceleration: run the register-machine CFG and collapse loops in closed form.

A compiled loop ``while g>0: g--; body`` runs in O(g) fraction-firings, and
nested loops multiply: ``mul`` is O(a*b), ``factorial`` worse. But if a loop's
per-iteration effect is the *same every time*, k iterations collapse to
``state += k * delta`` — one arithmetic step instead of k.

Each loop head is **analyzed once** (cached), by probing two iterations: they
must agree, the guard must fall by exactly one, and every register that steered
control flow during the body (branch guards, inner-loop counters) must be left
unchanged — so the body provably behaves identically every iteration. A head is
then classified:

  * ``const``  — nothing but the guard was read, so the per-iteration delta is a
    fixed vector, cached and applied in O(1) with no re-execution.
  * ``invlin`` — the delta depends on loop-invariant registers (e.g. ``dst+=b``
    in ``mul``); it is re-measured with a single body pass on each entry, but
    that pass applies the *cached* inner summaries, so it stays cheap.

Analyzing bottom-up and applying via cached summaries keeps the whole run
polynomial: ``mul`` collapses to O(1), ``fibonacci``/``factorial`` to O(n)
macro-ops. Loops that don't fit (non-constant effect, e.g. ``f*=n``) are simply
stepped — results are identical to the reference interpreter (see ``bench.py``).
"""

from __future__ import annotations

from .core import factorize
from .decompile import cfg

_BUDGET = 2_000_000  # step cap while measuring one loop body; overflow -> don't accelerate


def _sub(a, b):
    keys = set(a) | set(b)
    return {k: a.get(k, 0) - b.get(k, 0) for k in keys if a.get(k, 0) != b.get(k, 0)}


class Accelerator:
    def __init__(self, fractions, control_primes):
        self.nodes = cfg(fractions, control_primes)
        self.controls = set(control_primes)
        self._cache: dict = {}  # head -> False | {"g","kind","delta","exit"}

    # -- one raw Minsky step; records tested register primes into `tested` ----
    def _fire(self, pc, state, tested):
        for e in self.nodes.get(pc, ()):  # edges in priority order
            dec = e["dec"]
            ok = True
            for r, amt in dec.items():
                tested.add(r)
                if state.get(r, 0) < amt:
                    ok = False
                    break
            if ok:
                for r, amt in dec.items():
                    v = state.get(r, 0) - amt
                    if v:
                        state[r] = v
                    else:
                        state.pop(r, None)
                for r, amt in e["inc"].items():
                    state[r] = state.get(r, 0) + amt
                return e["next"]
        return None  # halt

    def _loop_edges(self, pc):
        """If pc is a loop head, return (guard, continue_edge, exit_edge)."""
        edges = self.nodes.get(pc)
        if not edges or len(edges) < 2:
            return None
        cont = exit_e = None
        ci = ei = -1
        for i, e in enumerate(edges):
            d = e["dec"]
            if cont is None and len(d) == 1 and next(iter(d.values())) == 1:
                cont, ci = e, i
            elif exit_e is None and len(d) == 0:
                exit_e, ei = e, i
        if cont is None or exit_e is None or ci > ei:
            return None
        return next(iter(cont["dec"])), cont, exit_e

    def _iterate_once(self, head, state, tested):
        """Run exactly one loop iteration (head -> body -> head) in place.

        Applies cached inner summaries via ``_advance``. Returns True on a clean
        return to head, False on halt / budget overflow.
        """
        nxt = self._fire(head, state, tested)  # takes the continue edge (guard>=1)
        if nxt is None:
            return False
        pc = nxt
        budget = _BUDGET
        while pc != head:
            budget -= 1
            if budget <= 0:
                return False
            pc = self._advance(pc, state, tested)
            if pc is None:
                return False
        return True

    def _analyze(self, head, state):
        """Analyze a loop head once; cache and return its verdict."""
        info = self._loop_edges(head)
        if info is None:
            self._cache[head] = False
            return False
        g, _cont, exit_e = info

        S0 = dict(state)
        t1 = set()
        s1 = dict(S0)
        if not self._iterate_once(head, s1, t1):
            self._cache[head] = False
            return False
        s2 = dict(s1)
        if not self._iterate_once(head, s2, set()):
            self._cache[head] = False
            return False

        d1, d2 = _sub(s1, S0), _sub(s2, s1)
        if d1 != d2 or d1.get(g, 0) != -1:
            self._cache[head] = False
            return False
        for r in t1:  # every control-relevant register must be loop-invariant
            if r != g and d1.get(r, 0) != 0:
                self._cache[head] = False
                return False

        kind = "const" if t1 <= {g} else "invlin"
        verdict = {"g": g, "kind": kind, "delta": d1 if kind == "const" else None,
                   "exit": exit_e["next"]}
        self._cache[head] = verdict
        return verdict

    @staticmethod
    def _apply(state, k, delta):
        """state += k*delta in place; return False on underflow (caller falls back)."""
        for r, dv in delta.items():
            v = state.get(r, 0) + k * dv
            if v < 0:
                return False
            if v:
                state[r] = v
            else:
                state.pop(r, None)
        return True

    def _advance(self, pc, state, tested):
        """One macro-action at pc: accelerate a loop or take one raw step.

        Returns the next pc, or None on halt.
        """
        v = self._cache.get(pc, None)
        if v is None:  # not yet classified
            info = self._loop_edges(pc)
            if info is None:
                self._cache[pc] = False
                v = False
            elif state.get(info[0], 0) < 2:
                return self._fire(pc, state, tested)  # too small to probe; step
            else:
                v = self._analyze(pc, state)

        if v is False:
            return self._fire(pc, state, tested)

        g = v["g"]
        gv = state.get(g, 0)
        if gv < 1:
            return self._fire(pc, state, tested)  # guard empty -> exit edge
        tested.add(g)

        if v["kind"] == "const":
            delta = v["delta"]
        else:  # invlin: re-measure this entry's delta (inner loops apply cached)
            probe = dict(state)
            if not self._iterate_once(pc, probe, set()):
                return self._fire(pc, state, tested)
            delta = _sub(probe, state)
            if delta.get(g, 0) != -1:
                return self._fire(pc, state, tested)

        snapshot = dict(state)
        if not self._apply(state, gv, delta):
            state.clear()
            state.update(snapshot)
            return self._fire(pc, state, tested)  # would underflow: step instead
        return pc  # guard is now 0; the next visit takes the exit edge

    def run(self, start, entry=None, max_ops=100_000_000):
        """Run to halt. Returns (register_state, op_count)."""
        st = factorize(start) if isinstance(start, int) else dict(start)
        ctrl = [p for p in st if p in self.controls]
        if entry is None:
            if len(ctrl) != 1:
                raise ValueError("cannot infer entry: need exactly one control prime present")
            entry = ctrl[0]
        pc = entry
        state = {p: e for p, e in st.items() if p not in self.controls}
        ops = 0
        while True:
            nxt = self._advance(pc, state, set())
            if nxt is None:
                return state, ops
            pc = nxt
            ops += 1
            if ops > max_ops:
                raise RuntimeError("operation budget exceeded")
