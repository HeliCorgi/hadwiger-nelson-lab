# Closed cyclic copy control: order 3, anchor (95,101)

Date: 2026-09-14

Classification: **D for both A and B** for this concrete completed graph.

Construction: three complete exact copies of pinned G510 are arranged in the closed cyclic seam defined by anchor pair `(95,101)`. Copy `i` maps its anchor `b` to copy `i+1`'s anchor `a`, including the final/first seam. Only literal unit-distance edges are constraints.

## Exact geometry

- vertices: **1,192**
- inherited copy edges after point deduplication: **6,219**
- additional exact cross-copy edges found in screening: **789**
- exact induced unit edges: **7,008**
- all unordered point pairs checked exactly: **709,836**
- floating prefilter in final completion: **none**
- omitted unit edges after exact completion: **0** (the screening set already equalled the full exact induced edge set)
- completed graph SHA-256: `29c047daa1da5f52ad4bde52cea63104a94229fe7bf946189c30f34f1b4b52ac`

## Coloring result

CaDiCaL195 found a proper 5-coloring, so the graph is not an A witness. The probe retained **14 validated proper 5-colorings** and their vertex color-signatures separate every distinct pair:

- remaining unseparated pairs: **0**
- status: `SAT_NO_FORCED_EQUAL_PAIR`

Therefore no distinct vertex pair is same-colored in every proper 5-coloring, so this graph is also D for B.

## Reproduction

- Actions run: https://github.com/HeliCorgi/hadwiger-nelson-lab/actions/runs/34783119580
- artifact id: `10324729119`
- workflow: `.github/workflows/hn-closed-copy-anchor95.yml`
- builder: `tools/hn_closed_copy_direct.py`
- exact completion: `tools/hn_exact_completion.cpp`
- A/B probe: `tools/hn_probe_completed_graph.py`

This closes only this concrete order-3 anchor choice. It does not close the closed-copy construction family.
