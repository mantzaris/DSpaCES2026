# Graph-flow comparison with primary research

Verified on 2026-10-01. Downloaded paper and author-code hashes are in
`graph_flow_sources.json`. PDFs and upstream caches are not Git artifacts.
The reviewed methods establish graph-conditioned flows, explicit probabilistic
fault hypotheses, likelihood ratios and Bayesian reconstruction. This project
is an empirical combination and extension, not an invention of these equations.
The search cannot establish that no earlier system implements the same procedure.

| Primary source | Established method | Relationship to this study |
| --- | --- | --- |
| [GANF, Dai and Chen, 2022](https://arxiv.org/abs/2202.07857), [author code](https://github.com/EnyanDai/GANF) | Recurrent history, learned directed associations and conditional normalizing flows model multivariate series. Likelihood supports anomaly detection and localization. | Closest required graph-flow baseline. We import the authors' unchanged RNN, GNN and MAF at revision `bce38333b109f325a403dae9aff4987ae5bd6e1f`. Our hypothesis integration is an added procedure, not a new graph-flow principle. |
| [MTGFlow, 2022](https://arxiv.org/abs/2208.02108), [extended study](https://arxiv.org/abs/2312.11549) | Dynamic graph conditioning and entity-specific density modeling address multivariate anomaly detection. | Confirms that graph and temporal conditional density modeling is established. Reviewed as a further comparator. No custom model is labeled MTGFlow. Its execution status is reported separately. |
| [Ren et al., 2019](https://proceedings.neurips.cc/paper/2019/hash/1e79596878b2320cac26dd792a6c51c9-Abstract.html) | A likelihood ratio separates background statistics from semantic signals in out-of-distribution detection. | Ordinary likelihood can be misleading. Our numerator integrates specified measurement channels instead of training the paper's background model. The ratio itself is established. |
| [Tipping and Bishop, PPCA, 1999](https://www.microsoft.com/en-us/research/publication/probabilistic-principal-component-analysis/) | A linear Gaussian latent-variable model yields a normalized density and posterior distributions. | Supplies the analytic conditional Gaussian control and repairs. We never claim PCA-family models cannot generate values or provide uncertainty. |
| [Tipping and Bishop, mixture PPCA, 1999](https://www.microsoft.com/en-us/research/publication/mixtures-of-probabilistic-principal-component-analyzers/) | Mixtures combine local probabilistic linear models, fitted through EM. | Required multiple-regime control. Context-dependent mixture weights follow Bayes' rule, without seeing the tested target. |
| [CSDI, 2021](https://arxiv.org/abs/2107.03502) | Conditional diffusion generates missing time-series values from observed coordinates. | Conditional numerical generation and distributional imputation precede this study. The legacy diffusion witness method is a separate implementation and is not renamed CSDI. |
| [PriSTI, 2023](https://arxiv.org/abs/2302.09746) | Conditional diffusion combines spatial dependencies and temporal information for imputation. | Graph-informed generation is established. Imputation of missing values differs from deciding whether an observed interval is faulty. |
| [ImDiffusion, 2023](https://arxiv.org/abs/2307.00754) | Diffusion imputation supports multivariate time-series anomaly detection. | Generative reconstruction for detection is not novel. Our normal and corruption densities explicitly define the two explanations. |
| [Whang, Lei and Dimakis, 2021](https://proceedings.mlr.press/v139/whang21a.html) | A flow prior and structured noise likelihood define MAP recovery for inverse problems. | Direct precedent for a generative prior plus corruption model and Bayesian repair. Our score estimates marginal fault evidence, then reports a weighted distribution instead of only MAP. |
| [Wright and Horowitz, 2017](https://horowitz.me.berkeley.edu/Publications_files/All_papers_numbered/Wright_Particle-Filter-Enabled-Faults_IEEE_CDC_2017.pdf) | Particle filtering treats latent states and sensor-fault indicators jointly, integrating uncertain system state when judging sensors. | A particularly close conceptual precedent. Comparing normal and faulty observation explanations through sampled latent states is established. We evaluate a learned conditional neural flow with fixed short-block corruption channels and explicit provenance. |
| [Mehranbod, Soroush and Panjapornpon, 2005](https://doi.org/10.1016/j.jprocont.2004.06.009) | Bayesian belief networks support sensor-fault detection and identification under transient and steady operation. | Bias, drift and noise hypotheses and probabilistic sensor diagnosis have a long history. The publicly accessible primary abstract was reviewed; unavailable full text is not represented as inspected. |
| [Weilbach et al., 2020](https://proceedings.mlr.press/v108/weilbach20a.html) | Graphical-model structure constrains conditional continuous flows for amortized inference. | Structure-aware conditional flow inference is established. Our small affine-coupling architecture is a practical choice, not a new flow family. |
| [Baumgartner, da Silva and Urteaga, UAI 2026](https://proceedings.mlr.press/v337/baumgartner26a.html) | Conditional flows impose temporal latent-state dynamics and test compliance with those dynamics. | Recent evidence that observed-space likelihood alone is insufficient. Their latent goodness-of-fit test differs from our integrated measurement-channel ratio. |

The candidate contribution is a reproducible comparison of conditional graph
sampling, normalized sensor-corruption hypotheses, interval localization and
weighted repair in three dataset families. Matched Gaussian channels, a classifier
with the same fault information, ordinary likelihood and graph-context ablations
identify which ingredients deserve credit. Unseen mechanisms, missing context and
coordinated changes test the limits. Acceptance-worthy evidence can be a clear
negative result with a useful explanation. No superiority claim is made here.

The workshop's [current instructions](https://sites.google.com/unisalento.it/ieee-dspaces-2026/home)
allow full papers of at most ten IEEE two-column pages including references.
This was rechecked on 2026-10-01. No supplementary-file permission is assumed.
