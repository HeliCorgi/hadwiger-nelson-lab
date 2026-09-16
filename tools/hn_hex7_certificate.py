#!/usr/bin/env python3
"""Exact finite checks supporting an explicit infinite seven-coloring.

Hexagon circumradius s=2/5; centers i*a+j*b, a=(sqrt(3)*s,0),
b=(sqrt(3)*s/2,3*s/2); color (i+3*j) mod 7. Arbitrarily assign
shared boundaries to incident cells. This is an upper bound on the plane.
The K7 below is a CELL-CONFLICT graph, not a planar unit-distance witness.
"""
from fractions import Fraction as F
from itertools import combinations
import argparse,json
from pathlib import Path


def certificate():
    s=F(2,5)
    q=lambda i,j:i*i+i*j+j*j
    short=[(i,j) for i in range(-3,4) for j in range(-3,4) if 0<q(i,j)<7]
    assert len(short)==18
    assert all((i+3*j)%7!=0 for i,j in short)
    # Q=(i+j/2)^2+3*j^2/4 >= (i^2+j^2)/2. Thus Q<7 => |i|,|j|<=3.
    assert q(1,2)==7 and (1+3*2)%7==0
    assert 2*s<1
    # Same-color center gap >= sqrt(21)*s. Subtracting both circumradii
    # gives (sqrt(21)-2)*s > 1; all terms are positive, so square safely.
    assert (2+1/s)**2<21
    cells=[(0,0),(1,0),(0,1),(-1,1),(-1,0),(0,-1),(1,-1)]
    checks=[]
    for a,b in combinations(cells,2):
        n=q(b[0]-a[0],b[1]-a[1]); assert n in (1,3,4)
        # Along the center-center line, distance is L and each cell's radial
        # extent is r. |L-1|<2*r gives unit-separated points strictly inside
        # the two cells: p=c1+(L-1)u/2, q=c2-(L-1)u/2.
        if n==1:
            # L=sqrt(3)*s, r=sqrt(3)*s/2: 0<1<2*sqrt(3)*s.
            assert 12*s*s>1
        elif n==3:
            # L=3*s, r=s.
            assert abs(3*s-1)<2*s
        else:
            # L=2*sqrt(3)*s, r=sqrt(3)*s/2:
            # sqrt(3)*s < 1 < 3*sqrt(3)*s.
            assert 3*s*s<1<27*s*s
        checks.append({'cells':[list(a),list(b)],'center_norm_form':n,'interior_unit_pair':True})
    assert len(checks)==21
    return {'status':'PASS','circumradius':'2/5','color_rule':'(i+3*j) mod 7',
        'infinite_plane_seven_coloring_certified':True,
        'short_nonzero_lattice_vectors_checked':len(short),
        'minimum_same_color_lattice_norm':7,'within_cell_diameter':'4/5 < 1',
        'between_same_color_cells_distance_lower_bound':'(2/5)*(sqrt(21)-2) > 1',
        'boundary_handling':'Choose any incident cell; strict bounds protect all boundary points.',
        'fixed_tiling_no_six_certificate':{'cell_vertices':cells,'cell_edges':checks,'clique_size':7},
        'scope':'Six colors excluded ONLY for this fixed tiling with one color on each entire hexagon. No arbitrary six-coloring of the plane is excluded.',
        'not_a_seven_chromatic_unit_distance_graph':True,'float_used':False}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path)
    args=ap.parse_args();r=certificate();text=json.dumps(r,indent=2)+'\n'
    if args.out:args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(text)
    print(text)

if __name__=='__main__':main()
