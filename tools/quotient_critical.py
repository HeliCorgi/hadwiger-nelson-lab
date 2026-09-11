#!/usr/bin/env python3
from __future__ import annotations

import argparse, json
from collections import deque, Counter
from itertools import combinations
from pathlib import Path

from pysat.solvers import Cadical195

K=5
P,Q=217,490
UPSTREAM_SHA='d1e80998bda337d9fa721f2e96d203ae54e97fc8'

def load_json(p): return json.loads(Path(p).read_text())

def build(data_dir):
    g=load_json(data_dir/'g510_k2.json'); full=[tuple(map(int,e)) for e in g['edges']]
    raw=load_json(data_dir/'B5_MULTICORE.json')['cores'][0]
    h=[full[i] for i in raw] if raw and isinstance(raw[0],int) else [tuple(map(int,e)) for e in raw]
    c88=[tuple(map(int,e)) for e in load_json(data_dir/'B5_P2_LEMMA.json')['C_min']]
    edges=sorted({(min(a,b),max(a,b)) for a,b in h})
    verts=sorted({x for e in edges for x in e}|{x for e in c88 for x in e})
    parent={v:v for v in verts}
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:
            if a>b: a,b=b,a
            parent[b]=a
    for a,b in c88: union(a,b)
    comps={}
    for v in verts: comps.setdefault(find(v),[]).append(v)
    roots=sorted(comps,key=lambda r:min(comps[r])); qid={r:i for i,r in enumerate(roots)}
    vq={v:qid[find(v)] for v in verts}; qe=set()
    for a,b in edges:
        u,v=vq[a],vq[b]
        if u==v: raise RuntimeError('internal quotient edge')
        qe.add((min(u,v),max(u,v)))
    return verts,comps,roots,vq,qe

def adj_from(n,edges):
    adj=[set() for _ in range(n)]
    for u,v in edges: adj[u].add(v); adj[v].add(u)
    return adj

def components_without(adj, removed):
    n=len(adj); seen=set(removed); comps=[]
    for s in range(n):
        if s in seen: continue
        q=[s]; seen.add(s); c=[]
        for x in q:
            c.append(x)
            for y in adj[x]:
                if y not in seen and y not in removed:
                    seen.add(y); q.append(y)
        comps.append(c)
    return comps

def articulation_points(adj, removed=frozenset()):
    n=len(adj); disc=[-1]*n; low=[0]*n; parent=[-1]*n; out=set(); t=0
    def dfs(u):
        nonlocal t
        disc[u]=low[u]=t; t+=1; children=0
        for v in adj[u]:
            if v in removed: continue
            if disc[v]<0:
                parent[v]=u; children+=1; dfs(v); low[u]=min(low[u],low[v])
                if parent[u]<0 and children>1: out.add(u)
                if parent[u]>=0 and low[v]>=disc[u]: out.add(u)
            elif v!=parent[u]: low[u]=min(low[u],disc[v])
    for u in range(n):
        if u not in removed and disc[u]<0: dfs(u)
    return out

def two_cuts(adj):
    cuts=[]; n=len(adj)
    for u in range(n):
        arts=articulation_points(adj,{u})
        for v in arts:
            if u<v:
                cs=components_without(adj,{u,v})
                if len(cs)>1:
                    sizes=sorted(map(len,cs))
                    cuts.append((u,v,sizes))
    return cuts

def shortest(adj,s,t):
    prev={s:None}; q=deque([s])
    while q:
        u=q.popleft()
        if u==t: break
        for v in adj[u]:
            if v not in prev: prev[v]=u; q.append(v)
    if t not in prev: return None,[]
    path=[]; x=t
    while x is not None: path.append(x); x=prev[x]
    path.reverse(); return len(path)-1,path

class Dinic:
    def __init__(self,n): self.g=[[] for _ in range(n)]
    def add(self,u,v,c):
        a=[v,c,None]; b=[u,0,a]; a[2]=b; self.g[u].append(a); self.g[v].append(b)
    def flow(self,s,t):
        ans=0; n=len(self.g); INF=10**9
        while True:
            level=[-1]*n; level[s]=0; q=deque([s])
            while q:
                u=q.popleft()
                for e in self.g[u]:
                    if e[1]>0 and level[e[0]]<0: level[e[0]]=level[u]+1; q.append(e[0])
            if level[t]<0: return ans
            it=[0]*n
            def dfs(u,f):
                if u==t: return f
                while it[u]<len(self.g[u]):
                    e=self.g[u][it[u]]
                    if e[1]>0 and level[e[0]]==level[u]+1:
                        z=dfs(e[0],min(f,e[1]))
                        if z: e[1]-=z; e[2][1]+=z; return z
                    it[u]+=1
                return 0
            while True:
                f=dfs(s,INF)
                if not f: break
                ans+=f

def vertex_connectivity_st(adj,s,t):
    n=len(adj); INF=n+5; D=Dinic(2*n)
    for v in range(n): D.add(2*v,2*v+1, INF if v in (s,t) else 1)
    for u in range(n):
        for v in adj[u]:
            D.add(2*u+1,2*v,INF)
    return D.flow(2*s+1,2*t)

def guarded_vertex_critical(n,edges):
    def X(v,c): return v*K+c+1
    def A(v): return n*K+v+1
    cls=[]
    for v in range(n):
        cls.append([-A(v)]+[X(v,c) for c in range(K)])
        for c,d in combinations(range(K),2): cls.append([-A(v),-X(v,c),-X(v,d)])
    for u,v in edges:
        for c in range(K): cls.append([-A(u),-A(v),-X(u,c),-X(v,c)])
    allA=[A(v) for v in range(n)]
    with Cadical195(bootstrap_with=cls) as s:
        whole=s.solve(assumptions=allA)
        deletion=[]
        if whole is False:
            for v in range(n):
                ass=[A(u) for u in range(n) if u!=v]
                deletion.append(bool(s.solve(assumptions=ass)))
    return whole,deletion

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-dir',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); args=ap.parse_args()
    verts,comps,roots,vq,qe=build(args.data_dir); n=len(roots); p,q=vq[P],vq[Q]
    G=set(qe); G.add((min(p,q),max(p,q))); adj=adj_from(n,G)
    deg=[len(x) for x in adj]
    d,path=shortest(adj_from(n,qe),p,q)
    arts=sorted(articulation_points(adj)); cuts=two_cuts(adj)
    cuts_sorted=sorted(cuts,key=lambda x:(x[2][0],len(x[2]),x[0],x[1]))
    conn=vertex_connectivity_st(adj_from(n,qe),p,q)
    whole,vd=guarded_vertex_critical(n,G)
    low=[v for v,x in enumerate(deg) if x==5]
    lowset=set(low); lowedges=[(u,v) for u,v in G if u in lowset and v in lowset]
    lowadj=adj_from(n,lowedges)
    seen=set(); lowcomps=[]
    for s in low:
        if s in seen: continue
        stack=[s]; seen.add(s); cc=[]
        while stack:
            u=stack.pop(); cc.append(u)
            for v in lowadj[u]:
                if v in lowset and v not in seen: seen.add(v); stack.append(v)
        lowcomps.append(sorted(cc))
    low_comp_stats=[]
    for cc in lowcomps:
        ss=set(cc); m=sum(1 for u,v in lowedges if u in ss and v in ss)
        low_comp_stats.append({'size':len(cc),'edges':m,'cycle_rank':m-len(cc)+1,'qnodes':cc})
    report={
        'upstream_sha':UPSTREAM_SHA,
        'quotient_vertices':n,'quotient_edges':len(qe),'critical_graph_edges_with_217_490':len(G),
        'p_qnodes':[p,q], 'p_component':comps[roots[p]], 'q_component':comps[roots[q]],
        'p_q_distance_in_Q':d,'one_shortest_path_qnodes':path,
        'p_q_vertex_connectivity_in_Q':conn,
        'degree_min':min(deg),'degree_max':max(deg),'degree_histogram':dict(sorted(Counter(deg).items())),
        'p_degree_in_G':deg[p],'q_degree_in_G':deg[q],
        'articulation_points_count':len(arts),'articulation_points':arts,
        'two_vertex_cuts_count':len(cuts),'two_vertex_cuts_smallest_sides':[
            {'cut':[u,v],'component_sizes':sz} for u,v,sz in cuts_sorted[:50]],
        'five_colorable_G':whole,
        'vertex_deletion_all_5_colorable': bool(vd) and all(vd),
        'vertex_deletion_failures':[i for i,x in enumerate(vd) if not x],
        'degree5_vertices_count':len(low),
        'degree5_induced_edges':len(lowedges),
        'degree5_component_stats':sorted(low_comp_stats,key=lambda x:-x['size']),
        'interpretation':'G=Q+(217,490). whole=False means G is not 5-colorable; all vertex deletions SAT verifies vertex-criticality.'
    }
    args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:report[k] for k in ['quotient_vertices','quotient_edges','critical_graph_edges_with_217_490','p_q_distance_in_Q','p_q_vertex_connectivity_in_Q','degree_min','degree_max','articulation_points_count','two_vertex_cuts_count','five_colorable_G','vertex_deletion_all_5_colorable','degree5_vertices_count']},indent=2))
if __name__=='__main__': main()
