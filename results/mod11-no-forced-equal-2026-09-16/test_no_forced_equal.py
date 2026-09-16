#!/usr/bin/env python3
"""Small regression/negative-input tests; standard library only."""
from pathlib import Path
import json
import tempfile
import unittest
import hn_mod11_no_forced_equal as h


def point(real_integer):
    return {'a':[real_integer]+[0]*7,'b':[0]*8,'den':1}


class BarrierTests(unittest.TestCase):
    def test_finite_lemma(self):
        c = h.finite_certificate()
        self.assertEqual(c['edges_checked'],726)
        self.assertEqual(c['nonzero_displacements_separated'],120)
        self.assertEqual(c['neighbor_colors'],[0,1,4])

    def test_all_same_fiber_pairs_in_complete_bipartite_lift(self):
        residues = [(0,0)]*9+[(1,0)]*9
        edges = [(i,j) for i in range(9) for j in range(9,18)]
        for u in range(18):
            for v in range(u+1,18):
                colors,_ = h.separate(residues,u,v)
                h.check_coloring(edges,colors)
                self.assertNotEqual(colors[u],colors[v])

    def test_all_pair_family(self):
        residues = [(0,0)]*9+[(1,0)]*9
        edges = [(i,j) for i in range(9) for j in range(9,18)]
        with tempfile.TemporaryDirectory() as d:
            report = h.all_pairs_family(residues,edges,Path(d))
        self.assertEqual(report['all_distinct_pairs'],153)
        self.assertEqual(report['distinct_signatures'],18)

    def test_reject_same_actual_vertex(self):
        with self.assertRaises(ValueError):
            h.separate([(0,0)],0,0)

    def test_reject_nonintegral_direct_reduction(self):
        p = point(1)
        p['den'] = 11
        with self.assertRaises(ValueError):
            h.cartesian(p)

    def test_reject_larger_field_vector(self):
        p = {'a':[0]*12,'b':[0]*12,'den':1}
        with self.assertRaises(ValueError):
            h.cartesian(p)

    def test_reject_false_unit_edge(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'GRAPH.json'
            path.write_text(json.dumps({'pts':[point(0),point(2)],'edges':[[0,1]]}))
            with self.assertRaises(ValueError):
                h.audit_old_graph(path,Path(d))

    def test_reject_duplicate_actual_points(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'GRAPH.json'
            path.write_text(json.dumps({'pts':[point(0),point(0)],'edges':[]}))
            with self.assertRaises(ValueError):
                h.audit_old_graph(path,Path(d))

    def test_reject_bad_coloring(self):
        with self.assertRaises(ValueError):
            h.check_coloring([(0,1)],[2,2])

    def test_simple_integral_geometry(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'GRAPH.json'
            path.write_text(json.dumps({'pts':[point(0),point(1),point(11)],'edges':[[0,1]]}))
            report = h.audit_old_graph(path,Path(d),specified_pair=(0,2),all_pairs=True)
        self.assertEqual(report['sample_pair_witnesses'][0]['terminal_colors'],[2,3])
        self.assertEqual(report['all_pairs_family']['distinct_signatures'],3)


if __name__ == '__main__':
    unittest.main()
