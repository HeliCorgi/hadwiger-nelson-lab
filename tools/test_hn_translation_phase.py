import itertools,unittest
from hn_translation_phase import DSU,NoPhaseModel,encode,lift

class Tests(unittest.TestCase):
    def test_potential_sign_and_compression(self):
        d=DSU(4);d.merge(0,1,2);d.merge(1,2,3);d.merge(2,3,4)
        r,w=d.find(0);s,v=d.find(3)
        self.assertEqual(r,s);self.assertEqual((w-v)%5,4)
        d.merge(0,3,4)
        with self.assertRaises(NoPhaseModel):d.merge(0,3,3)
    def test_inconsistent_overlap(self):
        with self.assertRaises(NoPhaseModel):encode(1,[],[[0],[0]],[0,1])
    def test_collapsed_edge(self):
        with self.assertRaises(NoPhaseModel):encode(2,[(0,1)],[[0],[1]],[0,0])
    def test_matching_edges_allow_shift(self):
        cs,recipe,n=encode(2,[(0,1)],[[0],[1]],[0,1])
        self.assertEqual(n,1);self.assertEqual(lift([1,-2,-3,-4,-5],recipe,n),[0,1])
    def test_missing_vertex(self):
        with self.assertRaises(ValueError):encode(3,[],[[0],[1]],[0,1])
    def test_noninjective_copy(self):
        with self.assertRaises(ValueError):encode(2,[],[[0,0]],[0])
    def test_bad_model(self):
        with self.assertRaises(ValueError):lift([1,2],[(0,0)],1)
    def test_exhaustive_small_graphs_and_phases(self):
        # All 64 graphs on 4 vertices, and every offset for the second copy.
        edges=list(itertools.combinations(range(4),2));count=0
        for mask in range(64):
            es=[e for i,e in enumerate(edges) if mask>>i&1]
            for phase in range(5):
                expected=[]
                for x in range(5):
                    c=[0,x,phase,(x+phase)%5]
                    if all(c[a]!=c[b] for a,b in es):expected.append(c)
                try:cs,recipe,n=encode(4,es,[[0,1],[2,3]],[0,phase])
                except NoPhaseModel:
                    self.assertFalse(expected);continue
                actual=[]
                for colors in itertools.product(range(5),repeat=n):
                    pos={r*5+c+1 for r,c in enumerate(colors)}
                    if all(any((lit in pos) if lit>0 else (-lit not in pos) for lit in cl) for cl in cs):
                        actual.append(lift(list(pos),recipe,n))
                self.assertEqual(sorted(actual),sorted(expected));count+=1
        self.assertGreater(count,0)
if __name__=='__main__':unittest.main()
