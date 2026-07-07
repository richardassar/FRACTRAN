"""Order-free evolution: unfold reachability graphs, check confluence and normal
forms, and evolve whole bounded regions of states at once."""

from fractran import reachability as R
from fractran.core import program


def unfold(title, prog, start, grid=None):
    r = R.reachable(prog, start)
    a = R.analyze(prog, r)
    print(f"\n=== {title} ===")
    print(f"  states={a['states']} edges={a['edges']}  "
          f"branches: {a['concurrency_branches']} concurrency / {a['conflict_branches']} conflict")
    nf, halted = R.normal_form(prog, start)
    print(f"  normal forms = {sorted(R.as_int(t) for t in a['terminals'])}  "
          f"confluent(structural)={R.confluent(prog)}  one-reduction NF={nf if halted else 'diverges'}")
    if grid:
        for line in R.render_grid(r["seen"], *grid).splitlines():
            print("    " + line)


print("# UNFOLD from a start state -------------------------------------------")
unfold("{1/2, 1/3} from 2^3*3^2  (distributive lattice / grid)",
       program("1/2 1/3"), 2**3 * 3**2, grid=(2, 3))
unfold("{3/2, 5/2} from 2^2  (resource conflict)",
       program("3/2 5/2"), 2**2)
unfold("{7/3, 5/2} from 2^3*3  (confluent chainer: disjoint denominators)",
       program("7/3 5/2"), 2**3 * 3)

print("\n# REGION: evolve ALL states in a box at once --------------------------")
for title, prog, bounds in [
    ("{1/2, 1/3} over 2^0..3 x 3^0..2  (drains to 1)", program("1/2 1/3"), {2: 3, 3: 2}),
    ("{2/3, 3/2} over 2^0..3 x 3^0..3  (conserves v2+v3 -> anti-diagonal cycles)",
     program("2/3 3/2"), {2: 3, 3: 3}),
]:
    a = R.analyze_region(prog, bounds)
    print(f"\n=== {title} ===")
    print(f"  states={a['states']} sinks(normal forms)={a['sinks']} boundary={a['boundary_states']}")
    print(f"  cyclic components: {a['cyclic_components'] or 'none'}")
