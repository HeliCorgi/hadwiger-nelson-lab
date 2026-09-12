# Separator left proof-tree composition check

- status: **PROOF-TREE-COMPOSITION-VERIFIED**
- checks: **19**
- all checks passed: **True**

Trust boundary:
This checker uses only Python standard-library logic and saved JSON evidence. It independently verifies the composition of the hierarchical human-readable proof tree, canonical-state formulas, palette-set deductions, and the final K4-minus-edge reduction. It does **not** re-solve the graph-coloring SAT instances that produced the leaf state tables/palette predicates. Those leaves remain supported by the separately recorded CaDiCaL195/Glucose4 cross-checks.

Finite conclusion checked:
Given the saved, solver-crosschecked leaf lemmas, the left side of the six-vertex quotient separator permits exactly `012202` and `012203`, via `q5=q6`, `q0=q10`, `q8=q9` and the final K4-minus-one-edge relation.

Scope: conditional quotient/P2 finite statement only; no new unit-distance or Hadwiger-Nelson lower-bound claim.

Workflow run: `34699960544`. Artifact id: `10300111590`. Artifact SHA-256: `0ef3e3c4de58c8e1d9ec7cad4a40de8a452a02bbdf176bfcc9c454052d411408`.
