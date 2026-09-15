"""
Productivity Analyzer.

Analyzes completed study session distributions across the 24-hour cycle
to detect optimal cognitive performance windows and low-yield periods.
"""

from typing import Dict, List, Any
from collections import defaultdict

try:
    from integration.data_contracts import StudySession, ProductivitySlot, SessionStatus
except ImportError:
    from student_intelligence.integration.data_contracts import StudySession, ProductivitySlot, SessionStatus


class ProductivityAnalyzer:
    """
    Extracts peak and dead study slots from historical session execution.
    """

    def __init__(self) -> None:
        pass

    def analyze(self, sessions: List[StudySession]) -> Dict[str, Any]:
        """
        Calculates hourly task completion rates and extracts clustered productivity windows.
        """
        hour_counts: Dict[int, int] = defaultdict(int)
        hour_completed: Dict[int, int] = defaultdict(int)

        for session in sessions:
            dt = session.actual_start or session.planned_start
            if not dt:
                continue

            hour = dt.hour
            hour_counts[hour] += 1

            if session.status == SessionStatus.COMPLETED:
                hour_completed[hour] += 1

        hourly_scores: Dict[int, float] = {}
        for hour, total in hour_counts.items():
            if total >= 2:
                hourly_scores[hour] = round(hour_completed[hour] / total, 2)

        peak_hours = sorted([h for h, score in hourly_scores.items() if score >= 0.7])
        dead_hours = sorted([h for h, score in hourly_scores.items() if score <= 0.35])

        peak_slots = self._group_hours_to_slots(peak_hours, hourly_scores)
        dead_slots = self._group_hours_to_slots(dead_hours, hourly_scores)

        return {
            'hourly_scores': hourly_scores,
            'peak_slots': peak_slots,
            'dead_slots': dead_slots
        }

    def _group_hours_to_slots(self, hours: List[int], scores: Dict[int, float]) -> List[ProductivitySlot]:
        """Clusters consecutive hours into continuous temporal windows."""
        if not hours:
            return []

        slots = []
        current_group = [hours[0]]

        for i in range(1, len(hours)):
            if hours[i] == current_group[-1] + 1:
                current_group.append(hours[i])
            else:
                slots.append(self._create_slot(current_group, scores))
                current_group = [hours[i]]

        slots.append(self._create_slot(current_group, scores))
        return slots

    def _create_slot(self, group: List[int], scores: Dict[int, float]) -> ProductivitySlot:
        """Instantiates a formatted ProductivitySlot."""
        start_hour = group[0]
        end_hour = group[-1] + 1

        start_str = f"{start_hour:02d}:00"
        end_str = f"{end_hour:02d}:00" if end_hour < 24 else "00:00"

        avg_score = sum(scores.get(h, 0.5) for h in group) / len(group)

        return ProductivitySlot(
            start_hour=start_str,
            end_hour=end_str,
            productivity_score=round(avg_score, 2)
        )
