#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from collections import deque
from itertools import combinations
from pathlib import Path
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
class Dinic:
 def __init__(self,n):self.g=[[] for _ in range(n)]
 def add(self,u,v,c):
  a=[v,c,None];b=[u,0,a];a[2]=b;self.g[u].append(a);self.g[v].append(b)
 def flow(self,s,t):
  ans=0;INF=10**9
  while True:
   lev=[-1]*len(self.g);lev[s]=0;dq=deque([s])
   while dq:
    u=dq.popleft()
    for e in self.g[u]:
     if e[1]>0 and lev[e[0]]<0:lev[e[0]]=lev[u]+1;dq.append(e[0])
   if lev[t]<0:return ans
   it=[0]*len(self.g)
   def dfs(u,f):
    if u==t:return f
    while it[u]<len(self.g[u]):
     e=self.g[u][it[u]]
     if e[1]>0 and lev[e[0]]==lev[u]+1:
      z=dfs(e[0],min(f,e[1]))
      if z:e[1]-=z;e[2][1]+=z;return z
     it[u]+=1
    return 0
   while True:
    z=dfs(s,INF)
    if not z:break
    ans+=z
 def reachable(self,s):
  seen={s};dq=deque([s])
  while dq:
   u=dq.popleft()
   for e in self.g[u]:
    if e[1]>0 and e[0] not in seen:seen.add(e[0]);dq.append(e[0])
  return seen
def min_vertex_cut(n,E,p,q):
 INF=n+5;D=Dinic(2*n)
 for v in range(n):D.add(2*v,2*v+1,INF if v in (p,q) else 1)
 for u,v in E:D.add(2*u+1,2*v,INF);D.add(2*v+1,2*u,INF)
 val=D.flow(2*p+1,2*q);reach=D.reachable(2*p+1);cut=sorted(v for v in range(n) if v not in (p,q) and 2*v in reach and 2*v+1 not in reach)
 return val,cut
def components_without(n,E,cut):
 adj=[set() for _ in range(n)]
 for u,v in E:adj[u].add(v);adj[v].add(u)
 rem=set(cut);seen=set(rem);out=[]
 for s in range(n):
  if s in seen:continue
  st=[s];seen.add(s);cc=[]
  while st:
   u=st.pop();cc.append(u)
   for v in adj[u]:
    if v not in seen and v not in rem:seen.add(v);st.append(v)
  out.append(sorted(cc))
 return out
def rgs(n,maxb=5):
 a=[0]*n
 def rec(i,m):
  if i==n:yield tuple(a);return
  for x in range(min(m+1,maxb-1)+1):a[i]=x;yield from rec(i+1,max(m,x))
 yield from rec(1,0)
def bag_solver(nodes,E):
 ns=sorted(nodes);idx={v:i for i,v in enumerate(ns)};cls=[]
 def X(v,c):return idx[v]*K+c+1
 for v in ns:
  cls.append([X(v,c) for c in range(K)])
  for a,b in combinations(range(K),2):cls.append([-X(v,a),-X(v,b)])
 for u,v in E:
  if u in idx and v in idx:
   for c in range(K):cls.append([-X(u,c),-X(v,c)])
 return Cadical195(bootstrap_with=cls),X
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--data-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();C,R,vq,E=build(a.data_dir);n=len(R);p,q=vq[P],vq[Q];val,S=min_vertex_cut(n,E,p,q);cc=components_without(n,E,S);pc=next(x for x in cc if p in x);qc=next(x for x in cc if q in x);other=[x for x in cc if x is not pc and x is not qc]
 if len(S)!=val:raise RuntimeError((val,S))
 # One bag per component plus boundary; bag colorability factors exactly over the cut.
 bags=[]
 for comp in cc:
  solver,X=bag_solver(set(comp)|set(S),E);bags.append((comp,solver,X))
 rows=[]
 try:
  for st in rgs(len(S)):
   # Boundary must itself be proper in every bag; test all detached components too.
   base_by=[];ok=True
   for comp,sol,X in bags:
    ass=[X(v,st[i]) for i,v in enumerate(S)]
    if not sol.solve(assumptions=ass):ok=False;break
    base_by.append(ass)
   if not ok:continue
   pbag=next((z for z in bags if p in z[0]),None);qbag=next((z for z in bags if q in z[0]),None)
   pcols=[c for c in range(K) if pbag[1].solve(assumptions=[pbag[2](v,st[i]) for i,v in enumerate(S)]+[pbag[2](p,c)])]
   qcols=[c for c in range(K) if qbag[1].solve(assumptions=[qbag[2](v,st[i]) for i,v in enumerate(S)]+[qbag[2](q,c)])]
   rows.append({'boundary_state':''.join(map(str,st)),'blocks':max(st)+1,'p_colors':pcols,'q_colors':qcols,'all_cross_pairs_equal':all(x==y for x in pcols for y in qcols)})
 finally:
  for _,s,_ in bags:s.delete()
 bad=[r for r in rows if not r['all_cross_pairs_equal']]
 rep={'upstream_sha':UPSTREAM_SHA,'quotient_vertices':n,'quotient_edges':len(E),'p_qnodes':[p,q],'min_vertex_cut_value':val,'separator_qnodes':S,'separator_components':[C[R[x]] for x in S],'components_after_cut_sizes':sorted([len(x) for x in cc]),'p_component_size':len(pc),'q_component_size':len(qc),'other_component_sizes':sorted(map(len,other)),'viable_boundary_state_count':len(rows),'states':rows,'all_viable_states_force_p_eq_q':not bad,'bad_states':bad,'singleton_same_color_states':sum(len(r['p_colors'])==len(r['q_colors'])==1 and r['p_colors']==r['q_colors'] for r in rows),'interpretation':'Removing the six separator qnodes disconnects p from q. For each canonical color partition of the separator, component colorings are independent. Thus p/q option sets can be combined by Cartesian product; if every viable boundary state has only equal cross-pairs, p=q follows from the boundary table.'}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(rep,indent=2));print(json.dumps({k:rep[k] for k in ['min_vertex_cut_value','separator_qnodes','components_after_cut_sizes','p_component_size','q_component_size','viable_boundary_state_count','all_viable_states_force_p_eq_q','singleton_same_color_states']},indent=2))
if __name__=='__main__':main()
