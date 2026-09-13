# Closed cyclic multi-copy portfolio — 2026-09-14

This is the first portfolio run of the new unconditional closed-copy lane after Cycle 7.

## Portfolio

Pinned base: exact G510 (`510 / 2504`). The search arranged complete exact copies in closed `zeta30` orbits with the final/first seam included, and used only literal unit-distance edges as coloring constraints.

- geometric candidates screened: **36** (orders 3 and 6; 18 anchors each)
- SAT-screened candidates: **4** (top 2 by exact cross-copy edge count for each order)
- order 3 / anchor `(95,101)`: SAT; 1,192 vertices; 789 added exact cross-copy edges
- order 3 / anchor `(44,192)`: SAT; 1,180 vertices; 720 added exact cross-copy edges
- order 6 / anchor `(45,173)`: `UNKNOWN` under the limited screening budget; non-evidence
- order 6 / anchor `(95,101)`: `UNKNOWN` under the limited screening budget; non-evidence

The selector chose order 3 / anchor `(95,101)` among the candidates with an actual SAT result. That point/edge set is semantically identical to the independently launched direct control run.

## Selected graph: exact completion

- vertices: **1,192**
- screening edges: **7,008**
- exact induced unit edges after all-pairs completion: **7,008**
- all unordered point pairs checked exactly: **709,836**
- floating prefilter used for final completion: **no**
- semantic SHA-256 of `{pts,edges}`: `35898dab08d69084b0ac6323e3fccfadbcfa63d62d4cccf38fc8a430f42e28f4`
- artifact `COMPLETED_GRAPH.json` SHA-256: `5bf5f6d01f865e472944a560436e5e2fb2f0c593f12b254a547bac99a0d65ed4`

## A/B result

CaDiCaL195 found a proper 5-coloring, so the selected graph is not an A witness. Fourteen validated proper 5-colorings separate every distinct vertex pair:

- classification: **D**
- status: `SAT_NO_FORCED_EQUAL_PAIR`
- proper 5-color witnesses retained: **14**
- remaining unseparated pairs: **0**

Thus this selected graph is D for both A and B.

## Reproduction

- Actions run: https://github.com/HeliCorgi/hadwiger-nelson-lab/actions/runs/34783221549
- artifact id: `10324734261`
- workflow: `.github/workflows/hn-closed-copy-assembly.yml`
- search: `tools/hn_closed_copy_assembly.py`
- exact completion: `tools/hn_exact_completion.cpp`
- probe: `tools/hn_probe_completed_graph.py`

The order-6 `UNKNOWN` screening results are explicitly not a D/B/A conclusion. A separate exact order-6 control run was launched for `(45,173)`.
