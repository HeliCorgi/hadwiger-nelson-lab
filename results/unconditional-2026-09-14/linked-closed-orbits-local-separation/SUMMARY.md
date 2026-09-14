# Linked closed-orbit local separation — 2026-09-14

## geometry
```json
{
  "vertices": 2373,
  "screen_edges": 14178,
  "exact_induced_edges": 14178,
  "new_edges_from_exact_completion": 0,
  "all_pairs_exactly_checked": 2814378,
  "float_prefilter_used_for_final_completion": false,
  "screen_edges_subset_of_exact_completion": true,
  "graph_sha256": "ffbe6d46def8ac5b6a0081279f56a2b91f1cad84a59a689a90252057a6fa6f41",
  "semantic_pts_edges_sha256": "866590e7d7b61e10fd59d551dfa98ce73c98532c79364068ee073ce3d947fc06"
}
```

## seed
```json
{
  "status": "SAT",
  "classification": "NOT_A",
  "vertices": 2373,
  "edges": 14178,
  "graph_sha256": "ffbe6d46def8ac5b6a0081279f56a2b91f1cad84a59a689a90252057a6fa6f41",
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
  "vertices": 2373,
  "edges": 14178,
  "generated_witness_count": 380,
  "saved_witness_count": 119,
  "compressed_witness_count": 119,
  "remaining_pairs": 0,
  "failures": [
    {
      "pair": [
        0,
        2229
      ],
      "best_conflicts": 2
    }
  ],
  "timeout_or_repair_failure_is_evidence": false,
  "all_witnesses_validated_on_all_edges": true,
  "elapsed_seconds": 26.053
}
```

All saved proper colorings are validated on all exact edges. Repair failure or timeout is non-evidence.
