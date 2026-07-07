"""Run FRACTRAN I/O demos from the terminal.

    python3 demos.py pyramid 6
    python3 demos.py bars            # then type numbers, Ctrl-D to end
    python3 demos.py march 30        # animation: a '*' walks across
    python3 demos.py collatz 27      # the Collatz trajectory of 27
    python3 demos.py gcd 1071 462

    python3 demos.py <name> --show   # print the program's fraction list
    python3 demos.py list            # list demos

Everything is computed by the fraction list; the host only ferries numbers
across the I/O boundary and renders characters (chr) for the graphical ones.
"""

import sys
import time

from fractran.demos import REGISTRY
from fractran.io import io_host, trampoline


def stdin_ints():
    while True:
        line = sys.stdin.readline()
        if not line:
            return
        for tok in line.split():
            yield int(tok)


class CharSink(list):
    """Render each emitted number as a character; code 12 = clear a frame."""

    def __init__(self, delay=0.0):
        super().__init__()
        self.delay = delay

    def append(self, code):
        if code == 12:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()
            if self.delay:
                time.sleep(self.delay)
        else:
            sys.stdout.write(chr(code))
            sys.stdout.flush()


class IntSink(list):
    def append(self, n):
        print(n, flush=True)


def main(argv):
    if not argv or argv[0] in ("list", "-h", "--help"):
        print("demos:", ", ".join(REGISTRY))
        return
    name = argv[0]
    if name not in REGISTRY:
        print(f"unknown demo '{name}'. try: {', '.join(REGISTRY)}", file=sys.stderr)
        return
    builder, kind, nargs = REGISTRY[name]
    rest = argv[1:]
    show = "--show" in rest
    rest = [a for a in rest if a != "--show"]
    delay = 0.08
    if "--delay" in rest:
        i = rest.index("--delay")
        delay = float(rest[i + 1])
        del rest[i:i + 2]

    compiled = builder()
    if show:
        frs = [f"{f.num}/{f.den}" for f in compiled.fractions]
        print(f"# {name}: {len(frs)} fractions")
        for i in range(0, len(frs), 6):
            print("  ".join(frs[i:i + 6]))
        return

    if nargs == "stdin":
        inputs = stdin_ints()
    else:
        if len(rest) < nargs:
            print(f"{name} needs {nargs} argument(s)", file=sys.stderr)
            return
        inputs = [int(x) for x in rest[:nargs]]

    sink = IntSink() if kind == "int" else CharSink(delay if kind == "anim" else 0.0)
    host = io_host(**compiled.io_config(), inputs=inputs, outputs=sink)
    try:
        trampoline(compiled.fractions, {compiled.label_prime[compiled.entry]: 1}, host)
        if kind != "int":
            sys.stdout.write("\n")
    except (BrokenPipeError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main(sys.argv[1:])
