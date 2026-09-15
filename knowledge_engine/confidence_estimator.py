"""
Confidence Estimator.

Quantifies measurement certainty based on sample size and observation volume.
"""

import math


class ConfidenceEstimator:
    """
    Computes statistical confidence scores for knowledge and behavior states.
    """

    def __init__(self, scaling_factor: float = 0.1):
        """
        Args:
            scaling_factor: Exponential scale parameter controlling rate of saturation (beta).
        """
        self.scaling_factor = scaling_factor

    def estimate(self, num_observations: int) -> float:
        """
        Calculates confidence score in range [0, 1].

        Formula:
            confidence = 1 - exp(-beta * num_observations)
        """
        return 1.0 - math.exp(-self.scaling_factor * max(0, num_observations))

    def get_confidence_label(self, num_observations: int) -> str:
        """Categorizes sample size into discrete confidence tiers."""
        if num_observations < 5:
            return 'cold_start'
        elif num_observations < 15:
            return 'low'
        elif num_observations < 30:
            return 'moderate'
        else:
            return 'high'

    def is_reliable(self, num_observations: int, threshold: float = 0.5) -> bool:
        """Evaluates whether observations satisfy reliability cutoff."""
        return self.estimate(num_observations) >= threshold
