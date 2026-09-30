# Equation audit

The extracted NumPy oracle passes 13 checks in `results/audits/reference_checks.json`. The illustrative score is R 0.50 minus U 0.05 minus 0.2 times Omega 0.10, giving S 0.43. This is not detection performance.

Production E4 and E6 through E11 are implemented in `src/iot_repair/scoring.py`. E9 is in `costs.py`, E1 in `preprocessing.py` and E12 through E14 in `calibration.py`. `scripts/audit_equations.py` saves identical inputs and compares scalar reference values against batched Torch on CPU and CUDA. Tolerances are 1e-11 for float64 and 2e-6 for float32. Model-context and integration checks remain required.
