"""Draw a FRACTRAN reachability graph to a PNG.

    python3 plot_reach.py "1/2 1/3" 72 graph.png       # a connected grid/lattice
    python3 plot_reach.py "3/2 5/2" 4 conflict.png     # a branching (conflict) graph

Nodes are states (labelled by the integer); green = start, red = halting normal
form. Two-prime programs are laid out on the exponent lattice (v_p, v_q). Open the
resulting PNG in any image viewer.
"""

import sys

from fractran.core import program
from fractran.plot import plot_reachability


def main(argv):
    if len(argv) < 3 or argv[0] in ("-h", "--help"):
        print(__doc__)
        return
    prog = program(argv[0])
    start = int(argv[1])
    out = argv[2]
    path, n, sinks = plot_reachability(prog, start, out, title=None)
    print(f"wrote {path}  ({n} states, normal forms {sinks})")


if __name__ == "__main__":
    main(sys.argv[1:])
