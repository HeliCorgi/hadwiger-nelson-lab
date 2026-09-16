# Translation/overlap series: u and fork now have verified five-colorings

2026-09-16 JST. **No new Hadwiger–Nelson lower bound is claimed.**
The affine follow-up found full proper five-colorings of both remaining mixed
candidates. Their former UNKNOWN target-A statuses are superseded by **NOT_A**.
All five graphs in this bounded translation series are now excluded for A.
This does not exclude larger constructions, the ambient field, or other point pairs.

## Current checkpoint

| case | vertices | unit edges | current A status | decisive evidence |
|---|---:|---:|---|---|
| g3-shift-2 | 3,812 | 24,275 | NOT_A | 1 prior full five-coloring |
| g3-shift-3 | 5,493 | 36,106 | NOT_A | 2 prior full five-colorings |
| u | 15,908 | 103,045 | NOT_A | 2 new full five-colorings |
| fork | 23,090 | 154,809 | NOT_A | 2 new full five-colorings |
| one | 17,040 | 109,688 | NOT_A | historical explicit phase-shift construction |

For **only the specified a,b pair** in each mixed graph, both equality and
inequality have full proper five-color witnesses. Thus these interfaces are
NOT_FORCED_EQUAL and NOT_H_PHI. This is not an exclusion of every possible B pair.
The exact pairs are u: indices (377,1000), fork: (378,1084), each with a=(0,0),
b=(phi,0). Their displacement was rechecked independently in QQ[z]/Phi210.

`SUMMARY.json` is the current machine-readable checkpoint. The previous summary
is preserved in Git at commit `a4f399e31f9cc5946910be98ea89404a9a33082c`.
`ARCHIVE_INDEX.json`, the prior G3 witnesses, reflection work, and seven-color
proof have not been replaced.

## What changed in the search

The old phase search shared an entire 8,520-point rhombus coloring between
translations. The new search exposes its four constituent G3 copies and permits
an affine permutation of the five color names for each copy:

    C(copy_s[i]) = a_s * X_i + b_s (mod 5).

For t in {1,2,3,4}, the four local slopes are [1,t,-1,-t] and offsets are
[0,1,1+t,t]. External translations add offsets [0,1] for u and [0,1,t] for fork.
The G3 source points 0 and 1 are pinned to colors 0 and 1 as part of this extra
search restriction. Affine union-find enforces actual overlaps, including cycles
that fix a root color. Every original edge is included in the resulting CNF.

The source-level systems have 1,584 color variables for u and 1,572 for fork,
compared with 7,388 and 6,309 in the previous whole-rhombus phase systems.
A restricted model is lifted and checked on every original edge. Restricted
UNSAT, an inconsistent template, or timeout never excludes ordinary colorability.
No assumption is made that these templates cover all possible colorings.

## Completed runs

[35057449450](https://github.com/HeliCorgi/hadwiger-nelson-lab/actions/runs/35057449450),
source `528997412960b6b34530eeca3e6557d8a6be606f`, ran both solvers on both graphs.
CaDiCaL found u witnesses for t=1 and t=4 in 23.931 and 51.330 worker seconds.
The other twelve restricted probes timed out at 60 seconds. Both exact original
graphs were independently audited in these jobs, not approximated numerically.

[35058000720](https://github.com/HeliCorgi/hadwiger-nelson-lab/actions/runs/35058000720),
source `dfdecef3d644a3fcb554a0ee283e3d9b72799d27`, used those u witnesses as soft
initial phase preferences for fork. The CNFs were unchanged and **no variables
were frozen**. CaDiCaL found fork witnesses for t=1 and t=4 in 1.521 and 0.771
worker seconds; both Glucose probes timed out at 60 seconds. These are measured
run times, not evidence of rigidity or proximity to a six-chromatic graph.

The eight search jobs completed. The 12 affine tests and then all 15 tests with
the seed transformation passed locally and in their respective Actions runs.
All eight ZIP hashes, all original graph identities, all reconstructed CNFs and
all four full positive models were checked locally. Details: `AFFINE_AUDIT.json`.

## Two-port consequence and scope

For each mixed graph the witnesses realize terminal colors (0,2) and (0,0).
Global color renaming therefore realizes all 25 ordered assignments of five
colors to these two terminals. Their complete two-port relation is unrestricted.

Consequently, joining copies only through these terminals, with disjoint interiors
and no additional edges touching the interiors, adds no extra five-color
restriction to the terminal skeleton. Different ports, new interior overlaps,
additional cross edges, or genuinely new constructions are not covered.

## Durable witnesses and reproduction

`AFFINE_FIVE_COLORINGS.json.gz` contains all four **full** color vectors, not just
seeds. Its repository SHA-256 is
`cb49029f740741dd5c24c38128fd860d9af97a11fb6d235488d0c5c039b82ecc`.
The canonical uncompressed JSON SHA-256 is
`72240175a62057f5be4c5fe455df28569b49ad4057c6f94a7562c697f0b5fb7c`.
A Python-version-dependent gzip OS header can differ; compare uncompressed bytes
when regenerating. No solver is needed to check the stored witnesses.

After extracting the matching graph from an artifact listed in `AFFINE_AUDIT.json`:

```sh
python tools/hn_verify_translation_witness.py --graph /tmp/candidate/GRAPH.json \
  --bundle results/interior-overlap-2026-09-16/AFFINE_FIVE_COLORINGS.json.gz
python tools/hn_cyclotomic210_independent_audit.py \
  --graph /tmp/candidate/GRAPH.json --out /tmp/geometry.json
PYTHONPATH=tools python -m unittest discover -s tools -p 'test_hn_affine*.py' -v
```

The first command uses standard Python and validates two full colorings for the
chosen graph. The second needs NumPy/SymPy and audits all 126,524,278 (u) or
266,562,505 (fork) point pairs using sound filters and exact norm calculations.

The archive run [35058561996](https://github.com/HeliCorgi/hadwiger-nelson-lab/actions/runs/35058561996)
independently checked all four full color vectors without importing the solver or
search encoder. Its uncompressed bytes match the locally audited bundle exactly.
The full vectors are committed to Git and do not expire with Actions artifacts.
Large graphs, CNFs and logs remain in artifacts expiring 2026-12-15.

## Next checkpoint

Do not rerun these unchanged five graphs as an A-search. There is no unresolved
A candidate left in this bounded series. Other terminal selections remain
unexamined; any new construction must add constraints not already defeated by
these explicit witnesses. The two-port interfaces above are not forcing gadgets.

The new search workflows are manual-only after the results commit, and the
archive workflow is returned to read-only, local archive reproduction. The results
commit launches no further search. No six-color necessity, plane-wide five-coloring,
or field-wide impossibility theorem follows from this finite checkpoint.
