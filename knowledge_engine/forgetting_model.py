"""
Multi-factor Forgetting Curve Model.

Models retention degradation over elapsed time and accounts for the stabilizing
effects of spaced repetition based on modified Ebbinghaus formulations.
"""

import math
from typing import Tuple


class ForgettingModel:
    """
    Decay model incorporating base forgetting rate and repetition reinforcement.
    """

    def __init__(self, base_decay_rate: float = 0.05, review_benefit: float = 0.3):
        """
        Args:
            base_decay_rate: Baseline exponential decay velocity (lambda).
            review_benefit: Attenuation coefficient per successful repetition (alpha).
        """
        self.base_decay_rate = base_decay_rate
        self.review_benefit = review_benefit

    def apply_decay(self, base_mastery: float, days_since_review: float, successful_reviews: int) -> float:
        """
        Computes retention after an elapsed interval.

        Formula:
            mastery(t) = base_mastery * exp(-lambda / (1 + alpha * n_reviews) * delta_t)
        """
        effective_decay = self.base_decay_rate / (1.0 + self.review_benefit * successful_reviews)
        decayed_mastery = base_mastery * math.exp(-effective_decay * days_since_review)
        return max(0.0, min(1.0, decayed_mastery))

    def get_review_urgency(self, base_mastery: float, days_since_review: float, successful_reviews: int) -> Tuple[str, float]:
        """
        Evaluates review urgency by projecting prospective retention loss.

        Returns:
            Tuple of (urgency_level_str, projected_retention).
        """
        predicted_mastery = self.apply_decay(base_mastery, days_since_review, successful_reviews)

        if predicted_mastery < 0.3:
            urgency = 'critical'
        elif predicted_mastery < 0.5:
            urgency = 'high'
        elif predicted_mastery < 0.7:
            urgency = 'medium'
        else:
            urgency = 'low'

        return urgency, predicted_mastery
