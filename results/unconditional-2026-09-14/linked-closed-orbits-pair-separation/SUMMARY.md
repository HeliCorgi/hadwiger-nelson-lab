# Asymmetric linked closed-orbit pair separation — 2026-09-14

Fixed candidate: order-3 ring anchor `(95,101)`, asymmetric rotation `(-1+3*sqrt(-11))/10`, pivot link `(dst,src)=(0,911)`.

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

## sampled colorings
```json
{
  "status": "VALIDATED_COLORING_FAMILY",
  "vertices": 2373,
  "edges": 14178,
  "graph_sha256": "ffbe6d46def8ac5b6a0081279f56a2b91f1cad84a59a689a90252057a6fa6f41",
  "models": 8,
  "signature_stats": {
    "models": 8,
    "distinct_signatures": 2354,
    "remaining_unseparated_pairs": 19,
    "remaining_pair_ratio": 6.751047656000722e-06,
    "max_signature_block": 2
  },
  "all_models_validated_on_all_edges": true,
  "first_model_seeded": true,
  "first_model_conflicts": 800000,
  "first_model_seed": 20260914
}
```

## pair separation
```json
{
  "status": "NO_FORCED_EQUAL_PAIR",
  "classification": "D",
  "vertices": 2373,
  "edges": 14178,
  "initial_model_count": 8,
  "initial_remaining_pairs": 19,
  "generated_witness_count": 18,
  "saved_witness_count": 11,
  "compressed_witness_count": 11,
  "remaining_pairs": 0,
  "failures": [],
  "timeout_or_repair_failure_is_evidence": false,
  "all_witnesses_validated_on_all_edges": true,
  "elapsed_seconds": 4.114
}
```

Every retained coloring is validated on every exact edge. Timeout or failed repair is non-evidence.
