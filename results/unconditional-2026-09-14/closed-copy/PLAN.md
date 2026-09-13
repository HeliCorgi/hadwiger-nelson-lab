# Closed cyclic multi-copy continuation — 2026-09-14

This is the first new unconditional lane after Cycle 7 top-200 was closed D for both A and B.

The construction is intentionally different from the old open frontier/contact-closure loop. For an exact base graph and anchor pair `(a,b)`, complete isometric copies are placed around a finite `zeta30` orbit so copy `i` maps `b` onto copy `i+1`'s `a`; the final copy closes back to the first. This creates a literal closed seam and lets cross-copy unit edges constrain global 5-color compatibility.

Implementation:

- `tools/hn_closed_copy_assembly.py`: deterministic portfolio over closed orders 3 and 6, exact validation of every screening edge, SAT/model-signature scoring, and selection of one concrete point set.
- `tools/hn_probe_completed_graph.py`: ordinary 5-colorability plus diverse coloring signatures and direct residual pair-inequality SAT on the exact-completed graph.
- `.github/workflows/hn-closed-copy-assembly.yml`: rebuilds from the pinned upstream G510, runs the portfolio, completes **all** unordered pairs with `tools/hn_exact_completion.cpp` (no float prefilter), and stores the full evidence as an Actions artifact.

The geometric prefilter is not a proof step: floating point only proposes cross-copy edges during portfolio screening. Every screening edge is exact-checked, and the selected point set is subsequently completed by exact all-pairs arithmetic before any D/B conclusion. `UNKNOWN` remains non-evidence.
