"""Live terminal visualizer for a running FRACTRAN machine.

Renders the state as a set of register bars (one per prime, exponent = length),
highlights the fraction that just fired, and logs emitted events (e.g. the primes
PRIMEGAME passes through). ``watch`` animates in place; ``record`` returns frames
as strings for non-interactive use/testing.
"""

from __future__ import annotations

import os
import sys
import time

from .core import factorize, run_iter

_NOCOLOR = bool(os.environ.get("NO_COLOR"))


def _c(code: str) -> str:
    return "" if _NOCOLOR else code


RESET = _c("\033[0m")
BOLD = _c("\033[1m")
DIM = _c("\033[2m")
BAR = _c("\033[38;5;43m")  # teal-green bars
ACC = _c("\033[38;5;214m")  # amber: the fraction that fired
STATE = _c("\033[38;5;140m")  # muted violet: control/state primes
LABEL = _c("\033[38;5;66m")  # slate: labels

MAXBAR = 34
RULE = "─"


def _bar(exp: int, maxexp: int) -> str:
    if exp <= 0:
        return DIM + "·" + RESET
    n = int(round(exp / maxexp * MAXBAR)) if maxexp else 1
    n = max(1, min(n, MAXBAR))
    return BAR + "█" * n + RESET


def frame(prog, fired, state, primes, names, controls, emitted, width=60) -> str:
    """Render one frame as a multi-line string."""
    names = names or {}
    controls = controls or set()
    rule = DIM + RULE * width + RESET

    fr = prog[fired] if fired is not None else None

    # program strip with the active fraction highlighted
    strip = []
    for i, f in enumerate(prog):
        s = f"{f.num}/{f.den}"
        strip.append(f"{ACC}{BOLD}[{s}]{RESET}" if i == fired else f"{DIM}{s}{RESET}")
    prog_line = " ".join(strip)

    maxexp = max((state.get(p, 0) for p in primes), default=1) or 1
    rows = []
    for p in sorted(primes):
        exp = state.get(p, 0)
        nm = names.get(p, str(p))
        col = STATE if p in controls else LABEL
        tag = f"{col}{nm:>5}{RESET}"
        val = f"{BOLD}{exp}{RESET}" if exp else f"{DIM}0{RESET}"
        rows.append(f"  {tag} {_bar(exp, maxexp)} {val}")

    lines = []
    fired_str = f"{ACC}{fr}{RESET}" if fr else f"{DIM}—{RESET}"
    lines.append(f"{BOLD}fired{RESET} {fired_str}")
    lines.append(f"{DIM}prog{RESET}  {prog_line}")
    lines.append(rule)
    lines.extend(rows)
    lines.append(rule)
    if emitted:
        shown = " ".join(str(e) for e in emitted[-16:])
        lines.append(f"{BOLD}emitted{RESET} {shown}")
    return "\n".join(lines)


def _driver(prog, start, names, controls, stride, max_steps, emit):
    """Yield (fired_index, state, emitted_list) frames to render."""
    state = factorize(start) if isinstance(start, int) else dict(start)
    primes = set(state)
    emitted = []
    yield None, state, primes, emitted  # initial frame
    steps = 0
    for i, s in run_iter(prog, state):
        steps += 1
        primes |= s.keys()
        event = emit(s) if emit else None
        if event is not None:
            emitted.append(event)
        if event is not None or steps % stride == 0:
            yield i, s, primes, emitted
        if steps >= max_steps:
            break
    yield None, state, primes, emitted  # final frame (halt)


def record(prog, start, names=None, *, controls=None, stride=1, max_steps=2000, emit=None):
    """Collect rendered frames as a list of strings (no animation)."""
    frames = []
    for fired, state, primes, emitted in _driver(prog, start, names, controls, stride, max_steps, emit):
        frames.append(frame(prog, fired, state, primes, names, controls, emitted))
    return frames


def watch(prog, start, names=None, *, controls=None, stride=1, delay=0.06, max_steps=1_000_000, emit=None, title=None):
    """Animate a run in place. Ctrl-C to stop."""
    names = names or {}
    controls = controls or set()
    prev = 0
    hide, show_cur = _c("\033[?25l"), _c("\033[?25h")
    sys.stdout.write(hide)
    if title:
        sys.stdout.write(f"{BOLD}{title}{RESET}\n\n")
    try:
        for fired, state, primes, emitted in _driver(prog, start, names, controls, stride, max_steps, emit):
            f = frame(prog, fired, state, primes, names, controls, emitted)
            n = f.count("\n") + 1
            if prev:
                sys.stdout.write(f"\033[{prev}A\033[J")
            sys.stdout.write(f + "\n")
            sys.stdout.flush()
            prev = n
            if delay:
                time.sleep(delay)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(show_cur)
        sys.stdout.flush()


def power_of_two(state):
    """Emit predicate for PRIMEGAME: pure powers of two > 1 -> the exponent."""
    if len(state) == 1 and 2 in state and state[2] > 1:
        return state[2]
    return None
