#!/usr/bin/env python3
"""Exact palette-deficit SAT probe for independent added centers.

If added centers are pairwise nonadjacent, fixing a center to color c is exactly
 equivalent to forbidding color c on every base-graph neighbor of that center.
Global S_k color symmetry lets center colorings be represented by canonical
restricted-growth strings (set partitions).  For m centers and 5 colors, only
partitions with at most 5 blocks need be tested.

Each SAT model is validated on every base edge and every center-neighbor edge.
A completed UNSAT sweep for one block count is only that block-count result; a
whole-graph A claim requires exhaustion of all block counts plus independent
confirmation/certification.
"""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
from pysat.solvers import Cadical195, Glucose4
from hn_exact import K2, unit_modulus
from hn_unconditional_scan import color_cnf, valid_coloring, write_json
from hn_symmetry_sat_probe import extract

SOLVERS={'cadical195':Cadical195,'glucose4':Glucose4}


def rgs(n, blocks):
    out=[]
    def rec(a,mx):
        if len(a)==n:
            if mx+1==blocks: out.append(tuple(a))
            return
        # Restricted-growth string: a[0]=0 and a_i <= 1+max(previous).
        for x in range(min(mx+1, blocks-1)+1):
            rec(a+[x], max(mx,x))
    if n:
        rec([0],0)
    return out


def load_seed(path,n):
    if path is None: return None
    s=path.read_text().strip()
    assert len(s)==n and all(ch in '01234' for ch in s)
    return [int(ch) for ch in s]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True,help='induced-complete base graph')
    ap.add_argument('--centers',type=Path,required=True,help='JSON with center points and exact neighbor lists')
    ap.add_argument('--blocks',type=int,required=True,choices=range(1,6))
    ap.add_argument('--solver',choices=sorted(SOLVERS),default='cadical195')
    ap.add_argument('--seed-coloring',type=Path,default=None)
    ap.add_argument('--out-dir',type=Path,required=True)
    a=ap.parse_args(); a.out_dir.mkdir(parents=True,exist_ok=True)

    raw=a.graph.read_bytes(); gd=json.loads(raw)
    pts=[K2(p['a'],p['b'],p['den']) for p in gd['pts']]
    edges=sorted({tuple(map(int,e)) for e in gd['edges']}); n=len(pts)
    assert len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    cd=json.loads(a.centers.read_text()); centers=cd['centers']; m=len(centers)
    assert m>=1
    for i,c in enumerate(centers):
        x=K2(c['point']['a'],c['point']['b'],c['point']['den'])
        ns=list(map(int,c['neighbors']))
        assert ns==[v for v,p in enumerate(pts) if unit_modulus(p-x)]
        assert all(0<=v<n for v in ns)
    # This reduction requires pairwise nonadjacent centers.
    xs=[K2(c['point']['a'],c['point']['b'],c['point']['den']) for c in centers]
    assert all(not unit_modulus(xs[i]-xs[j]) for i in range(m) for j in range(i+1,m))

    patterns=rgs(m,a.blocks)
    # More blocks first is handled by the workflow; within a block count, spread
    # repeated labels lexicographically for deterministic reproducibility.
    seed=load_seed(a.seed_coloring,n)
    if seed is not None: assert valid_coloring(seed,n,edges)
    cls=SOLVERS[a.solver]; records=[]; found=None
    clauses=color_cnf(n,edges)
    with cls(bootstrap_with=clauses) as s:
        if seed is not None and hasattr(s,'set_phases'):
            s.set_phases([v*5+seed[v]+1 for v in range(n)])
        for idx,pat in enumerate(patterns):
            assumptions=[]
            for ci,color in enumerate(pat):
                for v in centers[ci]['neighbors']:
                    assumptions.append(-(int(v)*5+int(color)+1))
            ans=s.solve(assumptions=assumptions)
            rec={'index':idx,'pattern':list(pat),'status':'SAT' if ans is True else 'UNSAT' if ans is False else 'UNKNOWN'}
            records.append(rec)
            write_json(a.out_dir/'ACTIVE.json',{'solver':a.solver,'blocks':a.blocks,'tested':len(records),'total':len(patterns),'last':rec})
            print(json.dumps(rec),flush=True)
            if ans is True:
                colors=extract(s.get_model(),n); assert valid_coloring(colors,n,edges)
                for ci,color in enumerate(pat):
                    assert all(colors[int(v)]!=color for v in centers[ci]['neighbors'])
                full=colors+list(pat)
                # Validate all base and center edges explicitly.
                assert all(full[u]!=full[v] for u,v in edges)
                for ci,c in enumerate(centers):
                    cv=n+ci
                    assert all(full[int(v)]!=full[cv] for v in c['neighbors'])
                found={'pattern':list(pat),'base_colors':colors,'full_colors':full}
                (a.out_dir/'COLORING.txt').write_text(''.join(map(str,full))+'\n')
                break
            if ans is not False:
                break

    if found is not None:
        status='SAT'; classification='NOT_A'
    elif records and all(r['status']=='UNSAT' for r in records) and len(records)==len(patterns):
        status='BLOCKCOUNT_UNSAT'; classification=None
    else:
        status='UNKNOWN'; classification=None
    out={'status':status,'classification':classification,'solver':a.solver,'blocks':a.blocks,
         'centers':m,'patterns_total':len(patterns),'patterns_tested':len(records),
         'vertices_base':n,'edges_base':len(edges),'graph_sha256':hashlib.sha256(raw).hexdigest(),
         'pairwise_center_nonadjacency_exactly_verified':True,
         'center_neighbor_sets_exactly_verified':True,'records':records,
         'all_sat_models_validated':found is not None if status=='SAT' else True,
         'timeout_or_unknown_is_evidence':False}
    if found is not None: out['sat_pattern']=found['pattern']
    write_json(a.out_dir/'PARTITION_PROBE.json',out)
    print(json.dumps({k:v for k,v in out.items() if k!='records'},indent=2))

if __name__=='__main__': main()
