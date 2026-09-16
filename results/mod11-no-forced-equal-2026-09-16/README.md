# mod-11: no forced-equal pair in the old coordinate field

Date: 2026-09-16 JST. This is a negative search result, not a six-chromatic unit-distance graph or a new Hadwiger-Nelson lower bound.

## Statement and scope

For every pair of distinct points a,b in E^2, where E=Q(sqrt3,sqrt5,sqrt11), there is a proper at-most-five-coloring c of E^2 with c(a) != c(b). Different pairs may use different colorings. Consequently neither target A nor target B can be realized entirely in this old real coordinate field.

More generally, every loopless graph admitting a graph homomorphism to Gamma(F_11^2) has a proper at-most-five-coloring separating any specified distinct pair. The argument uses aperiodic translations of Madore's five-color table and a single-vertex recoloring when both vertices have the same image. The valuation-coset reduction supplies the homomorphism for the full field E; there is no field homomorphism E -> F_11.

See [the full Japanese proof](PROOF_ja.md). This supersedes the earlier checkpoint's statements that the old-field obstruction did not settle B. It does not newly rule out the sevenfold or mixed-field constructions, and it does not provide H_phi. The general proof has not been Lean formalized or independently peer reviewed. No literature-wide novelty claim is made.

## Evidence retained here

The two Python files are self-contained and use only the standard library. The source differs from the original result package only in correcting its documentation link from PROOF.md to PROOF_ja.md.

`results/CERTIFICATE.json.gz`, `results/ALL_PAIRS_RECIPES.json.gz`, and the two `results/PAIR_*_COLORING.txt.gz` files preserve the original output bytes after gzip decompression. `EVIDENCE_MANIFEST.json` lists SHA-256 hashes for the code, proof, compressed data, and uncompressed evidence. `results/TEST_LOG.txt` preserves the original ten-test run.

The input Gen2 graph is Actions run **34957362184**, artifact **10391403066**, containing GRAPH.json. The source ZIP is not duplicated here. Its semantic {pts,sorted edges} SHA-256 is:

`b46ea400f8b8fdd536916aa7b1dbc5eadc7658fa269186091a9fdb90e32f559f`

Before repository integration, the original package manifest was verified and the ten tests and full Gen2 audit were rerun locally. The rerun reproduced both coloring files and all 875 recipes byte for byte; its certificate matched the original except for elapsed_seconds. These are local execution results, not a claim about a GitHub Actions run.

| Check | Result |
|---|---:|
| Distinct exact Gen2 points | 12,102 |
| Saved edges checked for exact unit distance | 80,678 |
| Proper five-colorings checked on every saved edge | 875 |
| Translation / binary-fiber colorings | 7 / 868 |
| Edge-color checks for the full family | 70,593,250 |
| Pairwise-distinct vertex color signatures | 12,102 |
| Distinct pairs separated by the family | 73,223,151 |
| Regression tests | 10 passed |

The all-pairs conclusion is checked by distinct color signatures, not inferred from sampling. The ring-map proof also protects true unit edges omitted from the saved list; no all-pairs geometric edge completion is claimed.

## Reproduce

From the repository root, using Python 3.10 or later:

```bash
cd results/mod11-no-forced-equal-2026-09-16
python -m unittest -v test_no_forced_equal.py
python hn_mod11_no_forced_equal.py --out-dir /tmp/hn-mod11-finite
python hn_mod11_no_forced_equal.py \
  --graph /absolute/path/to/gen2-source.zip \
  --all-pairs-certificate --out-dir /tmp/hn-mod11-gen2
```

The last command requires the original input artifact, not an unrelated graph with similar counts. Alternatively, pass its extracted GRAPH.json. ZIP and JSON packaging have different input_file_sha256 values; the semantic graph hash remains the identity check.

Verify and decompress the retained evidence without overwriting tracked files:

```bash
python - <<'PY'
import gzip, hashlib, json
from pathlib import Path
root = Path('.')
manifest = json.loads((root/'EVIDENCE_MANIFEST.json').read_text())
for name, expected in manifest['files_sha256'].items():
    data = (root/name).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('hash mismatch: ' + name)
out = Path('/tmp/hn-mod11-retained')
out.mkdir(parents=True, exist_ok=True)
for name, expected in manifest['uncompressed_sha256'].items():
    data = gzip.decompress((root/(name + '.gz')).read_bytes())
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('decompressed hash mismatch: ' + name)
    (out/Path(name).name).write_bytes(data)
print('Evidence verified and decompressed:', out)
PY
```

To compare a fresh Gen2 run against these outputs, compare the recipe JSON and two coloring files byte for byte; compare certificate JSON after removing elapsed_seconds. When switching between ZIP and extracted JSON input, input_file_sha256 will also differ by design.

## Attribution

The finite table and valuation reduction are from D. A. Madore, *The Hadwiger-Nelson problem over certain fields*, arXiv:1509.07023, Proposition 3.2, Corollary 3.4 and Lemma 4.5. The old-K2 decoder follows tools/hn_mod11_barrier.py at source commit 3a1e42eab803cb17c49fd7c5cd4410e4feca8350. The present addition is the pair-separation argument and its explicit Gen2 certificate; see the proof for details and limits.
