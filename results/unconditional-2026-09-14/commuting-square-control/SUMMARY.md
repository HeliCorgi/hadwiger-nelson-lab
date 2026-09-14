# Commuting four-orbit square control — 2026-09-14

## selection
```json
{
  "selection": {
    "vertices": 4742,
    "inherited_edges": 28032,
    "added_cross_edges": 427,
    "screen_edges": 28459,
    "pair_cross_counts": {
      "AB": 162,
      "AC": 49,
      "AD": 2,
      "BC": 4,
      "BD": 49,
      "CD": 162
    },
    "float_proposal": {
      "float_near_pairs": 28461,
      "exact_checked_proposals": 28461
    },
    "r1": {
      "a": [
        -1,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      "b": [
        3,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      "den": 10
    },
    "r2": {
      "a": [
        7,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      "b": [
        5,
        0,
        0,
        0,
        0,
        0,
        0,
        0
      ],
      "den": 18
    },
    "s1": {
      "a": [
        -2,
        0,
        0,
        0,
        0,
        15,
        0,
        0
      ],
      "b": [
        -4,
        0,
        0,
        0,
        0,
        5,
        0,
        0
      ],
      "den": 30
    },
    "s2": {
      "a": [
        -7,
        0,
        0,
        0,
        0,
        25,
        0,
        0
      ],
      "b": [
        -5,
        0,
        0,
        0,
        0,
        5,
        0,
        0
      ],
      "den": 54
    },
    "commutes_exactly": true
  }
}
```

## geometry
```json
{
  "vertices": 4742,
  "screen_edges": 28459,
  "exact_induced_edges": 28459,
  "new_edges_from_exact_completion": 0,
  "all_pairs_exactly_checked": 11240911,
  "float_prefilter_used_for_final_completion": false,
  "screen_edges_subset_of_exact_completion": true,
  "graph_sha256": "e0d5f01a8f34fe92ac96fcbd043b1531d80d0718c9e1de125e1f9582e39c3eb9"
}
```

## seed
```json
{
  "status": "SAT",
  "classification": "NOT_A",
  "vertices": 4742,
  "edges": 28459,
  "graph_sha256": "e0d5f01a8f34fe92ac96fcbd043b1531d80d0718c9e1de125e1f9582e39c3eb9",
  "triangle": [
    0,
    1280,
    1261
  ],
  "symmetry_assumptions_sound": true
}
```

## separation
```json
{
  "status": "NO_FORCED_EQUAL_PAIR",
  "classification": "D",
  "vertices": 4742,
  "edges": 28459,
  "generated_witness_count": 901,
  "saved_witness_count": 223,
  "compressed_witness_count": 223,
  "remaining_pairs": 0,
  "failures": [],
  "timeout_or_repair_failure_is_evidence": false,
  "all_witnesses_validated_on_all_edges": true,
  "elapsed_seconds": 56.101
}
```

The two affine rotations commute exactly. Only literal exact unit edges are constraints; final point set receives all-pairs exact completion.
