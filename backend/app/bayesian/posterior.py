from dataclasses import dataclass

import numpy as np

from app.bayesian.likelihood import logit_to_prob, score_to_logit
from app.bayesian.prior import get_prior_up_prob
from app.config import settings


@dataclass
class PosteriorResult:
    posterior_up_prob: float
    prior_logit: float
    contributions: dict[str, float]


class PosteriorCalculator:
    def __init__(
        self,
        weights: tuple[float, float, float] | None = None,
        prior: float | None = None,
    ):
        self.weights = weights or (
            settings.factor_weights_pbr,
            settings.factor_weights_flow,
            settings.factor_weights_eps,
        )
        self.prior = prior if prior is not None else get_prior_up_prob()

    def compute(
        self,
        pbr_score: float,
        flow_score: float,
        eps_score: float,
    ) -> PosteriorResult:
        prior_logit = float(np.log(self.prior / (1.0 - self.prior)))
        names = ("pbr", "flow", "eps")
        scores = (pbr_score, flow_score, eps_score)
        contributions: dict[str, float] = {}
        logit = prior_logit
        for name, weight, score in zip(names, self.weights, scores):
            contrib = weight * score_to_logit(score)
            contributions[name] = contrib
            logit += contrib
        return PosteriorResult(
            posterior_up_prob=logit_to_prob(logit),
            prior_logit=prior_logit,
            contributions=contributions,
        )
