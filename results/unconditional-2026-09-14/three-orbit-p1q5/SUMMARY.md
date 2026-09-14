# Three-orbit p1q5 portfolio winner — 2026-09-14

## selection
```json
{
  "selection": {
    "c_parameter": [
      1,
      5
    ],
    "c_rotation": {
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
    "dst_pivot": 583,
    "src_pivot": 553,
    "vertices": 3562,
    "inherited_edges": 21183,
    "added_cross_edges": 28,
    "c_to_a_edges": 23,
    "c_to_b_edges": 7,
    "exact_proposals_checked": 84,
    "c_shift": {
      "a": [
        -24,
        0,
        0,
        0,
        0,
        95,
        0,
        0
      ],
      "b": [
        6,
        0,
        0,
        0,
        0,
        19,
        0,
        0
      ],
      "den": 54
    }
  }
}
```

## geometry
```json
{
  "vertices": 3562,
  "screen_edges": 21211,
  "exact_induced_edges": 21211,
  "new_edges_from_exact_completion": 0,
  "all_pairs_exactly_checked": 6342141,
  "float_prefilter_used_for_final_completion": false,
  "screen_edges_subset_of_exact_completion": true,
  "graph_sha256": "60239933909c74c344d1fc78c667fb41acdc64d76d4a15fe186673b11c2c26bd"
}
```

## seed
```json
{
  "status": "SAT",
  "classification": "NOT_A",
  "vertices": 3562,
  "edges": 21211,
  "graph_sha256": "60239933909c74c344d1fc78c667fb41acdc64d76d4a15fe186673b11c2c26bd",
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
  "vertices": 3562,
  "edges": 21211,
  "generated_witness_count": 585,
  "saved_witness_count": 159,
  "compressed_witness_count": 159,
  "remaining_pairs": 0,
  "failures": [],
  "timeout_or_repair_failure_is_evidence": false,
  "all_witnesses_validated_on_all_edges": true,
  "elapsed_seconds": 37.386
}
```

Every saved coloring is validated on every exact edge. UNKNOWN, timeout, or repair failure is non-evidence.
