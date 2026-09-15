"""
Synthetic Data Generator.

Generates realistic assessment interactions and study sessions
across student behavioral archetypes (diligent, average, procrastinator).
"""

import json
import random
import uuid
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import numpy as np

try:
    from integration.data_contracts import QuizInteraction, StudySession, SessionStatus
except ImportError:
    from student_intelligence.integration.data_contracts import QuizInteraction, StudySession, SessionStatus

SUBJECT_ID = 'machine_learning'
TOPICS = {
    'linear_regression': {'difficulty': 0.3},
    'decision_trees': {'difficulty': 0.4},
    'svm': {'difficulty': 0.7},
    'backpropagation': {'difficulty': 0.8},
    'cnn': {'difficulty': 0.9}
}


def generate_timestamp(start_date: datetime, end_date: datetime, peak_hours: List[int] = None) -> datetime:
    """Generates a random timestamp within window, optionally weighted to peak hours."""
    delta = end_date - start_date
    random_seconds = random.randrange(int(delta.total_seconds()))
    base_time = start_date + timedelta(seconds=random_seconds)

    if peak_hours:
        hour = random.choice(peak_hours)
        base_time = base_time.replace(hour=hour)

    return base_time


def generate_quiz_interactions(
    user_id: str,
    archetype: str,
    start_date: datetime,
    end_date: datetime,
    num_days: int
) -> List[QuizInteraction]:
    """Generates assessment logs conditioned on student archetype."""
    interactions = []

    if archetype == 'diligent':
        base_prob = 0.80
        time_mean = 30
        peak_hours = [14, 15, 16, 17, 18, 19]
    elif archetype == 'average':
        base_prob = 0.60
        time_mean = 45
        peak_hours = [10, 11, 12, 14, 15, 20, 21]
    else:  # procrastinator
        base_prob = 0.45
        time_mean = 60
        peak_hours = [22, 23, 0, 1, 2]

    for topic_id, topic_info in TOPICS.items():
        difficulty = topic_info['difficulty']
        num_interactions = random.randint(40, 70)

        for i in range(num_interactions):
            if archetype == 'diligent':
                learning_progress = min(0.30, i * 0.006)
            elif archetype == 'average':
                learning_progress = min(0.15, i * 0.003)
            else:
                learning_progress = min(0.05, i * 0.001)

            success_prob = max(0.1, min(0.95, base_prob - (difficulty * 0.3) + learning_progress))

            if archetype == 'procrastinator' and difficulty < 0.5:
                success_prob = max(success_prob, 0.70)

            is_correct = random.random() < success_prob

            resp_time_variance = time_mean * 0.3
            response_time = int(np.random.normal(time_mean, resp_time_variance))
            if not is_correct:
                response_time = int(response_time * 1.4)
            response_time = max(5, min(300, response_time))

            ts = generate_timestamp(start_date, end_date, peak_hours)

            interactions.append(
                QuizInteraction(
                    user_id=user_id,
                    topic_id=topic_id,
                    subject_id=SUBJECT_ID,
                    question_id=f"q_{topic_id}_{i}",
                    is_correct=is_correct,
                    response_time_seconds=response_time,
                    difficulty=difficulty,
                    attempt_number=1,
                    timestamp=ts
                )
            )

    interactions.sort(key=lambda x: x.timestamp)
    return interactions


def generate_study_sessions(
    user_id: str,
    archetype: str,
    start_date: datetime,
    num_days: int
) -> List[StudySession]:
    """Generates study sessions reflecting student planning and execution habits."""
    sessions = []

    for day in range(num_days):
        current_date = start_date + timedelta(days=day)
        num_sessions = random.randint(2, 4)

        for _ in range(num_sessions):
            session_id = str(uuid.uuid4())
            task_id = str(uuid.uuid4())
            planned_duration = random.choice([30, 45, 60, 90])

            hour = random.randint(8, 21)
            planned_start = current_date.replace(hour=hour, minute=random.choice([0, 15, 30, 45]))

            if archetype == 'diligent':
                status = SessionStatus.COMPLETED if random.random() < 0.9 else SessionStatus.POSTPONED
                postpone_count = 0 if status == SessionStatus.COMPLETED else 1
                actual_start = planned_start + timedelta(minutes=random.randint(-5, 5))
                actual_duration = planned_duration + random.randint(-5, 5)

            elif archetype == 'average':
                rand_val = random.random()
                if rand_val < 0.70:
                    status = SessionStatus.COMPLETED
                elif rand_val < 0.90:
                    status = SessionStatus.POSTPONED
                else:
                    status = SessionStatus.CANCELLED

                postpone_count = random.randint(0, 2)
                actual_start = planned_start + timedelta(minutes=random.randint(5, 25))
                actual_duration = planned_duration + random.randint(-10, 20)

            else:  # procrastinator
                rand_val = random.random()
                if rand_val < 0.40:
                    status = SessionStatus.COMPLETED
                elif rand_val < 0.80:
                    status = SessionStatus.POSTPONED
                else:
                    status = SessionStatus.CANCELLED

                postpone_count = random.randint(1, 4)
                if planned_start.hour < 12:
                    status = SessionStatus.POSTPONED if rand_val < 0.6 else SessionStatus.CANCELLED
                    postpone_count += 1

                actual_start = planned_start + timedelta(hours=random.randint(1, 12))
                actual_duration = planned_duration * random.uniform(1.2, 1.6) if status == SessionStatus.COMPLETED else 0

            actual_duration = max(5, int(actual_duration)) if status == SessionStatus.COMPLETED else 0
            record_timestamp = actual_start if status == SessionStatus.COMPLETED else planned_start

            sessions.append(
                StudySession(
                    user_id=user_id,
                    session_id=session_id,
                    task_id=task_id,
                    subject_id=SUBJECT_ID,
                    planned_start=planned_start,
                    actual_start=actual_start,
                    planned_duration_minutes=planned_duration,
                    actual_duration_minutes=actual_duration,
                    status=status,
                    postpone_count=postpone_count,
                    timestamp=record_timestamp
                )
            )

    sessions.sort(key=lambda x: x.timestamp)
    return sessions


def generate_all_data(num_days: int = 30, students_per_type: int = 1) -> Dict[str, Any]:
    """Generates synthetic dataset encompassing all student personas."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=num_days)

    all_interactions = []
    all_sessions = []
    user_profiles = {}

    archetypes = ['diligent', 'average', 'procrastinator']

    for archetype in archetypes:
        for i in range(students_per_type):
            user_id = f"user_{archetype}_{i}"
            user_profiles[user_id] = {
                "archetype": archetype,
                "join_date": start_date.isoformat()
            }

            all_interactions.extend(
                generate_quiz_interactions(user_id, archetype, start_date, end_date, num_days)
            )
            all_sessions.extend(
                generate_study_sessions(user_id, archetype, start_date, num_days)
            )

    return {
        'quiz_interactions': all_interactions,
        'study_sessions': all_sessions,
        'user_profiles': user_profiles
    }


def save_to_json(data: Dict[str, Any], output_dir: str):
    """Saves generated dataset to serialized JSON files."""
    os.makedirs(output_dir, exist_ok=True)

    class CustomEncoder(json.JSONEncoder):
        def default(self, obj):
            if hasattr(obj, 'model_dump'):
                return obj.model_dump(mode='json')
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)

    for key, value in data.items():
        file_path = os.path.join(output_dir, f"{key}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(value, f, cls=CustomEncoder, indent=2)
        print(f"Serialized {len(value)} items to {file_path}")


if __name__ == '__main__':
    dataset = generate_all_data(num_days=14, students_per_type=1)
    print(f"Generated {len(dataset['quiz_interactions'])} quiz interactions.")
    print(f"Generated {len(dataset['study_sessions'])} study sessions.")
    output_path = os.path.join(os.path.dirname(__file__), 'output')
    save_to_json(dataset, output_path)
