#!/usr/bin/env python3
"""Small regression tests for the independent evidence verifier."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from hn_hex7_certificate import certificate
from hn_verify_reflection_evidence import verify


def point(x):
    return {'coeffs':[x]+[0]*47,'den':1}


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def graph(self,points,edges):
        raw=(json.dumps({'pts':points,'edges':edges})+'\n').encode()
        (self.p/'GRAPH.json').write_bytes(raw);return hashlib.sha256(raw).hexdigest()
    def witness(self,sha,text,pins=[]):
        p=self.p/'probes'/'test'/'5-ordinary';p.mkdir(parents=True,exist_ok=True)
        (p/'RESULT.json').write_text(json.dumps({'status':'SAT','colors':5,'pins':pins,'graph_file_sha256':sha}))
        (p/'COLORING.txt').write_text(text+'\n')
    def test_hex7(self):
        r=certificate();self.assertEqual(r['status'],'PASS');self.assertEqual(len(r['fixed_tiling_no_six_certificate']['cell_edges']),21)
    def test_single_edge_positive(self):
        sha=self.graph([point(0),point(1)],[[0,1]]);self.witness(sha,'01',[[0,0]])
        self.assertEqual(len(verify(self.p)['witnesses_verified']),1)
    def test_missing_unit_edge_rejected(self):
        self.graph([point(0),point(1)],[])
        with self.assertRaises(AssertionError):verify(self.p)
    def test_nonunit_edge_rejected(self):
        self.graph([point(0),point(2)],[[0,1]])
        with self.assertRaises(AssertionError):verify(self.p)
    def test_duplicate_point_rejected(self):
        self.graph([point(0),point(0)],[])
        with self.assertRaises(AssertionError):verify(self.p)
    def test_monochromatic_edge_rejected(self):
        sha=self.graph([point(0),point(1)],[[0,1]]);self.witness(sha,'00')
        with self.assertRaises(AssertionError):verify(self.p)
    def test_bad_pin_rejected(self):
        sha=self.graph([point(0),point(1)],[[0,1]]);self.witness(sha,'01',[[1,0]])
        with self.assertRaises(AssertionError):verify(self.p)
    def test_wrong_graph_hash_rejected(self):
        self.graph([point(0),point(1)],[[0,1]]);self.witness('0'*64,'01')
        with self.assertRaises(AssertionError):verify(self.p)

if __name__=='__main__':unittest.main(verbosity=2)
