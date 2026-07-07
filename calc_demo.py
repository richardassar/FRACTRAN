"""Self-check for the FRACTRAN calculator: run a battery of commands through the
compiled fraction list and compare to Python arithmetic."""

from fractran.calc import build_calculator
from fractran.io import io_host, trampoline

calc = build_calculator()
print(f"calculator compiled to {len(calc.fractions)} fractions")


def run(commands):
    inputs = []
    for op, a, b in commands:
        inputs += [op, a, b]
    outputs = []
    host = io_host(**calc.io_config(), inputs=inputs, outputs=outputs)
    state = {calc.label_prime[calc.entry]: 1}
    trampoline(calc.fractions, state, host)
    return outputs


def expected(commands):
    out = []
    for op, a, b in commands:
        if op == 0:
            out.append(a + b)
        elif op == 1:
            out.append(a * b)
        elif op == 2:
            out.append(max(a - b, 0))
        elif op == 3:
            out += [a // b, a % b]
    return out


cmds = [
    (0, 3, 4), (0, 100, 250),
    (1, 6, 7), (1, 12, 12), (1, 0, 9),
    (2, 10, 3), (2, 3, 10), (2, 50, 50),
    (3, 17, 5), (3, 100, 7), (3, 42, 6),
]
got, want = run(cmds), expected(cmds)
print(f"  {'op a b':>12}   result")
i = 0
for op, a, b in cmds:
    n = 2 if op == 3 else 1
    r = got[i:i + n]
    label = {0: "+", 1: "*", 2: "-", 3: "divmod"}[op]
    print(f"  {a:>4} {label:^3} {b:<3} = {' '.join(map(str, r))}")
    i += n
assert got == want, f"MISMATCH: {got} != {want}"
print("\nAll results match Python arithmetic. It's a calculator, in fractions.")
