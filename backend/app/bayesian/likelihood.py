import numpy as np


def score_to_logit(score: float) -> float:
    clipped = float(np.clip(score, 0.01, 0.99))
    return float(np.log(clipped / (1.0 - clipped)))


def logit_to_prob(logit: float) -> float:
    return float(1.0 / (1.0 + np.exp(-logit)))
