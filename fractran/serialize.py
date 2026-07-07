"""A compact binary format for FRACTRAN programs, and its inverse.

The bases carry no information (primes are relabelable), so a program is stored
as exponent vectors over dense prime *indices*: per fraction, the denominator
`{idx: exp}` (the guard) and the delta `{idx: num-den}` (the state change).
Indices and exponents are LEB128 varints; deltas are zig-zagged. If the program
uses exactly the first P primes (the common case for compiled programs), no prime
table is stored at all — index i *is* the i-th prime.

Layout:
    "FR30" | version | P | F | consecutive?          (varints; 1 flag byte)
    [ P prime varints, only if not consecutive ]
    per fraction: nden | (idx,exp)*nden | ndelta | (idx, zigzag(delta))*ndelta
"""

from __future__ import annotations

import gzip

from .core import Fraction

MAGIC = b"FR30"


def _uv(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def _rv(data, i):
    n = shift = 0
    while True:
        b = data[i]
        i += 1
        n |= (b & 0x7F) << shift
        if not (b & 0x80):
            return n, i
        shift += 7


def _zz(s: int) -> int:
    return 2 * s if s >= 0 else -2 * s - 1


def _unzz(u: int) -> int:
    return u >> 1 if not (u & 1) else -((u + 1) >> 1)


def first_primes(count: int):
    primes = []
    c = 2
    while len(primes) < count:
        if all(c % p for p in primes if p * p <= c):
            primes.append(c)
        c += 1
    return primes


def _delta(f: Fraction):
    d = {}
    for p, e in f.den_f.items():
        d[p] = d.get(p, 0) - e
    for p, e in f.num_f.items():
        d[p] = d.get(p, 0) + e
    return {p: v for p, v in d.items() if v}


def to_bytes(fractions) -> bytes:
    primes = sorted({p for f in fractions for p in set(f.num_f) | set(f.den_f)})
    idx = {p: i for i, p in enumerate(primes)}
    consecutive = primes == first_primes(len(primes))

    out = bytearray(MAGIC)
    out += _uv(1)
    out += _uv(len(primes))
    out += _uv(len(fractions))
    out.append(1 if consecutive else 0)
    if not consecutive:
        for p in primes:
            out += _uv(p)

    for f in fractions:
        den = sorted(f.den_f.items())
        delta = sorted(_delta(f).items())
        out += _uv(len(den))
        for p, e in den:
            out += _uv(idx[p])
            out += _uv(e)
        out += _uv(len(delta))
        for p, d in delta:
            out += _uv(idx[p])
            out += _uv(_zz(d))
    return bytes(out)


def from_bytes(data) -> list:
    assert data[:4] == MAGIC, "bad magic"
    i = 4
    _ver, i = _rv(data, i)
    P, i = _rv(data, i)
    F, i = _rv(data, i)
    consecutive = data[i]
    i += 1
    if consecutive:
        primes = first_primes(P)
    else:
        primes = []
        for _ in range(P):
            p, i = _rv(data, i)
            primes.append(p)

    fractions = []
    for _ in range(F):
        nden, i = _rv(data, i)
        den_f = {}
        for _ in range(nden):
            ix, i = _rv(data, i)
            e, i = _rv(data, i)
            den_f[primes[ix]] = e
        ndelta, i = _rv(data, i)
        num_f = dict(den_f)
        for _ in range(ndelta):
            ix, i = _rv(data, i)
            z, i = _rv(data, i)
            p = primes[ix]
            num_f[p] = num_f.get(p, 0) + _unzz(z)
        num_f = {p: e for p, e in num_f.items() if e}
        num = den = 1
        for p, e in num_f.items():
            num *= p**e
        for p, e in den_f.items():
            den *= p**e
        fractions.append(Fraction(num, den, num_f, den_f))
    return fractions


MAGIC_C = b"FR3C"


def to_bytes_columnar(fractions) -> bytes:
    """Compression-oriented layout: six separate streams (den-counts,
    delta-counts, den-index-gaps, den-exps, delta-index-gaps, delta-values).

    Grouping like values lets a general compressor exploit the register-machine
    regularity: the exponent stream is almost all 1s, and gap-coded indices are
    small and repetitive.
    """
    primes = sorted({p for f in fractions for p in set(f.num_f) | set(f.den_f)})
    idx = {p: i for i, p in enumerate(primes)}
    consecutive = primes == first_primes(len(primes))

    ndens, ndels = bytearray(), bytearray()
    di, de, ki, kv = bytearray(), bytearray(), bytearray(), bytearray()
    for f in fractions:
        den = sorted(f.den_f.items())      # by prime == by index
        delta = sorted(_delta(f).items())
        ndens += _uv(len(den))
        ndels += _uv(len(delta))
        prev = 0
        for p, e in den:
            di += _uv(idx[p] - prev)
            prev = idx[p]
            de += _uv(e)
        prev = 0
        for p, d in delta:
            ki += _uv(idx[p] - prev)
            prev = idx[p]
            kv += _uv(_zz(d))

    head = bytearray(MAGIC_C)
    head += _uv(1) + _uv(len(primes)) + _uv(len(fractions))
    head.append(1 if consecutive else 0)
    if not consecutive:
        for p in primes:
            head += _uv(p)
    body = bytearray()
    for s in (ndens, ndels, di, de, ki, kv):
        body += _uv(len(s)) + s
    return bytes(head + body)


def from_bytes_columnar(data) -> list:
    assert data[:4] == MAGIC_C, "bad magic"
    i = 4
    _ver, i = _rv(data, i)
    P, i = _rv(data, i)
    F, i = _rv(data, i)
    consecutive = data[i]
    i += 1
    primes = first_primes(P) if consecutive else None
    if not consecutive:
        primes = []
        for _ in range(P):
            p, i = _rv(data, i)
            primes.append(p)
    streams = []
    for _ in range(6):
        ln, i = _rv(data, i)
        streams.append((data[i:i + ln], 0))
        i += ln
    cur = [list(s) for s, _ in streams]
    pos = [0, 0, 0, 0, 0, 0]

    def take(k):
        v, pos[k] = _rv(streams[k][0], pos[k])
        return v

    fractions = []
    for _ in range(F):
        nden = take(0)
        ndel = take(1)
        den_f, prev = {}, 0
        for _ in range(nden):
            prev += take(2)
            e = take(3)
            den_f[primes[prev]] = e
        num_f, prev = dict(den_f), 0
        for _ in range(ndel):
            prev += take(4)
            d = _unzz(take(5))
            num_f[primes[prev]] = num_f.get(primes[prev], 0) + d
        num_f = {p: e for p, e in num_f.items() if e}
        num = den = 1
        for p, e in num_f.items():
            num *= p**e
        for p, e in den_f.items():
            den *= p**e
        fractions.append(Fraction(num, den, num_f, den_f))
    return fractions


def sizes(fractions) -> dict:
    """Compare storage: decimal text vs this binary, each raw and gzipped."""
    text = " ".join(f"{f.num}/{f.den}" for f in fractions).encode()
    binary = to_bytes(fractions)
    return {
        "fractions": len(fractions),
        "text": len(text),
        "text_gz": len(gzip.compress(text, 9)),
        "binary": len(binary),
        "binary_gz": len(gzip.compress(binary, 9)),
    }
