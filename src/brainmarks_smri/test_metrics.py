import numpy as np
import pytest
import torch
from sklearn import metrics as sklearn_metrics

from brainmarks_smri.metrics import (
    auroc,
    bootstrap_ci,
    bootstrap_score,
    lesion_f1,
    r2_score,
)


def test_auroc_matches_sklearn():
    rng = np.random.default_rng(0)
    labels = rng.integers(0, 3, 200)
    probabilities = rng.dirichlet(np.ones(3), 200)
    probabilities[:20] = probabilities[20:40]  # ties
    expected = sklearn_metrics.roc_auc_score(
        labels, probabilities, multi_class="ovr", average="macro"
    )
    assert auroc(labels, probabilities) == pytest.approx(expected)
    binary = (labels > 0).astype(int)
    assert auroc(binary, probabilities[:, :2]) == pytest.approx(
        sklearn_metrics.roc_auc_score(binary, probabilities[:, 1])
    )


def test_r2_score_matches_sklearn():
    rng = np.random.default_rng(0)
    targets = rng.normal(size=50)
    predictions = targets + rng.normal(size=50)
    expected = sklearn_metrics.r2_score(targets, predictions)
    assert r2_score(targets, predictions) == pytest.approx(expected)


def test_bootstrap_score_strata():
    strata = np.array([0] * 7 + [1] * 43)
    point, values = bootstrap_score(np.mean, strata, strata=strata, n_bootstrap=100)
    assert point == pytest.approx(43 / 50)
    # the stratum sizes are kept, so the share of ones never changes
    assert values == pytest.approx(np.full(100, 43 / 50))


def test_bootstrap_ci_from_bootstrap_score():
    values = np.random.default_rng(0).normal(size=50)
    _, resampled = bootstrap_score(np.mean, values, seed=3)
    assert bootstrap_ci(np.mean, values, seed=3) == pytest.approx(
        np.percentile(resampled, [2.5, 97.5])
    )


def test_lesion_f1():
    """Two label lesions, one detected (by one overlapping voxel) by one of three predicted
    lesions; diagonal neighbours are one lesion (26-connectivity)."""
    target = torch.zeros(10, 10, 10, dtype=torch.bool)
    target[1, 1, 1] = target[2, 2, 2] = True  # one lesion, diagonal neighbours
    target[7, 7, 7] = True
    predicted = torch.zeros_like(target)
    predicted[2, 2, 2] = predicted[2, 2, 3] = True  # overlaps the first lesion
    predicted[5, 0, 0] = True
    predicted[0, 9, 9] = True
    # sensitivity 1/2, precision 1/3
    assert lesion_f1(predicted, target) == pytest.approx(2 * (1 / 2) * (1 / 3) / (1 / 2 + 1 / 3))
    assert lesion_f1(torch.zeros_like(target), target) == 0.0
    assert np.isnan(lesion_f1(predicted, torch.zeros_like(target)))
