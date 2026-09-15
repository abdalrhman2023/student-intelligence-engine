"""
Bayesian Knowledge Tracing (BKT) Model.

Tracks latent concept mastery over sequential evaluation attempts
using a two-state Hidden Markov Model formulation.
"""

from typing import Dict, List, Optional

try:
    from integration.data_contracts import BKTParams, QuizInteraction
except ImportError:
    from student_intelligence.integration.data_contracts import BKTParams, QuizInteraction


class BKTKnowledgeTracer:
    """
    Standard Bayesian Knowledge Tracing implementation with observation updating
    and learning state transition mechanics.
    """

    def __init__(self, default_params: Optional[BKTParams] = None):
        self.default_params = default_params
        # Mapping: user_id -> topic_id -> latent mastery probability P(L)
        self._states: Dict[str, Dict[str, float]] = {}
        # Mapping: user_id -> topic_id -> list of raw interaction records
        self._history: Dict[str, Dict[str, List[QuizInteraction]]] = {}

    def update(self, interaction: QuizInteraction) -> float:
        """
        Updates the latent mastery probability P(L) following an observed response.

        Args:
            interaction: Evaluated QuizInteraction instance.

        Returns:
            Updated posterior probability of mastery P(L_t+1).
        """
        user_id = interaction.user_id
        topic_id = interaction.topic_id
        is_correct = interaction.is_correct

        if user_id not in self._states:
            self._states[user_id] = {}
        if user_id not in self._history:
            self._history[user_id] = {}

        if topic_id not in self._history[user_id]:
            self._history[user_id][topic_id] = []

        self._history[user_id][topic_id].append(interaction)

        # Retrieve parameters
        p_t = self.default_params.p_transit if self.default_params else 0.15
        p_g = self.default_params.p_guess if self.default_params else 0.25
        p_s = self.default_params.p_slip if self.default_params else 0.10
        p_l0 = self.default_params.p_init if self.default_params else 0.10

        p_l = self._states[user_id].get(topic_id, p_l0)

        # Observation update
        if is_correct:
            numerator = p_l * (1.0 - p_s)
            denominator = numerator + (1.0 - p_l) * p_g
        else:
            numerator = p_l * p_s
            denominator = numerator + (1.0 - p_l) * (1.0 - p_g)

        p_l_given_obs = numerator / denominator if denominator > 0 else 0.0

        # Learning transition update
        p_l_new = p_l_given_obs + (1.0 - p_l_given_obs) * p_t

        self._states[user_id][topic_id] = p_l_new
        return p_l_new

    def get_mastery(self, user_id: str, topic_id: str) -> float:
        """Returns current mastery estimate or 0.0 if unobserved."""
        return self._states.get(user_id, {}).get(topic_id, 0.0)

    def get_all_masteries(self, user_id: str) -> Dict[str, float]:
        """Returns topic mastery mapping for a given user."""
        return self._states.get(user_id, {})

    def get_answer_history(self, user_id: str, topic_id: str) -> List[QuizInteraction]:
        """Returns chronological assessment history for a concept."""
        return self._history.get(user_id, {}).get(topic_id, [])

    def batch_update(self, interactions: List[QuizInteraction]) -> Dict[str, Dict[str, float]]:
        """Processes a chronological sequence of interactions."""
        try:
            sorted_interactions = sorted(interactions, key=lambda i: i.timestamp)
        except AttributeError:
            sorted_interactions = interactions

        for interaction in sorted_interactions:
            self.update(interaction)

        return self._states
