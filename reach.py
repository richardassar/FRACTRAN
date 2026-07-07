"""Explore FRACTRAN's order-free (nondeterministic) evolution from the terminal.

Two modes.

  UNFOLD a start state -- fire ANY applicable fraction (ignore priority), build
  the reachability graph, and report its structure: branch types (concurrency
  diamonds vs conflict forks), normal forms, and whether it is confluent.

      python3 reach.py "1/2 1/3" 36        # a grid / distributive lattice
      python3 reach.py "3/2 5/2" 4         # a resource conflict -> 3 normal forms

  REGION -- evolve a whole bounded box of *all* states at once (the "all states"
  view), reporting sinks (normal forms) and cyclic components (each a conserved
  quantity / Petri-net place-invariant orbit).

      python3 reach.py "2/3 3/2" --region 2:3,3:3

Options:  --max N   cap on reachable states explored (default 20000).
"""

import sys

from fractran import reachability as R
from fractran.core import program


def parse_region(spec):
    bounds = {}
    for part in spec.split(","):
        p, e = part.split(":")
        bounds[int(p)] = int(e)
    return bounds


def unfold(prog, start, maxs):
    r = R.reachable(prog, start, max_states=maxs)
    a = R.analyze(prog, r)
    print(f"start = {start}")
    print(f"  reachable states : {a['states']}" + ("  (truncated)" if a["truncated"] else ""))
    print(f"  edges            : {a['edges']}")
    print(f"  branches         : {a['concurrency_branches']} concurrency (diamonds)"
          f" / {a['conflict_branches']} conflict (true forks)")
    print(f"  normal forms     : {sorted(R.as_int(t) for t in a['terminals'])}")
    print(f"  confluent (structural): {R.confluent(prog)}"
          f"   single normal form: {len(a['terminals']) == 1}")
    primes = sorted({p for s in r["seen"].values() for p in s})
    if len(primes) == 2:
        print(f"\n  reachable set (grid over primes {primes[0]},{primes[1]}; '#'=reachable):")
        for line in R.render_grid(r["seen"], *primes).splitlines():
            print("    " + line)


def region(prog, bounds, maxs):
    a = R.analyze_region(prog, bounds)
    box = ", ".join(f"{p}^0..{e}" for p, e in sorted(bounds.items()))
    print(f"box = {{{box}}}   ({a['states']} states)")
    print(f"  sinks (normal forms)         : {a['sinks']}")
    print(f"  boundary states (leave box)  : {a['boundary_states']}")
    if a["cyclic_components"]:
        print(f"  cyclic components (conserved-quantity orbits): {len(a['cyclic_components'])}")
        for c in a["cyclic_components"]:
            print(f"      cycle of {len(c):>2}: {c}")
    else:
        print("  cyclic components            : none (acyclic)")


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return
    prog = program(argv[0])
    rest = argv[1:]
    maxs = 20000
    if "--max" in rest:
        i = rest.index("--max")
        maxs = int(rest[i + 1])
        del rest[i:i + 2]
    if "--region" in rest:
        i = rest.index("--region")
        region(prog, parse_region(rest[i + 1]), maxs)
    elif rest:
        unfold(prog, int(rest[0]), maxs)
    else:
        print("give a start integer, or --region p:e,p:e", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
