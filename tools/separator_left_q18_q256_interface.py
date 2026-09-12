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
INNER=[14,18,54,55,256]
TARGET=(18,256)
EXPECTED=[23,35,57,86,159]


def make_solver(nodes, edges, Solver):
    ns=sorted(nodes); idx={v:i for i,v in enumerate(ns)}
    def X(v,c): return idx[v]*K+c+1
    cls=[]; V=set(ns)
    for v in ns:
        lits=[X(v,c) for c in range(K)]; cls.append(lits)
        for a,b in combinations(lits,2): cls.append([-a,-b])
    for u,v in edges:
        if u in V and v in V:
            for c in range(K): cls.append([-X(u,c),-X(v,c)])
    return Solver(bootstrap_with=cls), X


def opts(sol,X,sep,st,v):
    base=[X(x,st[i]) for i,x in enumerate(sep)]
    return [c for c in range(K) if sol.solve(assumptions=base+[X(v,c)])]


def induced(nodes,edges):
    V=set(nodes); return [(u,v) for u,v in edges if u in V and v in V]


def neigh(v,nodes,edges):
    V=set(nodes); out=set()
    for a,b in edges:
        if a==v and b in V: out.add(b)
        elif b==v and a in V: out.add(a)
    return sorted(out)


def analyze_with_solver(q0bag,q0edges,sep,ucomp,vcomp,Solver):
    us,uX=make_solver(set(ucomp)|set(sep),q0edges,Solver)
    vs,vX=make_solver(set(vcomp)|set(sep),q0edges,Solver)
    left=[]; right=[]; both=[]
    try:
        for st in rgs(len(sep)):
            st=tuple(st); key=''.join(map(str,st))
            ua=[uX(x,st[i]) for i,x in enumerate(sep)]
            va=[vX(x,st[i]) for i,x in enumerate(sep)]
            lu=us.solve(assumptions=ua); rv=vs.solve(assumptions=va)
            if lu:
                left.append({'key':key,'state':list(st),'u_colors':opts(us,uX,sep,st,TARGET[0])})
            if rv:
                right.append({'key':key,'state':list(st),'v_colors':opts(vs,vX,sep,st,TARGET[1])})
            if lu and rv:
                uo=opts(us,uX,sep,st,TARGET[0]); vo=opts(vs,vX,sep,st,TARGET[1])
                all_distinct=all(a!=b for a in uo for b in vo)
                both.append({'key':key,'state':list(st),'u_colors':uo,'v_colors':vo,'all_cross_pairs_distinct':all_distinct})
    finally:
        us.delete(); vs.delete()
    return {'left':left,'right':right,'intersection':both}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-dir',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    C,R,vq,E=build(a.data_dir); n=len(R); p,q=vq[P],vq[Q]
    val,S=min_vertex_cut(n,E,p,q)
    if p!=5 or S!=OUTER: raise RuntimeError((p,q,S))
    comps=components_without(n,E,S); pc=next(x for x in comps if p in x); left=set(pc)|set(S); ledges=induced(left,E)
    old=sorted(left); mp={v:i for i,v in enumerate(old)}; redges=[(mp[u],mp[v]) for u,v in ledges]
    cv,cn=min_vertex_cut(len(old),redges,mp[0],mp[10]); sep0=[old[x] for x in cn]
    if cv!=5 or sep0!=INNER: raise RuntimeError((cv,sep0))
    cc=components_without(len(old),redges,cn); ccold=[[old[x] for x in c] for c in cc]; q0comp=next(c for c in ccold if 0 in c)
    q0bag=set(q0comp)|set(sep0); q0edges=induced(q0bag,ledges)
    old2=sorted(q0bag); mp2={v:i for i,v in enumerate(old2)}; re2=[(mp2[u],mp2[v]) for u,v in q0edges]
    cutval,cutnew=min_vertex_cut(len(old2),re2,mp2[TARGET[0]],mp2[TARGET[1]])
    sep=[old2[x] for x in cutnew]
    if cutval!=5 or sep!=EXPECTED: raise RuntimeError((cutval,sep))
    c2=components_without(len(old2),re2,cutnew); c2old=[[old2[x] for x in c] for c in c2]
    uc=next(c for c in c2old if TARGET[0] in c); vc=next(c for c in c2old if TARGET[1] in c)
    if len(vc)!=1 or vc[0]!=TARGET[1]: raise RuntimeError(('q256 side not singleton',vc))
    n256=neigh(256,q0bag,q0edges)
    if n256!=sep: raise RuntimeError(('q256 neighborhood mismatch',n256,sep))
    results={}
    for name,Solver in [('Cadical195',Cadical195),('Glucose4',Glucose4)]:
        results[name]=analyze_with_solver(q0bag,q0edges,sep,uc,vc,Solver)
    # Require the two independent solvers to agree on state keys and endpoint option sets.
    def normalized(x):
        return {
            'left':[(r['key'],tuple(r['u_colors'])) for r in x['left']],
            'right':[(r['key'],tuple(r['v_colors'])) for r in x['right']],
            'intersection':[(r['key'],tuple(r['u_colors']),tuple(r['v_colors']),r['all_cross_pairs_distinct']) for r in x['intersection']],
        }
    agree=normalized(results['Cadical195'])==normalized(results['Glucose4'])
    if not agree: raise RuntimeError('solver disagreement')
    z=results['Cadical195']
    rep={
      'upstream_sha':UPSTREAM_SHA,'target_pair':list(TARGET),'separator_qnodes':sep,'min_cut_value':cutval,
      'q18_component_size':len(uc),'q256_component_size':len(vc),'q256_neighborhood_is_separator':n256==sep,
      'all_canonical_states':len(list(rgs(5))),
      'q18_side_extendable_count':len(z['left']),'q256_side_extendable_count':len(z['right']),'intersection_count':len(z['intersection']),
      'q18_side_rows':z['left'],'q256_side_rows':z['right'],'intersection':z['intersection'],
      'all_intersection_states_force_distinct':bool(z['intersection']) and all(r['all_cross_pairs_distinct'] for r in z['intersection']),
      'solver_crosscheck_exact_agreement':agree,
      'separator_induced_edges':[list(e) for e in induced(sep,q0edges)],
      'interpretation':'The only q0-side boundary disequality not explained by equality-class contraction is factored through the minimum size-5 separator equal to the complete neighborhood of singleton q256. All 52 canonical boundary partitions are enumerated independently by CaDiCaL195 and Glucose4.'
    }
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps({
      'separator':sep,'side_sizes':[len(uc),len(vc)],
      'left_count':len(z['left']),'right_count':len(z['right']),'intersection_count':len(z['intersection']),
      'intersection':z['intersection'],'all_force_distinct':rep['all_intersection_states_force_distinct'],'solver_agree':agree,
      'separator_edges':rep['separator_induced_edges']
    },indent=2))

if __name__=='__main__': main()
