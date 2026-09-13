# Cycle 7 top-200 fixed-pair scan — D

Graph SHA-256: `632ab11f24bf084221db31fec8e1eda522a18eba8d95dbd3bddf9cbcae1fe49d`

## Result

The 9,115-point Cycle 7 top-200 graph is **D for target B**.

- vertices: **9,115**
- all point pairs checked exactly: **41,537,055**
- exact unit-distance edges: **81,068**
- saved edges: **81,068**
- omitted unit edges: **0**
- spurious saved edges: **0**
- proper 5-colorings in the regenerated separating family: **456**
- compact separating certificate after greedy compression: **79**
- distinct vertex color signatures under the compact certificate: **9,115**

Therefore every distinct vertex pair is separated by at least one proper 5-coloring. No distinct fixed forced-equal pair exists in this full induced unit-distance graph.

## Hard-pair resolution

Generic SAT runs were misleadingly hard:

- `(0,375)` survived hundreds of heuristic/Kempe colorings but CaDiCaL195 eventually found a separating coloring.
- final two generic SAT probes `(9,2282)` and `(395,1098)` ran for about 90 minutes and were cancelled without a result.

Neither timeout was forcing evidence. Both pairs were later separated by graph-valid local list-coloring repairs:

- `(9,2282)`: radius-3 neighborhood around vertex 2282, 200 vertices changed;
- `(395,1098)`: radius-3 neighborhood around vertex 1098, 59 vertices changed.

The independently regenerated separation pass then had three residual pairs, all also separated:

- `(327,6016)`: one-vertex recolor;
- `(403,5111)`: radius-1 local list-coloring repair;
- `(500,897)`: radius-4 local list-coloring repair, 322 vertices changed.

## Geometry audit

`tools/hn_exact_completion.cpp` was run over all 41,537,055 unordered point pairs with no floating-point prefilter. It found exactly 81,068 unit-distance pairs, and that edge set equals the saved graph edge set exactly.

## Certificate

The regenerated 456-coloring family was greedily compressed to 79 colorings. The compact JSON certificate has SHA-256

`7a179e6cbb85abc7c63665cc85a0ac38ccef139e48e3e6cbdedbb78aec802d04`.

Its XZ-compressed payload has SHA-256

`bcf593c30d4c069f251a6e1a926a8f283eb2b6686ab8b1ebbf5393f83ba782a6`.

Metadata is preserved in `CERTIFICATE_META.json`. `tools/verify_cycle7_top200_separation.py` verifies a recovered certificate by checking the graph SHA, every coloring against every edge, and uniqueness of all 9,115 vertex signatures.

This closes the tested Cycle 7 top-200 family as **D for both A and B**. It does not imply anything about all possible Cycle 7 candidates or all constructions in the ambient field.
