"""End-to-end self-test / demo of the FRACTRAN toolchain."""

from fractran import program, render, run, trampoline, stream_host
from fractran import programs as P
from fractran import decompile


def hdr(t):
    print("\n" + "=" * 68 + f"\n{t}\n" + "=" * 68)


def check(name, got, want):
    ok = got == want
    print(f"  [{'ok' if ok else 'FAIL'}] {name}: {got}" + ("" if ok else f"  (want {want})"))
    assert ok, f"{name}: got {got}, want {want}"


# 1. Raw interpreter -------------------------------------------------------
hdr("1. Raw interpreter")

primes = P.primegame_primes(limit=8)
check("PRIMEGAME first 8 primes", primes, [2, 3, 5, 7, 11, 13, 17, 19])

# ADD: 2^5 * 3^3 -> 3^8
state, steps, status = run(P.ADD, 2**5 * 3**3)
check("ADD 5+3", state.get(3, 0), 8)

# MULTIPLY: 2^3 * 3^4 -> 5^12
state, steps, status = run(P.MULTIPLY, 2**3 * 3**4)
check("MULTIPLY 3*4", state.get(5, 0), 12)
print(f"        (multiply took {steps} steps)")


# 2. Streaming I/O trampoline ---------------------------------------------
hdr("2. Streaming input + output (interactive doubler)")

outputs = []
host = stream_host(inputs=[3, 0, 5, 7], outputs=outputs, **P.DOUBLER_MARKERS)
trampoline(P.DOUBLER, {5: 1}, host)  # start at the READ marker
check("doubler([3,0,5,7])", outputs, [6, 0, 10, 14])


# 3. Minsky assembler + structured front-end ------------------------------
hdr("3. Compiled programs (structured front-end -> IR -> fractions)")

add = P.make_add()
st, *_ = run(add.fractions, add.start(a=4, b=7))
check("compiled add 4+7", add.read(st, "dst"), 11)
print(f"        add compiled to {len(add.fractions)} fractions")

mul = P.make_multiply()
st, *_ = run(mul.fractions, mul.start(a=6, b=7))
check("compiled mul 6*7", mul.read(st, "dst"), 42)
print(f"        mul compiled to {len(mul.fractions)} fractions")

fib = P.make_fibonacci()
got = []
for n in range(11):
    st, *_ = run(fib.fractions, fib.start(n=n))
    got.append(fib.read(st, "a"))
check("compiled fib(0..10)", got, [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55])
print(f"        fib compiled to {len(fib.fractions)} fractions")

fact = P.make_factorial()
got = []
for n in range(7):
    st, *_ = run(fact.fractions, fact.start(n=n))
    got.append(fact.read(st, "f"))
check("compiled factorial(0..6)", got, [1, 1, 2, 6, 24, 120, 720])
print(f"        factorial compiled to {len(fact.fractions)} fractions")


# 4. Decompiler -----------------------------------------------------------
hdr("4. Decompiler")

# (a) round-trip: recover the CFG of a program we compiled (ground truth).
print("\n(a) recovered control-flow graph of compiled ADD:")
print(decompile.describe(add.fractions, set(add.label_prime.values()), add.names))

# (b) blind analysis of Conway's hand-written MULTIPLY by simulation.
print("\n(b) blind classification of Conway's MULTIPLY (2^3*3^4):")
info = decompile.classify(P.MULTIPLY, 2**3 * 3**4)
print(f"    registers/scratch : {sorted(info['registers'])}")
print(f"    control primes     : {sorted(info['controls'])}")
print(f"    one-hot counter?   : {info['one_hot']}")
print("    recovered CFG (using detected control primes):")
print(decompile.describe(P.MULTIPLY, info["controls"]))

print("\nAll checks passed.")
