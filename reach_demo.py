"""Order-free evolution: unfold the reachability graph, ignoring priority."""
from fractran.core import program
from fractran import reachability as R

def show(title, prog, start, grid=None):
    r = R.reachable(prog, start)
    a = R.analyze(prog, r)
    print(f"\n=== {title} ===")
    print(f"  states={a['states']} edges={a['edges']} "
          f"branches: {a['concurrency_branches']} concurrency / {a['conflict_branches']} conflict")
    terms = sorted(R.as_int(t) for t in a['terminals'])
    print(f"  terminals (normal forms) = {terms}   confluent={a['confluent']}")
    if grid:
        print(R.render_grid(r['seen'], *grid))

# 1. conflict-free: a distributive lattice (grid). {1/2,1/3} from 2^3*3^2
show("{1/2, 1/3} from 2^3*3^2  (a grid / distributive lattice)",
     program("1/2 1/3"), 2**3 * 3**2, grid=(2, 3))

# 2. conflict: two moves competing for factors of 2 -> genuine bifurcation
show("{3/2, 5/2} from 2^2  (resource conflict -> multiple normal forms)",
     program("3/2 5/2"), 2**2)

# 3. a bigger commuting box
show("{1/2, 1/3, 1/5} from 2^2*3^2*5^1  (product of 3 chains)",
     program("1/2 1/3 1/5"), 2**2 * 3**2 * 5)

# 4. a cycle: nondeterministic set is finite but has no normal form
show("{2/3, 3/2} from 6  (oscillation -> cycles, no terminal)",
     program("2/3 3/2"), 6)
