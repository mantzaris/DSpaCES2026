"""Outcome scoring lives outside the deployable consumer boundary."""
import numpy as np


def score(mean, variance, outcomes, mask, scale, correction=None):
    valid = np.asarray(mask) & np.isfinite(outcomes) & np.isfinite(mean) & np.isfinite(variance) & (variance >= 0)
    y, mu, sd = outcomes[valid], mean[valid], np.sqrt(variance[valid])
    if len(y) == 0:
        raise ValueError('No observed scoring targets')
    q90, q95, q80 = (1.6448536269514722, 1.959963984540054, .8416212335729143) if correction is None else (correction['q90'], correction['q95'], correction['q80'])
    lower, upper = mu-q90*sd, mu+q90*sd
    interval = upper-lower + 20*np.maximum(lower-y, 0) + 20*np.maximum(y-upper, 0)
    reserve = np.maximum(mu + q80*sd, 0)
    loss = 4*np.maximum(y-reserve, 0) + np.maximum(reserve-y, 0)
    error = mu-y
    return dict(n=len(y), mae=float(np.mean(np.abs(error))), rmse=float(np.sqrt(np.mean(error**2))),
                bias=float(np.mean(error)), coverage90=float(np.mean(np.abs(error) <= q90*sd)),
                coverage95=float(np.mean(np.abs(error) <= q95*sd)), width90=float(np.mean(upper-lower)),
                normalized_is90=float(np.mean(interval)/scale), interval_score90=float(np.mean(interval)),
                reservation_loss=float(np.mean(loss)), normalized_reservation_loss=float(np.mean(loss)/scale))


def autocorrelation(residuals, lag):
    a, b = residuals[:-lag], residuals[lag:]
    valid = np.isfinite(a) & np.isfinite(b)
    if valid.sum() < 3 or np.std(a[valid]) == 0 or np.std(b[valid]) == 0:
        return None
    return float(np.corrcoef(a[valid], b[valid])[0, 1])
