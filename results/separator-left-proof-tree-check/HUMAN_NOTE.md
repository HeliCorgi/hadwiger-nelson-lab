# Human-readable checkpoint: the p-side is now a checked proof tree

The original exact statement was opaque: among 202 canonical color partitions of the outer six-vertex separator, the 267-qnode left bag extends only `012202` and `012203`.

The current explanation is hierarchical rather than a single small induced gadget.

## Outer reduction

The left bag forces three equalities:

- `q5=q6`;
- `q0=q10`;
- `q8=q9`.

After contracting these, the four tracked classes form `K4` minus one edge. Therefore there are exactly two color-symmetric outer states, `012202` and `012203`.

## q0=q10 branch

A minimum five-vertex separator isolates degree-5 q10. Its large side permits only `01230`, `01233`, `01234`; the singleton q10 gate rejects the all-five-colors state `01234`, leaving two states where q0 and q10 are the same unique missing color.

The three-state large-side language is exactly eight disequalities. Seven become ordinary graph edges after forced-equality-class contraction. The only residual is `q18!=q256`, which itself factors through another degree-5 singleton palette gate: q18 may use only colors present on the boundary while q256 may use exactly the missing colors.

## q8=q9 branch

A seven-vertex separator isolates degree-7 q104. The large side has exactly 12 states. Those 12 states are now compressed exactly to a color-name-invariant CNF:

- 13 pairwise disequalities common to all 12 states;
- plus four two-literal clauses:
  - `(q4!=q226) OR (q33!=q68)`;
  - `(q4!=q226) OR (q62!=q78)`;
  - `(q4!=q226) OR (q68!=q78)`;
  - `(q5=q33) OR (q78!=q226)`.

Pairwise constraints alone permit 21 states; the four clauses remove exactly the nine extras. Among all valid width-2 clauses, the minimum cover has size four and is unique.

The q104 singleton gate rejects the ten five-color large-side states. The two surviving four-color states are `0112323` and `0112333`; in both, q8, q9 and q104 are forced to the unique missing fifth color.

## q5=q6 branch

A local K4 common-neighborhood lemma gives `q5=q22`. A width-10 separator then gives a conditional palette argument: the large q6 side requires at least four boundary colors, and whenever the boundary uses at most four colors the q6 color is absent from the boundary. Compatibility with singleton q22 requires at most four boundary colors. Hence the boundary uses exactly four colors and q6=q22 is the unique missing fifth color, so q5=q6.

## Machine audit of the composition

`tools/check_separator_left_proof_tree.py` is deliberately solver-free: it imports no PySAT and rechecks the saved proof-tree composition with Python standard-library logic. It verifies the pairwise languages, palette-set deductions, the q8/q9 relation CNF, the singleton missing-color gates, the outer three equalities, and the final `K4-e` reduction.

Workflow run `34699960544` passed all 19 checks (`PROOF-TREE-COMPOSITION-VERIFIED`).

Trust boundary: this checker does **not** independently solve the graph-coloring SAT instances underlying the leaves. The leaf tables/palette predicates are separately supported by the recorded CaDiCaL195/Glucose4 cross-checks. The new checker independently audits how those leaves compose into the human-readable outer proof.

This is a conditional finite explanation inside the pinned quotient/P2 system. It is not a unit-distance construction and does not change the Hadwiger–Nelson bound.
