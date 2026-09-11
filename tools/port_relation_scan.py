#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from collections import deque
from pathlib import Path
from itertools import combinations
from pysat.solvers import Cadical195
K=5;P,Q=217,490
UPSTREAM_SHA='d1e80998bda337d9fa721f2e96d203ae54e97fc8'
def load(p):return json.loads(Path(p).read_text())
def build(d):
 g=load(d/'g510_k2.json');full=[tuple(map(int,e)) for e in g['edges']];raw=load(d/'B5_MULTICORE.json')['cores'][0];h=[full[i] for i in raw] if raw and isinstance(raw[0],int) else [tuple(map(int,e)) for e in raw];c=[tuple(map(int,e)) for e in load(d/'B5_P2_LEMMA.json')['C_min']];E=sorted({(min(a,b),max(a,b)) for a,b in h});V=sorted({x for e in E for x in e}|{x for e in c for x in e});par={v:v for v in V}
 def f(x):
  while par[x]!=x:par[x]=par[par[x]];x=par[x]
  return x
 def u(a,b):
  a,b=f(a),f(b)
  if a!=b:
   if a>b:a,b=b,a
   par[b]=a
 for a,b in c:u(a,b)
 C={}
 for v in V:C.setdefault(f(v),[]).append(v)
 R=sorted(C,key=lambda r:min(C[r]));qid={r:i for i,r in enumerate(R)};vq={v:qid[f(v)] for v in V};QE=set()
 for a,b in E:
  x,y=vq[a],vq[b]
  if x==y:raise RuntimeError('internal edge')
  QE.add((min(x,y),max(x,y)))
 return C,R,vq,sorted(QE)
def cnf(n,E):
 def x(v,c):return v*K+c+1
 out=[]
 for v in range(n):
  out.append([x(v,c) for c in range(K)])
  for a,b in combinations(range(K),2):out.append([-x(v,a),-x(v,b)])
 for u,v in E:
  for c in range(K):out.append([-x(u,c),-x(v,c)])
 return out
def dist(adj,s):
 d=[None]*len(adj);d[s]=0;q=deque([s])
 while q:
  u=q.popleft()
  for v in adj[u]:
   if d[v] is None:d[v]=d[u]+1;q.append(v)
 return d
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--data-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();C,R,vq,E=build(a.data_dir);n=len(R);p,q=vq[P],vq[Q];adj=[set() for _ in range(n)]
 for u,v in E:adj[u].add(v);adj[v].add(u)
 dp=dist(adj,p);dq=dist(adj,q);base=cnf(n,E);p0=p*K+1
 eq=[];diff=[];flex=[]
 with Cadical195(bootstrap_with=base+[[p0]]) as s:
  for v in range(n):
   if v==p:eq.append(v);continue
   v0=v*K+1
   can_diff=s.solve(assumptions=[-v0])
   can_same=s.solve(assumptions=[v0])
   if not can_diff and can_same:eq.append(v)
   elif can_diff and not can_same:diff.append(v)
   elif can_diff and can_same:flex.append(v)
   else:raise RuntimeError(f'inconsistent relation v={v}')
 eqset=set(eq);boundary=sorted({w for v in eq for w in adj[v] if w not in eqset})
 report={'upstream_sha':UPSTREAM_SHA,'quotient_vertices':n,'quotient_edges':len(E),'p_qnodes':[p,q],'forced_equal_to_p_count':len(eq),'forced_equal_to_p':[{'qnode':v,'component':C[R[v]],'dist_p':dp[v],'dist_q':dq[v],'degree':len(adj[v])} for v in eq],'forced_different_from_p_count':len(diff),'flexible_vs_p_count':len(flex),'forced_different_qnodes':diff,'flexible_qnodes':flex,'equal_class_boundary_count':len(boundary),'equal_class_boundary':[{'qnode':v,'component':C[R[v]],'neighbors_in_equal_class':sorted(adj[v]&eqset),'degree':len(adj[v])} for v in boundary],'equal_class_induced_edges':[[u,v] for u,v in E if u in eqset and v in eqset],'q_is_forced_equal':q in eqset}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['forced_equal_to_p_count','forced_different_from_p_count','flexible_vs_p_count','equal_class_boundary_count','q_is_forced_equal']},indent=2));print('equal qnodes',eq)
if __name__=='__main__':main()
