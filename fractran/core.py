"""Core FRACTRAN interpreter.

The state of a FRACTRAN machine is a positive integer ``n``. A program is an
ordered list of positive fractions. One step multiplies ``n`` by the first
fraction ``a/b`` for which ``n*a/b`` is an integer (i.e. ``b | n``); the machine
halts when no fraction applies.

Rather than carry the (astronomically large) integer around, this interpreter
works on the exponent vector of ``n``'s prime factorization: ``n = prod p^e``.
In that view each prime is a register holding ``e``, divisibility ``b | n`` is
componentwise domination of exponent vectors, and applying ``a/b`` is a guarded
vector subtract-then-add. No big-integer multiplication ever happens.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# A machine state: prime -> exponent. Zero exponents are omitted (sparse).
State = dict


def factorize(n: int) -> State:
    """Prime factorization of ``n`` as an exponent vector, by trial division.

    Used only on small human-written start integers; the running state is never
    factored because it is maintained directly as a vector.
    """
    if n <= 0:
        raise ValueError("FRACTRAN state must be a positive integer")
    f: State = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            f[d] = f.get(d, 0) + 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        f[n] = f.get(n, 0) + 1
    return f


def to_int(state: State) -> int:
    """Reassemble the integer from an exponent vector (small states only)."""
    n = 1
    for p, e in state.items():
        n *= p**e
    return n


@dataclass(frozen=True)
class Fraction:
    """A single FRACTRAN fraction with its numerator/denominator factored."""

    num: int
    den: int
    num_f: State = field(compare=False)
    den_f: State = field(compare=False)

    def __str__(self) -> str:
        return f"{self.num}/{self.den}"


def fraction(num: int, den: int) -> Fraction:
    return Fraction(num, den, factorize(num), factorize(den))


def program(spec) -> list:
    """Build a program (list of Fraction) from flexible input.

    Accepts a string like ``"17/91 78/85 ..."``, or an iterable of ``(num, den)``
    pairs, ``"a/b"`` strings, or Fraction objects.
    """
    if isinstance(spec, str):
        spec = spec.replace(",", " ").split()
    out = []
    for item in spec:
        if isinstance(item, Fraction):
            out.append(item)
        elif isinstance(item, str):
            a, b = item.split("/")
            out.append(fraction(int(a), int(b)))
        else:
            a, b = item
            out.append(fraction(int(a), int(b)))
    return out


def _applies(state: State, den_f: State) -> bool:
    for p, e in den_f.items():
        if state.get(p, 0) < e:
            return False
    return True


def step(prog: list, state: State):
    """Apply the first applicable fraction to ``state`` in place.

    Returns the index of the fired fraction, or ``None`` if the machine halts.
    """
    for i, fr in enumerate(prog):
        if _applies(state, fr.den_f):
            for p, e in fr.den_f.items():
                v = state[p] - e
                if v:
                    state[p] = v
                else:
                    del state[p]
            for p, e in fr.num_f.items():
                state[p] = state.get(p, 0) + e
            return i
    return None


def run_iter(prog: list, state: State):
    """Yield ``(fired_index, state)`` after each step until halt.

    ``state`` is the live, mutated dict — do not hold references across steps.
    Iteration ends (StopIteration) when the machine halts.
    """
    while True:
        i = step(prog, state)
        if i is None:
            return
        yield i, state


def run(prog: list, start, max_steps: int | None = None):
    """Run to halt (or ``max_steps``). Returns ``(state, steps, status)``.

    ``start`` may be an integer (factored once) or an exponent-vector dict.
    ``status`` is ``"halt"`` or ``"maxsteps"``.
    """
    state = factorize(start) if isinstance(start, int) else dict(start)
    steps = 0
    for _ in run_iter(prog, state):
        steps += 1
        if max_steps is not None and steps >= max_steps:
            return state, steps, "maxsteps"
    return state, steps, "halt"


def render(state: State, names: dict | None = None, hide_states=None) -> str:
    """Human-readable view of a state as ``name^exp * ...`` sorted by prime.

    ``names`` maps prime -> label (e.g. register/state names). Primes without a
    name show as ``p<prime>``. ``hide_states`` optionally suppresses a set of
    control primes to declutter the register view.
    """
    names = names or {}
    hide = hide_states or set()
    parts = []
    for p in sorted(state):
        if p in hide:
            continue
        label = names.get(p, f"p{p}")
        e = state[p]
        parts.append(label if e == 1 else f"{label}^{e}")
    return " * ".join(parts) if parts else "1"
