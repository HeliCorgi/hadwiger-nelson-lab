# hadwiger-nelson-lab

Computational research workspace for the Hadwiger–Nelson problem, currently focused on the five-color forcing structures handed off from [`HeliCorgi/five-color-forcing-anatomy`](https://github.com/HeliCorgi/five-color-forcing-anatomy).

> This repository does **not** claim a solution of the Hadwiger–Nelson problem. Results here are computational intermediate statements with explicitly stated scope.

## Current lane

We are testing whether the P2 forcing system has a **port-free semantic interface supported on at most four vertices**.

The upstream data are pinned to commit:

`d1e80998bda337d9fa721f2e96d203ae54e97fc8`

Let

- `A = H* ∧ C88`, where `H*` is the first minimal edge core and `C88` is the 88-condition P2 forcing set;
- `B = H* ∧ (c(217) != c(490))`.

For a set `S` of non-port vertices, the observable is the equality partition induced on `S` by a proper 5-coloring. The search asks whether some four-set `S` separates the projected model sets of `A` and `B`.

Searching exactly four vertices is complete for support `<= 4`: a separating equality interface on fewer vertices remains separating after adding arbitrary non-port vertices.

## Run 1 — 2026-09-10

GitHub Actions run [`34436888946`](https://github.com/HeliCorgi/hadwiger-nelson-lab/actions/runs/34436888946) completed all three original time slices successfully.

Status after the final checkpoint:

- system: 393 vertices, 1599 `H*` edges, 88 forcing conditions;
- non-port universe: 391 vertices / 76,245 equality atoms;
- validated upstream seed fooling pairs: 872;
- newly generated fooling pairs: **2525**;
- total sound CEGIS cuts represented after the run: **3397**;
- terminal result: **none** — neither a separating support-4 interface nor master UNSAT was reached;
- latest checkpoint commit: `5283a5f` on `research/semantic-interface`;
- stage-3 artifact digest: `sha256:a90421e0ec8351a896b039bc7bb9ae94cc9374b41097ac0c714448f8f270b172`.

This is progress in search-space elimination, not a new chromatic-number bound.

## Search method

`tools/semantic_cegis_portfree.py` runs an exact master/oracle CEGIS loop.

The master selects four non-port vertices. Every known A/B fooling pair induces a difference graph on the non-port vertices; the selected four-set must contain at least one edge of every such difference graph. Equivalently, it may not be an independent four-set in any accumulated difference graph.

The oracle asks for an `A` coloring and a `B` coloring with the same complete equality pattern on the proposed four-set. SAT produces another sound fooling-pair cut. UNSAT produces a genuine semantic-interface candidate. If the master itself becomes UNSAT, all port-free equality interfaces of support at most four are excluded.

## Reliability and timeouts

The workflow uses a pinned upstream commit, validates every seed coloring, writes checkpoints atomically, and treats timeout/UNKNOWN states as **non-results**. A timeout is never converted into SAT or UNSAT evidence.

After Run 1, the workflow was revised to avoid the Node.js 20 deprecation path and to reduce timeout risk: current Node-24 action majors are used, search is executed in shorter guarded slices, the checkpoint is written every completed CEGIS iteration, and each slice is committed before the next one starts.

See [`RESEARCH.md`](RESEARCH.md) for the mathematical setup and [`HANDOFF.md`](HANDOFF.md) for continuation details and certificate policy.
