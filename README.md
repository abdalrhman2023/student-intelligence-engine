<<<<<<< HEAD
# Student Intelligence Engine

A production-grade Python intelligence engine for personalized education and adaptive study systems. This module serves as the **Learner Modeling & Student Profiling Microservice**, implementing:

1. **Knowledge Tracing Engine**: Tracks latent concept mastery, accounts for retention loss via multi-factor spaced repetition, adjusts priors using a curriculum prerequisite DAG, and ranks revision priorities.
2. **Personal Behavior Engine**: Detects circadian productivity peaks, quantifies procrastination tendencies, estimates uninterrupted focus duration, and monitors habit momentum.

---

## Architecture Overview

```
                      [Backend / Database (Person 5)]
                                     │
              ┌──────────────────────┴──────────────────────┐
              │ Quiz Interactions              Study Sessions│
              ▼                                             ▼
┌───────────────────────────────────┐     ┌───────────────────────────────────┐
│     Knowledge Tracing Engine      │     │     Personal Behavior Engine      │
│  - Bayesian Knowledge Tracing     │     │  - Peak Productivity Analyzer     │
│  - Prerequisite DAG Modeling      │     │  - Effective Focus Estimator      │
│  - Multi-factor Forgetting Curve  │     │  - Procrastination Index Tracker  │
│  - Statistical Confidence Metric  │     │  - Daily Capacity Analyzer        │
│  - Dual-EMA Trend Detection       │     │  - Habit Consistency & Streak     │
│  - Priority Review Scheduler      │     │  - Time Estimation Bias           │
└─────────────────┬─────────────────┘     └─────────────────┬─────────────────┘
                  │                                         │
                  │ Weak Topics & Mastery                   │ Productivity Slots & Focus
                  ▼                                         ▼
      [Tutor Service (Person 1)]                 [Adaptive Scheduler (Person 4)]
                  │                                         ▲
                  └────────────► [Risk Model (Person 3)] ───┘
                                   Failure Probabilities
```

---

## Directory Structure

```text
student_intelligence/
├── data/
│   ├── knowledge_graph.json          # Machine Learning curriculum DAG (23 topics, 7 categories)
│   └── synthetic_generator.py        # Generates realistic student logs across 3 archetypes
│
├── knowledge_engine/
│   ├── bkt_tracer.py                 # Bayesian Knowledge Tracing with dynamic observation update
│   ├── forgetting_model.py           # Multi-factor exponential decay with repetition benefits
│   ├── prerequisite_graph.py         # Kahn's topological sort & prerequisite prior adjustments
│   ├── confidence_estimator.py       # Exponential confidence saturation metric
│   ├── trend_detector.py             # Dual-EMA short/long momentum analyzer
│   └── review_scheduler.py           # Multi-criteria revision urgency ranking queue
│
├── behavior_engine/
│   ├── productivity_analyzer.py      # 24-hour completion distributions & window clustering
│   ├── focus_estimator.py            # Median and 95th percentile sustained duration
│   ├── procrastination_tracker.py    # Global and per-subject postponement/delay indices
│   ├── capacity_analyzer.py          # Daily volume inflection point detection
│   ├── consistency_tracker.py        # Streak monitoring & EMA habit momentum
│   └── profile_builder.py            # Consolidates metrics into a single diagnostic profile
│
├── integration/
│   ├── data_contracts.py             # Pydantic v2 schemas for all service boundaries
│   └── student_intelligence_api.py   # Main orchestrator class & FastAPI REST server
│
├── tests/
│   └── test_intelligence.py          # Unit and integration test suite
│
├── .gitignore                        # Standard Python gitignore
└── README.md                         # Service documentation & team integration manual
```

---

## Team Integration Guide (How to Use This Module)

This section details exactly what data each team member provides and receives from this service.

### 1. For the Software / Backend Engineer (Person 5)
You can run this service as a standalone FastAPI server or import `StudentIntelligenceEngine` directly in Python.

#### Running the Server
```bash
uvicorn integration.student_intelligence_api:app --reload --port 8000
```
Interactive API docs are available at `http://localhost:8000/docs`.

#### Ingestion Endpoints
* **`POST /api/interactions`**: Call this whenever a student answers a quiz or practice question.
  ```json
  {
    "user_id": "usr_101",
    "topic_id": "backpropagation",
    "subject_id": "machine_learning",
    "question_id": "q_42",
    "is_correct": true,
    "response_time_seconds": 32.5,
    "difficulty": 0.65
  }
  ```
* **`POST /api/sessions`**: Call this whenever a student schedules, starts, or completes a study session.
  ```json
  {
    "user_id": "usr_101",
    "session_id": "sess_801",
    "task_id": "task_12",
    "subject_id": "machine_learning",
    "planned_start": "2026-09-15T19:00:00",
    "actual_start": "2026-09-15T19:15:00",
    "planned_duration_minutes": 45,
    "actual_duration_minutes": 40,
    "status": "completed",
    "postpone_count": 0
  }
  ```

---

### 2. For the LLM & Generative Learning Engineer (Person 1)
Query the knowledge endpoint to obtain the student's exact concept mastery and weak areas:

```bash
GET /api/users/{user_id}/knowledge?subject_id=machine_learning
```

#### Response Example
```json
{
  "user_id": "usr_101",
  "overall_mastery": 0.48,
  "weak_topics": ["backpropagation", "cnn"],
  "strong_topics": ["linear_regression", "python_programming"],
  "progressing_topics": ["decision_trees"],
  "review_priority_queue": ["backpropagation", "svm", "cnn"]
}
```
**How to use this:**
* In your RAG/Prompting pipeline, inject `weak_topics` so your LLM generates explanations, targeted flashcards, and quizzes that address known gaps.
* Use `review_priority_queue[0]` to suggest: *"Would you like to review Backpropagation today?"*

---

### 3. For the Risk Prediction Engineer (Person 3)
Retrieve structured numerical features for training and inferring failure/drop-off risk (e.g., XGBoost, Random Forest):

```bash
GET /api/users/{user_id}/behavior
```

#### Key Feature Inputs for Your Model
| Feature Name | Type | Description |
| :--- | :---: | :--- |
| `global_procrastination_score` | `float` [0, 1] | Quantified postponement and start delay latency |
| `time_estimation_bias` | `float` | Ratio of actual to planned time (>1 = underestimating work) |
| `consistency_score_7d` | `float` [0, 1] | 7-day EMA habit adherence |
| `current_streak_days` | `int` | Number of consecutive active study days |
| `effective_focus_minutes` | `float` | Median uninterrupted study capacity |
| `overall_mastery` | `float` [0, 1] | (From knowledge report) Macro curriculum grasp |

---

### 4. For the Adaptive Scheduler & Decision Engine (Person 4)
Retrieve both knowledge state and behavioral boundaries in one combined payload:

```bash
GET /api/users/{user_id}/intelligence?subject_id=machine_learning
```

#### Actionable Decision Parameters
* **`peak_slots`**: Array of optimal time intervals (e.g., `19:00` - `22:00`). Schedule high-difficulty tasks here.
* **`dead_slots`**: Array of low-completion intervals (e.g., `14:00` - `16:00`). Avoid heavy sessions during these hours.
* **`effective_focus_minutes`**: Cap single-session block lengths to this value (e.g., split a 2-hour task into 3x40-minute blocks).
* **`max_daily_study_hours`**: Maximum recommended daily capacity before fatigue sets in.
* **`review_priority_queue`**: Top concepts requiring revision based on Ebbinghaus forgetting curve decay.

---

## Mathematical Formulation

### 1. Bayesian Knowledge Tracing (BKT)
State observation equations:
$$P(L_t \mid \text{Correct}) = \frac{P(L_t)(1 - P(S))}{P(L_t)(1 - P(S)) + (1 - P(L_t))P(G)}$$
$$P(L_t \mid \text{Incorrect}) = \frac{P(L_t)P(S)}{P(L_t)P(S) + (1 - P(L_t))(1 - P(G))}$$

Learning transition equation:
$$P(L_{t+1}) = P(L_t \mid \text{Obs}) + (1 - P(L_t \mid \text{Obs})) \cdot P(T)$$

### 2. Multi-factor Forgetting Curve
$$R(t) = R_{\text{base}} \cdot \exp\left(-\frac{\lambda}{1 + \alpha \cdot n_{\text{reviews}}} \cdot \Delta t\right)$$
Where $\lambda$ represents base forgetting rate, $\alpha$ denotes repetition attenuation, and $\Delta t$ is elapsed days.

### 3. Statistical Confidence Saturation
$$\text{Confidence}(n) = 1 - \exp(-\beta \cdot n_{\text{observations}})$$

### 4. Dual-EMA Trend Detection
$$\text{Momentum} = \text{EMA}_{\text{short}}(\text{scores}) - \text{EMA}_{\text{long}}(\text{scores})$$

---

## Verification & Testing

To run the complete unit and integration test suite:
```bash
python tests/test_intelligence.py
```
All components validate without external test-runner dependencies.
=======
# student-intelligence-engine
>>>>>>> 5aef5617f4b3fabed7b639279adddd83294908e2
