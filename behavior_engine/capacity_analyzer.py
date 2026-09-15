"""
Daily Study Capacity Analyzer.

Identifies the inflection threshold where study volume begins
inducing fatigue and degrading session completion rates.
"""

from typing import Dict, List, Any, Tuple
from collections import defaultdict

try:
    from integration.data_contracts import StudySession, SessionStatus
except ImportError:
    from student_intelligence.integration.data_contracts import StudySession, SessionStatus


class CapacityAnalyzer:
    """
    Evaluates daily sustainable workload capacity.
    """

    def __init__(self) -> None:
        pass

    def analyze(self, sessions: List[StudySession]) -> Dict[str, Any]:
        daily_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {'hours': 0.0, 'completed': 0, 'planned': 0})

        for s in sessions:
            dt = s.actual_start or s.planned_start
            if not dt:
                continue

            date_str = dt.strftime("%Y-%m-%d")
            daily_stats[date_str]['planned'] += 1

            if s.status == SessionStatus.COMPLETED and s.actual_duration_minutes:
                daily_stats[date_str]['hours'] += s.actual_duration_minutes / 60.0
                daily_stats[date_str]['completed'] += 1

        if not daily_stats:
            return {
                'max_daily_capacity_hours': 4.0,
                'avg_daily_hours': 0.0,
                'daily_distribution': [],
                'overload_days': 0
            }

        daily_distribution: List[Tuple[str, float, float]] = []
        total_hours = 0.0

        for date_str, stats in daily_stats.items():
            hours = stats['hours']
            total_hours += hours
            completion_rate = stats['completed'] / stats['planned'] if stats['planned'] > 0 else 0.0
            daily_distribution.append((date_str, hours, completion_rate))

        avg_daily_hours = total_hours / len(daily_stats)
        daily_distribution_sorted = sorted(daily_distribution, key=lambda x: x[1])

        max_daily_capacity = 4.0
        overload_days = 0

        # Detect drop-off inflection point
        for date_str, hours, comp_rate in daily_distribution_sorted:
            if hours > 2.0 and comp_rate < 0.6:
                max_daily_capacity = max(2.0, hours - 0.5)
                break
        else:
            if daily_distribution_sorted:
                high_perf_days = [h for _, h, comp in daily_distribution_sorted if comp >= 0.75]
                max_daily_capacity = max(high_perf_days) if high_perf_days else 4.0

        for _, hours, comp_rate in daily_distribution:
            if hours > max_daily_capacity and comp_rate < 0.6:
                overload_days += 1

        return {
            'max_daily_capacity_hours': round(max_daily_capacity, 1),
            'avg_daily_hours': round(avg_daily_hours, 1),
            'daily_distribution': daily_distribution,
            'overload_days': overload_days
        }
