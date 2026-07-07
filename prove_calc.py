from fractran.core import program
from fractran.io import io_host, trampoline
from fractran.calc import build_calculator

calc = build_calculator()

# Serialize to bare "num/den" text, then RE-PARSE — nothing survives but fractions.
raw_text = " ".join(f"{f.num}/{f.den}" for f in calc.fractions)
prog = program(raw_text)                       # a plain fraction list
io = calc.io_config()                          # the 7 boundary primes
entry = calc.label_prime[calc.entry]           # start = PC at entry

def compute(commands):
    inputs = []
    for op, a, b in commands:
        inputs += [op, a, b]
    outs = []
    trampoline(prog, {entry: 1}, io_host(**io, inputs=inputs, outputs=outs))
    return outs

print(f"running the bare {len(prog)}-fraction list (re-parsed from text):")
print("  20 + 22   =", compute([(0, 20, 22)]))
print("  9 * 9     =", compute([(1, 9, 9)]))
print("  1000 /% 7 =", compute([(3, 1000, 7)]))
print("  batch     =", compute([(0,3,4),(1,6,7),(2,10,3),(3,17,5)]))
