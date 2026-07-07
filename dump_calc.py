"""Print the calculator's fraction list and save it as a standalone program."""

from fractran.calc import build_calculator

calc = build_calculator()
io = calc.io_config()

print("I/O boundary (the only primes the host touches):")
print(f"  IN  (input value)  = prime {io['in_reg']}      OUT (output value) = prime {io['out_reg']}")
print(f"  read-flag = {io['rf']}   write-flag = {io['wf']}")
print(f"  tokens: delivered = {io['dl']}   eof = {io['ef']}   write-done = {io['wd']}")
print(f"\n{len(calc.fractions)} fractions (the entire calculator):\n")

frs = [f"{f.num}/{f.den}" for f in calc.fractions]
for i in range(0, len(frs), 6):
    print("  " + "  ".join(frs[i:i + 6]))

with open("calc_program.fractran", "w") as fh:
    fh.write("# FRACTRAN calculator — op a b over stdin; op 0=add 1=mul 2=sub 3=divmod\n")
    fh.write("\n".join(frs) + "\n")
print("\nsaved to calc_program.fractran")
