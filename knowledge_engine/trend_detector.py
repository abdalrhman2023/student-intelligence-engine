"""
Trend Detector.

Detects performance momentum using Dual Exponential Moving Averages (Dual-EMA).
"""

from typing import List, Tuple

try:
    from integration.data_contracts import TrendDirection
except ImportError:
    from student_intelligence.integration.data_contracts import TrendDirection


class TrendDetector:
    """
    Computes directional momentum by contrasting short-term and long-term EMA windows.
    """

    def __init__(self, short_window: int = 5, long_window: int = 15, threshold: float = 0.03):
        self.short_window = short_window
        self.long_window = long_window
        self.threshold = threshold

    def _ema(self, values: List[float], window: int) -> float:
        """Calculates Exponential Moving Average across a series."""
        if not values:
            return 0.0

        alpha = 2.0 / (window + 1.0)
        ema = values[0]
        for value in values[1:]:
            ema = (value - ema) * alpha + ema
        return ema

    def detect(self, score_history: List[float]) -> Tuple[TrendDirection, float]:
        """
        Evaluates trend direction and returns (TrendDirection, delta).
        """
        if len(score_history) < self.short_window:
            return TrendDirection.STABLE, 0.0

        short_ema = self._ema(score_history[-self.short_window:], self.short_window)
        long_sub = score_history[-self.long_window:] if len(score_history) >= self.long_window else score_history
        long_ema = self._ema(long_sub, min(self.long_window, len(score_history)))

        delta = short_ema - long_ema

        if delta > self.threshold:
            return TrendDirection.IMPROVING, delta
        elif delta < -self.threshold:
            return TrendDirection.DECLINING, delta
        else:
            return TrendDirection.STABLE, delta
