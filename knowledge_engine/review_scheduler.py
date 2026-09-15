"""
Review Scheduler.

Ranks concepts by review urgency considering current mastery,
projected retention loss, measurement confidence, and recall history.
"""

from typing import List

from .forgetting_model import ForgettingModel

try:
    from integration.data_contracts import TopicKnowledgeState
except ImportError:
    from student_intelligence.integration.data_contracts import TopicKnowledgeState


class ReviewScheduler:
    """
    Spaced repetition queue generator.
    """

    def __init__(self, forgetting_model: ForgettingModel = None):
        self.forgetting_model = forgetting_model or ForgettingModel()

    def prioritize(self, topic_states: List[TopicKnowledgeState]) -> List[str]:
        """
        Ranks topic IDs in descending order of review urgency.

        Priority Score Formulation:
            priority = (1 - mastery_score) * (1 + days_since_review / 7) * confidence * (1 / (1 + successful_reviews))
        """
        priorities = []

        for state in topic_states:
            priority_score = (
                (1.0 - state.mastery_score) *
                (1.0 + state.days_since_review / 7.0) *
                state.confidence *
                (1.0 / (1.0 + state.successful_reviews))
            )
            priorities.append((state.topic_id, priority_score))

        priorities.sort(key=lambda x: x[1], reverse=True)
        return [topic_id for topic_id, score in priorities]
