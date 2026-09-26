# Primary-source comparison - checked 2026-09-23

| Source and access | Established result / assumptions | This pilot's use and unresolved difference |
|---|---|---|
| He and Kressner, [Randomized Joint Diagonalization of Symmetric Matrices](https://arxiv.org/html/2212.07248v4), [SIAM DOI](https://doi.org/10.1137/22M1541265). Full author text, Algorithm 1 and robust-recovery assumptions inspected; DOI endpoint failed retrieval. | Orthogonal eigensolves of Gaussian matrix combinations; select the best diagonalization across trials. Robust recovery concerns nearly commuting symmetric families. | Implements their RJD directly. London moving-horizon components are not assumed near commuting; measured failure is allowed. No new joint-diagonalization theorem. |
| Zahm and Nouy, [Interpolation of Inverse Operators for Preconditioning Parameter-Dependent Equations](https://arxiv.org/html/1504.07903v4), [SIAM J. Sci. Comput. 38(2), 2016](https://doi.org/10.1137/15M1019210). Full author text, Section 2 inspected; publication record retrieved. | Parameter-dependent inverse approximations, Frobenius projection, small Gram systems, randomized norm approximations, and residual-estimator conditioning. | Closely related offline/online reuse. Our full orthogonal basis and block majorant use a specific affine PSD measurement family. The general idea of shared matrix preprocessing and a cheap residual bound is inherited, not novel. |
| Bergamaschi and Martinez, [Parallel Newton-Chebyshev Polynomial Preconditioners for CG](https://arxiv.org/pdf/2008.01440). Full 13-page author text, Sections 2-4 inspected. | Polynomial inverse/preconditioner construction, spectral bounds, convergence/cost tradeoffs and large parallel solves. | Neumann corrections and PCG are established. A useful result here requires an empirical regime where setup, certification and corrections beat competent structured solves. This is not established by writing the bound. |
| [Ginkgo batched CG documentation](https://gko-project.org/user-guide/concepts/batched/cg.html). Official full page inspected. | Independent SPD systems with common dimensions/pattern; per-item stopping and Jacobi preconditioning. | Informs the competent batched comparator and residual stopping. Our PyTorch implementation is a transparent vectorized reference, not a performance claim against Ginkgo's fused kernels. |
| [NVIDIA cuSOLVER documentation](https://docs.nvidia.com/cuda/cusolver/). Official documentation retrieved; Cholesky routines consulted. | Existing dense/batched factorizations with hardware- and precision-dependent costs. | GPU Cholesky is accessed through PyTorch's supported library path. No new batching algorithm or assumed GPU advantage. Record synchronization, transfers and exact installed versions. |
| [UK Power Networks London Datastore release](https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d), official HTML and download metadata retrieved. | Half-hour interval energy, physical household identifiers and tariff groups; catalog approximately 167 million records and 5,567 households. [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) is the resource's linked license. | One 801,674,949-byte archive selected, not both representations. Actual counts belong in the manifest. Catalog does not resolve timezone/DST or supply provider access processes, feeders or boroughs. |

The prospective contribution is a measured connection between a real regional
household twin, source-access matrix families, computable block norm majorants,
output-level numerical error, and complete amortized cost. The inequalities use
standard norm domination and the inverse Neumann series. Neither their formal
originality nor publishability is established. If matrices do not admit useful
certificates or structured solvers dominate, the report must say so. There is
no unlearning, privacy, operational resilience, tariff causality, or production
distributed-deployment guarantee. Providers are simulated partitions of actual
sampled households. A complete publication novelty audit remains beyond this
bounded computational feasibility test.
