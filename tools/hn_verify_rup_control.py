#!/usr/bin/env python3
"""Small independent RUP checker for the saved K6 calibration proof.

This intentionally checks the RUP subset of DRAT, not arbitrary RAT proofs.
No SAT library or repository coloring implementation is imported.
"""
import argparse,hashlib,json
from pathlib import Path


def conflict(clauses,assumptions):
    values={}
    def assign(lit):
        var=abs(lit);value=lit>0
        if var in values:return values[var]==value
        values[var]=value;return True
    if not all(assign(lit) for lit in assumptions):return True
    while True:
        changed=False
        for c in clauses:
            if any(values.get(abs(l))==(l>0) for l in c if abs(l) in values):continue
            free=[l for l in c if abs(l) not in values]
            if not free:return True
            if len(free)==1:
                if not assign(free[0]):return True
                changed=True
        if not changed:return False


def check(cnf,proof):
    raw=cnf.read_bytes();trace=proof.read_bytes();clauses=[];nv=nc=None
    def clause(tokens):
        v=list(map(int,tokens));assert v and v[-1]==0 and 0 not in v[:-1]
        assert all(abs(l)<=nv for l in v[:-1]);return tuple(sorted(set(v[:-1])))
    for line in raw.decode().splitlines():
        if not line or line.startswith('c'):continue
        if line.startswith('p'):
            _,kind,v,c=line.split();assert kind=='cnf';nv,nc=int(v),int(c);continue
        assert nv is not None;clauses.append(clause(line.split()))
    assert len(clauses)==nc
    added=deleted=0;empty=False
    for line in trace.decode().splitlines():
        if not line or line.startswith('c'):continue
        words=line.split()
        if words[0]=='d':
            c=clause(words[1:])
            if c in clauses:clauses.remove(c)
            deleted+=1;continue
        c=clause(words);assert conflict(clauses,[-l for l in c]),'non-RUP lemma'
        clauses.append(c);added+=1;empty|=len(c)==0
    assert empty,'no verified empty clause: not an UNSAT certificate'
    return {'status':'VERIFIED_RUP','added_lemmas':added,'deletions':deleted,
        'cnf_sha256':hashlib.sha256(raw).hexdigest(),'proof_sha256':hashlib.sha256(trace).hexdigest(),
        'scope':'Only this supplied CNF and this RUP trace; K6 control is not a planar unit-distance witness.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cnf',type=Path,required=True)
    p.add_argument('--proof',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=check(a.cnf,a.proof);a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))

if __name__=='__main__':main()
