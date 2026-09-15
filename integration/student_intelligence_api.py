"""
Student Intelligence Engine — Core Orchestrator & REST API.

Provides unified interface for Knowledge Tracing and Behavioral Profiling
for adaptive learning systems.
"""

from datetime import datetime
from typing import List, Dict, Optional
import numpy as np

try:
    from integration.data_contracts import (
        QuizInteraction,
        StudySession,
        TopicKnowledgeState,
        KnowledgeStateReport,
        BehaviorProfile,
        StudentIntelligenceOutput,
        TopicStatus,
        ReviewUrgency,
        ProfileConfidenceLevel,
    )
except ImportError:
    from student_intelligence.integration.data_contracts import (
        QuizInteraction,
        StudySession,
        TopicKnowledgeState,
        KnowledgeStateReport,
        BehaviorProfile,
        StudentIntelligenceOutput,
        TopicStatus,
        ReviewUrgency,
        ProfileConfidenceLevel,
    )

from knowledge_engine.bkt_tracer import BKTKnowledgeTracer
from knowledge_engine.forgetting_model import ForgettingModel
from knowledge_engine.prerequisite_graph import PrerequisiteGraph
from knowledge_engine.confidence_estimator import ConfidenceEstimator
from knowledge_engine.trend_detector import TrendDetector
from knowledge_engine.review_scheduler import ReviewScheduler

from behavior_engine.profile_builder import BehaviorProfileBuilder


class StudentIntelligenceEngine:
    """
    Unified analytics engine encapsulating knowledge tracing and behavioral modeling.
    """

    def __init__(self, graph_path: Optional[str] = None):
        self.bkt_tracer = BKTKnowledgeTracer()
        self.forgetting_model = ForgettingModel(base_decay_rate=0.05, review_benefit=0.3)
        self.prereq_graph = PrerequisiteGraph(graph_path=graph_path)
        self.confidence_estimator = ConfidenceEstimator(scaling_factor=0.1)
        self.trend_detector = TrendDetector(short_window=5, long_window=15, threshold=0.03)
        self.review_scheduler = ReviewScheduler(forgetting_model=self.forgetting_model)

        self.behavior_builder = BehaviorProfileBuilder()

        self._user_quiz_interactions: Dict[str, List[QuizInteraction]] = {}
        self._user_study_sessions: Dict[str, List[StudySession]] = {}

    def log_quiz_interaction(self, interaction: QuizInteraction) -> float:
        """Logs an assessment attempt and updates latent mastery."""
        user_id = interaction.user_id
        topic_id = interaction.topic_id

        if user_id not in self._user_quiz_interactions:
            self._user_quiz_interactions[user_id] = []
        self._user_quiz_interactions[user_id].append(interaction)

        # Ensure prerequisite-adjusted prior is set if topic is newly encountered
        if self.bkt_tracer.get_mastery(user_id, topic_id) == 0.0:
            user_masteries = self.bkt_tracer.get_all_masteries(user_id)
            adjusted_prior = self.prereq_graph.adjust_prior(topic_id, user_masteries)
            self.bkt_tracer.set_prior(user_id, topic_id, adjusted_prior)

        return self.bkt_tracer.update(interaction)

    def log_study_session(self, session: StudySession):
        """Logs a completed or scheduled study session."""
        user_id = session.user_id
        if user_id not in self._user_study_sessions:
            self._user_study_sessions[user_id] = []
        self._user_study_sessions[user_id].append(session)

    def generate_knowledge_report(
        self,
        user_id: str,
        subject_id: str = "machine_learning",
        reference_time: Optional[datetime] = None
    ) -> KnowledgeStateReport:
        """Generates comprehensive curriculum mastery diagnostics."""
        if reference_time is None:
            reference_time = datetime.now()

        interactions = self._user_quiz_interactions.get(user_id, [])
        subject_interactions = [i for i in interactions if i.subject_id == subject_id]

        topic_interactions: Dict[str, List[QuizInteraction]] = {}
        for interaction in subject_interactions:
            topic_interactions.setdefault(interaction.topic_id, []).append(interaction)

        all_topics = set(self.prereq_graph.get_all_topics())
        all_topics.update(topic_interactions.keys())

        topic_states: List[TopicKnowledgeState] = []
        weak_topics: List[str] = []
        strong_topics: List[str] = []
        progressing_topics: List[str] = []

        for topic_id in all_topics:
            t_ints = topic_interactions.get(topic_id, [])
            total_attempts = len(t_ints)

            base_mastery = self.bkt_tracer.get_mastery(user_id, topic_id)
            if base_mastery == 0.0 and total_attempts == 0:
                user_masteries = self.bkt_tracer.get_all_masteries(user_id)
                base_mastery = self.prereq_graph.adjust_prior(topic_id, user_masteries)

            confidence = self.confidence_estimator.estimate(total_attempts)

            days_since_review = 0.0
            last_dt = None
            successful_reviews = 0

            if t_ints:
                sorted_ints = sorted(t_ints, key=lambda x: x.timestamp)
                last_interaction = sorted_ints[-1]
                last_dt = last_interaction.timestamp

                if isinstance(last_dt, str):
                    try:
                        last_dt = datetime.fromisoformat(last_dt)
                    except ValueError:
                        last_dt = reference_time

                delta_days = (reference_time - last_dt).total_seconds() / 86400.0
                days_since_review = max(0.0, delta_days)
                successful_reviews = sum(1 for i in t_ints if i.is_correct)

            decayed_mastery = self.forgetting_model.apply_decay(
                base_mastery=base_mastery,
                days_since_review=days_since_review,
                successful_reviews=successful_reviews
            )

            score_history = [1.0 if i.is_correct else 0.0 for i in t_ints]
            trend_dir, trend_delta = self.trend_detector.detect(score_history)

            if decayed_mastery < 0.4:
                status = TopicStatus.WEAK
                weak_topics.append(topic_id)
            elif decayed_mastery < 0.7:
                status = TopicStatus.PROGRESSING
                progressing_topics.append(topic_id)
            else:
                status = TopicStatus.MASTERED
                strong_topics.append(topic_id)

            urgency_str, _ = self.forgetting_model.get_review_urgency(
                base_mastery=base_mastery,
                days_since_review=days_since_review,
                successful_reviews=successful_reviews
            )
            urgency_map = {
                'critical': ReviewUrgency.CRITICAL,
                'high': ReviewUrgency.HIGH,
                'medium': ReviewUrgency.MEDIUM,
                'low': ReviewUrgency.LOW
            }
            review_urgency = urgency_map.get(urgency_str, ReviewUrgency.MEDIUM)

            p_guess = 0.25
            p_slip = 0.10
            predicted_prob = decayed_mastery * (1.0 - p_slip) + (1.0 - decayed_mastery) * p_guess

            state = TopicKnowledgeState(
                topic_id=topic_id,
                subject_id=subject_id,
                mastery_score=round(float(decayed_mastery), 4),
                confidence=round(float(confidence), 4),
                trend=trend_dir,
                trend_delta=round(float(trend_delta), 4),
                status=status,
                review_urgency=review_urgency,
                days_since_review=round(float(days_since_review), 1),
                total_attempts=total_attempts,
                successful_reviews=successful_reviews,
                predicted_success_prob=round(float(predicted_prob), 4),
                last_interaction=last_dt
            )
            topic_states.append(state)

        overall = float(np.mean([ts.mastery_score for ts in topic_states])) if topic_states else 0.1
        review_queue = self.review_scheduler.prioritize(topic_states)

        return KnowledgeStateReport(
            user_id=user_id,
            overall_mastery=round(overall, 4),
            topics=topic_states,
            weak_topics=weak_topics,
            strong_topics=strong_topics,
            progressing_topics=progressing_topics,
            review_priority_queue=review_queue,
            generated_at=datetime.now()
        )

    def generate_behavior_profile(self, user_id: str) -> BehaviorProfile:
        """Generates diagnostic behavioral habit profile."""
        sessions = self._user_study_sessions.get(user_id, [])
        return self.behavior_builder.build_profile(user_id=user_id, sessions=sessions)

    def get_full_student_intelligence(
        self,
        user_id: str,
        subject_id: str = "machine_learning"
    ) -> StudentIntelligenceOutput:
        """Assembles unified knowledge and behavioral payload."""
        k_report = self.generate_knowledge_report(user_id=user_id, subject_id=subject_id)
        b_profile = self.generate_behavior_profile(user_id=user_id)

        return StudentIntelligenceOutput(
            user_id=user_id,
            knowledge_report=k_report,
            behavior_profile=b_profile,
            generated_at=datetime.now()
        )


# =============================================================================
# REST API (FastAPI Service)
# =============================================================================
try:
    from fastapi import FastAPI

    app = FastAPI(
        title="Student Intelligence API",
        description="Knowledge Tracing & Behavioral Modeling Microservice for Adaptive Learning Systems",
        version="1.0.0"
    )

    engine = StudentIntelligenceEngine()

    @app.get("/")
    def root():
        return {
            "service": "Student Intelligence Engine",
            "status": "healthy",
            "version": "1.0.0"
        }

    @app.post("/api/interactions", summary="Log Assessment Interaction")
    def log_interaction_endpoint(interaction: QuizInteraction):
        new_mastery = engine.log_quiz_interaction(interaction)
        return {"status": "success", "new_mastery": new_mastery}

    @app.post("/api/sessions", summary="Log Study Session")
    def log_session_endpoint(session: StudySession):
        engine.log_study_session(session)
        return {"status": "success"}

    @app.get("/api/users/{user_id}/knowledge", response_model=KnowledgeStateReport)
    def get_knowledge_report(user_id: str, subject_id: str = "machine_learning"):
        return engine.generate_knowledge_report(user_id=user_id, subject_id=subject_id)

    @app.get("/api/users/{user_id}/behavior", response_model=BehaviorProfile)
    def get_behavior_profile(user_id: str):
        return engine.generate_behavior_profile(user_id=user_id)

    @app.get("/api/users/{user_id}/intelligence", response_model=StudentIntelligenceOutput)
    def get_full_intelligence(user_id: str, subject_id: str = "machine_learning"):
        return engine.get_full_student_intelligence(user_id=user_id, subject_id=subject_id)

except ImportError:
    app = None
