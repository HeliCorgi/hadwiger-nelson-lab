#!/usr/bin/env python3
"""Finite census for small exact non-root unit-modulus rotations in K2.

Primary target: normalized denominator 5, as requested by the post-Cycle-7
closed-orbit linker plan. We enumerate sparse numerator coefficient vectors in
K2 = Q(zeta30,sqrt(-11)). Floating embedding is used only as a necessary
prefilter for |numerator| ~= denominator. Every retained candidate is then
checked by exact K2 arithmetic: r*conj(r) == 1. All zeta30 roots are removed.

This is a bounded census only; exhaustion means only that this coefficient box
and support bound contained no candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
from time import monotonic

from hn_exact import K2, Z0, zpow, unit_modulus, vemb


def pack(z: K2):
    return {'a':z.a,'b':z.b,'den':z.den}


def is_zeta30_root(z: K2):
    for k in range(30):
        if z==zpow(k):
            return k
    return None


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--denominator',type=int,default=5)
    ap.add_argument('--max-support',type=int,default=4)
    ap.add_argument('--coeff-max',type=int,default=3)
    ap.add_argument('--float-tolerance',type=float,default=1e-9)
    ap.add_argument('--max-results',type=int,default=200)
    args=ap.parse_args(); args.out_dir.mkdir(parents=True,exist_ok=True)
    if args.denominator<=1 or args.max_support<1 or args.coeff_max<1:
        raise SystemExit('bad bounds')

    # Basis slots 0..7 are zeta^i; 8..15 are zeta^i*sqrt(-11).
    sqrt11=11**0.5
    basis=[]
    for i in range(8): basis.append(vemb([1 if j==i else 0 for j in range(8)]))
    for i in range(8): basis.append(1j*sqrt11*vemb([1 if j==i else 0 for j in range(8)]))

    coeff_values=[x for x in range(-args.coeff_max,args.coeff_max+1) if x]
    target=float(args.denominator*args.denominator)
    tol=args.float_tolerance*max(1.0,target)
    checked=0; float_near=0; exact_unit=0; roots_removed=0; results=[]
    started=monotonic()

    # Fix the first nonzero coefficient positive. Since r and -r are equivalent
    # up to the existing zeta30 root -1, this removes a harmless sign duplicate.
    for support in range(1,args.max_support+1):
        for slots in itertools.combinations(range(16),support):
            for coeffs in itertools.product(coeff_values,repeat=support):
                if coeffs[0]<0: continue
                checked+=1
                approx=sum(c*basis[s] for s,c in zip(slots,coeffs))
                if abs((approx.real*approx.real+approx.imag*approx.imag)-target)>tol:
                    continue
                float_near+=1
                a=Z0[:]; b=Z0[:]
                for slot,c in zip(slots,coeffs):
                    if slot<8: a[slot]=c
                    else: b[slot-8]=c
                r=K2(a,b,args.denominator)
                if r.den!=args.denominator:
                    continue
                if not unit_modulus(r):
                    continue
                exact_unit+=1
                root=is_zeta30_root(r)
                if root is not None:
                    roots_removed+=1
                    continue
                rec={
                    'rotation':pack(r),
                    'support_slots':list(slots),
                    'support_coefficients':list(coeffs),
                    'approx_xy':[r.emb().real,r.emb().imag],
                    'exact_unit_modulus':True,
                    'zeta30_root':False,
                }
                results.append(rec)
                print(json.dumps({'stage':'candidate','index':len(results)-1,**rec}),flush=True)
                if len(results)>=args.max_results: break
            if len(results)>=args.max_results: break
        print(json.dumps({'stage':'support_done','support':support,'checked':checked,
                          'float_near':float_near,'exact_unit':exact_unit,
                          'nonroot_results':len(results),'elapsed_seconds':round(monotonic()-started,3)}),flush=True)
        if len(results)>=args.max_results: break

    payload={
        'status':'FOUND_NONROOT_ROTATIONS' if results else 'BOUNDED_CENSUS_EMPTY',
        'field':'Q(zeta30,sqrt(-11))',
        'denominator':args.denominator,
        'max_support':args.max_support,
        'coeff_max':args.coeff_max,
        'sign_symmetry_reduced':True,
        'numerators_checked':checked,
        'float_near_candidates':float_near,
        'exact_unit_candidates_before_root_filter':exact_unit,
        'zeta30_roots_removed':roots_removed,
        'nonroot_count':len(results),
        'results':results,
        'elapsed_seconds':round(monotonic()-started,3),
        'scope_note':'Finite sparse coefficient census only; empty does not exclude denominator-5 rotations outside these bounds.',
    }
    raw=json.dumps(payload,indent=2)+'\n'
    (args.out_dir/'ROTATIONS.json').write_text(raw)
    (args.out_dir/'SUMMARY.md').write_text(
        '# Exact denominator-%d rotation census\n\n'%args.denominator+
        f"- status: **{payload['status']}**\n"
        f"- sparse numerator support <= **{args.max_support}**\n"
        f"- nonzero coefficient magnitude <= **{args.coeff_max}**\n"
        f"- numerators checked: **{checked}**\n"
        f"- float-near candidates exact-checked: **{float_near}**\n"
        f"- exact unit candidates before root filter: **{exact_unit}**\n"
        f"- zeta30 roots removed: **{roots_removed}**\n"
        f"- non-root exact rotations found: **{len(results)}**\n\n"
        'Floating point is proposal filtering only. Every retained rotation satisfies exact `r*conj(r)=1` and is unequal to all 30 `zeta30^k`.\n'
        'This is a bounded sparse census, not a field-wide nonexistence result.\n')
    print(json.dumps({k:v for k,v in payload.items() if k!='results'},indent=2))

if __name__=='__main__': main()
