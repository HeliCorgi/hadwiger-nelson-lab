# Hadwiger–Nelson lab

## Current lane: port-free support-4 semantic interface

This repository continues the computational handoff from `HeliCorgi/five-color-forcing-anatomy` at pinned commit `d1e80998bda337d9fa721f2e96d203ae54e97fc8`.

The immediate unresolved question in that handoff is whether the P2 forcing system admits a semantic interface supported on four vertices away from the marked ports 217 and 490.

Let

- `A = H* ∧ C88`, where `H*` is the order-0 minimal core and `C88` is the 88-condition forcing set;
- `B = H* ∧ (c(217) != c(490))`.

For a non-port vertex set `S`, its observable state is the equality partition induced by a proper 5-coloring on `S`. A support-4 semantic interface exists exactly when some four-set `S` has disjoint projected state sets `π_S(Mod(A))` and `π_S(Mod(B))`.

The search in `tools/semantic_cegis_portfree.py` uses a master/oracle CEGIS loop over exact four-sets rather than arbitrary subsets of equality atoms. This is complete for support at most four: if a separating interface exists on fewer than four vertices, adding arbitrary non-port vertices cannot create a common projected state, so it extends to a separating four-set.

Each SAT oracle counterexample is an explicit pair `(alpha |= A, beta |= B)` whose equality partitions agree on the proposed four-set. That pair becomes a sound master cut. Master UNSAT therefore certifies that no port-free equality interface of support at most four exists. Oracle UNSAT yields an explicit four-vertex interface candidate for independent verification.

### Seed library

The search reuses two certified sources from the pinned handoff:

1. the 244 fooling pairs in `SEMANTIC_CEGIS_FINAL.json`;
2. the 689 exact survivor witness pairs in `K4_CERTIFICATE.json`.

Every seed coloring is rechecked against `H*`, `C88`, and the port-difference condition before it is admitted as a cut.

### Checkpointing

New fooling pairs are stored in `checkpoints/semantic_portfree_s4.json.gz`. GitHub Actions runs the search in time slices and commits the latest checkpoint and any terminal result to the research branch. The upstream source is always checked out at the pinned SHA above.

A positive semantic-interface result is not by itself a proof that `χ(R²) >= 6`; it is an intermediate object. Any candidate must next be translated into unit-distance structure and independently certified. Lean is reserved for formalizing stable finite certificates or the eventual bridge argument once a useful object survives independent checking.
