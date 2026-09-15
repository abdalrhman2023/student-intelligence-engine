"""
Consistency and Habit Momentum Tracker.

Monitors daily study streak and evaluates longitudinal habit formation
using 7-day and 14-day Exponential Moving Averages (EMA).
"""

from typing import Dict, List, Any
import datetime

try:
    from integration.data_contracts import StudySession, SessionStatus, MomentumState
except ImportError:
    from student_intelligence.integration.data_contracts import StudySession, SessionStatus, MomentumState


class ConsistencyTracker:
    """
    Computes habit momentum and streak adherence.
    """

    def __init__(self, ema_alpha_7d: float = 0.3, ema_alpha_14d: float = 0.15) -> None:
        self.ema_alpha_7d = ema_alpha_7d
        self.ema_alpha_14d = ema_alpha_14d

    def _compute_ema(self, daily_scores: List[float], alpha: float) -> float:
        """Calculates EMA over a chronological score list."""
        if not daily_scores:
            return 0.0

        ema = daily_scores[0]
        for score in daily_scores[1:]:
            ema = alpha * score + (1.0 - alpha) * ema
        return ema

    def analyze(self, sessions: List[StudySession], reference_date: datetime.datetime = None) -> Dict[str, Any]:
        """Analyzes 30-day consistency and determines momentum status."""
        if not reference_date:
            reference_date = datetime.datetime.now()

        daily_activity: Dict[datetime.date, float] = {}
        for i in range(30):
            d = (reference_date - datetime.timedelta(days=i)).date()
            daily_activity[d] = 0.0

        for s in sessions:
            dt = s.actual_start or s.planned_start
            if not dt:
                continue
            d = dt.date()
            if d in daily_activity:
                if s.status == SessionStatus.COMPLETED:
                    daily_activity[d] = 1.0
                elif s.status != SessionStatus.COMPLETED and daily_activity[d] < 1.0:
                    daily_activity[d] = max(daily_activity[d], 0.5)

        sorted_days = sorted(daily_activity.keys())
        daily_scores = [daily_activity[d] for d in sorted_days]

        ema_7d = self._compute_ema(daily_scores[-7:], self.ema_alpha_7d) if len(daily_scores) >= 7 else 0.5
        ema_14d = self._compute_ema(daily_scores[-14:], self.ema_alpha_14d) if len(daily_scores) >= 14 else 0.5

        # Compute consecutive streak counting backwards
        current_streak = 0
        for d in reversed(sorted_days):
            if daily_activity[d] >= 0.5:
                current_streak += 1
            else:
                break

        # Determine momentum trajectory
        if ema_7d >= 0.75:
            momentum = MomentumState.STRONG
        elif ema_7d >= 0.5 and ema_7d >= ema_14d:
            momentum = MomentumState.BUILDING
        elif ema_7d < 0.3:
            momentum = MomentumState.AT_RISK
        else:
            momentum = MomentumState.DECLINING

        return {
            'consistency_score_7d': round(ema_7d, 2),
            'consistency_score_14d': round(ema_14d, 2),
            'current_streak_days': current_streak,
            'momentum': momentum,
            'daily_scores': daily_scores
        }
