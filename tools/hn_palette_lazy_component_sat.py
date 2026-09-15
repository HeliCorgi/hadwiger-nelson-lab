#!/usr/bin/env python3
"""Lazy exact 5-color SAT for a prefix graph plus disconnected fresh-center components.

The prefix is solved by a master SAT instance.  Fresh vertices are decomposed into
connected components using only fresh-fresh edges.  For each master coloring, each
fresh component is solved as a list-coloring problem induced by its prefix-neighbor
colors.  If a component is UNSAT, selector assumptions yield a core of prefix
vertex/color assignments sufficient for non-extension.  The corresponding clause
forbidding that conjunction is soundly learned by the master.

A full SAT coloring is validated on every supplied exact edge.  If the master
becomes UNSAT after only independently confirmed component nogoods, the result is
an A candidate that still requires the repository's independent certificate path.
Timeout/iteration limit is non-evidence.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from collections import Counter
from itertools import combinations
from pathlib import Path
from pysat.solvers import Cadical195,Glucose4
from hn_exact import K2,unit_modulus
from hn_unconditional_scan import color_cnf,valid_coloring,write_json
from hn_symmetry_sat_probe import find_triangle,extract


def load_seed(path,n):
    s=path.read_text().strip()
    if len(s)==n and all(ch in '01234' for ch in s): return [int(ch) for ch in s]
    raise ValueError('seed must be a plain 0..4 coloring string')


def fresh_components(prefix_n,n,center_edges):
    adj={v:set() for v in range(prefix_n,n)}
    for u,v in center_edges: adj[u].add(v);adj[v].add(u)
    unseen=set(adj); comps=[]
    while unseen:
        s=unseen.pop(); stack=[s]; comp=[]
        while stack:
            u=stack.pop();comp.append(u)
            ns=adj[u]&unseen
            unseen.difference_update(ns);stack.extend(ns)
        comps.append(sorted(comp))
    comps.sort(key=lambda c:(-len(c),c[0]))
    return comps


def solve_component(comp, internal_edges, cross_by_fresh, prefix_colors, confirm=True):
    loc={v:i for i,v in enumerate(comp)}; m=len(comp)
    clauses=[]
    def var(v,c): return loc[v]*5+c+1
    for v in comp:
        xs=[var(v,c) for c in range(5)];clauses.append(xs)
        for a,b in combinations(xs,2):clauses.append([-a,-b])
    for u,v in internal_edges:
        if u in loc and v in loc:
            for c in range(5):clauses.append([-var(u,c),-var(v,c)])
    boundary=sorted({p for v in comp for p in cross_by_fresh.get(v,())})
    sel_base=m*5+1; selector={p:sel_base+i for i,p in enumerate(boundary)}
    for v in comp:
        for p in cross_by_fresh.get(v,()):
            c=prefix_colors[p]
            clauses.append([-selector[p],-var(v,c)])
    assumptions=[selector[p] for p in boundary]
    with Cadical195(bootstrap_with=clauses) as s:
        ans=s.solve(assumptions=assumptions)
        if ans is True:
            pos={x for x in s.get_model() if x>0}; cols={}
            for v in comp:
                cc=[c for c in range(5) if var(v,c) in pos];assert len(cc)==1;cols[v]=cc[0]
            return True,cols,None,len(clauses),len(boundary)
        assert ans is False
        core=s.get_core() or []
    inv={lit:p for p,lit in selector.items()}
    core_prefix=sorted({inv[abs(lit)] for lit in core if abs(lit) in inv})
    assert core_prefix, ('empty selector core',len(comp),len(boundary))
    if confirm:
        core_assumptions=[selector[p] for p in core_prefix]
        with Glucose4(bootstrap_with=clauses) as g:
            gg=g.solve(assumptions=core_assumptions)
        assert gg is False, ('core not independently UNSAT',len(comp),len(core_prefix),gg)
    return False,None,core_prefix,len(clauses),len(boundary)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--prefix-vertices',type=int,required=True)
    ap.add_argument('--seed-coloring',type=Path,default=None)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--iterations',type=int,default=5000)
    ap.add_argument('--cores-per-iteration',type=int,default=32)
    ap.add_argument('--seconds',type=float,default=14000)
    a=ap.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    raw=a.graph.read_bytes();d=json.loads(raw)
    pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    edges=sorted({tuple(map(int,e)) for e in d['edges']});n=len(pts);pfx=a.prefix_vertices
    assert 0<pfx<n and len(set(pts))==n and all(unit_modulus(pts[u]-pts[v]) for u,v in edges)
    prefix_edges=[];center_edges=[];cross=[]
    for u,v in edges:
        if v<pfx:prefix_edges.append((u,v))
        elif u>=pfx:center_edges.append((u,v))
        else:cross.append((u,v))
    comps=fresh_components(pfx,n,center_edges)
    comp_of={v:i for i,c in enumerate(comps) for v in c}
    assert len(comp_of)==n-pfx
    cross_by_fresh={v:[] for v in range(pfx,n)}
    for p,v in cross:cross_by_fresh[v].append(p)
    internal_by_comp=[[] for _ in comps]
    for u,v in center_edges:
        ci=comp_of[u];assert ci==comp_of[v];internal_by_comp[ci].append((u,v))
    seed=None
    if a.seed_coloring:
        full=load_seed(a.seed_coloring,n);seed=full[:pfx]
        assert valid_coloring(seed,pfx,prefix_edges)
    tri=find_triangle(pfx,prefix_edges);assert tri is not None
    triass=[tri[0]*5+1,tri[1]*5+2,tri[2]*5+3]
    clauses=color_cnf(pfx,prefix_edges); learned=set();records=[];started=time.monotonic();status='ITERATION_LIMIT';solution=None
    # Harder/larger components first.
    order=sorted(range(len(comps)),key=lambda i:(-len(comps[i]),-len(internal_by_comp[i]),-sum(len(cross_by_fresh[v]) for v in comps[i]),i))
    with Cadical195(bootstrap_with=clauses) as master:
        if seed is not None and hasattr(master,'set_phases'):
            master.set_phases([v*5+seed[v]+1 for v in range(pfx)])
        for it in range(a.iterations):
            if time.monotonic()-started>a.seconds:
                status='TIME_LIMIT';break
            ans=master.solve(assumptions=triass)
            if ans is False:
                # Confirm the learned master CNF independently.
                allclauses=clauses+[list(c) for c in learned]
                with Glucose4(bootstrap_with=allclauses) as g:
                    gg=g.solve(assumptions=triass)
                assert gg is False
                status='MASTER_UNSAT_A_CANDIDATE_REQUIRES_CERTIFICATE';break
            assert ans is True
            pc=extract(master.get_model(),pfx);assert valid_coloring(pc,pfx,prefix_edges)
            comp_colors={};new_cores=[];tested=0;core_sizes=[]
            for ci in order:
                tested+=1
                ok,cc,core,ncla,nb=solve_component(comps[ci],internal_by_comp[ci],cross_by_fresh,pc,confirm=True)
                if ok:
                    comp_colors.update(cc)
                    continue
                clause=tuple(sorted({-(p*5+pc[p]+1) for p in core}))
                assert clause
                if clause not in learned:
                    learned.add(clause);master.add_clause(list(clause));new_cores.append((ci,core,clause));core_sizes.append(len(core))
                if len(new_cores)>=a.cores_per_iteration:break
            rec={'iteration':it,'components_tested':tested,'new_nogoods':len(new_cores),'total_nogoods':len(learned),
                 'core_sizes':core_sizes,'elapsed_seconds':round(time.monotonic()-started,3)}
            records.append(rec)
            if it%10==0 or not new_cores:
                print(json.dumps(rec),flush=True)
                write_json(a.out_dir/'LAZY_ACTIVE.json',{'status':'ACTIVE','records':records[-100:],'total_nogoods':len(learned)})
            if not new_cores:
                # Every component extended this same master model.
                colors=pc+[0]*(n-pfx)
                for v,c in comp_colors.items():colors[v]=c
                assert valid_coloring(colors,n,edges)
                solution=colors;status='SAT';break
    if solution is not None:
        out={'status':'SAT','classification':'NOT_A','vertices':n,'edges':len(edges),'prefix_vertices':pfx,
             'fresh_vertices':n-pfx,'fresh_components':len(comps),'max_component':max(map(len,comps)),
             'learned_nogoods':len(learned),'iterations':len(records),'records':records,'all_edges_validated':True,'colors':solution}
        (a.out_dir/'COLORING.txt').write_text(''.join(map(str,solution))+'\n')
    else:
        out={'status':status,'classification':'A_CANDIDATE_REQUIRES_CERTIFICATE' if status.startswith('MASTER_UNSAT') else None,
             'vertices':n,'edges':len(edges),'prefix_vertices':pfx,'fresh_vertices':n-pfx,'fresh_components':len(comps),
             'max_component':max(map(len,comps)),'fresh_internal_edges':len(center_edges),'cross_edges':len(cross),
             'learned_nogoods':len(learned),'iterations':len(records),'records':records,
             'component_unsat_cores_independently_confirmed':True,'master_unsat_independently_confirmed':status.startswith('MASTER_UNSAT'),
             'timeout_or_iteration_limit_is_evidence':False}
    out['graph_sha256']=hashlib.sha256(raw).hexdigest();out['triangle_symmetry']=list(tri)
    write_json(a.out_dir/'LAZY_COMPONENT_SAT.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('colors','records')},indent=2))

if __name__=='__main__':main()
