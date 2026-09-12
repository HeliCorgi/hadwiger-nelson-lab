#!/usr/bin/env python3
import argparse, hashlib, json, lzma
from collections import Counter
from pathlib import Path


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph-xz',type=Path,required=True)
    ap.add_argument('--witnesses',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    raw=lzma.decompress(args.graph_xz.read_bytes())
    graph=json.loads(raw)
    gsha=hashlib.sha256(raw).hexdigest()
    n=len(graph['pts']); edges=[tuple(map(int,e)) for e in graph['edges']]
    wraw=args.witnesses.read_bytes()
    if args.witnesses.suffix == '.xz': wraw=lzma.decompress(wraw)
    W=json.loads(wraw)
    assert W['graph_sha256']==gsha
    assert W['vertices']==n and W['edges']==len(edges) and W['colors']==5
    colors=[]
    for s in W['colorings']:
        assert len(s)==n and set(s)<=set('01234')
        c=[ord(ch)-48 for ch in s]
        assert all(c[u]!=c[v] for u,v in edges)
        colors.append(c)
    sigs=[tuple(c[v] for c in colors) for v in range(n)]
    counts=Counter(sigs)
    dup=sum(k*(k-1)//2 for k in counts.values())
    out={
        'status':'NO_FORCED_EQUAL_PAIR' if dup==0 else 'UNRESOLVED',
        'graph_sha256':gsha,
        'vertices':n,
        'edges':len(edges),
        'colorings':len(colors),
        'all_colorings_proper':True,
        'distinct_signatures':len(counts),
        'remaining_unseparated_pairs':dup,
        'all_pairs_separated':dup==0,
        'witness_bundle_sha256':hashlib.sha256(wraw).hexdigest(),
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
