# Execution amendments to the supplied prospective plan

The full user-supplied plan is preserved in `RESEARCH_PLAN.md`. These changes
were made during Stage 1 and do not authorize the full study.

1. The user explicitly authorized committing and pushing all code to the existing
   `main`; no branch or remote is created. No applicable AGENTS.md was present.
2. Hardware is one RTX PRO 4500 Blackwell, 32,623 MiB, not an RTX 6000 Ada.
   The pilot limits allocated device memory to 24 GiB (and at most 80% of device
   capacity). Allocation accounting starts at 2026-09-22 23:25:34 UTC and has
   an immutable two-hour deadline, including idle development and setup time.
3. The verified v1.0 archive is 595,266,464 bytes. Its cleaned file is named
   `electricity_cleaned.csv`. The archive root LICENSE is **MIT**; the current
   repository LICENSE begins **Attribution-ShareAlike 4.0 Unported**. Preserve
   both texts and record this version discrepancy. Raw data are not committed.
4. The fixed public calendar recipe has 19 candidate columns. The first fit
   failed before outcome scoring because an OOF training fold lacked full rank.
   Apply the plan's training-only redundancy rule: retain columns in recipe
   order only when the full provider design and every OOF training fold have
   full rank. Log retained columns. Counts, evidence sharing, target selection
   and outcome criteria are unchanged; the failed log is retained.
5. OOF residual scales are provider-local, with five deterministic day blocks.
   The shared empirical future allowance is the mean of the four local OOF
   mean squared residuals. This is an explicit working convention, not an
   identified physical innovation variance. Primary unresolved allowance is
   frozen at zero, with .5 and 1 scale sensitivities on a fixed small panel.
6. October 1-10 supplies historical covariance, October 11-20 supplies interval
   corrections, and October 21-31 supplies pilot scores. A seven-day validation
   embargo keeps seasonal-naive lag-168 inputs in October; all methods share
   the same observed target set. Up to 256 target origins per building cover
   these roles together, not 256 per method/role. November onward stays sealed.
7. The audited primary wire and matched CPU/GPU timing path use FP64. FP32 Gram
   discrepancies and hypothetical payload size are reported separately. No
   unconditional floating-point certificate is claimed.
8. Bounded active-face enumeration replaces projected-gradient iteration for
   p<=8; it reports a Frank–Wolfe objective gap and is checked against SciPy.
   Larger-provider and compiled-GPU experiments belong to later gated work.
9. Newly retrieved conservative covariance-compression and distributed-sketch
   literature narrows the novelty claim to a provisional interface synthesis.
   See `NOVELTY_AUDIT.md` before interpreting the mathematical corollary.
