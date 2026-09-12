#!/usr/bin/env python3
from __future__ import annotations

import argparse,json
from itertools import combinations
from pathlib import Path
from pysat.solvers import Cadical195,Glucose4
from separator_interface import P,Q,UPSTREAM_SHA,build,components_without,min_vertex_cut,rgs

K=5
OUTER=[0,6,8,9,10,266]
SEP=[4,5,33,62,68,78,226]
TRACK=(8,9,104)


def make_solver(nodes,edges,Solver):
    ns=sorted(nodes);idx={v:i for i,v in enumerate(ns)}
    def X(v,c):return idx[v]*K+c+1
    cls=[];V=set(ns)
    for v in ns:
        lits=[X(v,c) for c in range(K)];cls.append(lits)
        for a,b in combinations(lits,2):cls.append([-a,-b])
    for u,v in edges:
        if u in V and v in V:
            for c in range(K):cls.append([-X(u,c),-X(v,c)])
    return Solver(bootstrap_with=cls),X


def opts(sol,X,sep,st,v):
    base=[X(x,st[i]) for i,x in enumerate(sep)]
    return [c for c in range(K) if sol.solve(assumptions=base+[X(v,c)])]


def enumerate_interface(big,small,edges,Solver):
    bs,bX=make_solver(set(big)|set(SEP),edges,Solver);ss,sX=make_solver(set(small)|set(SEP),edges,Solver)
    br=[];sr=[];both=[]
    try:
        for st0 in rgs(len(SEP)):
            st=tuple(st0);key=''.join(map(str,st));ba=[bX(x,st[i]) for i,x in enumerate(SEP)];sa=[sX(x,st[i]) for i,x in enumerate(SEP)]
            lb=bs.solve(assumptions=ba);rs=ss.solve(assumptions=sa)
            b8=opts(bs,bX,SEP,st,8) if lb else [];b9=opts(bs,bX,SEP,st,9) if lb else [];o104=opts(ss,sX,SEP,st,104) if rs else []
            if lb:br.append({'state':key,'q8_colors':b8,'q9_colors':b9})
            if rs:sr.append({'state':key,'q104_colors':o104})
            if lb and rs:
                used=sorted(set(st));missing=sorted(set(range(K))-set(st))
                both.append({'state':key,'q8_colors':b8,'q9_colors':b9,'q104_colors':o104,'used_colors':used,'missing_colors':missing,
                             'q104_equals_missing':set(o104)==set(missing),
                             'all_three_same_singleton':len(b8)==len(b9)==len(o104)==1 and b8[0]==b9[0]==o104[0],
                             'q8_subset_missing':set(b8)<=set(missing),'q9_subset_missing':set(b9)<=set(missing)})
    finally:bs.delete();ss.delete()
    return {'big_rows':br,'small_rows':sr,'intersection_rows':both}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    C,R,vq,E=build(a.data_dir);n=len(R);p,q=vq[P],vq[Q];_,S=min_vertex_cut(n,E,p,q)
    if p!=5 or S!=OUTER:raise RuntimeError((p,S))
    cc=components_without(n,E,S);pc=next(x for x in cc if p in x);left=set(pc)|set(S);ledges=[(u,v) for u,v in E if u in left and v in left]
    old=sorted(left);mp={v:i for i,v in enumerate(old)};redges=[(mp[u],mp[v]) for u,v in ledges]
    cv,cut=min_vertex_cut(len(old),redges,mp[8],mp[104]);sep=[old[x] for x in cut]
    if cv!=7 or sep!=SEP:raise RuntimeError((cv,sep))
    ccs=components_without(len(old),redges,cut);ccs=[[old[x] for x in c] for c in ccs]
    small=next(c for c in ccs if 104 in c);big=next(c for c in ccs if 8 in c)
    if 9 not in big or len(small)!=1:raise RuntimeError((len(big),small,9 in big))
    ca=enumerate_interface(big,small,ledges,Cadical195);gl=enumerate_interface(big,small,ledges,Glucose4)
    if ca!=gl:raise RuntimeError('Cadical195/Glucose4 enumeration mismatch')
    n104=sorted({v for u,v in ledges if u==104}|{u for u,v in ledges if v==104})
    rows=ca['intersection_rows']
    rep={'upstream_sha':UPSTREAM_SHA,'separator_qnodes':SEP,'min_cut_value':cv,'big_component_size':len(big),'small_component_size':len(small),
         'q104_neighbors_in_left':n104,'q104_degree':len(n104),'q104_neighborhood_is_separator':set(n104)==set(SEP),
         'big_side_extendable_count':len(ca['big_rows']),'q104_side_extendable_count':len(ca['small_rows']),'intersection_count':len(rows),
         'big_side_rows':ca['big_rows'],'intersection_rows':rows,
         'all_intersection_q104_colors_equal_missing':all(x['q104_equals_missing'] for x in rows),
         'all_intersection_q8_subset_missing':all(x['q8_subset_missing'] for x in rows),
         'all_intersection_q9_subset_missing':all(x['q9_subset_missing'] for x in rows),
         'all_intersection_three_same_singleton':all(x['all_three_same_singleton'] for x in rows),
         'solver_crosscheck':'Cadical195 and Glucose4 enumerations identical',
         'interpretation':'A single seven-vertex separator isolates q104 while q8 and q9 remain together on the large side. Exact boundary enumeration checks whether globally viable states force q8, q9 and q104 to the same missing palette color, thereby proving q8=q9 through one shared interface rather than two separate pairwise arguments.'}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps({k:rep[k] for k in ['q104_degree','q104_neighborhood_is_separator','big_side_extendable_count','q104_side_extendable_count','intersection_count','all_intersection_q104_colors_equal_missing','all_intersection_q8_subset_missing','all_intersection_q9_subset_missing','all_intersection_three_same_singleton']},indent=2))
if __name__=='__main__':main()
