import copy
import hashlib
import unittest
from hn_verify_translation_witness import semantic, verify

class Tests(unittest.TestCase):
    def setUp(self):
        self.g = {'pts': [0, 1, 2], 'edges': [[0, 1], [1, 2]]}
        self.b = {'witnesses': [{'case': 'control', 'solver': 'fixture', 'artifact_id': 0,
            'semantic_sha256': semantic(self.g), 'colors': '010',
            'coloring_sha256': hashlib.sha256(b'010\n').hexdigest()}]}
    def test_valid(self):
        self.assertEqual(verify(self.g, self.b)['status'], 'PASS')
    def test_missing_edge_rejected_by_hash(self):
        self.g['edges'].pop()
        with self.assertRaises(ValueError): verify(self.g, self.b)
    def test_reordered_points_rejected(self):
        self.g['pts'].reverse()
        with self.assertRaises(ValueError): verify(self.g, self.b)
    def test_bad_color(self):
        self.b['witnesses'][0]['colors'] = '050'
        with self.assertRaises(ValueError): verify(self.g, self.b)
    def test_monochromatic_edge_even_with_rehashed_vector(self):
        w = self.b['witnesses'][0]; w['colors'] = '000'
        w['coloring_sha256'] = hashlib.sha256(b'000\n').hexdigest()
        with self.assertRaises(ValueError): verify(self.g, self.b)
    def test_bad_coloring_hash(self):
        self.b['witnesses'][0]['coloring_sha256'] = '0'*64
        with self.assertRaises(ValueError): verify(self.g, self.b)
    def test_bad_edge_index(self):
        self.g['edges'][0] = [-1, 2]
        with self.assertRaises(ValueError): verify(self.g, self.b)
    def test_duplicate_edge(self):
        self.g['edges'].append([0, 1])
        with self.assertRaises(ValueError): verify(self.g, self.b)
if __name__ == '__main__': unittest.main()
