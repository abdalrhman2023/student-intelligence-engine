"""
Procrastination Tracker.

Quantifies procrastination metrics globally and per subject area based on
rescheduling counts and initiation delay latencies.
"""

from typing import Dict, List, Any
from collections import defaultdict

try:
    from integration.data_contracts import StudySession, SessionStatus, ProcrastinationLevel, SubjectProcrastination
except ImportError:
    from student_intelligence.integration.data_contracts import StudySession, SessionStatus, ProcrastinationLevel, SubjectProcrastination


class ProcrastinationTracker:
    """
    Computes weighted procrastination indices.
    """

    def __init__(self, postpone_weight: float = 0.6, delay_weight: float = 0.4) -> None:
        self.postpone_weight = postpone_weight
        self.delay_weight = delay_weight

    def _calculate_score(self, sessions: List[StudySession]) -> float:
        """Computes combined postponement and delay latency index."""
        if not sessions:
            return 0.0

        total_sessions = len(sessions)
        postponed_count = sum(1 for s in sessions if s.status in [SessionStatus.POSTPONED, SessionStatus.CANCELLED])
        postpone_ratio = postponed_count / total_sessions

        started_sessions = [s for s in sessions if s.actual_start and s.planned_start]

        if not started_sessions:
            normalized_delay = 0.0
        else:
            total_delay = 0.0
            for s in started_sessions:
                delay = (s.actual_start - s.planned_start).total_seconds() / 60.0
                delay = max(0.0, delay)
                total_delay += delay

            avg_delay = total_delay / len(started_sessions)
            normalized_delay = min(avg_delay / 120.0, 1.0)

        score = (self.postpone_weight * postpone_ratio) + (self.delay_weight * normalized_delay)
        return max(0.0, min(1.0, score))

    def _get_level(self, score: float) -> ProcrastinationLevel:
        """Maps numerical score to categorical level."""
        if score < 0.3:
            return ProcrastinationLevel.LOW
        elif score < 0.6:
            return ProcrastinationLevel.MEDIUM
        else:
            return ProcrastinationLevel.HIGH

    def analyze(self, sessions: List[StudySession]) -> Dict[str, Any]:
        """Performs global and per-subject procrastination diagnostic."""
        if not sessions:
            return {
                'global_score': 0.0,
                'global_level': ProcrastinationLevel.LOW,
                'per_subject': [],
                'most_procrastinated_subject': None,
                'least_procrastinated_subject': None
            }

        global_score = self._calculate_score(sessions)
        global_level = self._get_level(global_score)

        subject_sessions = defaultdict(list)
        for s in sessions:
            subject_sessions[s.subject_id].append(s)

        per_subject = []
        for sub_id, sub_s in subject_sessions.items():
            score = self._calculate_score(sub_s)
            level = self._get_level(score)
            per_subject.append(SubjectProcrastination(subject_id=sub_id, score=round(score, 2), level=level))

        per_subject_sorted = sorted(per_subject, key=lambda x: x.score, reverse=True)
        most_procrastinated = per_subject_sorted[0].subject_id if per_subject_sorted else None
        least_procrastinated = per_subject_sorted[-1].subject_id if per_subject_sorted else None

        return {
            'global_score': round(global_score, 2),
            'global_level': global_level,
            'per_subject': per_subject,
            'most_procrastinated_subject': most_procrastinated,
            'least_procrastinated_subject': least_procrastinated
        }
