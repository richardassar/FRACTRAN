"""Compile interactive, streaming FRACTRAN programs and run them via the host
trampoline. These use read/write, which compile to halt-and-resume waits."""

from fractran import build as B
from fractran.io import io_host, trampoline


def run_io(compiled, inputs):
    outputs = []
    host = io_host(**compiled.io_config(), inputs=inputs, outputs=outputs)
    state = {compiled.label_prime[compiled.entry]: 1}
    trampoline(compiled.fractions, state, host)
    return outputs


# 1. echo-doubler: for each input x, emit 2x; stop at EOF.
doubler = B.compile_program(
    B.read_until_eof("x", B.seq(
        B.zero("y"),
        B.add("y", "x", "t"),
        B.add("y", "x", "t"),   # y = 2x
        B.write("y"),
    ))
)

# 2. running sum: emit the cumulative total after each input (state persists).
runsum = B.compile_program(
    B.read_until_eof("x", B.seq(
        B.add("sum", "x", "t"),  # sum += x
        B.write("sum"),
    ))
)

print(f"doubler compiled to {len(doubler.fractions)} fractions; "
      f"runsum to {len(runsum.fractions)} fractions")

cases = [
    ("doubler", doubler, [3, 0, 5, 7], [6, 0, 10, 14]),
    ("runsum ", runsum, [3, 1, 4, 1, 10], [3, 4, 8, 9, 19]),
]
for name, prog, inp, want in cases:
    got = run_io(prog, inp)
    ok = got == want
    print(f"  [{'ok' if ok else 'FAIL'}] {name}  {inp} -> {got}" + ("" if ok else f"  (want {want})"))
    assert ok

print("\nCompiled streaming I/O works: read/write lower to trampoline waits.")
