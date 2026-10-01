# Additional primary-source verification

Checked 2026-10-01 UTC. Original verified bibliography and source notes remain
in `literature/verified_bibliography.json` and `docs/literature.md`.

* Bandt and Pompe, *Physical Review Letters* 88(17), 174102 (2002),
  DOI10.1103/PhysRevLett.88.174102: [publisher record](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.88.174102).
  Ordinal-pattern diversity is based on neighboring-value ordering; monotone
  amplitude transformations can preserve it. Our normalized estimator and
  missing/tie support rules are specified explicitly rather than assuming all
  short-window estimates are reliable. This is not a new entropy definition.
* Richman and Moorman, *American Journal of Physiology—Heart and Circulatory
  Physiology* 278(6), H2039–H2049 (2000), DOI10.1152/ajpheart.2000.278.6.H2039:
  [publisher record](https://journals.physiology.org/doi/abs/10.1152/ajpheart.2000.278.6.H2039),
  [authors' PhysioNet implementation and citation](https://physionet.org/content/sampen/1.0.0/).
  The publisher's full text was inaccessible during this recheck. Metadata is
  cross-checked against the original authors' software resource. Our common
  pair set, Theiler exclusion, tolerance and censoring conventions are explicit;
  they need not equal every software variant called sample entropy.
* Costa, Goldberger and Peng, *Physical Review Letters* 89(6), 068102 (2002),
  DOI10.1103/PhysRevLett.89.068102:
  [original paper hosted by PhysioNet](https://physionet.org/files/mse/1.0/papers/prl-2002.pdf).
  Coarse-graining followed by sample entropy is multiscale sample entropy;
  replacing the estimator by ordinal entropy is labeled multiscale permutation
  entropy. The original paper itself distinguishes irregularity from complexity;
  we make no transfer of physiological health claims to IoT streams.

Dataset rechecks: [Intel original source](https://db.csail.mit.edu/labdata/labdata.html)
confirms 54 sensors, approximately 31-second acquisition, coordinate units in
metres, Celsius, relative humidity, lux and volts, and missing/truncated streams.
[DCRNN's original repository](https://github.com/liyaguang/DCRNN) remains the
PEMS-BAY release source. Exact file hashes, the pinned source revision and
causal preprocessing are in the original dataset manifests; the extension
records their hashes and new split/episode lineage.
