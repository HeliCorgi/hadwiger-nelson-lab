# Recheck and export the completed run

This procedure does not start another search or workflow and does not change repository files.

1. Download the four production artifact ZIPs from run 35083448620 before their expiry. Keep the exact ZIP bytes. Name them `cegis-11-guided-35083448620.zip`, `cegis-11-random-35083448620.zip`, `cegis-29-guided-35083448620.zip`, and `cegis-29-random-35083448620.zip`. Expected SHA-256 values and artifact IDs are in README.md and SUMMARY.json.
2. Run the standard-Python verifier from the repository root, with an output directory that does not yet exist:

```sh
python results/cegis-contact-2026-09-16/run-35083448620/verify_export.py \
  --artifact-dir /path/to/original-zips --out /tmp/cegis-run-export
```

It checks the ZIP hashes, 24 candidate semantic identities, the 12 full candidate five-color vectors and four retained color banks on every saved edge, recorded CNF hashes, seven fixed-parent unit-propagation contradictions, and checkpoint identities. It exports SUMMARY.json, CANDIDATES.csv, PROBE_INDEX.json, WITNESSES_AND_CHECKPOINTS.json.gz and EXPORT_HASHES.json. It does not rerun unit-distance geometry or SAT search. The geometry audit entries are explicitly imported from the original Actions artifacts.

Compare the generated SUMMARY.json and CANDIDATES.csv with the committed files. The expected uncompressed witness/checkpoint JSON SHA-256 is `9191c62c6a22faa0874c8a800ccc9272d9dcb5b224b1fb4a2af5f60be7b4884c`. Compare uncompressed bytes across compression-library versions; EXPORT_HASHES.json also records the gzip bytes produced in the recording environment. The generated PROBE_INDEX lists all saved result/CNF hashes. These generated files are not all duplicated as Git blobs by this recording commit.

The witness/checkpoint export contains complete color vectors and checkpoint objects, but not the graph coordinate arrays. To resume, keep the original artifact's output/CURRENT.json.gz and output/SOURCE.json.gz together with output/CHECKPOINT.json. Do not treat the export bundle alone as a self-contained resume directory. The README distinguishes next_round=4 continuation from the old workflow's round=2 replay.

Fixed-parent contradiction is not free-coloring impossibility. All unresolved candidates remain UNKNOWN. No new HN bound or improved discovery rate is asserted.
