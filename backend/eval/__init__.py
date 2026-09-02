"""Evaluation harness.

Everything in this package reads the seeded corpus and reports what the system actually
does with it. Nothing here tunes a threshold or edits a detector — the harness measures,
and the measurements are committed to `reports/` so a reader can diff them against a
re-run rather than take them on trust.
"""
