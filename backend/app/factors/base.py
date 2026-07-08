from abc import ABC, abstractmethod

import pandas as pd


class FactorCalculator(ABC):
    name: str

    @abstractmethod
    def compute(self, **kwargs) -> pd.Series:
        """Return ticker-indexed scores in [0, 1]."""
