---
name: tabular-data-deliverables
description: Use when transforming tabular data into computed results and one or more structured output files.
---
- Read the output specification first; list required fields, formats, metadata, filters, and counting rules.
- Inspect input headers, representative values, duplicates, missing-value markers, and malformed or ambiguous records.
- Keep input-row counts separate from deduplicated-record counts; deduplicate using the specified key before computing distinct-record results.
- Parse dates with explicit timezone handling and convert to the required timezone and exact representation.
- Normalize categories only to the specified canonical values.
- Use decimal-safe arithmetic for money and serialize it in the required unit and type.
- Write every required artifact, then independently validate its schema, formatting, row counts, and computed values against the specification.