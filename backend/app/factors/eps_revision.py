import numpy as np
import pandas as pd

from app.factors.base import FactorCalculator


class EpsRevisionFactor(FactorCalculator):
    name = "eps_revision"

    def compute(self, eps_revision_pct: pd.Series) -> pd.Series:
        if eps_revision_pct.empty:
            return pd.Series(dtype="float64")
        valid = eps_revision_pct.dropna()
        if valid.empty:
            return pd.Series(0.5, index=eps_revision_pct.index, dtype="float64")
        z = (valid - valid.mean()) / (valid.std() + 1e-9)
        scores = 1.0 / (1.0 + np.exp(-z))
        return scores.reindex(eps_revision_pct.index).fillna(0.5)
