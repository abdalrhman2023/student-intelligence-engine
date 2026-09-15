"""
Data Contracts — Schema definitions for inputs, internal representations, and outputs.

Defines standardized Pydantic v2 schemas used across the Student Intelligence module
and ensures seamless serialization between microservices/endpoints.

Module interfaces:
- Input from Backend (Person 5): Quiz answers and study session logs
- Output to Tutor Service (Person 1): Topic mastery and weakness flags
- Output to Risk Model (Person 3): Numerical knowledge and behavioral features
- Output to Adaptive Scheduler (Person 4): Productivity windows, focus thresholds, and mastery status
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class TopicStatus(str, Enum):
    """Classification of student mastery on a specific topic."""
    WEAK = "weak"              # Mastery < 0.4
    PROGRESSING = "progressing" # 0.4 <= Mastery < 0.7
    MASTERED = "mastered"      # Mastery >= 0.7


class TrendDirection(str, Enum):
    """Directional performance momentum computed via Dual-EMA."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"


class ReviewUrgency(str, Enum):
    """Urgency level for scheduling spaced repetition review."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MomentumState(str, Enum):
    """Longitudinal study consistency momentum."""
    BUILDING = "building"
    STRONG = "strong"
    DECLINING = "declining"
    AT_RISK = "at_risk"


class ProcrastinationLevel(str, Enum):
    """Categorical evaluation of student procrastination tendencies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SessionStatus(str, Enum):
    """Operational status of a scheduled study session."""
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"
    IN_PROGRESS = "in_progress"


class ProfileConfidenceLevel(str, Enum):
    """Confidence grade assigned to a profile based on sample size."""
    COLD_START = "cold_start"      # < 10 records
    LOW = "low"                    # 10-30 records
    MODERATE = "moderate"          # 30-60 records
    HIGH = "high"                  # > 60 records


# =============================================================================
# Input Schemas (Inbound from Backend / Database)
# =============================================================================

class QuizInteraction(BaseModel):
    """
    Represents a single assessment interaction record.
    Primary input for Bayesian Knowledge Tracing.
    """
    user_id: str = Field(..., description="Unique student identifier")
    topic_id: str = Field(..., description="Target concept/topic identifier (e.g., 'backpropagation')")
    subject_id: str = Field(..., description="Course/subject identifier (e.g., 'machine_learning')")
    question_id: str = Field(..., description="Unique question identifier")
    is_correct: bool = Field(..., description="Binary assessment outcome")
    response_time_seconds: float = Field(..., ge=0, description="Elapsed response time in seconds")
    difficulty: float = Field(default=0.5, ge=0.0, le=1.0, description="Normalized item difficulty [0, 1]")
    attempt_number: int = Field(default=1, ge=1, description="Sequential attempt count")
    timestamp: datetime = Field(default_factory=datetime.now, description="Interaction ISO timestamp")


class StudySession(BaseModel):
    """
    Represents an execution record of a scheduled study session.
    Primary input for behavior profiling and habit analytics.
    """
    user_id: str = Field(..., description="Unique student identifier")
    session_id: str = Field(..., description="Unique session identifier")
    task_id: str = Field(..., description="Associated task identifier")
    subject_id: str = Field(..., description="Course/subject identifier")
    planned_start: datetime = Field(..., description="Scheduled start time")
    actual_start: Optional[datetime] = Field(None, description="Actual session start timestamp")
    planned_duration_minutes: float = Field(..., gt=0, description="Planned duration in minutes")
    actual_duration_minutes: Optional[float] = Field(None, ge=0, description="Actual duration in minutes")
    status: SessionStatus = Field(..., description="Final session status")
    postpone_count: int = Field(default=0, ge=0, description="Number of times session was rescheduled")
    timestamp: datetime = Field(default_factory=datetime.now, description="Record generation timestamp")


# =============================================================================
# Internal Models
# =============================================================================

class BKTParams(BaseModel):
    """
    Bayesian Knowledge Tracing latent parameters for a topic.
    """
    p_init: float = Field(default=0.10, ge=0.0, le=1.0, description="Prior knowledge probability P(L0)")
    p_transit: float = Field(default=0.15, ge=0.0, le=1.0, description="Learning transition probability P(T)")
    p_guess: float = Field(default=0.25, ge=0.0, le=1.0, description="Guess probability P(G)")
    p_slip: float = Field(default=0.10, ge=0.0, le=1.0, description="Slip probability P(S)")


class TopicKnowledgeState(BaseModel):
    """
    Fine-grained knowledge state representation for an individual concept.
    """
    topic_id: str
    subject_id: str
    mastery_score: float = Field(..., ge=0.0, le=1.0, description="Latent mastery score [0, 1]")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Measurement confidence [0, 1]")
    trend: TrendDirection = Field(..., description="Directional performance momentum")
    trend_delta: float = Field(..., description="Magnitude and sign of recent trend delta")
    status: TopicStatus = Field(..., description="Categorical mastery tier")
    review_urgency: ReviewUrgency = Field(..., description="Spaced repetition urgency flag")
    days_since_review: float = Field(..., ge=0, description="Elapsed days since latest review")
    total_attempts: int = Field(..., ge=0, description="Total assessments completed")
    successful_reviews: int = Field(default=0, ge=0, description="Count of successful recall events")
    predicted_success_prob: float = Field(..., ge=0.0, le=1.0, description="P(Correct) for upcoming item")
    last_interaction: Optional[datetime] = Field(None, description="Timestamp of latest interaction")


# =============================================================================
# Output Schemas (Outbound to Team Pipelines)
# =============================================================================

class KnowledgeStateReport(BaseModel):
    """
    Consolidated student mastery report across a course curriculum.
    Consumed by Person 1 (LLM Tutor), Person 3 (Risk), and Person 4 (Scheduler).
    """
    user_id: str
    overall_mastery: float = Field(..., ge=0.0, le=1.0, description="Macro curriculum mastery average")
    topics: list[TopicKnowledgeState] = Field(default_factory=list, description="Detailed concept breakdowns")
    weak_topics: list[str] = Field(default_factory=list, description="Identifiers of concepts below mastery threshold")
    strong_topics: list[str] = Field(default_factory=list, description="Identifiers of mastered concepts")
    progressing_topics: list[str] = Field(default_factory=list, description="Identifiers of concepts in progress")
    review_priority_queue: list[str] = Field(default_factory=list, description="Ranked concept review priorities")
    generated_at: datetime = Field(default_factory=datetime.now)


class ProductivitySlot(BaseModel):
    """Temporal window characterizing learner productivity."""
    start_hour: str = Field(..., description="Window start in HH:MM format")
    end_hour: str = Field(..., description="Window end in HH:MM format")
    productivity_score: float = Field(..., ge=0.0, le=1.0, description="Normalized completion rate [0, 1]")


class SubjectProcrastination(BaseModel):
    """Domain-specific procrastination assessment."""
    subject_id: str
    score: float = Field(..., ge=0.0, le=1.0)
    level: ProcrastinationLevel


class BehaviorProfile(BaseModel):
    """
    Behavioral diagnostic profile detailing study habits, velocity, and risks.
    Consumed by Person 3 (Risk Model) and Person 4 (Adaptive Scheduler).
    """
    user_id: str

    # Productivity Dynamics
    peak_slots: list[ProductivitySlot] = Field(default_factory=list, description="Optimal focus intervals")
    dead_slots: list[ProductivitySlot] = Field(default_factory=list, description="Low-completion intervals")
    effective_focus_minutes: float = Field(..., ge=0, description="Median uninterrupted session span")
    max_daily_study_hours: float = Field(..., ge=0, description="Daily cognitive threshold before fatigue")

    # Procrastination Indices
    global_procrastination_score: float = Field(..., ge=0.0, le=1.0, description="Global procrastination metric")
    global_procrastination_level: ProcrastinationLevel
    per_subject_procrastination: list[SubjectProcrastination] = Field(default_factory=list)

    # Consistency & Habit Metrics
    consistency_score_7d: float = Field(..., ge=0.0, le=1.0, description="7-day EMA habit adherence")
    consistency_score_14d: float = Field(..., ge=0.0, le=1.0, description="14-day EMA habit adherence")
    current_streak_days: int = Field(..., ge=0, description="Current consecutive active days")
    momentum: MomentumState = Field(..., description="Momentum indicator")

    # Time Estimation Accuracy
    time_estimation_bias: float = Field(..., description="Actual/Planned duration ratio (>1 indicates underestimation)")

    # Metadata
    profile_confidence: ProfileConfidenceLevel = Field(..., description="Profile statistical reliability tier")
    data_points_collected: int = Field(..., ge=0, description="Sample size of logged study sessions")
    generated_at: datetime = Field(default_factory=datetime.now)


class StudentIntelligenceOutput(BaseModel):
    """
    Unified payload delivering simultaneous knowledge and behavioral profiles.
    """
    user_id: str
    knowledge_report: KnowledgeStateReport
    behavior_profile: BehaviorProfile
    generated_at: datetime = Field(default_factory=datetime.now)
