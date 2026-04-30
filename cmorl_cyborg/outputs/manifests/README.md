# Output Manifests

This directory holds lightweight metadata for result lines that we still care
about after cleanup.

A manifest should answer three questions:

1. Which config defines the line?
2. Which exported summaries are official?
3. Which heavy run products are only being kept temporarily as anchors?

Current convention:

- put paper-facing lines in `official_artifacts.yaml`
- keep manifests small and hand-auditable
- prefer recording paths to selected seed anchors over copying large artifacts
