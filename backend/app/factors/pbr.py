import numpy as np
import pandas as pd

from app.factors.base import FactorCalculator


class PbrFactor(FactorCalculator):
    name = "pbr"

    def compute(self, pbr: pd.Series) -> pd.Series:
        if pbr.empty:
            return pd.Series(dtype="float64")
        valid = pbr.dropna()
        valid = valid[valid > 0]
        if valid.empty:
            return pd.Series(0.5, index=pbr.index, dtype="float64")
        ranks = valid.rank(pct=True, ascending=True)
        scores = 1.0 - ranks
        return scores.reindex(pbr.index).fillna(0.5)
