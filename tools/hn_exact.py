# Adapted from the user research file cnp6/k16.py; arithmetic portion only.
"""K2 = Q(zeta30, sqrt(-11)) exact arithmetic (degree 16) for ROUND B4.

Element representation: (a, b, den) meaning (a + b*sqrt(-11))/den, where
a, b are integer vectors of length 8 over the basis 1..zeta30^7 (reduction
by Phi30) and den is a positive integer. All Python ints (no overflow).

Also: residue maps at the two primes P (sqrt(-11) -> 2) and Pbar
(sqrt(-11) -> 3 = -2) above 5, residue field F25 = F5(s), s^2 = 2,
red(zeta30) = 3+2s; rotation census over the (m,n) norm form.
"""
import cmath
from math import gcd

CORR = [-1, -1, 0, 1, 1, 1, 0, -1]  # zeta^8 in basis 1..zeta^7

def _zpows():
    P = [[1, 0, 0, 0, 0, 0, 0, 0]]
    for _ in range(29):
        v = P[-1]
        w = [0] + v[:]
        c = w[8]
        w = [w[i] + c * CORR[i] for i in range(8)]
        P.append(w)
    return P

ZP = _zpows()
Z0 = [0] * 8
E0 = [1, 0, 0, 0, 0, 0, 0, 0]

def vmul(a, b):
    prod = [0] * 15
    for i in range(8):
        if a[i]:
            for j in range(8):
                prod[i + j] += a[i] * b[j]
    for d in range(14, 7, -1):
        c = prod[d]
        if c:
            prod[d] = 0
            for i in range(8):
                prod[d - 8 + i] += c * CORR[i]
    return prod[:8]

def vadd(a, b): return [x + y for x, y in zip(a, b)]
def vsub(a, b): return [x - y for x, y in zip(a, b)]
def vsc(s, a): return [s * x for x in a]

# conjugation on the zeta-part: zeta^i -> zeta^(30-i)
_CONJ = [ZP[0]] + [ZP[30 - i] for i in range(1, 8)]
def vconj(a):
    out = [0] * 8
    for i in range(8):
        if a[i]:
            out = vadd(out, vsc(a[i], _CONJ[i]))
    return out

_Z = cmath.exp(2j * cmath.pi / 30)
def vemb(a): return sum(a[i] * _Z ** i for i in range(8))

class K2:
    """(a + b*sqrt(-11)) / den, a,b int8-vectors, den > 0."""
    __slots__ = ("a", "b", "den")

    def __init__(self, a, b=None, den=1):
        self.a = list(a)
        self.b = list(b) if b is not None else Z0[:]
        self.den = den
        self._norm()

    def _norm(self):
        if self.den < 0:
            self.den = -self.den
            self.a = vsc(-1, self.a)
            self.b = vsc(-1, self.b)
        g = self.den
        for x in self.a:
            g = gcd(g, x)
        for x in self.b:
            g = gcd(g, x)
        if g > 1:
            self.a = [x // g for x in self.a]
            self.b = [x // g for x in self.b]
            self.den //= g

    def __add__(s, o):
        return K2(vadd(vsc(o.den, s.a), vsc(s.den, o.a)),
                  vadd(vsc(o.den, s.b), vsc(s.den, o.b)), s.den * o.den)

    def __sub__(s, o):
        return K2(vsub(vsc(o.den, s.a), vsc(s.den, o.a)),
                  vsub(vsc(o.den, s.b), vsc(s.den, o.b)), s.den * o.den)

    def __mul__(s, o):
        # (a1+b1 r)(a2+b2 r) = a1a2 - 11 b1b2 + (a1b2 + b1a2) r
        a = vsub(vmul(s.a, o.a), vsc(11, vmul(s.b, o.b)))
        b = vadd(vmul(s.a, o.b), vmul(s.b, o.a))
        return K2(a, b, s.den * o.den)

    def conj(s):
        return K2(vconj(s.a), vsc(-1, vconj(s.b)), s.den)

    def __eq__(s, o):
        return s.a == o.a and s.b == o.b and s.den == o.den

    def __hash__(s):
        return hash((tuple(s.a), tuple(s.b), s.den))

    def emb(s):
        return (vemb(s.a) + 1j * (11 ** 0.5) * vemb(s.b)) / s.den

    def is_one(s):
        return s.den == 1 and s.b == Z0 and s.a == E0

    def __repr__(s):
        return f"K2({s.a},{s.b})/{s.den}"

ONE = K2(E0)
SQM11 = K2(Z0, E0)
ZETA = K2(ZP[1])
def zpow(k): return K2(ZP[k % 30])

def unit_modulus(u):
    """exact |u| == 1 test: u * conj(u) == 1."""
    return (u * u.conj()).is_one()

