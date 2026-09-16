import unittest,random
from itertools import product,combinations
from hn_affine_copy_probe import AffineDSU,NoAffineModel,encode,lift,rhombus_templates
from hn_affine_rhombus_run import validate

class Tests(unittest.TestCase):
    def test_exhaustive_template_cnf_equivalence(self):
        rng=random.Random(21916)
        for _ in range(160):
            k=3;size=rng.randint(1,3);n=rng.randint(size,min(5,size*2));count=rng.randint(1,3)
            cps=[rng.sample(range(n),size) for _ in range(count)]
            if set(v for cp in cps for v in cp)!=set(range(n)):continue
            slopes=[rng.randint(1,k-1) for _ in cps];offsets=[rng.randrange(k) for _ in cps]
            edges=[e for e in combinations(range(n),2) if rng.randrange(3)==0]
            pins=[(0,0)] if rng.randrange(2) else [];expected=set()
            for xs in product(range(k),repeat=size):
                if any(xs[i]!=c for i,c in pins):continue
                ys=[None]*n;ok=True
                for cp,a,b in zip(cps,slopes,offsets):
                    for i,v in enumerate(cp):
                        c=(a*xs[i]+b)%k
                        if ys[v] is not None and ys[v]!=c:ok=False
                        ys[v]=c
                if ok and all(ys[u]!=ys[v] for u,v in edges):expected.add(tuple(ys))
            try:cs,rec,nr=encode(n,edges,cps,slopes,offsets,k,pins)
            except NoAffineModel:
                self.assertFalse(expected);continue
            actual=set()
            for xs in product(range(k),repeat=nr):
                pos={r*k+c+1 for r,c in enumerate(xs)}
                if all(any((v>0)==(abs(v) in pos) for v in cl) for cl in cs):actual.add(tuple(lift(list(pos),rec,nr,k)))
            self.assertEqual(actual,expected)
    def test_affine_cycle_fixes_color(self):
        d=AffineDSU(2);d.merge(0,1,2,1);d.merge(0,1,3,4)
        self.assertEqual(d.dom[d.find(1)[0]],{2})
    def test_inconsistent_cycle(self):
        d=AffineDSU(2);d.merge(0,1,1,0)
        with self.assertRaises(NoAffineModel):d.merge(0,1,1,1)
    def test_restriction_survives_union(self):
        d=AffineDSU(3);d.restrict(0,{1});d.merge(0,1,2,3);d.merge(1,2,3,2)
        for i in range(3):
            r,a,b=d.find(i);self.assertEqual(len(d.dom[r]),1)
        r,a,b=d.find(0);self.assertEqual({(a*x+b)%5 for x in d.dom[r]},{1})
    def test_edge_collapsed(self):
        with self.assertRaises(NoAffineModel):encode(2,[(0,1)],[[0],[1]],[1,1],[0,0])
    def test_edge_same_root_different_slopes(self):
        cs,rec,n=encode(2,[(0,1)],[[0],[1]],[1,2],[0,0])
        self.assertEqual(n,1);self.assertIn([-1],cs)
    def test_bad_maps(self):
        for cps in ([[0,0]],[[0]]):
            with self.assertRaises(ValueError):encode(2,[],cps,[1],[0])
    def test_bad_slope(self):
        with self.assertRaises(ValueError):encode(1,[],[[0]],[0],[0])
    def test_non_one_hot_rejected(self):
        with self.assertRaises(ValueError):lift([1,2],[(0,1,0)],1)
    def test_mono_witness_rejected(self):
        with self.assertRaises(ValueError):validate({'pts':[0,1],'edges':[[0,1]]},[2,2])
    def test_bad_witness_rejected(self):
        for c in ([1], [0,5], [0,True]):
            with self.assertRaises(ValueError):validate({'pts':[0,1],'edges':[[0,1]]},c)
    def test_parameters(self):
        for name,count in [('u',8),('fork',12)]:
            for t in range(1,5):
                a,b=rhombus_templates(name,t);self.assertEqual(len(a),count);self.assertEqual(len(b),count)
                self.assertTrue(all(1<=x<5 for x in a));self.assertTrue(all(0<=x<5 for x in b))
if __name__=='__main__':unittest.main()
