#!/usr/bin/env python3
from __future__ import annotations

import argparse, json
from collections import Counter, deque
from itertools import combinations, permutations
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
    edges=sorted({(min(a,b),max(a,b)) for a,b in h}); verts=sorted({x for e in edges for x in e}|{x for e in c88 for x in e})
    par={v:v for v in verts}
    def find(x):
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:
            if a>b:a,b=b,a
            par[b]=a
    for a,b in c88:union(a,b)
    comps={}
    for v in verts:comps.setdefault(find(v),[]).append(v)
    roots=sorted(comps,key=lambda r:min(comps[r])); qid={r:i for i,r in enumerate(roots)}; vq={v:qid[find(v)] for v in verts}
    qe=set()
    for a,b in edges:
        u,v=vq[a],vq[b]
        if u==v:raise RuntimeError('internal quotient edge')
        qe.add((min(u,v),max(u,v)))
    return comps,roots,vq,sorted(qe)

def coloring_cnf(n,edges):
    def x(v,c):return v*K+c+1
    cls=[]
    for v in range(n):
        cls.append([x(v,c) for c in range(K)])
        for a,b in combinations(range(K),2):cls.append([-x(v,a),-x(v,b)])
    for u,v in edges:
        for c in range(K):cls.append([-x(u,c),-x(v,c)])
    return cls

def decode(model,n):
    pos={x for x in model if x>0}; out=[]
    for v in range(n):
        cs=[c for c in range(K) if v*K+c+1 in pos]
        if len(cs)!=1:raise RuntimeError('bad color model')
        out.append(cs[0])
    return out

def shortest_bichromatic(adj,colors,p,q,a,b):
    allowed={a,b}; prev={p:None}; dq=deque([p])
    while dq:
        u=dq.popleft()
        if u==q:break
        for v in adj[u]:
            if colors[v] in allowed and v not in prev:
                prev[v]=u;dq.append(v)
    if q not in prev:return None
    path=[];x=q
    while x is not None:path.append(x);x=prev[x]
    return list(reversed(path))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--models',type=int,default=300);args=ap.parse_args()
    comps,roots,vq,edges=build(args.data_dir);n=len(roots);p,q=vq[P],vq[Q]
    adj=[set() for _ in range(n)]
    for u,v in edges:adj[u].add(v);adj[v].add(u)
    cls=coloring_cnf(n,edges)
    # Symmetry break: p has canonical color 0. Critical-edge property should force q=0.
    cls.append([p*K+1])
    path_len=Counter(); edge_use=Counter(); vertex_use=Counter(); channel_records=[]; models=0
    with Cadical195(bootstrap_with=cls) as s:
        while models<args.models and s.solve():
            col=decode(s.get_model(),n)
            if col[p]!=0 or col[q]!=0:raise RuntimeError('found p != q coloring; forcing broken')
            one=[]
            for c in range(1,K):
                path=shortest_bichromatic(adj,col,p,q,0,c)
                if path is None:raise RuntimeError(f'missing Kempe chain color {c}')
                path_len[len(path)-1]+=1
                for v in path:vertex_use[v]+=1
                for u,v in zip(path,path[1:]):edge_use[(min(u,v),max(u,v))]+=1
                one.append({'color':c,'length':len(path)-1,'qnodes':path})
            if models<20:channel_records.append(one)
            # Block the whole orbit under permutations of the four nonzero colors.
            for perm in permutations(range(1,K)):
                mp={0:0,1:perm[0],2:perm[1],3:perm[2],4:perm[3]}
                s.add_clause([-(v*K+mp[col[v]]+1) for v in range(n)])
            models+=1
    denom=max(1,models*4)
    report={
        'upstream_sha':UPSTREAM_SHA,'quotient_vertices':n,'quotient_edges':len(edges),'p_qnodes':[p,q],
        'sampled_color_partitions':models,'kempe_channels_checked':models*4,
        'path_length_histogram':dict(sorted(path_len.items())),
        'top_path_vertices':[{'qnode':v,'component':comps[roots[v]],'count':c,'fraction':c/denom} for v,c in vertex_use.most_common(40)],
        'top_path_edges':[{'edge':[u,v],'count':c,'fraction':c/denom} for (u,v),c in edge_use.most_common(60)],
        'first_models_channels':channel_records,
        'all_channels_found':True,
        'interpretation':'For every sampled 5-coloring of Q with p=q=0, each other color has a bichromatic p-q Kempe path. This is required abstractly by criticality; frequency data probes for a stable structural backbone.'
    }
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2))
    print(json.dumps({'sampled_color_partitions':models,'kempe_channels_checked':models*4,'path_length_histogram':report['path_length_histogram'],'top_path_vertices':report['top_path_vertices'][:10]},indent=2))
if __name__=='__main__':main()
