#!/usr/bin/env python3
"""Bounded graph-color probes, with explicit terminal scope and proof checking.

All extra conditions are hard clauses in the saved DIMACS file. Pair tests use
only the sound global color renaming u=0,v=0 or u=0,v=1, never an additional
triangle pin. Ordinary tests pin a real triangle if present. Geometry must have
been certified by the producing tool; this tool independently checks the model
against every supplied edge and every terminal pin. UNKNOWN is non-evidence.
"""
from __future__ import annotations
import argparse, hashlib, json, multiprocessing, os, signal, subprocess, traceback
from itertools import combinations
from pathlib import Path
from time import monotonic


def write(path,data):
    path=Path(path); tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,indent=2)+'\n'); tmp.replace(path)


def color_cnf(n,edges,k):
    if k<1: raise ValueError('bad color count')
    cs=[]
    for v in range(n):
        xs=[v*k+c+1 for c in range(k)]; cs.append(xs)
        cs.extend([[-a,-b] for a,b in combinations(xs,2)])
    for u,v in edges:
        cs.extend([[-(u*k+c+1),-(v*k+c+1)] for c in range(k)])
    return cs


def validated_model(model,n,edges,k,pins):
    positive={x for x in model if x>0}; colors=[]
    for v in range(n):
        got=[c for c in range(k) if v*k+c+1 in positive]
        if len(got)!=1: raise AssertionError('model is not one-hot')
        colors.append(got[0])
    if any(colors[u]==colors[v] for u,v in edges): raise AssertionError('invalid coloring')
    if any(colors[v]!=c for v,c in pins): raise AssertionError('terminal pin not satisfied')
    return colors


def worker(graph_path,k,pins,solver_name,out,checker):
    os.setsid(); out=Path(out); start=monotonic()
    try:
        from pysat.solvers import Solver
        raw=Path(graph_path).read_bytes(); g=json.loads(raw); n=len(g['pts'])
        edges=[tuple(e) for e in g['edges']]
        assert len(set(edges))==len(edges)
        assert all(0<=u<v<n for u,v in edges)
        assert all(0<=v<n and 0<=c<k for v,c in pins)
        clauses=color_cnf(n,edges,k)+[[v*k+c+1] for v,c in pins]
        cnf='p cnf %d %d\n'%(n*k,len(clauses))+''.join(' '.join(map(str,c))+' 0\n' for c in clauses)
        (out/'INPUT.cnf').write_text(cnf)
        base={'vertices':n,'edges':len(edges),'colors':k,'pins':pins,'solver':solver_name,
              'graph_file_sha256':hashlib.sha256(raw).hexdigest(),
              'cnf_sha256':hashlib.sha256(cnf.encode()).hexdigest(),
              'scope':'Exactly this graph, color count, and explicitly recorded terminal pins.'}
        write(out/'RESULT.json',dict(base,status='RUNNING',classification=None))
        with Solver(name=solver_name,bootstrap_with=clauses,with_proof=True) as s:
            ans=s.solve()
            if ans is True:
                colors=validated_model(s.get_model(),n,edges,k,pins)
                (out/'COLORING.txt').write_text(''.join(map(str,colors))+'\n')
                write(out/'RESULT.json',dict(base,status='SAT',all_edges_and_pins_validated=True,
                      elapsed_seconds=round(monotonic()-start,3)))
                return
            if ans is None:
                write(out/'RESULT.json',dict(base,status='UNKNOWN',classification=None)); return
            proof=s.get_proof()
        if proof is None: raise RuntimeError('solver returned UNSAT without a proof')
        (out/'PROOF.drat').write_text('\n'.join(proof)+'\n')
        result=dict(base,status='UNSAT_UNCHECKED',proof_lines=len(proof),
                    proof_sha256=hashlib.sha256((out/'PROOF.drat').read_bytes()).hexdigest())
        write(out/'RESULT.json',result)
        if checker:
            check=subprocess.run([str(Path(checker).resolve()),str(out/'INPUT.cnf'),str(out/'PROOF.drat')],
                                 capture_output=True,text=True,timeout=120)
            log=check.stdout+'\n'+check.stderr; (out/'CHECKER.txt').write_text(log)
            result['checker_returncode']=check.returncode
            if check.returncode==0 and any(line.strip()=='s VERIFIED' for line in log.splitlines()):
                result['status']='UNSAT_PROOF_VERIFIED'
            else:
                result['status']='PROOF_CHECK_FAILED'
        result['elapsed_seconds']=round(monotonic()-start,3)
        write(out/'RESULT.json',result)
    except BaseException:
        (out/'ERROR.txt').write_text(traceback.format_exc())
        write(out/'RESULT.json',{'status':'ERROR','classification':None,'error':traceback.format_exc()})


def run_case(graph,k,pins,solver,out,seconds,checker=None):
    out=Path(out).resolve(); out.mkdir(parents=True,exist_ok=True)
    p=multiprocessing.get_context('fork').Process(target=worker,
        args=(str(Path(graph).resolve()),k,pins,solver,str(out),checker))
    p.start(); p.join(seconds)
    if p.is_alive():
        try: os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError: p.kill()
        p.join()
        write(out/'RESULT.json',{'status':'UNKNOWN_TIMEOUT','classification':None,
              'colors':k,'pins':pins,'solver':solver,'wall_seconds':seconds,
              'timeout_is_evidence':False})
    path=out/'RESULT.json'
    if not path.exists():
        write(path,{'status':'ERROR_NO_RESULT','exitcode':p.exitcode,'classification':None})
    return json.loads(path.read_text())


def select_pins(g,k,relation,ports):
    if relation in ('equal','different'):
        vs=[g['ports'][name] for name in ports.split(',')]
        if len(vs)!=2 or vs[0]==vs[1]: raise ValueError('two distinct ports required')
        return [(vs[0],0),(vs[1],0 if relation=='equal' else 1)]
    adj=[set() for _ in g['pts']]
    for u,v in g['edges']: adj[u].add(v); adj[v].add(u)
    if k>=3:
        for u,v in g['edges']:
            common=adj[u]&adj[v]
            if common: return [(u,0),(v,1),(min(common),2)]
    return [(0,0)] if adj else []


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--colors',type=int,required=True); ap.add_argument('--solver',default='cadical195')
    ap.add_argument('--relation',choices=['ordinary','equal','different'],default='ordinary')
    ap.add_argument('--ports',default=''); ap.add_argument('--seconds',type=int,default=600)
    ap.add_argument('--out-dir',type=Path,required=True); ap.add_argument('--proof-checker',default=None)
    a=ap.parse_args(); g=json.loads(a.graph.read_text()); pins=select_pins(g,a.colors,a.relation,a.ports)
    r=run_case(a.graph,a.colors,pins,a.solver,a.out_dir,a.seconds,a.proof_checker)
    print(json.dumps(r,indent=2))

if __name__=='__main__': main()
