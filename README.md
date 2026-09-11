# hadwiger-nelson-lab

Computational research workspace for the Hadwiger–Nelson problem, currently focused on the five-color forcing structures handed off from [`HeliCorgi/five-color-forcing-anatomy`](https://github.com/HeliCorgi/five-color-forcing-anatomy).

> This repository does **not** claim a solution of the Hadwiger–Nelson problem. Results here are computational intermediate statements with explicitly stated scope.

## Result-recording policy

Whenever a search produces a lemma-like or theorem-like mathematical statement, record it in the relevant research-branch README together with:

- the exact statement and scope;
- why it follows mathematically from the computed object;
- the generating code and compact result/certificate path;
- solver/checker identity and whether an independent implementation rechecked it;
- an explicit warning when the statement is conditional or does not imply a new Hadwiger–Nelson bound.

Large reproducible SAT proof traces should normally remain GitHub Actions artifacts rather than Git blobs. The repository should retain regeneration code, compact metadata, hashes/artifact IDs, and the human-readable mathematical claim.

## Current lane

We are testing whether the P2 forcing system has a **port-free semantic interface supported on at most four vertices**.

The upstream data are pinned to commit:

`d1e80998bda337d9fa721f2e96d203ae54e97fc8`

Let

- `A = H* ∧ C88`, where `H*` is the first minimal edge core and `C88` is the 88-condition P2 forcing set;
- `B = H* ∧ (c(217) != c(490))`.

For a set `S` of non-port vertices, the observable is the equality partition induced on `S` by a proper 5-coloring. The search asks whether some four-set `S` separates the projected model sets of `A` and `B`.

Searching exactly four vertices is complete for support `<= 4`: a separating equality interface on fewer vertices remains separating after adding arbitrary non-port vertices.

## Current checkpoint

After Actions runs #1 and #2:

- system: 393 vertices, 1599 `H*` edges, 88 forcing conditions;
- non-port universe: 391 vertices / 76,245 equality atoms;
- validated upstream seed fooling pairs: 872;
- newly generated fooling pairs: **3205**;
- total represented sound cuts: **4077**;
- terminal result: **none** — no separating support-4 interface, no master-UNSAT exhaustion, and no global empty-difference fooling pair has been produced;
- latest durable checkpoint commit: `a10e0f9` on `research/semantic-interface`.

This is search-space elimination, not a new chromatic-number bound.

## Run 1 — 2026-09-10

GitHub Actions run [`34436888946`](https://github.com/HeliCorgi/hadwiger-nelson-lab/actions/runs/34436888946) completed all three original long time slices.

It advanced the lab-specific fooling-pair library to 2525 new pairs, for 3397 total sound cuts. No terminal result was produced.

Latest checkpoint commit after Run 1: `5283a5f`.

Stage-3 artifact digest: `sha256:a90421e0ec8351a896b039bc7bb9ae94cc9374b41097ac0c714448f8f270b172`.

## Run 2 — 2026-09-10

GitHub Actions run [`34493404794`](https://github.com/HeliCorgi/hadwiger-nelson-lab/actions/runs/34493404794) used the hardened Node-24 / guarded-slice workflow and completed successfully at the workflow level.

It resumed at iteration 2525 and reached **iteration 3205**, adding **680** new fooling pairs during the run. The cumulative library is therefore 872 validated upstream seeds plus 3205 lab-generated pairs = **4077 sound cuts**.

No `FINAL.json` or `INTERFACE.json` was produced. In particular, Run 2 did **not** establish either existence or nonexistence of a port-free support-4 semantic interface.

The sixth slice reached iteration 3205 at `2026-09-10T19:44:25Z`; the outer 3000-second guard terminated the still-active solver process at about `19:51:18Z`. Because the search was running with `--checkpoint-every 1` and atomic gzip writes, iteration 3205 was already durable and was committed immediately afterward. The timeout is treated only as `UNKNOWN / continue later`, never as SAT or UNSAT evidence.

Latest checkpoint commit after Run 2: `a10e0f9`.

Run-2 artifact:

- artifact id: `10170346817`
- digest: `sha256:44021dfa60c29f76f61df23e69c24f6469fc5a4c571f8bf1975bde129e8c95c3`

The run also confirms that the Node.js 20 deprecation warning from Run 1 is gone: Run 2 used `actions/checkout@v7`, `actions/setup-python@v7`, and `actions/upload-artifact@v7`.

## Search method

`tools/semantic_cegis_portfree.py` runs an exact master/oracle CEGIS loop.

The master selects four non-port vertices. Every known A/B fooling pair induces a difference graph on the non-port vertices; the selected four-set must contain at least one edge of every such difference graph. Equivalently, it may not be an independent four-set in any accumulated difference graph.

The oracle asks for an `A` coloring and a `B` coloring with the same complete equality pattern on the proposed four-set. SAT produces another sound fooling-pair cut. UNSAT produces a genuine semantic-interface candidate. If the master itself becomes UNSAT, all port-free equality interfaces of support at most four are excluded.

## Reliability and timeouts

The workflow uses a pinned upstream commit, validates every seed coloring, writes checkpoints atomically, and treats timeout/UNKNOWN states as **non-results**. A timeout is never converted into SAT or UNSAT evidence.

Run 2 showed why the guard is necessary: one solver call remained active for several minutes after the last completed CEGIS iteration. The outer timeout safely stopped it without losing the previous checkpoint. Before another large continuation run, the preferred engineering improvement is a sound per-query interruption/UNKNOWN path or a specialized fast four-set candidate generator, while retaining exact SAT for certificate-producing decisions.

See [`RESEARCH.md`](RESEARCH.md) for the mathematical setup and [`HANDOFF.md`](HANDOFF.md) for continuation details and certificate policy.
