# Fast three-orbit asymmetric control — 2026-09-14

## selection
```json
{
  "selection": {
    "dst_pivot": 1358,
    "dst_owner": "B",
    "src_pivot": 365,
    "vertices": 3564,
    "inherited_edges": 21186,
    "added_cross_edges": 7,
    "c_to_a_edges": 2,
    "c_to_b_edges": 5,
    "couples_to_both": true,
    "exact_proposals_checked": 33,
    "shift": {
      "a": [
        -28,
        0,
        0,
        0,
        0,
        5,
        0,
        0
      ],
      "b": [
        -8,
        0,
        0,
        0,
        0,
        19,
        0,
        0
      ],
      "den": 90
    }
  }
}
```

## geometry
```json
{
  "vertices": 3564,
  "screen_edges": 21193,
  "exact_induced_edges": 21193,
  "new_edges_from_exact_completion": 0,
  "all_pairs_exactly_checked": 6349266,
  "float_prefilter_used_for_final_completion": false,
  "screen_edges_subset_of_exact_completion": true,
  "graph_sha256": "f8bfaa6d0945ee12600001384ca839ebebd6d9b1438c1c4f6d46c436f832dacd",
  "semantic_pts_edges_sha256": "b2df4fddf5196f8b72cf64f5e1c68055fee3089e764a14c82750ad27a4915250"
}
```

## seed
```json
{
  "status": "SAT",
  "classification": "NOT_A",
  "vertices": 3564,
  "edges": 21193,
  "graph_sha256": "f8bfaa6d0945ee12600001384ca839ebebd6d9b1438c1c4f6d46c436f832dacd",
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
  "vertices": 3564,
  "edges": 21193,
  "generated_witness_count": 609,
  "saved_witness_count": 145,
  "compressed_witness_count": 145,
  "remaining_pairs": 0,
  "failures": [
    {
      "pair": [
        3,
        3455
      ],
      "best_conflicts": 1
    },
    {
      "pair": [
        3,
        3455
      ],
      "best_conflicts": 1
    },
    {
      "pair": [
        3,
        3455
      ],
      "best_conflicts": 1
    },
    {
      "pair": [
        3,
        3455
      ],
      "best_conflicts": 1
    }
  ],
  "timeout_or_repair_failure_is_evidence": false,
  "all_witnesses_validated_on_all_edges": true,
  "elapsed_seconds": 86.028
}
```

Fast control selected by two-sided exact geometric coupling, not coloring rigidity. UNKNOWN/timeout/local repair failure is non-evidence.
