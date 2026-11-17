"""Judge calibration and paired evaluation statistics.

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    if len(human) != len(judge):
        raise ValueError("human and judge must have the same number of labels")
    h = [str(x).strip().upper() == POS for x in human]
    j = [str(x).strip().upper() == POS for x in judge]
    return {"tp": sum(a and b for a, b in zip(h, j)),
            "fp": sum(not a and b for a, b in zip(h, j)),
            "fn": sum(a and not b for a, b in zip(h, j)),
            "tn": sum(not a and not b for a, b in zip(h, j))}


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    """Return failure-class precision and recall, using zero for empty denominators."""
    cm = confusion(human, judge)
    tp, fp, fn = cm["tp"], cm["fp"], cm["fn"]
    return (tp / (tp + fp) if tp + fp else 0.0,
            tp / (tp + fn) if tp + fn else 0.0)


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    cm = confusion(human, judge)
    n = sum(cm.values())
    if not n:
        raise ValueError("kappa is undefined for empty labels")
    po = (cm["tp"] + cm["tn"]) / n
    human_pos = cm["tp"] + cm["fn"]
    judge_pos = cm["tp"] + cm["fp"]
    pe = (human_pos * judge_pos + (n - human_pos) * (n - judge_pos)) / (n * n)
    if pe == 1:
        raise ValueError("kappa is undefined when expected agreement is 1")
    return (po - pe) / (1 - pe)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    if not all(0 <= x <= 1 for x in (observed_rate, sensitivity, specificity)):
        raise ValueError("rates must be between 0 and 1")
    denom = sensitivity + specificity - 1
    if denom <= 0:
        raise ValueError("sensitivity and specificity do not identify the true rate")
    return min(1.0, max(0.0, (observed_rate + specificity - 1) / denom))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    import numpy as np
    from scipy.stats import bootstrap
    if len(a) != len(b) or not a:
        raise ValueError("paired samples must have equal, nonzero length")
    if n_resamples <= 0 or not 0 < confidence < 1:
        raise ValueError("n_resamples must be positive and confidence between 0 and 1")
    aa, bb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if not np.isfinite(aa).all() or not np.isfinite(bb).all():
        raise ValueError("samples must be finite")
    delta = float(np.mean(aa) - np.mean(bb))
    if np.array_equal(aa, bb):
        return (0.0, 0.0, 0.0)
    res = bootstrap((aa, bb), lambda x, y: np.mean(x - y), paired=True,
                    vectorized=False, n_resamples=n_resamples,
                    confidence_level=confidence, method="percentile",
                    rng=np.random.default_rng(rng))
    return delta, float(res.confidence_interval.low), float(res.confidence_interval.high)


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    _validate_pass_args(n, c, k)
    import math
    if k > n - c:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    _validate_pass_args(n, c, k)
    import math
    return math.comb(c, k) / math.comb(n, k) if k <= c else 0.0


def _validate_pass_args(n: int, c: int, k: int) -> None:
    if any(not isinstance(x, int) or isinstance(x, bool) for x in (n, c, k)):
        raise ValueError("n, c, and k must be integers")
    if n <= 0 or not 0 <= c <= n or not 1 <= k <= n:
        raise ValueError("require n > 0, 0 <= c <= n, and 1 <= k <= n")
