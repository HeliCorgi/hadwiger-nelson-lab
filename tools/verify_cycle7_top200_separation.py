#!/usr/bin/env python3
import argparse, hashlib, json
from collections import Counter
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--certificate',type=Path,required=True)
    args=ap.parse_args()
    raw=args.graph.read_bytes(); graph=json.loads(raw)
    cert=json.loads(args.certificate.read_text())
    gsha=hashlib.sha256(raw).hexdigest()
    assert cert['graph_sha256']==gsha
    n=len(graph['pts']); edges=[tuple(map(int,e)) for e in graph['edges']]
    assert cert['vertices']==n and cert['edges']==len(edges) and cert['colors']==5
    colors=[]
    for s in cert['colorings']:
        assert len(s)==n and set(s)<=set('01234')
        c=[ord(ch)-48 for ch in s]
        assert all(c[u]!=c[v] for u,v in edges)
        colors.append(c)
    sigs=[bytes(c[v] for c in colors) for v in range(n)]
    counts=Counter(sigs)
    remaining=sum(k*(k-1)//2 for k in counts.values())
    out={'status':'NO_FORCED_EQUAL_PAIR' if remaining==0 else 'UNRESOLVED','graph_sha256':gsha,'vertices':n,'edges':len(edges),'colorings':len(colors),'all_colorings_proper':True,'distinct_signatures':len(counts),'remaining_unseparated_pairs':remaining,'all_pairs_separated':remaining==0,'certificate_sha256':hashlib.sha256(args.certificate.read_bytes()).hexdigest()}
    print(json.dumps(out,indent=2))
    if remaining: raise SystemExit(2)

if __name__=='__main__': main()
