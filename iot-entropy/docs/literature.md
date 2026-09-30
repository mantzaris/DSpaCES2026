# Source and novelty audit (2026-09-30)

Original PDFs are cached, with extracted text, under ignored `literature/raw/`.
DOI publisher metadata is recorded in `literature/verified_bibliography.json`.
Bibliography fields are taken from publisher/author sources rather than generated
from titles. The final paper distinguishes these lines of work:

| Source | Verified relevance and boundary |
|---|---|
| [Mantzaris et al., 2024](https://doi.org/10.1038/s41598-024-70029-x) | Entropy trajectories are compared with evolving collective organization under network topology. Its degree/homophily distributions differ from the correlation-eigenvalue distribution here. The transferable idea is trajectory-based description of organization, not the same entropy definition. |
| [Mantzaris and Domenikos, 2025](https://doi.org/10.3389/fcpxs.2024.1516812) | Flocking is described through defined microstates and thermodynamic quantities. We transfer attention to collective entropy trajectories only. This sensor score establishes no temperature, heat flow, second law or causal explanation. Published February 3, 2025; volume 2 and DOI contain 2024. |
| [Roy and Vetterli, 2007](https://zenodo.org/records/40328) | Effective rank exponentiates entropy of normalized singular values. For PSD R these singular values equal its eigenvalues, giving effective rank m^H before normalization/shrinkage qualifications. Spectral entropy is established. |
| [FINGER, Chen et al., 2019](https://proceedings.mlr.press/v97/chen19j.html) | Von Neumann graph entropy and graph-distance anomaly monitoring predate this work. Their Laplacian spectrum is different from a local sensor-correlation spectrum. Do not claim the first entropy-based graph monitor. |
| [DiffSTG, Wen et al., 2023](https://doi.org/10.1145/3589132.3625614) | Joint graph-temporal diffusion forecasting is prior work. We use a compact independently implemented graph/temporal denoiser, not a reproduction of its U-Net UGnet. |
| [CSDI, Tashiro et al., 2021](https://proceedings.nips.cc/paper_files/paper/2021/hash/cfe8504bda37b575c70ee1a8276f3486-Abstract.html) | Mask-aware conditional joint diffusion is established. Here the allowed conditioning is strictly historical; no observed target is revealed to the main generator. |
| [TimeGrad, Rasul et al., 2021](https://proceedings.mlr.press/v139/rasul21a.html) | Diffusion for multivariate predictive distributions is established. Our block forecast differs from its autoregressive formulation. |
| [DiffAD, Xiao et al., 2023](https://doi.org/10.1145/3580305.3599391) | Conditional diffusion imputation for time-series anomaly detection is close prior work. Its original authors' repository verifies the KDD title and authors: https://github.com/ChunjingXiao/DiffAD . |
| [ImDiffusion, Chen et al., 2023](https://arxiv.org/abs/2307.00754) | Imputation-based diffusion anomaly detection explicitly models temporal/inter-series dependency. PVLDB 17(3):359–372, November 2023; the PDF filename contains Zhang but the first author is Yuhang Chen. |
| [ICDiffAD, Zhang et al., 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/59a9cc95f046e9125d8816ef971873e7-Abstract-Conference.html) | Current work uses partially corrupted observed inputs for implicit conditioning. The present historically issued forecasts impose a different information boundary; no claim of the first diffusion fault detector. |
| [GDN, Deng and Hooi, 2021](https://doi.org/10.1609/aaai.v35i5.16523) | Learned embedding graphs, attention and robust prediction-error scoring motivate the strong conventional comparison. Reimplementation deviations: multiple channels, shared MLP head without batch normalization, group mapping, development normalization and independently calibrated thresholds. It sees causal target history, giving a shorter forecasting horizon than the diffusion reference. |
| [DCRNN, Li et al., 2018](https://github.com/liyaguang/DCRNN) | Original PEMS-BAY data/road graph source. The released file actually extends through June 30, unlike the prose's May 31 endpoint. The supplied file is an upstream processed product; per-value imputation lineage is not supplied. Our code retains zero masks and the March 12 timestamp gap. |
| [Chernozhukov et al., 2018](https://proceedings.mlr.press/v75/chernozhukov18a.html) | Dependent-data conformal inference requires additional assumptions/methodology. Our simpler scan-max rank proof is exchangeability-only. We do not claim their dependent-data guarantee for gapped sensor windows. Original PDF identifies the third author as Yinchu Zhu (the HTML citation metadata reverses the name). |

Proposed contribution: a testable, auditable combination of bidirectional local
correlation-spectrum trajectories, historically conditioned joint normal
references, group scanning, explicit missingness abstention, and a matched
feature-by-generator study. Novelty is the formulation and evidence, not any
individual entropy, diffusion, graph forecasting or rank-calibration primitive.
No superiority is presumed. Local spectral entropy discards information present
in full R, making the full-correlation comparison essential.
