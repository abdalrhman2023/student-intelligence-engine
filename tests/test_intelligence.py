"""
Unit & Integration Tests for Student Intelligence Engine
========================================================
To run tests: pytest tests/test_intelligence.py
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from integration.data_contracts import (
    QuizInteraction,
    StudySession,
    SessionStatus,
    TrendDirection,
    TopicStatus
)
from knowledge_engine.bkt_tracer import BKTKnowledgeTracer
from knowledge_engine.forgetting_model import ForgettingModel
from knowledge_engine.confidence_estimator import ConfidenceEstimator
from knowledge_engine.trend_detector import TrendDetector
from knowledge_engine.prerequisite_graph import PrerequisiteGraph
from behavior_engine.focus_estimator import FocusEstimator
from behavior_engine.procrastination_tracker import ProcrastinationTracker
from integration.student_intelligence_api import StudentIntelligenceEngine


def test_bkt_updates():
    tracer = BKTKnowledgeTracer()
    user_id = "test_student"
    topic_id = "linear_regression"

    # Initial mastery should be 0
    assert tracer.get_mastery(user_id, topic_id) == 0.0

    # Answer correctly -> mastery should rise
    interaction1 = QuizInteraction(
        user_id=user_id,
        topic_id=topic_id,
        subject_id="machine_learning",
        question_id="q1",
        is_correct=True,
        response_time_seconds=25.0
    )
    m1 = tracer.update(interaction1)
    assert m1 > 0.10

    # Answer correctly again -> mastery should rise further
    interaction2 = QuizInteraction(
        user_id=user_id,
        topic_id=topic_id,
        subject_id="machine_learning",
        question_id="q2",
        is_correct=True,
        response_time_seconds=20.0
    )
    m2 = tracer.update(interaction2)
    assert m2 > m1


def test_forgetting_model():
    model = ForgettingModel(base_decay_rate=0.05, review_benefit=0.3)
    base_m = 0.85

    # With 0 days passed, mastery unchanged
    assert model.apply_decay(base_m, days_since_review=0, successful_reviews=1) == base_m

    # With 10 days passed, mastery decreases
    decayed_10 = model.apply_decay(base_m, days_since_review=10, successful_reviews=1)
    assert decayed_10 < base_m

    # More successful reviews should slow down decay
    decayed_with_more_reviews = model.apply_decay(base_m, days_since_review=10, successful_reviews=5)
    assert decayed_with_more_reviews > decayed_10


def test_confidence_estimator():
    estimator = ConfidenceEstimator(scaling_factor=0.1)
    
    # 0 observations = 0 confidence
    assert estimator.estimate(0) == 0.0
    
    # More observations = higher confidence
    c5 = estimator.estimate(5)
    c25 = estimator.estimate(25)
    assert c25 > c5
    assert c25 < 1.0


def test_trend_detector():
    detector = TrendDetector(short_window=3, long_window=6, threshold=0.05)

    # Clearly improving sequence (0, 0, 0, 1, 1, 1)
    history_improving = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
    direction, delta = detector.detect(history_improving)
    assert direction == TrendDirection.IMPROVING
    assert delta > 0

    # Clearly declining sequence (1, 1, 1, 0, 0, 0)
    history_declining = [1.0, 1.0, 1.0, 0.0, 0.0, 0.0]
    direction_d, delta_d = detector.detect(history_declining)
    assert direction_d == TrendDirection.DECLINING
    assert delta_d < 0


def test_prerequisite_graph():
    graph = PrerequisiteGraph()
    prereqs = graph.get_prerequisites("cnn")
    assert "backpropagation" in prereqs
    assert "neural_networks_basics" in prereqs

    learning_path = graph.get_learning_path(["cnn"])
    # Prerequisites should appear before cnn
    assert learning_path.index("neural_networks_basics") < learning_path.index("cnn")


def test_focus_and_procrastination():
    now = datetime.now()
    sessions = [
        StudySession(
            user_id="u1",
            session_id="s1",
            task_id="t1",
            subject_id="ml",
            planned_start=now,
            actual_start=now,
            planned_duration_minutes=45.0,
            actual_duration_minutes=45.0,
            status=SessionStatus.COMPLETED
        ),
        StudySession(
            user_id="u1",
            session_id="s2",
            task_id="t2",
            subject_id="ml",
            planned_start=now,
            actual_start=now,
            planned_duration_minutes=45.0,
            actual_duration_minutes=45.0,
            status=SessionStatus.POSTPONED,
            postpone_count=2
        )
    ]

    focus_estimator = FocusEstimator()
    focus_metrics = focus_estimator.estimate(sessions)
    assert focus_metrics["effective_focus"] == 45.0

    procrastination_tracker = ProcrastinationTracker()
    res = procrastination_tracker.analyze(sessions)
    assert res["global_score"] > 0.0


def test_end_to_end_engine():
    engine = StudentIntelligenceEngine()
    now = datetime.now()

    # Log quiz
    engine.log_quiz_interaction(QuizInteraction(
        user_id="student_1",
        topic_id="linear_regression",
        subject_id="machine_learning",
        question_id="q101",
        is_correct=True,
        response_time_seconds=15.0
    ))

    # Log session
    engine.log_study_session(StudySession(
        user_id="student_1",
        session_id="sess_101",
        task_id="task_1",
        subject_id="machine_learning",
        planned_start=now,
        actual_start=now,
        planned_duration_minutes=40.0,
        actual_duration_minutes=40.0,
        status=SessionStatus.COMPLETED
    ))

    # Generate full report
    output = engine.get_full_student_intelligence("student_1", subject_id="machine_learning")
    assert output.user_id == "student_1"
    assert output.knowledge_report is not None
    assert output.behavior_profile is not None
    assert len(output.knowledge_report.topics) > 0
    print("\nAll unit and integration tests passed successfully!")


if __name__ == "__main__":
    test_bkt_updates()
    test_forgetting_model()
    test_confidence_estimator()
    test_trend_detector()
    test_prerequisite_graph()
    test_focus_and_procrastination()
    test_end_to_end_engine()
    print("ALL TESTS PASSED!")
