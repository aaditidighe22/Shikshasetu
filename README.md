# ShikshaSetu AI 🎓
### *"From Score to Learning Gap to Improvement"*

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)](https://streamlit.io)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-Random%20Forest-orange)](https://scikit-learn.org)
[![SDG4](https://img.shields.io/badge/SDG%204-Quality%20Education-green)](https://sdgs.un.org/goals/goal4)

---

## Problem Statement

Traditional tests only provide **marks**. They do not identify:
- *Why* a student is weak
- *Which specific topic or concept* the student needs to improve

ShikshaSetu AI solves this by detecting learning gaps at **two levels** — Subject and Topic — using ML-powered diagnostics and generating **personalized learning pathways**.

---

## Why This Project is Needed

- 1 in 3 school students struggles with foundational gaps that go undetected
- Teachers lack tools to identify *which specific concept* each student is missing
- Marks alone do not guide students on *what to study next*
- Personalized remediation at scale requires AI assistance

---

## SDG 4 — Quality Education

ShikshaSetu AI directly supports **Sustainable Development Goal 4**:
> *"Ensure inclusive and equitable quality education and promote lifelong learning opportunities for all."*

By identifying individual learning gaps and providing personalized improvement pathways, it enables equitable, targeted, and evidence-based education.

---

## Unique Idea

```
ALL-SUBJECT DIAGNOSTIC TEST
         ↓
   AI/ML ANALYSIS
         ↓
  IDENTIFY WEAK SUBJECT
         ↓
SUBJECT-SPECIFIC DIAGNOSTIC TEST
         ↓
   IDENTIFY WEAK TOPIC
         ↓
PERSONALIZED LEARNING RECOMMENDATION
         ↓
       PRACTICE
         ↓
    REASSESSMENT
         ↓
  MEASURE IMPROVEMENT
```

**Two-level detection** (Subject → Topic/Concept) is the core innovation.

---

## Features

| Feature | Description |
|---|---|
| Multi-Subject Diagnostic Test | 5 subjects × 5 questions = 25 MCQs |
| AI Weak Subject Detection | Identifies lowest-performing subject |
| Subject Topic Diagnostic Test | 5 topics × 3 questions = 15 MCQs per subject |
| ML Learning Status Classification | Random Forest: Strong / Moderate / Needs Support |
| Personalized Learning Pathway | Topic-specific step-by-step recommendations |
| Practice Module | 5 topic-focused MCQs with explanations |
| Reassessment | Before vs After improvement measurement |
| Student Dashboard | Full progress tracking with Plotly charts |
| Teacher Dashboard | Class overview, learning gap analytics, student profiles |
| Demo Data | Pre-seeded demo students and sample assessment records |
| Optional AI Assistant | Chatbot (OpenAI/Google Gemini) for learning support |

---

## AI/ML Methodology

### Model
- **Algorithm:** Random Forest Classifier (`n_estimators=100`, balanced class weights)
- **Training Data:** 100-sample synthetic dataset (clearly labeled as demo/prototype data)
- **Features:** `prev_score`, `current_score`, `correct_answers`, `incorrect_answers`, `avg_time_per_question`, `topic_score`, `easy_correct_pct`, `medium_correct_pct`, `hard_correct_pct`, `num_attempts`, `prev_improvement`
- **Target:** `learning_status` → Strong | Moderate | Needs Support
- **Split:** 80% train / 20% test, stratified

### Classification Rules (fallback if model not trained)
| Score | Status |
|---|---|
| ≥ 80% | Strong |
| 60–79% | Moderate |
| < 60% | Needs Support |

> ⚠️ **Important Note:** Prototype ML results are based on **synthetic/demo assessment data** and should not be interpreted as real-world educational effectiveness.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Application Framework | Python + Streamlit |
| Machine Learning | scikit-learn (Random Forest) |
| Data Processing | Pandas + NumPy |
| Visualization | Plotly |
| Database | SQLite (sqlite3) |
| Model Persistence | joblib |
| Environment Config | python-dotenv |

---

## Architecture

```
app.py  (Streamlit entry point)
├── database/
│   └── database.py          ← Schema, CRUD, seeding
├── models/
│   ├── train_model.py        ← Random Forest training + prediction
│   └── learning_gap_model.pkl
├── modules/
│   ├── auth.py               ← Login / register
│   ├── diagnostic_test.py    ← Level-1 & Level-2 tests
│   ├── learning_analysis.py  ← Profile + charts
│   ├── recommendation.py     ← Learning pathways
│   ├── practice.py           ← Practice MCQs
│   ├── reassessment.py       ← Before vs After
│   ├── student_dashboard.py  ← Student view
│   └── teacher_dashboard.py  ← Teacher view
├── utils/
│   ├── preprocessing.py      ← Scoring, feature building
│   └── helpers.py            ← UI helpers, constants
└── data/
    ├── questions.csv
    └── ml_training_data.csv
```

---

## Installation

### 1. Clone / Download the project

```bash
git clone <repo-url>
cd shikshasetu_ai
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## How to Train the ML Model

The ML model trains **automatically** on first run. To retrain manually:

```bash
python models/train_model.py
```

This will:
1. Load `data/ml_training_data.csv`
2. Train a Random Forest Classifier
3. Print accuracy, classification report, and confusion matrix
4. Save `models/learning_gap_model.pkl` and `models/label_encoder.pkl`

---

## How to Initialize the Database

The database initializes **automatically** on first `streamlit run`. To initialize manually:

```python
from database.database import initialize_all
initialize_all()
```

---

## How to Run the Application

```bash
streamlit run app.py
```

The app will open at **http://localhost:8501**

---

## Demo Credentials

| Role | Username | Password |
|---|---|---|
| Demo Student | `demo` | `demo123` |
| Student 1 | `student1` | `student123` |
| Student 2 | `student2` | `student123` |
| Student 3 | `student3` | `student123` |
| Teacher | `teacher` | `teacher123` |

---

## How to Test the Complete Workflow

1. **Open** the application: `streamlit run app.py`
2. **Login** as `demo` / `demo123`
3. Navigate to **Diagnostic Test** → Answer 25 questions → Submit
4. View subject scores → Weakest subject is detected automatically
5. Navigate to **Subject Diagnostic Test** → Answer 15 questions → Submit
6. View topic scores → Weakest topic is detected
7. Navigate to **Learning Profile** → See ML classification + gap summary
8. Navigate to **Personalized Learning** → View step-by-step recommendations
9. Navigate to **Practice** → Answer 5 practice questions → Submit
10. Navigate to **Reassessment** → Answer 5 reassessment questions → Submit
11. View **Before vs After** improvement chart
12. Navigate to **Progress / Dashboard** → Full summary with all charts
13. **Logout** → Login as `teacher` / `teacher123`
14. Navigate to **Teacher Dashboard** → View class overview, gaps, student profiles

---

## Project Structure

```
shikshasetu_ai/
│
├── app.py                   ← Main entry point
├── requirements.txt
├── README.md
├── .env.example
│
├── data/
│   ├── questions.csv        ← All MCQ questions (5 subjects × topics)
│   └── ml_training_data.csv ← Synthetic training data (100 records)
│
├── database/
│   └── database.py          ← SQLite schema + CRUD + seed data
│
├── models/
│   ├── train_model.py        ← Random Forest training + predict_from_score()
│   └── learning_gap_model.pkl (auto-generated)
│
├── modules/
│   ├── auth.py
│   ├── diagnostic_test.py
│   ├── learning_analysis.py
│   ├── recommendation.py
│   ├── practice.py
│   ├── reassessment.py
│   ├── student_dashboard.py
│   └── teacher_dashboard.py
│
├── utils/
│   ├── preprocessing.py
│   └── helpers.py
│
└── assets/
    └── README.txt
```

---

## Future Scope — Agentic Personalized Learning

The project is architectured to support a future **Learning Agent** that will:

1. **Analyze** the student profile and diagnostic results autonomously
2. **Identify** priority learning gaps using multi-factor analysis
3. **Select** appropriate learning content and resources
4. **Generate** adaptive practice questions (adjusting difficulty dynamically)
5. **Evaluate** practice performance in real time
6. **Adjust** difficulty and topic focus based on student responses
7. **Orchestrate** the full improvement cycle: Diagnose → Learn → Practice → Reassess → Repeat

This would transform ShikshaSetu from a diagnostic platform into a fully autonomous **personalized tutoring agent**.

---

## Presentation Talking Points

| Question | Answer |
|---|---|
| **WHY** | Traditional marks don't identify learning gaps |
| **WHAT** | AI-powered 2-level subject + topic gap detection |
| **HOW** | Diagnostic test → ML analysis → Recommendations → Practice → Reassessment |
| **UNIQUE** | Two-level detection: Subject → Topic/Concept |
| **IMPACT** | Students know exactly what to study; teachers identify who needs help |
| **SDG** | SDG 4 — Quality Education |

---

## Important Disclaimer

> This is a **prototype / MVP** built for educational demonstration purposes.
> The ML model is trained on **synthetic data** for illustration.
> Results should not be used for real academic decisions without validation on real educational datasets.

---

*Built with ❤️ using Python, Streamlit, and scikit-learn*
*Aligned with SDG 4 — Quality Education*
