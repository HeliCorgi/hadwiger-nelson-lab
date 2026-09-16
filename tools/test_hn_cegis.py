import itertools,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from hn_cegis_geometry import *
from hn_cegis_contact import validate,canonical,clauses,reference,kill_count,peel,proposal,library_extension,delete_center,oracle,orbit_blocks,run
from hn_cegis_verify import audit

class Tests(unittest.TestCase):
    def triangle(self):
        ps=[ORIGIN,UNIT,P(root(35))];es,_=complete(ps)
        return {'pts':[p.pack() for p in ps],'edges':es,'center':0}
    def test_exact_escape(self):
        self.assertTrue(unit(ESCAPE));self.assertNotEqual(ESCAPE.b,ZERO)
        self.assertEqual(ESCAPE*ESCAPE.conjugate(),UNIT)
    def test_cyclotomic_relation(self):self.assertEqual(reduce_poly(PHI),(0,)*48)
    def test_conjugation(self):
        for p in [ESCAPE,P(root(5)),ESCAPE+P(root(21))]:self.assertEqual(p.conjugate().conjugate(),p)
    def test_filters_keep_exact_edges(self):
        ps=[ORIGIN,UNIT,ESCAPE,P(root(35)),ESCAPE*P(root(35))]
        es,_=complete(ps);expected=[[i,j] for i in range(len(ps)) for j in range(i+1,len(ps)) if unit(ps[i]-ps[j])]
        self.assertEqual(es,expected)
    def test_rational_normalization(self):self.assertEqual(rational(2,4),rational(-1,-2))
    def test_bad_coordinate(self):
        for den in [0,True,1.0]:
            with self.assertRaises(ValueError):K((0,)*48,den)
    def test_no_float_coefficients(self):
        with self.assertRaises(ValueError):K((0.0,)+(0,)*47)
    def test_duplicate_points(self):
        with self.assertRaises(ValueError):complete([UNIT,UNIT])
    def test_canonical_names(self):self.assertEqual(canonical([4,3,4,1]),[0,1,0,2])
    def test_unknown_not_score(self):self.assertEqual(kill_count([{'status':s} for s in ['UNKNOWN_TIMEOUT','UNSAT_UNCHECKED','SAT_LIBRARY']]),0)
    def test_only_checked_negatives_score(self):self.assertEqual(kill_count([{'status':'UNSAT_PROOF_VERIFIED'}]),1)
    def test_bad_coloring(self):
        with self.assertRaises(ValueError):validate(self.triangle(),[0,0,1],3)
    def test_bad_pin(self):
        with self.assertRaises(ValueError):validate(self.triangle(),[0,1,2],3,[(0,1)])
    def test_duplicate_edges(self):
        g=self.triangle();g['edges'].append(g['edges'][0])
        with self.assertRaises(ValueError):validate(g,[0,1,2],3)
    def test_peel_extension(self):
        r=peel(self.triangle(),3);self.assertEqual(r['core_vertices'],0);validate(self.triangle(),r['model'],3)
    def test_nonempty_core_not_proof(self):self.assertEqual(peel(self.triangle(),2)['core_vertices'],3)
    def test_cnf_matches_exhaustive(self):
        for bits in range(64):
            g={'pts':[None]*4,'edges':[list(e) for i,e in enumerate(itertools.combinations(range(4),2)) if bits>>i&1]}
            cs=clauses(g,3,[(0,0)])
            for c in itertools.product(range(3),repeat=4):
                pos={v*3+x+1 for v,x in enumerate(c)}
                sat=all(any((x in pos) if x>0 else (-x not in pos) for x in clause) for clause in cs)
                self.assertEqual(sat,c[0]==0 and all(c[u]!=c[v] for u,v in g['edges']))
    def test_moser_geometry(self):
        src=[ORIGIN,UNIT,P(root(35)),UNIT+P(root(35))];es,_=complete(src)
        g={'pts':[p.pack() for p in src],'edges':es,'center':0}
        gg,cp,_=proposal(g,src,ESCAPE,ORIGIN)
        self.assertEqual((len(gg['pts']),len(gg['edges'])),(7,11))
        self.assertIsNone(reference(gg,3));c=reference(gg,4);validate(gg,c,4)
        parent,_=delete_center(gg);self.assertIsNotNone(reference(parent,3))
    def test_library_failure_not_unsat(self):
        g=self.triangle();self.assertIsNone(library_extension(g,[0],[0,0,0],[0,1,2],3))
        self.assertIsNotNone(reference(g,3))
    def test_fixed_failure_can_recolor(self):
        g={'pts':[None]*4,'edges':[[0,3],[1,3],[2,3]]}
        self.assertIsNone(reference(g,3,[(0,0),(1,1),(2,2)]));self.assertIsNotNone(reference(g,3))
    def test_blocked_negative_not_original(self):
        g={'pts':[None]*1,'edges':[]};self.assertIsNone(reference(g,3,blocks=[[0],[1],[2]]));self.assertIsNotNone(reference(g,3))
    def test_independent_geometry(self):self.assertEqual(audit(self.triangle(),[[0,1,2]],3)['status'],'PASS')
    def test_independent_missing_edge(self):
        g=self.triangle();g['edges'].pop()
        with self.assertRaises(ValueError):audit(g)
    def test_independent_nonunit_edge(self):
        g={'pts':[ORIGIN.pack(),(UNIT+UNIT).pack()],'edges':[[0,1]]}
        with self.assertRaises(ValueError):audit(g)
    def test_reference_oracle(self):
        with tempfile.TemporaryDirectory() as d:
            r=oracle(self.triangle(),2,[],Path(d),3,'reference');self.assertEqual(r['status'],'UNSAT_EXHAUSTIVE_SMALL')
    def test_orbit_blocks_remove_renamings(self):
        g=self.triangle();blocks=orbit_blocks([[0,1,2]],3)
        self.assertEqual(len(blocks),6);self.assertIsNone(reference(g,3,blocks=blocks))
        self.assertIsNotNone(reference(g,3))
    def test_geometric_fixed_vs_free(self):
        ps=[UNIT,P(root(70)),P(root(140)),ORIGIN];es,_=complete(ps)
        g={'pts':[p.pack() for p in ps],'edges':es,'center':3}
        self.assertIsNone(reference(g,3,[(0,0),(1,1),(2,2)]))
        c=reference(g,2);validate(g,c,2);self.assertEqual(audit(g,[c],2)['status'],'PASS')
    def test_contacts_include_all_shared_points(self):
        g=self.triangle();source=[P.unpack(p) for p in g['pts']]
        child,cp,meta=proposal(g,source,UNIT,ORIGIN)
        self.assertEqual(meta['cross_edges'],0)
        self.assertEqual(meta['shared_old_vertices'],3)
        self.assertEqual(meta['old_contact_vertices'],3)
    def test_reference_size_bound(self):
        with self.assertRaises(ValueError):reference({'pts':[None]*10,'edges':[]},3)

if __name__=='__main__':unittest.main()
