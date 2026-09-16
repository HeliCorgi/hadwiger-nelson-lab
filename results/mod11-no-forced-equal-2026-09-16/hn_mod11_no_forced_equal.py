#!/usr/bin/env python3
"""Check a no-forced-equal-pair obstruction for graphs mapping to Gamma(F_11^2).

No SAT solver, floating point, external package, or network is used.
The theorem, including the full-field lifting argument, is in PROOF_ja.md.

The TABLE is Madore, arXiv:1509.07023, Lemma 4.5, p.12.  The optional
old-K2 input decoder follows the independently auditable basis convention of
HeliCorgi/hadwiger-nelson-lab/tools/hn_mod11_barrier.py at commit
3a1e42eab803cb17c49fd7c5cd4410e4feca8350. It explicitly rejects larger fields
and denominators divisible by 11. The full-field theorem is NOT a claim that
a field homomorphism E -> F_11 exists.

Examples:
  python hn_mod11_no_forced_equal.py --out-dir output
  python hn_mod11_no_forced_equal.py --graph gen2-source.zip --out-dir output
  python hn_mod11_no_forced_equal.py --graph GRAPH.json --pair 10 200 --out-dir output

--graph accepts the repository's old K2 JSON (or ZIP containing GRAPH.json).
A supplied edge list is checked exactly; the symbolic ring-map argument also
protects true unit edges that were omitted from that list.
"""
from __future__ import annotations
import argparse
from collections import Counter
from itertools import combinations, product
import hashlib
import json
from math import gcd
from pathlib import Path
from time import perf_counter
import zipfile

TABLE = (
    (3,1,0,2,1,2,3,4,2,0,1),
    (1,2,1,0,4,1,2,3,4,3,2),
    (2,1,2,3,0,2,1,2,3,4,0),
    (0,2,3,1,3,4,0,4,1,3,4),
    (4,0,1,2,1,3,4,0,2,1,2),
    (3,4,0,1,2,1,3,4,1,2,1),
    (1,2,3,4,0,3,1,0,4,0,2),
    (2,1,4,3,4,0,2,3,0,3,4),
    (4,2,3,4,3,4,0,2,3,4,0),
    (0,4,1,2,1,0,4,0,2,3,2),
    (4,0,4,1,2,3,0,3,0,1,3),
)
POINTS = tuple(product(range(11), repeat=2))
RAD = (1,3,5,15,11,33,55,165)
BASIS = (
    (1,-1,-1,-3), (0,0,0,-4), (0,2,0,2), (0,2,0,2),
    (0,0,0,4), (0,0,2,2), (0,0,0,0), (0,-2,0,-2),
)
RESIDUE_BASIS = (1,5,4,20,0,0,0,0)

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def add(a: tuple[int,int], b: tuple[int,int]) -> tuple[int,int]:
    return ((a[0]+b[0]) % 11, (a[1]+b[1]) % 11)

def sub(a: tuple[int,int], b: tuple[int,int]) -> tuple[int,int]:
    return ((a[0]-b[0]) % 11, (a[1]-b[1]) % 11)

def color(a: tuple[int,int]) -> int:
    return TABLE[a[0]][a[1]]

def adjacent(a: tuple[int,int], b: tuple[int,int]) -> bool:
    return ((a[0]-b[0])**2+(a[1]-b[1])**2) % 11 == 1

def check_coloring(edges, colors) -> None:
    require(all(type(c) is int and 0 <= c < 5 for c in colors), 'bad color')
    for u, v in edges:
        require(colors[u] != colors[v], f'monochromatic edge {u},{v}')

def separate(residues: list[tuple[int,int]], u: int, v: int):
    """Produce a pair-separating coloring, conditional on the given homomorphism.

    Caller must validate that all graph edges map to adjacent residue vertices.
    No geometric assumption enters this function.
    """
    require(0 <= u < len(residues) and 0 <= v < len(residues) and u != v,
            'pair must consist of two distinct valid indices')
    delta = sub(residues[v], residues[u])
    if delta == (0,0):
        shift = sub((0,0), residues[u])
        colors = [color(add(r, shift)) for r in residues]
        require(colors[u] == colors[v] == 3, 'bad flexible-vertex normalization')
        colors[u] = 2
        method = 'translate_then_recolor_one_actual_vertex'
    else:
        s = next((s for s in POINTS if color(s) != color(add(s, delta))), None)
        require(s is not None, 'nonzero period would invalidate the theorem')
        shift = sub(s, residues[u])
        colors = [color(add(r, shift)) for r in residues]
        method = 'translate_table'
    require(colors[u] != colors[v], 'pair was not separated')
    return colors, {'pair':[u,v], 'residues':[list(residues[u]),list(residues[v])],
                    'delta':list(delta), 'shift':list(shift), 'method':method,
                    'terminal_colors':[colors[u],colors[v]]}

def finite_certificate() -> dict:
    edges = [(i,j) for i,j in combinations(range(121), 2)
             if adjacent(POINTS[i], POINTS[j])]
    require(len(edges) == 726, 'unexpected finite-field edge count')
    check_coloring(edges, [color(p) for p in POINTS])
    units = [p for p in POINTS if adjacent((0,0), p)]
    neighbors = sorted({color(p) for p in units})
    require(color((0,0)) == 3 and neighbors == [0,1,4], 'bad local freedom')
    counts = dict(sorted(Counter(color(p) for p in POINTS).items()))
    require(counts[0] == 23 and counts[0] % 11 != 0, 'bad aperiodicity count')
    shifts = {}
    same_shifts = {}
    periods = []
    for d in POINTS:
        unequal = [s for s in POINTS if color(s) != color(add(s,d))]
        equal = [s for s in POINTS if color(s) == color(add(s,d))]
        if not unequal:
            periods.append(d)
        else:
            shifts[f'{d[0]},{d[1]}'] = list(unequal[0])
        if equal:
            same_shifts[f'{d[0]},{d[1]}'] = list(equal[0])
    require(periods == [(0,0)], 'unexpected translation period')
    require(len(shifts) == 120, 'missing separating shift')
    require(len(same_shifts) == 109, 'unexpected same-color displacement census')
    require(all((f'{d[0]},{d[1]}' in same_shifts) == (d not in units)
                for d in POINTS), 'extra forced inequality under translations')
    return {
        'status':'FINITE_LEMMA_VERIFIED',
        'field':'F_11', 'vertices':121, 'edges_checked':726,
        'table_class_sizes':counts,
        'flexible_vertex':[0,0], 'original_color':3, 'replacement_color':2,
        'neighbor_colors':neighbors, 'unit_displacements':[list(u) for u in units],
        'translation_periods':[list(p) for p in periods],
        'nonzero_displacements_separated':120,
        'separating_shift_for_each_nonzero_displacement':shifts,
        'same_color_shift_for_each_nonunit_displacement':same_shifts,
        'table_sha256':hashlib.sha256(json.dumps(TABLE,separators=(',',':')).encode()).hexdigest(),
        'theorem_scope':'Every loopless graph admitting a homomorphism to Gamma(F_11^2) '
                        'has, for each pair of distinct vertices, a proper at-most-five-coloring '
                        'that separates that pair. Different pairs may use different colorings.',
        'not_claimed':['six-chromatic real unit-distance graph',
                       'one coloring separating all pairs simultaneously',
                       'no forced-equal pair in arbitrary real unit-distance graphs'],
    }

def twin_lift_test() -> dict:
    # Independent finite stress test: double every residue vertex; replace each
    # finite-field edge by all four edges between its two two-element fibers.
    residues = [p for p in POINTS for _ in range(2)]
    edges = [(i,j) for i,j in combinations(range(len(residues)),2)
             if adjacent(residues[i],residues[j])]
    require(len(edges) == 2904, 'bad doubled-fiber graph')
    signatures = [[] for _ in residues]
    witness_count = 0
    def accept(colors):
        nonlocal witness_count
        check_coloring(edges,colors)
        for signature, c in zip(signatures,colors):
            signature.append(c)
        witness_count += 1
    for shift in POINTS:
        accept([color(add(p,shift)) for p in residues])
    for u in range(len(residues)):
        v = u ^ 1  # The other, distinct vertex in the same residue fiber.
        colors, _ = separate(residues,u,v)
        accept(colors)
    require(len(set(map(tuple,signatures))) == 242, 'some pair was not separated')
    return {'status':'PASS','vertices':242,'edges':len(edges),
            'proper_colorings_checked':witness_count,
            'pairs_separated_by_verified_family':242*241//2,
            'scope':'finite regression test; universal conclusion also uses the written proof'}

def all_pairs_family(residues, edges, out_dir):
    """Explicit finite family separating EVERY pair, with full edge validation.

    Colorings are stored as regeneration recipes, not huge redundant matrices.
    Greedily chosen translations separate residue classes. Binary recolorings
    of each independent residue fiber separate distinct vertices in that fiber.
    """
    groups = {}
    for i,r in enumerate(residues):
        groups.setdefault(r,[]).append(i)
    used_residues = sorted(groups)
    small_signatures = {r:() for r in used_residues}
    translation_shifts = []
    while len(set(small_signatures.values())) < len(used_residues):
        best = min(POINTS, key=lambda t: (
            sum(n*(n-1)//2 for n in Counter(
                small_signatures[r]+(color(add(r,t)),) for r in used_residues).values()),t))
        old_count = len(set(small_signatures.values()))
        small_signatures = {r:small_signatures[r]+(color(add(r,best)),) for r in used_residues}
        require(len(set(small_signatures.values())) > old_count, 'translation family stalled')
        translation_shifts.append(best)
    signatures = [bytearray() for _ in residues]
    recipes = []
    def accept(colors, recipe):
        check_coloring(edges,colors)
        for sig,c in zip(signatures,colors):
            sig.append(c)
        recipes.append(recipe)
    for t in translation_shifts:
        accept([color(add(r,t)) for r in residues], {'kind':'translation','shift':list(t)})
    for r,ids in sorted(groups.items()):
        t = sub((0,0),r)
        base = [color(add(x,t)) for x in residues]
        for bit in range((len(ids)-1).bit_length()):
            colors = base.copy()
            for rank,u in enumerate(ids):
                if (rank >> bit) & 1:
                    colors[u] = 2
            accept(colors, {'kind':'fiber_binary','residue':list(r),
                            'shift':list(t),'bit':bit,
                            'fiber_order':'increasing input vertex index'})
    require(len(set(map(bytes,signatures))) == len(residues), 'two vertices have equal signatures')
    recipe_doc = {'recipes':recipes,
        'interpretation':'Use TABLE at residue+shift. For fiber_binary, enumerate the '
        'specified residue fiber by increasing vertex index and recolor to 2 '
        'precisely when the stated bit of its zero-based rank is 1.'}
    text = json.dumps(recipe_doc,indent=2)+'\n'
    (out_dir/'ALL_PAIRS_RECIPES.json').write_text(text)
    n = len(residues)
    return {'status':'ALL_PAIRS_SEPARATED_BY_VERIFIED_COLORING_FAMILY',
            'vertices':n,'distinct_signatures':n,'all_distinct_pairs':n*(n-1)//2,
            'colorings_checked':len(recipes),
            'translation_colorings':len(translation_shifts),
            'binary_fiber_colorings':len(recipes)-len(translation_shifts),
            'saved_edges_checked_per_coloring':len(edges),
            'total_edge_color_checks':len(edges)*len(recipes),
            'recipes_file':'ALL_PAIRS_RECIPES.json',
            'recipes_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'warning':'A family of 5-colorings; NOT one coloring with all vertices different.'}

def coeff4(v):
    require(isinstance(v,list) and len(v)==8 and all(type(x) is int for x in v),
            'not an old K2 vector; no statement about larger-field input')
    c = [4*v[0]+2*v[2]+2*v[5]-v[1], 2*v[2]+v[1], 2*v[5]+v[1], -v[1]]
    require(all(sum(b*q for b,q in zip(row,c)) == 4*w for row,w in zip(BASIS,v)),
            'point lies outside Q(sqrt5,sqrt(-3),sqrt(-11))')
    return c

def cartesian(p):
    require(type(p['den']) is int and p['den']>0, 'invalid denominator')
    a,b = coeff4(p['a']),coeff4(p['b'])
    x = [a[0],0,a[1],0,0,-b[2],0,-b[3]]
    y = [0,a[2],0,a[3],b[0],0,b[1],0]
    den = 4*p['den']
    factor = den
    for z in x+y:
        factor = gcd(factor,z)
    x,y,den = tuple(z//factor for z in x),tuple(z//factor for z in y),den//factor
    require(den % 11 != 0,
            'nonintegral direct input; requires valuation-coset treatment, not field reduction')
    return x,y,den

def residue(p):
    x,y,den = p
    inverse = pow(den,-1,11)
    return (sum(a*b for a,b in zip(x,RESIDUE_BASIS))*inverse % 11,
            sum(a*b for a,b in zip(y,RESIDUE_BASIS))*inverse % 11)

def square(v):
    out = [0]*8
    for i,a in enumerate(v):
        for j,b in enumerate(v):
            out[i^j] += a*b*RAD[i&j]
    return out

def exact_unit(p,q):
    x,y,d = p
    xx,yy,e = q
    sx = square([a*e-b*d for a,b in zip(x,xx)])
    sy = square([a*e-b*d for a,b in zip(y,yy)])
    return sx[0]+sy[0] == (d*e)**2 and all(sx[i]+sy[i] == 0 for i in range(1,8))

def read_graph(path: Path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            return json.loads(z.read('GRAPH.json'))
    return json.loads(path.read_text())

def audit_old_graph(path: Path, out_dir: Path, specified_pair=None, all_pairs=False):
    g = read_graph(path)
    pts = [cartesian(p) for p in g['pts']]
    require(len(pts) >= 2 and len(set(pts)) == len(pts), 'not distinct actual points')
    n = len(pts)
    edges = [tuple(e) for e in g['edges']]
    require(all(len(e)==2 and all(type(i) is int for i in e) and 0<=e[0]<e[1]<n
                for e in edges), 'bad edge index')
    require(len(set(edges)) == len(edges), 'duplicate edge')
    red = [residue(p) for p in pts]
    for u,v in edges:
        require(exact_unit(pts[u],pts[v]), f'false unit edge {u},{v}')
        require(adjacent(red[u],red[v]), f'reduction failed on {u},{v}')
    pairs = []
    if specified_pair is not None:
        pairs.append(tuple(specified_pair))
    else:
        first = {}
        for i,r in enumerate(red):
            if r in first:
                pairs.append((first[r],i))
                break
            first[r] = i
        j = next((j for j in range(1,n) if red[j] != red[0]),None)
        if j is not None:
            pairs.append((0,j))
    reports = []
    for u,v in pairs:
        colors, report = separate(red,u,v)
        check_coloring(edges,colors)
        text = ''.join(map(str,colors))+'\n'
        name = f'PAIR_{u}_{v}_COLORING.txt'
        (out_dir/name).write_text(text)
        report.update({'status':'PAIR_SEPARATED','saved_edges_checked':len(edges),
                       'conflicts':0,'coloring_file':name,
                       'coloring_sha256':hashlib.sha256(text.encode()).hexdigest()})
        reports.append(report)
    semantic = {'pts':g['pts'],'edges':[list(e) for e in sorted(edges)]}
    result = {'status':'NOT_A_AND_NO_FORCED_EQUAL_PAIR',
              'vertices':n, 'saved_edges_exactly_checked':len(edges),
              'residue_classes_used':len(set(red)),
              'semantic_pts_edges_sha256':hashlib.sha256(json.dumps(semantic,sort_keys=True,
                                         separators=(',',':')).encode()).hexdigest(),
              'input_file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              'sample_pair_witnesses':reports,
              'universal_pair_claim_basis':'Finite lemma plus verified homomorphism; '
                      'NOT inferred from the sample pair witnesses.',
              'geometry_scope':'All saved edges checked exactly. The ring-map proof also '
                      'protects any omitted true unit edges among these points.'}
    if all_pairs:
        result['all_pairs_family'] = all_pairs_family(red,edges,out_dir)
    return result

def main():
    ap = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out-dir',type=Path,default=Path('mod11-no-forced-equal-output'))
    ap.add_argument('--graph',type=Path)
    ap.add_argument('--all-pairs-certificate',action='store_true',
                    help='Also check a finite coloring family separating all input-graph vertex pairs.')
    ap.add_argument('--pair',nargs=2,type=int,metavar=('U','V'))
    args = ap.parse_args()
    if args.pair is not None and args.graph is None:
        ap.error('--pair requires --graph')
    args.out_dir.mkdir(parents=True,exist_ok=True)
    started = perf_counter()
    result = {'finite_certificate':finite_certificate(), 'twin_lift_regression':twin_lift_test()}
    if args.graph is not None:
        result['old_graph_audit'] = audit_old_graph(args.graph,args.out_dir,args.pair,args.all_pairs_certificate)
    result['elapsed_seconds'] = round(perf_counter()-started,6)
    (args.out_dir/'CERTIFICATE.json').write_text(json.dumps(result,indent=2)+'\n')
    brief = {'finite_lemma':result['finite_certificate']['status'],
             'twin_lift_test':result['twin_lift_regression'],
             'old_graph_audit':result.get('old_graph_audit'),
             'elapsed_seconds':result['elapsed_seconds']}
    print(json.dumps(brief,indent=2))

if __name__ == '__main__':
    main()
