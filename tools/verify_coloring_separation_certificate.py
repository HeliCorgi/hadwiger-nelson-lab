#!/usr/bin/env python3
"""Verify a compact proper-coloring separation certificate on an exact graph.

The certificate format is base64(xz(text)), with one coloring per line and one
base-10 color digit per vertex. Verification is independent of how the witnesses
were found: each coloring is checked on every saved exact edge, then all vertex
color-signatures across the witness family must be unique.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import lzma
from pathlib import Path

from hn_exact import K2, unit_modulus
from hn_unconditional_scan import valid_coloring


def load_certificate(path: Path):
    packed=base64.b64decode(path.read_text().strip(),validate=True)
    raw=lzma.decompress(packed)
    lines=[x.strip() for x in raw.decode('ascii').splitlines() if x.strip()]
    return packed,raw,lines


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--graph',type=Path,required=True)
    ap.add_argument('--certificate',type=Path,required=True)
    ap.add_argument('--expected-witnesses',type=int)
    ap.add_argument('--expected-graph-sha256')
    ap.add_argument('--expected-certificate-raw-sha256')
    ap.add_argument('--expected-certificate-xz-sha256')
    a=ap.parse_args()

    graph_bytes=a.graph.read_bytes()
    graph_sha=hashlib.sha256(graph_bytes).hexdigest()
    if a.expected_graph_sha256:
        assert graph_sha==a.expected_graph_sha256,(graph_sha,a.expected_graph_sha256)
    d=json.loads(graph_bytes)
    pts=[K2(p['a'],p['b'],p['den']) for p in d['pts']]
    edges=sorted({tuple(map(int,e)) for e in d['edges']}); n=len(pts)
    assert len(set(pts))==n
    assert all(unit_modulus(pts[u]-pts[v]) for u,v in edges)

    packed,raw,lines=load_certificate(a.certificate)
    raw_sha=hashlib.sha256(raw).hexdigest()
    packed_sha=hashlib.sha256(packed).hexdigest()
    if a.expected_certificate_raw_sha256:
        assert raw_sha==a.expected_certificate_raw_sha256,(raw_sha,a.expected_certificate_raw_sha256)
    if a.expected_certificate_xz_sha256:
        assert packed_sha==a.expected_certificate_xz_sha256,(packed_sha,a.expected_certificate_xz_sha256)
    if a.expected_witnesses is not None:
        assert len(lines)==a.expected_witnesses,(len(lines),a.expected_witnesses)

    models=[]
    for i,line in enumerate(lines):
        assert len(line)==n,(i,len(line),n)
        assert all(ch in '01234' for ch in line),i
        c=[ord(ch)-48 for ch in line]
        assert valid_coloring(c,n,edges),f'invalid coloring {i}'
        models.append(c)

    sigs=[bytes(c[v] for c in models) for v in range(n)]
    assert len(set(sigs))==n,'certificate does not separate every distinct vertex pair'

    out={
        'status':'VERIFIED_PAIR_SEPARATION_CERTIFICATE',
        'classification':'D_FOR_B',
        'vertices':n,
        'edges':len(edges),
        'witnesses':len(models),
        'distinct_vertex_signatures':len(set(sigs)),
        'remaining_unseparated_pairs':0,
        'graph_sha256':graph_sha,
        'certificate_raw_sha256':raw_sha,
        'certificate_xz_sha256':packed_sha,
        'all_colorings_validated_on_all_edges':True,
    }
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
