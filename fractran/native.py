"""Python binding to the native C++/GMP core (``native/fractran_core``).

Keeps the toolchain (assembler, decompiler, visualizer, accelerator) in Python
and shells out to the native binary for the hot stepping loop. Two modes:
``vector`` (int64 exponents — fast) and ``canonical`` (a real GMP integer —
the faithful, unbounded reference oracle).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .core import Fraction, factorize, fraction as _mk_fraction

_HERE = Path(__file__).resolve().parent
_NATIVE_DIR = _HERE.parent / "native"
_BIN = _NATIVE_DIR / "fractran_core"


def ensure_built() -> Path:
    """Return the path to the native binary, building it on first use."""
    if _BIN.exists():
        return _BIN
    make = shutil.which("make")
    if make:
        subprocess.run([make, "-C", str(_NATIVE_DIR)], check=True)
    if not _BIN.exists():
        raise RuntimeError(f"native core not built; run `make -C {_NATIVE_DIR}`")
    return _BIN


def _factored(fac: dict) -> str:
    return "*".join(f"{p}^{e}" for p, e in fac.items()) or "1"


def _prog_text(program) -> str:
    """Serialize a program in factored form so factors beyond 2^64 stay exact."""
    lines = []
    for f in program:
        if not isinstance(f, Fraction):
            a, b = f
            f = _mk_fraction(int(a), int(b))
        lines.append(f"{_factored(f.num_f)}/{_factored(f.den_f)}")
    return "\n".join(lines) + "\n"


def _startspec(start) -> str:
    d = factorize(start) if isinstance(start, int) else start
    return ",".join(f"{p}:{e}" for p, e in d.items() if e) or "1:0"


def run(program, start, mode="vector", *, max_steps=None, watch_pow2=None, read=None, timeout=None):
    """Run ``program`` from ``start`` in the native core; return a result dict.

    Keys: steps, status, elapsed, rate. Plus ``emitted`` (list of ints) when
    ``watch_pow2`` is set, ``read`` (prime -> exponent) when ``read`` is a list
    of primes, and ``result_digits`` (base-10 length of n) in canonical mode.
    """
    binp = ensure_built()
    args = [str(binp), mode, _startspec(start)]
    if max_steps:
        args += ["--max", str(max_steps)]
    if watch_pow2:
        args += ["--watch-pow2", str(watch_pow2)]
    if read:
        args += ["--read", ",".join(str(p) for p in read)]

    out = subprocess.run(args, input=_prog_text(program), capture_output=True, text=True, timeout=timeout)
    if out.returncode != 0:
        raise RuntimeError(f"native core failed ({out.returncode}): {out.stderr.strip()}")

    raw = {}
    for line in out.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            raw[k] = v

    res = {
        "steps": int(raw.get("steps", 0)),
        "status": raw.get("status"),
        "elapsed": float(raw.get("elapsed", 0.0)),
        "rate": float(raw.get("rate", 0.0)),
    }
    if "emitted" in raw:
        res["emitted"] = [int(x) for x in raw["emitted"].split()] if raw["emitted"] else []
    if "result_digits" in raw:
        res["result_digits"] = int(raw["result_digits"])
    reads = {int(k[5:-1]): int(v) for k, v in raw.items() if k.startswith("read[")}
    if reads:
        res["read"] = reads
    return res
