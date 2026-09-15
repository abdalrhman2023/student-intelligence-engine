"""
Focus Estimator.

Estimates effective cognitive focus duration before performance decay sets in.
"""

from typing import Dict, List
import numpy as np

try:
    from integration.data_contracts import StudySession, SessionStatus
except ImportError:
    from student_intelligence.integration.data_contracts import StudySession, SessionStatus


class FocusEstimator:
    """
    Computes uninterrupted focus capacity based on completed study logs.
    """

    def __init__(self) -> None:
        pass

    def estimate(self, sessions: List[StudySession]) -> Dict[str, float]:
        """
        Estimates sustained focus metrics from completed session durations.
        """
        completed_sessions = [s for s in sessions if s.status == SessionStatus.COMPLETED]

        if not completed_sessions:
            return {
                'effective_focus': 25.0,
                'mean_duration': 25.0,
                'max_sustained': 25.0,
                'recommended_session_length': 25.0
            }

        durations = [s.actual_duration_minutes for s in completed_sessions if s.actual_duration_minutes is not None]

        if not durations:
            return {
                'effective_focus': 25.0,
                'mean_duration': 25.0,
                'max_sustained': 25.0,
                'recommended_session_length': 25.0
            }

        durations_array = np.array(durations)

        effective_focus = float(np.median(durations_array))
        mean_duration = float(np.mean(durations_array))
        max_sustained = float(np.percentile(durations_array, 95))
        recommended_length = min(effective_focus, 50.0)

        return {
            'effective_focus': effective_focus,
            'mean_duration': mean_duration,
            'max_sustained': max_sustained,
            'recommended_session_length': recommended_length
        }
