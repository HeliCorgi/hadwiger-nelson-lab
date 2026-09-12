#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

from pysat.solvers import Cadical195, Glucose4

from separator_interface import P, Q, UPSTREAM_SHA, build, components_without, min_vertex_cut, rgs

K5 = 5
OUTER = [0, 6, 8, 9, 10, 266]
INNER = [14, 18, 54, 55, 256]
TARGET = (18, 256)


def color_cnf(nodes, edges, k):
    ns = sorted(nodes)
    idx = {v: i for i, v in enumerate(ns)}
    def X(v, c): return idx[v] * k + c + 1
    cls = []
    V = set(ns)
    for v in ns:
        lits = [X(v,c) for c in range(k)]
        cls.append(lits)
        for a,b in combinations(lits,2): cls.append([-a,-b])
    for u,v in edges:
        if u in V and v in V:
            for c in range(k): cls.append([-X(u,c),-X(v,c)])
    return cls, X


def kcolorable(nodes, edges, k, Solver):
    cls,_ = color_cnf(nodes,edges,k)
    with Solver(bootstrap_with=cls) as s:
        return s.solve()


def forced_different(nodes, edges, u, v, Solver):
    cls,X = color_cnf(nodes,edges,K5)
    for c in range(K5):
        cls.append([-X(u,c), X(v,c)])
        cls.append([-X(v,c), X(u,c)])
    with Solver(bootstrap_with=cls) as s:
        return not s.solve()


def minimize_non4(nodes, edges):
    active=set(nodes)
    # deterministic low-degree-first deletion, sufficient inclusion-minimal witness.
    def deg(x,V):
        return sum(1 for a,b in edges if (a==x and b in V) or (b==x and a in V))
    order=sorted(active,key=lambda x:(deg(x,active),x))
    for x in order:
        trial=active-{x}
        if trial and not kcolorable(trial,edges,4,Cadical195): active=trial
    return sorted(active)


def clique5(nodes, edges):
    V=sorted(nodes); E={(min(a,b),max(a,b)) for a,b in edges}
    for comb in combinations(V,5):
        if all((min(a,b),max(a,b)) in E for a,b in combinations(comb,2)):
            return list(comb)
    return None


def make_side_solver(nodes, edges):
    cls,X=color_cnf(nodes,edges,K5)
    return Glucose4(bootstrap_with=cls),X


def endpoint_opts(sol,X,sep,st,v):
    base=[X(x,st[i]) for i,x in enumerate(sep)]
    return [c for c in range(K5) if sol.solve(assumptions=base+[X(v,c)])]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-dir',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    C,R,vq,E=build(a.data_dir); n=len(R); p,q=vq[P],vq[Q]
    val,S=min_vertex_cut(n,E,p,q)
    if p!=5 or S!=OUTER: raise RuntimeError((p,S))
    comps=components_without(n,E,S); pc=next(x for x in comps if p in x); left=set(pc)|set(S)
    ledges=[(u,v) for u,v in E if u in left and v in left]

    # Reconstruct the q0-side bag from the known minimum q0-q10 separator.
    old=sorted(left); mp={v:i for i,v in enumerate(old)}; redges=[(mp[u],mp[v]) for u,v in ledges]
    cv,cutnew=min_vertex_cut(len(old),redges,mp[0],mp[10]); inner=[old[x] for x in cutnew]
    if cv!=5 or inner!=INNER: raise RuntimeError((cv,inner))
    ccs=components_without(len(old),redges,cutnew); ccs=[[old[x] for x in c] for c in ccs]
    q0c=next(c for c in ccs if 0 in c); bag=set(q0c)|set(inner)
    bedges=[(u,v) for u,v in ledges if u in bag and v in bag]
    if len(bag)!=266: raise RuntimeError(len(bag))

    u,v=TARGET
    Eset={(min(a,b),max(a,b)) for a,b in bedges}
    Nu={b for a,b in bedges if a==u}|{a for a,b in bedges if b==u}
    Nv={b for a,b in bedges if a==v}|{a for a,b in bedges if b==v}
    common=Nu & Nv; union=Nu | Nv

    neighborhoods={}
    for name,V in [('common',common),('union',union)]:
        satC=kcolorable(V,bedges,4,Cadical195) if V else True
        satG=kcolorable(V,bedges,4,Glucose4) if V else True
        rec={'vertices':sorted(V),'vertex_count':len(V),'4colorable_cadical195':satC,'4colorable_glucose4':satG,'k5_clique':clique5(V,bedges)}
        if not satC and not satG:
            core=minimize_non4(V,bedges)
            rec['inclusion_minimal_non4_vertices']=core
            rec['inclusion_minimal_non4_vertex_count']=len(core)
            rec['inclusion_minimal_non4_edge_count']=sum(1 for a,b in bedges if a in set(core) and b in set(core))
            rec['minimal_core_4colorable_glucose4']=kcolorable(core,bedges,4,Glucose4)
            rec['minimal_core_k5_clique']=clique5(core,bedges)
        neighborhoods[name]=rec

    # If the neighborhood lemma is insufficient, record a recursive min-cut interface.
    bold=sorted(bag); bmp={x:i for i,x in enumerate(bold)}; bredges=[(bmp[a],bmp[b]) for a,b in bedges]
    cutval,cutidx=min_vertex_cut(len(bold),bredges,bmp[u],bmp[v]); sep=[bold[x] for x in cutidx]
    interface={'min_vertex_cut_value':cutval,'separator_qnodes':sep}
    comps2=components_without(len(bold),bredges,cutidx); comps2=[[bold[x] for x in c] for c in comps2]
    uc=next(c for c in comps2 if u in c); vc=next(c for c in comps2 if v in c)
    interface['u_component_size']=len(uc); interface['v_component_size']=len(vc); interface['other_component_sizes']=[len(c) for c in comps2 if c is not uc and c is not vc]
    if cutval <= 8:
        us,uX=make_side_solver(set(uc)|set(sep),bedges); vs,vX=make_side_solver(set(vc)|set(sep),bedges)
        rows=[]; leftn=rightn=0
        try:
            for st in rgs(len(sep)):
                st=tuple(st); ua=[uX(x,st[i]) for i,x in enumerate(sep)]; va=[vX(x,st[i]) for i,x in enumerate(sep)]
                lu=us.solve(assumptions=ua); rv=vs.solve(assumptions=va)
                if lu:leftn+=1
                if rv:rightn+=1
                if lu and rv:
                    uo=endpoint_opts(us,uX,sep,st,u); vo=endpoint_opts(vs,vX,sep,st,v)
                    rows.append({'state':''.join(map(str,st)),'u_colors':uo,'v_colors':vo,'cross_disjoint':set(uo).isdisjoint(vo)})
        finally:
            us.delete(); vs.delete()
        interface.update({'enumerated':True,'u_side_extendable_count':leftn,'v_side_extendable_count':rightn,'intersection_count':len(rows),'all_intersection_states_force_different':bool(rows) and all(x['cross_disjoint'] for x in rows),'intersection_rows':rows})
    else:
        interface['enumerated']=False

    rep={
      'upstream_sha':UPSTREAM_SHA,'q0_side_bag_size':len(bag),'q0_side_edge_count':len(bedges),'target_pair':list(TARGET),
      'target_direct_edge':(min(u,v),max(u,v)) in Eset,
      'target_forced_different':{
        'Cadical195':forced_different(bag,bedges,u,v,Cadical195),
        'Glucose4':forced_different(bag,bedges,u,v,Glucose4)},
      'degrees':{str(u):len(Nu),str(v):len(Nv)},'neighborhood_tests':neighborhoods,'recursive_interface':interface,
      'interpretation':'If q18 and q256 had the same color, every vertex adjacent to either endpoint would have to avoid that color, so N(q18) union N(q256) would need a 4-coloring. Non-4-colorability of that union is therefore a direct graph-theoretic forced-disequality lemma. If that test fails, the recursive minimum-separator data records the next exact factorization target.'
    }
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps({'forced_different':rep['target_forced_different'],'degrees':rep['degrees'],'common':neighborhoods['common'],'union':neighborhoods['union'],'recursive_interface':interface},indent=2))

if __name__=='__main__': main()
