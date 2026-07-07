"""Bootstrap: a FRACTRAN self-interpreter compiled from our verified toolchain,
reading its object program off the input stream. Checked against the reference
interpreter — correct by construction, not transcribed."""

from fractran import bootstrap as BT
from fractran import build as B
from fractran.core import program, run, to_int


def ref(fracs, n0):
    txt = " ".join(f"{a}/{b}" for a, b in fracs)
    return to_int(run(program(txt), n0, max_steps=5_000_000)[0])


# The hard primitive underneath: exact divmod on a unary magnitude.
dm = B.compile_program(B.divmod_("q", "r", "n", "b", "cd", "rr", "t"), pin={"n": 2, "b": 3})
assert all(
    (run(dm.fractions, dm.start(n=n, b=b))[0].get(dm.reg_prime["q"], 0) == n // b
     and run(dm.fractions, dm.start(n=n, b=b))[0].get(dm.reg_prime["r"], 0) == n % b)
    for n in range(12) for b in range(1, 6)
)
print(f"divmod macro: {len(dm.fractions)} fractions, verified")

# Self-interpreters for k = 1, 2, 3 object fractions.
suites = {
    1: [([(3, 2)], n) for n in (2, 3, 6, 8, 9)],
    2: [([(3, 2), (5, 3)], n) for n in (6, 12, 4)] + [([(1, 2), (1, 3)], n) for n in (12, 36, 8)],
    3: [([(1, 2), (1, 3), (1, 5)], n) for n in (30, 60, 120)],
}
for k, cases in suites.items():
    interp = BT.make_interpreter(k)
    print(f"\nself-interpreter for {k}-fraction programs: {len(interp.fractions)} fractions")
    for fracs, n0 in cases:
        got, want = BT.interpret(interp, fracs, n0), ref(fracs, n0)
        assert got == want, f"MISMATCH {fracs} on {n0}: {got} != {want}"
        show = " ".join(f"{a}/{b}" for a, b in fracs)
        print(f"  [ok] interpret ({show}) on {n0} = {got}")

print("\nA FRACTRAN program, compiled from our toolchain, correctly interprets FRACTRAN.")
