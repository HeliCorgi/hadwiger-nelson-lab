import unittest
from hn_affine_seeded_fork import seed_phases
class SeedTests(unittest.TestCase):
    def test_inverse_affine_seed(self):
        self.assertEqual(seed_phases([2,1],[0,1],[(0,1,0),(0,2,2)],1),[-1,-2,3,-4,-5])
    def test_uncovered_root(self):
        with self.assertRaises(ValueError):seed_phases([1],[0],[(0,1,0)],2)
    def test_wrong_length(self):
        with self.assertRaises(ValueError):seed_phases([1,2],[0],[(0,1,0)],1)
if __name__=='__main__':unittest.main()
