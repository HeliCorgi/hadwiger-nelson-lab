# Three-orbit asymmetric network — 2026-09-14

Orbit B uses `r(1/3)=(-1+3*sqrt(-11))/10`; orbit C uses the distinct `r(1/2)=(-7+4*sqrt(-11))/15`. The geometry search prioritizes literal exact C-A and C-B coupling.

## selection
```json
{
  "selection": {
    "dst_pivot": 946,
    "dst_owner": "B",
    "src_pivot": 34,
    "vertices": 3564,
    "inherited_edges": 21186,
    "added_cross_edges": 20,
    "c_to_a_edges": 17,
    "c_to_b_edges": 3,
    "couples_to_both": true,
    "exact_proposals_checked": 95,
    "shift": {
      "a": [
        8,
        0,
        0,
        0,
        0,
        37,
        0,
        0
      ],
      "b": [
        -26,
        0,
        0,
        0,
        0,
        11,
        0,
        0
      ],
      "den": 90
    },
    "cadical195": "SAT",
    "signature_stats": {
      "models": 6,
      "distinct_signatures": 2999,
      "remaining_unseparated_pairs": 971,
      "remaining_pair_ratio": 0.00015293106321266113,
      "max_signature_block": 25
    },
    "classification": "SAT_SCREENING_CANDIDATE"
  }
}
```

## geometry
```json
{
  "vertices": 3564,
  "screen_edges": 21206,
  "exact_induced_edges": 21206,
  "new_edges_from_exact_completion": 0,
  "all_pairs_exactly_checked": 6349266,
  "float_prefilter_used_for_final_completion": false,
  "screen_edges_subset_of_exact_completion": true,
  "graph_sha256": "b203fe20fab7e69408a96f08c0d1c7d993fe70781690c76a4972719ef11c44d1",
  "semantic_pts_edges_sha256": "b0ddf3a161b8590c9c72290b39eb861e8f0f99507f3b5278451fe239ad08a39f"
}
```

## symmetry
```json
{
  "status": "SAT",
  "classification": "NOT_A",
  "vertices": 3564,
  "edges": 21206,
  "graph_sha256": "b203fe20fab7e69408a96f08c0d1c7d993fe70781690c76a4972719ef11c44d1",
  "triangle": [
    0,
    1280,
    1261
  ],
  "symmetry_assumptions_sound": true
}
```

## tabucol
```json
{
  "status": "VALIDATED_PROPER_5_COLORING",
  "classification": "NOT_A",
  "vertices": 3564,
  "edges": 21206,
  "all_edges_validated": true
}
```

## separation
```json
{
  "status": "NO_FORCED_EQUAL_PAIR",
  "classification": "D",
  "vertices": 3564,
  "edges": 21206,
  "generated_witness_count": 578,
  "saved_witness_count": 157,
  "compressed_witness_count": 157,
  "remaining_pairs": 0,
  "failures": [],
  "timeout_or_repair_failure_is_evidence": false,
  "all_witnesses_validated_on_all_edges": true,
  "elapsed_seconds": 29.412
}
```

Only exact unit edges are coloring constraints. The selected point set is all-pairs exact-completed before final classification. UNKNOWN/timeout/local-repair failure is non-evidence.
