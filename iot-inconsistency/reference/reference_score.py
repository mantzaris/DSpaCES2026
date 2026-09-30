"""Numerical reference for the proposed score, not a trained fault detector.

Loss axes: [ensemble_member, paired_replicate, provenance_group].
The production PyTorch/CUDA implementation must agree with this reference.
"""
from __future__ import annotations

import json
import numpy as np


def normalized_empirical_crps(
    predictive_samples: np.ndarray,
    observed_values: np.ndarray,
    training_scale: np.ndarray | float,
) -> np.ndarray:
    """Score a finite predictive sample distribution; sample axis is last."""
    samples = np.asarray(predictive_samples, dtype=np.float64)
    observed = np.asarray(observed_values, dtype=np.float64)
    scale = np.asarray(training_scale, dtype=np.float64)
    if samples.ndim < 1 or samples.shape[-1] == 0:
        raise ValueError("At least one predictive sample is required.")
    if observed.shape != samples.shape[:-1]:
        raise ValueError("Observation shape must match all non-sample axes.")
    scale = np.broadcast_to(scale, observed.shape)
    if not all(np.isfinite(values).all() for values in (samples, observed, scale)):
        raise ValueError("Exclude missing targets explicitly; inputs must be finite.")
    if np.any(scale <= 0):
        raise ValueError("Use positive, frozen training scales.")
    sample_count = samples.shape[-1]
    first_term = np.mean(np.abs(samples - observed[..., None]), axis=-1)
    sorted_samples = np.sort(samples, axis=-1)
    ranks = np.arange(1, sample_count + 1, dtype=np.float64)
    coefficients = 2 * ranks - sample_count - 1
    second_term = np.sum(sorted_samples * coefficients, axis=-1) / sample_count**2
    result = (first_term - second_term) / scale
    if np.any(result < -1e-10):
        raise ArithmeticError("CRPS should not be materially negative.")
    return np.maximum(result, 0.0)


def canonicalize_groups(
    loss_before: np.ndarray,
    loss_after: np.ndarray,
    provenance_ids: list[str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Deduplicate exact repeated groups and return uniform unique-group weights.

    This is a final arithmetic guard. Real provenance must be deduplicated
    before model inputs and group losses are constructed as well.
    """
    before = np.asarray(loss_before, dtype=np.float64)
    after = np.asarray(loss_after, dtype=np.float64)
    if before.ndim != 3 or before.shape != after.shape:
        raise ValueError("Expected matching [ensemble, replicate, group] losses.")
    if before.shape[-1] != len(provenance_ids) or not provenance_ids:
        raise ValueError("Every group needs a canonical provenance identity.")
    if not np.isfinite(before).all() or not np.isfinite(after).all():
        raise ValueError("Losses must be finite.")
    first_indices: dict[str, int] = {}
    for position, identity in enumerate(provenance_ids):
        if not isinstance(identity, str) or not identity:
            raise ValueError("Provenance identities must be nonempty strings.")
        if identity in first_indices:
            previous = first_indices[identity]
            for values in (before, after):
                if not np.allclose(values[..., position], values[..., previous],
                                   rtol=1e-12, atol=1e-12):
                    raise ValueError("Conflicting copies require explicit provenance resolution.")
        else:
            first_indices[identity] = position
    selected = list(first_indices.values())
    weights = np.full(len(selected), 1.0 / len(selected), dtype=np.float64)
    return before[..., selected], after[..., selected], weights


def repair_score(
    loss_before: np.ndarray,
    loss_after: np.ndarray,
    group_weights: np.ndarray,
    edit_cost: float,
    uncertainty_weight: float = 1.0,
    edit_weight: float = 0.2,
) -> dict[str, float]:
    """Compute mean gain minus ensemble disagreement and edit penalties.

    Each replicate includes a repair and paired before/after predictive draws.
    Model standard deviation is NOT divided by sqrt(ensemble_count).
    Monte Carlo SE is a sampling diagnostic, not fault confidence.
    """
    before = np.asarray(loss_before, dtype=np.float64)
    after = np.asarray(loss_after, dtype=np.float64)
    weights = np.asarray(group_weights, dtype=np.float64)
    if before.ndim != 3 or before.shape != after.shape:
        raise ValueError("Expected matching [ensemble, replicate, group] losses.")
    ensemble_count, replicate_count, group_count = before.shape
    if ensemble_count < 2 or replicate_count < 2 or group_count < 1:
        raise ValueError("Need at least two models, two replicates, and one group.")
    if weights.shape != (group_count,):
        raise ValueError("One weight is required per unique provenance group.")
    if not all(np.isfinite(values).all() for values in (before, after, weights)):
        raise ValueError("Losses and weights must be finite.")
    if np.any(before < 0) or np.any(after < 0):
        raise ValueError("CRPS losses must be nonnegative.")
    if np.any(weights < 0) or not np.isclose(weights.sum(), 1.0):
        raise ValueError("Weights must be nonnegative and sum to one.")
    penalties = np.asarray([edit_cost, uncertainty_weight, edit_weight])
    if not np.isfinite(penalties).all() or np.any(penalties < 0):
        raise ValueError("Costs and penalty weights must be finite and nonnegative.")
    paired_gains = np.sum((before - after) * weights[None, None, :], axis=-1)
    model_gains = paired_gains.mean(axis=1)
    mean_gain = float(model_gains.mean())
    model_instability = float(model_gains.std(ddof=1))
    monte_carlo_variance = np.sum(paired_gains.var(axis=1, ddof=1) / replicate_count)
    monte_carlo_standard_error = float(np.sqrt(monte_carlo_variance / ensemble_count**2))
    score = mean_gain - uncertainty_weight * model_instability - edit_weight * edit_cost
    return {
        "score": float(score),
        "mean_gain": mean_gain,
        "model_instability": model_instability,
        "edit_cost": float(edit_cost),
        "monte_carlo_standard_error": monte_carlo_standard_error,
    }


def null_tail_value(calibration_scores: np.ndarray, candidate_score: float) -> float:
    scores = np.asarray(calibration_scores, dtype=np.float64)
    if scores.ndim != 1 or scores.size == 0 or not np.isfinite(scores).all():
        raise ValueError("Provide a nonempty finite one-dimensional calibration array.")
    if not np.isfinite(candidate_score):
        raise ValueError("The candidate score must be finite.")
    return float((1 + np.count_nonzero(scores >= candidate_score)) / (scores.size + 1))


def run_numerical_checks() -> dict:
    checks: list[str] = []
    generator = np.random.default_rng(9026)
    samples = generator.normal(size=(7, 11))
    observations = generator.normal(size=7)
    scales = generator.uniform(0.5, 2.0, size=7)
    pairwise_crps = (
        np.abs(samples - observations[:, None]).mean(axis=-1)
        - 0.5 * np.abs(samples[:, :, None] - samples[:, None, :]).mean(axis=(-2, -1))
    ) / scales
    np.testing.assert_allclose(normalized_empirical_crps(samples, observations, scales),
                               pairwise_crps, rtol=1e-12, atol=1e-12)
    checks.append("sorted_CRPS_matches_pairwise_definition")
    np.testing.assert_allclose(normalized_empirical_crps(np.full((1, 8), 2.0),
                               np.array([3.0]), 2.0), [0.5])
    checks.append("deterministic_CRPS_equals_scaled_absolute_error")
    np.testing.assert_allclose(normalized_empirical_crps(-3 * samples + 7,
                               -3 * observations + 7, 3 * scales), pairwise_crps)
    checks.append("CRPS_invariant_to_consistent_affine_unit_change")

    before = np.ones((3, 4, 3))
    after = np.broadcast_to(np.array([0.45, 0.50, 0.55])[:, None, None], before.shape).copy()
    weights = np.full(3, 1 / 3)
    result = repair_score(before, after, weights, edit_cost=0.1)
    np.testing.assert_allclose([result['mean_gain'], result['model_instability'], result['score']],
                               [0.5, 0.05, 0.43], atol=1e-12)
    checks.append("hand_calculated_score_0_43")
    np.testing.assert_allclose(repair_score(before, before, weights, 0.0)['score'], 0.0)
    checks.append("no_op_repair_has_zero_score")
    assert repair_score(before, before + 0.2, weights, 0.0)['score'] < 0
    checks.append("worse_repair_has_negative_score")
    higher_cost = repair_score(before, after, weights, 0.3)
    np.testing.assert_allclose(result['score'] - higher_cost['score'], 0.2 * (0.3 - 0.1))
    checks.append("edit_cost_penalty_has_correct_sign_and_slope")
    unstable_after = np.broadcast_to(np.array([0.3, 0.5, 0.7])[:, None, None], before.shape)
    unstable_result = repair_score(before, unstable_after, weights, 0.1)
    np.testing.assert_allclose(unstable_result['mean_gain'], result['mean_gain'])
    assert unstable_result['score'] < result['score']
    checks.append("ensemble_disagreement_lowers_equal_mean_gain_score")

    duplicated_before = np.concatenate([before, before[..., [1]]], axis=-1)
    duplicated_after = np.concatenate([after, after[..., [1]]], axis=-1)
    unique_before, unique_after, unique_weights = canonicalize_groups(
        duplicated_before, duplicated_after, ['sensor_a', 'sensor_b', 'sensor_c', 'sensor_b'])
    np.testing.assert_allclose(repair_score(unique_before, unique_after, unique_weights, 0.1)['score'],
                               result['score'])
    checks.append("known_duplicate_provenance_does_not_change_score")
    conflicting_after = duplicated_after.copy()
    conflicting_after[..., -1] += 0.1
    try:
        canonicalize_groups(duplicated_before, conflicting_after,
                            ['sensor_a', 'sensor_b', 'sensor_c', 'sensor_b'])
    except ValueError:
        checks.append("conflicting_duplicate_evidence_is_rejected")
    else:
        raise AssertionError("Conflicting duplicated evidence was accepted.")

    noisy_before = generator.uniform(0.5, 1.5, size=(3, 9, 4))
    noisy_after = generator.uniform(0.1, 1.0, size=(3, 9, 4))
    nonuniform_weights = np.array([0.1, 0.2, 0.3, 0.4])
    reference_model_gains = []
    for model_index in range(3):
        replicate_gains = []
        for replicate_index in range(9):
            replicate_gains.append(sum(
                nonuniform_weights[group_index] *
                (noisy_before[model_index, replicate_index, group_index]
                 - noisy_after[model_index, replicate_index, group_index])
                for group_index in range(4)))
        reference_model_gains.append(sum(replicate_gains) / 9)
    scalar_score = np.mean(reference_model_gains) - np.std(reference_model_gains, ddof=1) - 0.02
    np.testing.assert_allclose(repair_score(noisy_before, noisy_after, nonuniform_weights, 0.1)['score'],
                               scalar_score, atol=1e-12)
    checks.append("vectorized_score_matches_independent_scalar_loops")
    reference_null = np.array([0.0, 0.1, 0.2, 0.3, 0.4])
    np.testing.assert_allclose(null_tail_value(reference_null, 0.43), 1 / 6)
    assert null_tail_value(reference_null, 0.43) <= null_tail_value(reference_null, 0.2)
    assert null_tail_value(reference_null, -1) == 1.0
    checks.append("rank_tail_value_has_correct_direction_and_resolution")
    invalid_before = before.copy()
    invalid_before[0, 0, 0] = np.nan
    try:
        repair_score(invalid_before, after, weights, 0.1)
    except ValueError:
        checks.append("missing_loss_is_not_silently_treated_as_zero")
    else:
        raise AssertionError("NaN loss was accepted.")
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "illustrative_score_components": result,
            "scope": "Arithmetic/reference checks only; no detector was trained or evaluated."}


if __name__ == '__main__':
    print(json.dumps(run_numerical_checks(), indent=2))

