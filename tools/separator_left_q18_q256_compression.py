#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

from pysat.solvers import Cadical195, Glucose4

from separator_interface import P, Q, UPSTREAM_SHA, build, components_without, min_vertex_cut, rgs

K=5
OUTER=[0,6,8,9,10,266]
Q0Q10=[14,18,54,55,256]
TARGET=(18,256)
EXPECTED=[23,35,57,86,159]


def make_solver(nodes,edges,Solver):
    ns=sorted(nodes); idx={v:i for i,v in enumerate(ns)}
    def X(v,c): return idx[v]*K+c+1
    cls=[]; V=set(ns)
    for v in ns:
        lits=[X(v,c) for c in range(K)]; cls.append(lits)
        for a,b in combinations(lits,2): cls.append([-a,-b])
    for u,v in edges:
        if u in V and v in V:
            for c in range(K): cls.append([-X(u,c),-X(v,c)])
    return Solver(bootstrap_with=cls),X


def opts(sol,X,sep,st,v):
    base=[X(x,st[i]) for i,x in enumerate(sep)]
    return [c for c in range(K) if sol.solve(assumptions=base+[X(v,c)])]


def enumerate_interface(uc,vc,sep,edges,Solver):
    us,uX=make_solver(set(uc)|set(sep),edges,Solver); vs,vX=make_solver(set(vc)|set(sep),edges,Solver)
    ur=[]; vr=[]; both=[]
    try:
        for st0 in rgs(len(sep)):
            st=tuple(st0); key=''.join(map(str,st)); ua=[uX(x,st[i]) for i,x in enumerate(sep)]; va=[vX(x,st[i]) for i,x in enumerate(sep)]
            lu=us.solve(assumptions=ua); rv=vs.solve(assumptions=va)
            uo=opts(us,uX,sep,st,TARGET[0]) if lu else []; vo=opts(vs,vX,sep,st,TARGET[1]) if rv else []
            if lu: ur.append({'state':key,'endpoint_colors':uo})
            if rv: vr.append({'state':key,'endpoint_colors':vo})
            if lu and rv:
                used=sorted(set(st)); missing=sorted(set(range(K))-set(st))
                both.append({'state':key,'u_colors':uo,'v_colors':vo,'used_colors':used,'missing_colors':missing,
                             'u_subset_used':set(uo)<=set(used),'v_equals_missing':set(vo)==set(missing),'cross_disjoint':set(uo).isdisjoint(vo)})
    finally:
        us.delete(); vs.delete()
    return {'u_side_rows':ur,'v_side_rows':vr,'intersection_rows':both}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-dir',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    C,R,vq,E=build(a.data_dir); n=len(R); p,q=vq[P],vq[Q]
    cv,S=min_vertex_cut(n,E,p,q)
    if p!=5 or S!=OUTER: raise RuntimeError((p,S))
    cc=components_without(n,E,S); pc=next(x for x in cc if p in x); left=set(pc)|set(S); ledges=[(u,v) for u,v in E if u in left and v in left]

    # q0-side bag after removing q10 via its known degree-5 separator.
    old=sorted(left); mp={v:i for i,v in enumerate(old)}; redges=[(mp[u],mp[v]) for u,v in ledges]
    cv2,cut2=min_vertex_cut(len(old),redges,mp[0],mp[10]); sep2=[old[x] for x in cut2]
    if cv2!=5 or sep2!=Q0Q10: raise RuntimeError((cv2,sep2))
    cc2=components_without(len(old),redges,cut2); cc2=[[old[x] for x in c] for c in cc2]; q0c=next(c for c in cc2 if 0 in c)
    bag=set(q0c)|set(sep2); bedges=[(u,v) for u,v in ledges if u in bag and v in bag]

    # Recursive q18-q256 separator.
    bold=sorted(bag); bmp={v:i for i,v in enumerate(bold)}; bredges=[(bmp[u],bmp[v]) for u,v in bedges]
    cv3,cut3=min_vertex_cut(len(bold),bredges,bmp[TARGET[0]],bmp[TARGET[1]]); sep=[bold[x] for x in cut3]
    if cv3!=5 or sep!=EXPECTED: raise RuntimeError((cv3,sep))
    cc3=components_without(len(bold),bredges,cut3); cc3=[[bold[x] for x in c] for c in cc3]
    uc=next(c for c in cc3 if TARGET[0] in c); vc=next(c for c in cc3 if TARGET[1] in c)

    ca=enumerate_interface(uc,vc,sep,bedges,Cadical195); gl=enumerate_interface(uc,vc,sep,bedges,Glucose4)
    if ca!=gl: raise RuntimeError('CaDiCaL/Glucose interface enumerations differ')
    data=ca
    n256=sorted({v for u,v in bedges if u==256}|{u for u,v in bedges if v==256})
    ukeys=[x['state'] for x in data['u_side_rows']]; ikeys=[x['state'] for x in data['intersection_rows']]
    excluded=[x for x in data['u_side_rows'] if x['state'] not in set(ikeys)]
    rep={
      'upstream_sha':UPSTREAM_SHA,'target_pair':list(TARGET),'separator_qnodes':sep,'min_cut_value':cv3,
      'u_component_size':len(uc),'v_component_size':len(vc),'solver_crosscheck':'Cadical195 and Glucose4 enumerations identical',
      'u_side_extendable_count':len(data['u_side_rows']),'v_side_extendable_count':len(data['v_side_rows']),'intersection_count':len(data['intersection_rows']),
      'u_side_rows':data['u_side_rows'],'intersection_rows':data['intersection_rows'],'u_side_rows_excluded_by_v_side':excluded,
      'q256_neighbors_in_q0_side':n256,'q256_degree':len(n256),'q256_neighborhood_is_separator':set(n256)==set(sep),
      'all_intersection_q18_colors_are_used_boundary_colors':all(x['u_subset_used'] for x in data['intersection_rows']),
      'all_intersection_q256_colors_equal_missing_boundary_colors':all(x['v_equals_missing'] for x in data['intersection_rows']),
      'all_intersection_cross_disjoint':all(x['cross_disjoint'] for x in data['intersection_rows']),
      'interpretation':'The q18-q256 forced disequality factors through a five-vertex separator that is exactly the degree-5 neighborhood of singleton q256. On every globally viable boundary state, q18 can use only colors already present on the separator, whereas q256 can use exactly colors missing from it; the option sets are therefore disjoint. The boundary table is independently reconstructed by CaDiCaL195 and Glucose4.'
    }
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps(rep,indent=2))

if __name__=='__main__': main()
