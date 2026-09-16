#!/usr/bin/env python3
"""Fail-closed color probes with independently checked positive witnesses.

The historical filename is retained for imports. Two K6 controls showed that
CaDiCaL195 proof extraction was incomplete, including after descriptor copying
and solver destruction. That attempted fix did NOT repair the trace. Therefore
CaDiCaL is now a witness finder only: its UNSAT is always UNSAT_UNCHECKED.
Glucose4 negatives require strict drat-trim verification. No empty clause is
invented, and a failed proof check is never waived for a mathematical claim.
This module does not modify the historical hn_certified_color_probe.py.
"""
from __future__ import annotations
import hashlib,json,multiprocessing,os,signal,subprocess,traceback
from pathlib import Path
from time import monotonic
from hn_certified_color_probe import color_cnf,validated_model,write


def worker(graph_path,k,pins,solver_name,out,checker):
    os.setsid();out=Path(out);start=monotonic()
    try:
        from pysat.solvers import Solver
        raw=Path(graph_path).read_bytes();g=json.loads(raw);n=len(g['pts'])
        edges=[tuple(e) for e in g['edges']]
        assert len(set(edges))==len(edges) and all(0<=u<v<n for u,v in edges)
        assert all(0<=v<n and 0<=c<k for v,c in pins)
        clauses=color_cnf(n,edges,k)+[[v*k+c+1] for v,c in pins]
        cnf='p cnf %d %d\n'%(n*k,len(clauses))+''.join(' '.join(map(str,c))+' 0\n' for c in clauses)
        (out/'INPUT.cnf').write_text(cnf)
        proof_enabled=solver_name=='glucose4'
        base={'vertices':n,'edges':len(edges),'colors':k,'pins':pins,'solver':solver_name,
            'proof_enabled':proof_enabled,'graph_file_sha256':hashlib.sha256(raw).hexdigest(),
            'cnf_sha256':hashlib.sha256(cnf.encode()).hexdigest(),
            'scope':'Only this exact graph, color count and these hard terminal pins.'}
        write(out/'RESULT.json',dict(base,status='RUNNING'))
        with Solver(name=solver_name,bootstrap_with=clauses,with_proof=proof_enabled) as s:
            ans=s.solve()
            if ans is True:
                colors=validated_model(s.get_model(),n,edges,k,pins)
                text=''.join(map(str,colors))+'\n';(out/'COLORING.txt').write_text(text)
                write(out/'RESULT.json',dict(base,status='SAT',all_edges_and_pins_validated=True,
                    coloring_sha256=hashlib.sha256(text.encode()).hexdigest(),elapsed_seconds=round(monotonic()-start,3)))
                return
            if ans is None:
                write(out/'RESULT.json',dict(base,status='UNKNOWN'));return
            if not proof_enabled:
                write(out/'RESULT.json',dict(base,status='UNSAT_UNCHECKED',classification=None,
                    reason='This solver is used only for directly validated SAT witnesses; no negative claim accepted.',
                    elapsed_seconds=round(monotonic()-start,3)))
                return
            proof=s.get_proof()
        if proof is None:raise RuntimeError('UNSAT without proof')
        text='\n'.join(proof)+'\n';(out/'PROOF.drat').write_text(text)
        result=dict(base,status='UNSAT_UNCHECKED',proof_lines=len(proof),
            proof_sha256=hashlib.sha256(text.encode()).hexdigest())
        write(out/'RESULT.json',result)
        if checker:
            check=subprocess.run([str(Path(checker).resolve()),str(out/'INPUT.cnf'),str(out/'PROOF.drat')],
                capture_output=True,text=True,timeout=120)
            log=check.stdout+'\n'+check.stderr;(out/'CHECKER.txt').write_text(log)
            result['checker_returncode']=check.returncode
            result['status']='UNSAT_PROOF_VERIFIED' if check.returncode==0 and any(
                line.strip()=='s VERIFIED' for line in log.splitlines()) else 'PROOF_CHECK_FAILED'
        result['elapsed_seconds']=round(monotonic()-start,3);write(out/'RESULT.json',result)
    except BaseException:
        error=traceback.format_exc();(out/'ERROR.txt').write_text(error)
        write(out/'RESULT.json',{'status':'ERROR','classification':None,'error':error})


def run_case(graph,k,pins,solver,out,seconds,checker=None):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    p=multiprocessing.get_context('fork').Process(target=worker,
        args=(str(Path(graph).resolve()),k,pins,solver,str(out),checker))
    p.start();p.join(seconds)
    if p.is_alive():
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:p.kill()
        p.join();write(out/'RESULT.json',{'status':'UNKNOWN_TIMEOUT','classification':None,
            'colors':k,'pins':pins,'solver':solver,'wall_seconds':seconds,'timeout_is_evidence':False})
    path=out/'RESULT.json'
    if not path.exists():write(path,{'status':'ERROR_NO_RESULT','exitcode':p.exitcode})
    return json.loads(path.read_text())
