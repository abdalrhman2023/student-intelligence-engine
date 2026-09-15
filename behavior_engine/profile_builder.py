"""
Behavior Profile Builder.

Orchestrates all behavior analytical modules to construct a consolidated
diagnostic BehaviorProfile schema for a student.
"""

from typing import List
import numpy as np

try:
    from integration.data_contracts import (
        StudySession, BehaviorProfile, ProfileConfidenceLevel, SessionStatus, ProcrastinationLevel
    )
except ImportError:
    from student_intelligence.integration.data_contracts import (
        StudySession, BehaviorProfile, ProfileConfidenceLevel, SessionStatus, ProcrastinationLevel
    )

from .productivity_analyzer import ProductivityAnalyzer
from .focus_estimator import FocusEstimator
from .procrastination_tracker import ProcrastinationTracker
from .capacity_analyzer import CapacityAnalyzer
from .consistency_tracker import ConsistencyTracker


class BehaviorProfileBuilder:
    """
    Master pipeline builder generating consolidated user behavior profiles.
    """

    def __init__(self) -> None:
        self.productivity_analyzer = ProductivityAnalyzer()
        self.focus_estimator = FocusEstimator()
        self.procrastination_tracker = ProcrastinationTracker()
        self.capacity_analyzer = CapacityAnalyzer()
        self.consistency_tracker = ConsistencyTracker()

    def build_profile(self, user_id: str, sessions: List[StudySession]) -> BehaviorProfile:
        """
        Executes analytical pipeline across logged study sessions.
        """
        num_sessions = len(sessions)
        if num_sessions < 10:
            confidence = ProfileConfidenceLevel.COLD_START
        elif num_sessions < 30:
            confidence = ProfileConfidenceLevel.LOW
        elif num_sessions < 60:
            confidence = ProfileConfidenceLevel.MODERATE
        else:
            confidence = ProfileConfidenceLevel.HIGH

        # Evaluate time estimation bias
        completed_sessions = [
            s for s in sessions
            if s.status == SessionStatus.COMPLETED and s.actual_duration_minutes and s.planned_duration_minutes
        ]

        if not completed_sessions:
            time_bias = 1.0
        else:
            biases = [
                (s.actual_duration_minutes / s.planned_duration_minutes)
                for s in completed_sessions if s.planned_duration_minutes > 0
            ]
            time_bias = round(float(np.mean(biases)), 2) if biases else 1.0

        # Execute component analyzers
        prod_res = self.productivity_analyzer.analyze(sessions)
        focus_res = self.focus_estimator.estimate(sessions)
        proc_res = self.procrastination_tracker.analyze(sessions)
        cap_res = self.capacity_analyzer.analyze(sessions)
        consist_res = self.consistency_tracker.analyze(sessions)

        # Assemble unified profile
        return BehaviorProfile(
            user_id=user_id,
            peak_slots=prod_res.get('peak_slots', []),
            dead_slots=prod_res.get('dead_slots', []),
            effective_focus_minutes=focus_res.get('effective_focus', 25.0),
            max_daily_study_hours=cap_res.get('max_daily_capacity_hours', 4.0),
            global_procrastination_score=proc_res.get('global_score', 0.0),
            global_procrastination_level=proc_res.get('global_level', ProcrastinationLevel.LOW),
            per_subject_procrastination=proc_res.get('per_subject', []),
            consistency_score_7d=consist_res.get('consistency_score_7d', 0.0),
            consistency_score_14d=consist_res.get('consistency_score_14d', 0.0),
            current_streak_days=consist_res.get('current_streak_days', 0),
            momentum=consist_res.get('momentum'),
            time_estimation_bias=time_bias,
            profile_confidence=confidence,
            data_points_collected=num_sessions
        )
