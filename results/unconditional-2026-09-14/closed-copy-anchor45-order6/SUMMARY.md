# Closed cyclic multi-copy order 6 / anchor (45,173) — checkpoint

Actions evidence:

- generic probe run `34783286450`: exact geometry completed; generic A/B probe was later cancelled while solving and is not evidence;
- sound triangle-symmetry run `34783432616`, artifact `10325667672`: **SAT**;
- validated local-coloring run `34783526599`, artifact `10324809446`: **VALIDATED_PROPER_5_COLORING**.

Exact induced graph:

- vertices: **2,628**;
- exact unit-distance edges: **15,708**;
- inherited-copy edges before cross-copy completion: **13,938**;
- additional exact cross-copy edges: **1,770**;
- all unordered point pairs checked exactly: **3,451,878**;
- final exact completion added **0** missed edges to the screening graph;
- completed graph SHA-256: `2275306ce8ad3d5bdb7d6c514990f08c103fa2474bfdc36a954c8abcac902bcb`.

## A classification

The symmetry-broken CaDiCaL run fixes the colors of an actual triangle `(0,1,5)` only up to global color-name symmetry. Attempts 0–2 returned UNKNOWN; attempt 3 returned SAT. The resulting full 5-coloring was validated on all 15,708 exact edges.

Independently, the TabuCol-style search reached zero conflicts at restart 2 / iteration 389,211, and that coloring was also validated on every exact edge.

Therefore this concrete exact graph is **not A** (it is 5-colorable). The earlier generic timeout/cancellation is superseded for ordinary 5-colorability.

## B status

B is not yet classified here. Two independently obtained proper 5-colorings already separate many pairs, but residual same-signature blocks remain. The active follow-up is targeted local-repair pair separation in `.github/workflows/hn-closed-copy-anchor45-order6-separation.yml`.

As always, timeout or failed local repair is non-evidence; a B claim would require a pair-inequality UNSAT result with independent confirmation.
