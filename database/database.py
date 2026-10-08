"""
ShikshaSetu AI - Database Module
Handles all SQLite database operations: schema creation, CRUD, and sample data seeding.
"""

import sqlite3
import os
import pandas as pd
import hashlib
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "shikshasetu.db")


def get_connection():
    """Return a SQLite connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS subjects (
            subject_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL UNIQUE,
            description  TEXT
        );

        CREATE TABLE IF NOT EXISTS topics (
            topic_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id  INTEGER NOT NULL,
            name        TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
            UNIQUE(subject_id, name)
        );

        CREATE TABLE IF NOT EXISTS students (
            student_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT NOT NULL UNIQUE,
            password     TEXT NOT NULL,
            full_name    TEXT NOT NULL,
            class_name   TEXT,
            section      TEXT,
            standard     TEXT DEFAULT '8',
            created_at   TEXT DEFAULT (datetime('now')),
            is_demo      INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS teachers (
            teacher_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT NOT NULL UNIQUE,
            password    TEXT NOT NULL,
            full_name   TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS questions (
            question_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            subject      TEXT NOT NULL,
            topic        TEXT NOT NULL,
            question     TEXT NOT NULL,
            option_a     TEXT NOT NULL,
            option_b     TEXT NOT NULL,
            option_c     TEXT NOT NULL,
            option_d     TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            difficulty   TEXT NOT NULL,
            explanation  TEXT,
            question_type TEXT NOT NULL DEFAULT 'diagnostic',
            standard     TEXT DEFAULT NULL
        );

        CREATE TABLE IF NOT EXISTS assessments (
            assessment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id      INTEGER NOT NULL,
            assessment_type TEXT NOT NULL,
            subject         TEXT,
            started_at      TEXT DEFAULT (datetime('now')),
            completed_at    TEXT,
            total_questions INTEGER,
            correct_answers INTEGER,
            score_pct       REAL,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );

        CREATE TABLE IF NOT EXISTS assessment_answers (
            answer_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER NOT NULL,
            question_id   INTEGER NOT NULL,
            selected_answer TEXT,
            is_correct    INTEGER,
            time_taken_sec INTEGER DEFAULT 30,
            FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id),
            FOREIGN KEY (question_id) REFERENCES questions(question_id)
        );

        CREATE TABLE IF NOT EXISTS results (
            result_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id    INTEGER NOT NULL,
            assessment_id INTEGER NOT NULL,
            subject       TEXT,
            topic         TEXT,
            score_pct     REAL,
            learning_status TEXT,
            recorded_at   TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
        );

        CREATE TABLE IF NOT EXISTS learning_gaps (
            gap_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id    INTEGER NOT NULL,
            assessment_id INTEGER NOT NULL,
            subject       TEXT NOT NULL,
            topic         TEXT,
            score_pct     REAL,
            ml_status     TEXT,
            priority_rank INTEGER,
            identified_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );

        CREATE TABLE IF NOT EXISTS practice_attempts (
            attempt_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id    INTEGER NOT NULL,
            topic         TEXT NOT NULL,
            subject       TEXT NOT NULL,
            question_id   INTEGER NOT NULL,
            selected_answer TEXT,
            is_correct    INTEGER,
            attempted_at  TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );

        CREATE TABLE IF NOT EXISTS reassessments (
            reassessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id      INTEGER NOT NULL,
            topic           TEXT NOT NULL,
            subject         TEXT NOT NULL,
            before_score    REAL,
            after_score     REAL,
            improvement     REAL,
            completed_at    TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );
    """)
    conn.commit()
    conn.close()


def seed_questions():
    """Load questions from CSV into the database (diagnostic + subject_diagnostic + practice + reassessment)."""
    conn = get_connection()
    c = conn.cursor()
    count = c.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    if count > 0:
        conn.close()
        return

    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "questions.csv")
    if not os.path.exists(csv_path):
        conn.close()
        return

    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        c.execute("""
            INSERT OR IGNORE INTO questions
            (subject, topic, question, option_a, option_b, option_c, option_d,
             correct_answer, difficulty, explanation, question_type, standard)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            row["subject"], row["topic"], row["question"],
            row["option_a"], row["option_b"], row["option_c"], row["option_d"],
            row["correct_answer"], row["difficulty"],
            row.get("explanation", ""), row.get("question_type", "diagnostic"),
            row.get("standard", None) if "standard" in row else None,
        ))
    conn.commit()
    conn.close()


def seed_standard_questions():
    """Load standard-wise questions from questions_standard.csv."""
    conn = get_connection()
    c = conn.cursor()
    # Check if standard_test questions already seeded
    count = c.execute(
        "SELECT COUNT(*) FROM questions WHERE question_type='standard_test'"
    ).fetchone()[0]
    if count > 0:
        conn.close()
        return

    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "questions_standard.csv")
    if not os.path.exists(csv_path):
        conn.close()
        return

    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        c.execute("""
            INSERT OR IGNORE INTO questions
            (subject, topic, question, option_a, option_b, option_c, option_d,
             correct_answer, difficulty, explanation, question_type, standard)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            row["subject"], row["topic"], row["question"],
            row["option_a"], row["option_b"], row["option_c"], row["option_d"],
            row["correct_answer"], row["difficulty"],
            row.get("explanation", ""), "standard_test",
            str(row.get("standard", "8")),
        ))
    conn.commit()
    conn.close()


def seed_demo_users():
    """Create demo student and teacher accounts."""
    conn = get_connection()
    c = conn.cursor()

    # Demo teacher
    c.execute("""
        INSERT OR IGNORE INTO teachers (username, password, full_name)
        VALUES (?, ?, ?)
    """, ("teacher", hash_password("teacher123"), "Demo Teacher"))

    # Demo students — one per standard (6-10) + a general demo
    demo_students = [
        ("student1", "student123", "Priya Sharma",  "8th", "A", "8"),
        ("student2", "student123", "Arjun Mehta",   "9th", "A", "9"),
        ("student3", "student123", "Sneha Patel",   "7th", "B", "7"),
        ("student4", "student123", "Rohan Kumar",   "10th","B", "10"),
        ("student5", "student123", "Anika Verma",   "6th", "A", "6"),
        ("demo",     "demo123",    "Demo Student",  "8th", "A", "8"),
    ]
    for uname, pwd, name, cls, sec, std in demo_students:
        c.execute("""
            INSERT OR IGNORE INTO students
            (username, password, full_name, class_name, section, standard, is_demo)
            VALUES (?,?,?,?,?,?,1)
        """, (uname, hash_password(pwd), name, cls, sec, std))

    conn.commit()
    conn.close()


def seed_sample_results():
    """Create sample assessment data for demo students to populate the teacher dashboard."""
    conn = get_connection()
    c = conn.cursor()

    # Only seed if no assessments exist
    count = c.execute("SELECT COUNT(*) FROM assessments").fetchone()[0]
    if count > 0:
        conn.close()
        return

    subjects = ["Mathematics", "Science", "English", "Social Science", "Computer Science"]
    topics_map = {
        "Mathematics": ["Arithmetic", "Fractions", "Algebra", "Geometry", "Linear Equations"],
        "Science": ["Matter", "Force and Motion", "Energy", "Human Body", "Environment"],
        "English": ["Grammar", "Vocabulary", "Reading Comprehension", "Sentence Formation", "Writing"],
        "Social Science": ["History", "Geography", "Civics", "Economics", "Environment"],
        "Computer Science": ["Computer Basics", "Programming Fundamentals", "Algorithms", "Databases", "Networking"],
    }

    # Get demo student IDs
    students = c.execute(
        "SELECT student_id FROM students WHERE is_demo=1 AND username != 'demo'"
    ).fetchall()

    random.seed(42)
    for student in students:
        sid = student["student_id"]
        # Multi-subject diagnostic
        total_q = 25
        correct = random.randint(12, 22)
        score = round(correct / total_q * 100, 1)
        c.execute("""
            INSERT INTO assessments (student_id, assessment_type, total_questions, correct_answers, score_pct, completed_at)
            VALUES (?,?,?,?,?,?)
        """, (sid, "multi_subject", total_q, correct, score,
              (datetime.now() - timedelta(days=random.randint(1, 10))).isoformat()))
        assessment_id = c.lastrowid

        # Subject results
        for subj in subjects:
            subj_score = round(random.uniform(35, 95), 1)
            status = "Strong" if subj_score >= 80 else ("Moderate" if subj_score >= 60 else "Needs Support")
            c.execute("""
                INSERT INTO results (student_id, assessment_id, subject, score_pct, learning_status)
                VALUES (?,?,?,?,?)
            """, (sid, assessment_id, subj, subj_score, status))

            # Topic results for weakest subject
            for topic in topics_map[subj]:
                topic_score = round(random.uniform(30, 90), 1)
                tstatus = "Strong" if topic_score >= 80 else ("Moderate" if topic_score >= 60 else "Needs Support")
                c.execute("""
                    INSERT INTO results (student_id, assessment_id, subject, topic, score_pct, learning_status)
                    VALUES (?,?,?,?,?,?)
                """, (sid, assessment_id, subj, topic, topic_score, tstatus))

            # Learning gaps for needs-support subjects
            if status == "Needs Support":
                c.execute("""
                    INSERT INTO learning_gaps (student_id, assessment_id, subject, score_pct, ml_status, priority_rank)
                    VALUES (?,?,?,?,?,1)
                """, (sid, assessment_id, subj, subj_score, status))

        # Reassessment for one topic
        before = round(random.uniform(30, 55), 1)
        after = round(before + random.uniform(15, 40), 1)
        after = min(after, 95.0)
        c.execute("""
            INSERT INTO reassessments (student_id, topic, subject, before_score, after_score, improvement)
            VALUES (?,?,?,?,?,?)
        """, (sid, "Databases", "Computer Science", before, after, round(after - before, 1)))

    conn.commit()
    conn.close()


# ─── CRUD helpers ──────────────────────────────────────────────────────────────

def get_student_by_username(username: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM students WHERE username=?", (username,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_teacher_by_username(username: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM teachers WHERE username=?", (username,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_student(username, password, full_name, class_name="", section="", standard="8"):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO students (username, password, full_name, class_name, section, standard)
            VALUES (?,?,?,?,?,?)
        """, (username, hash_password(password), full_name, class_name, section, str(standard)))
        conn.commit()
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists. Please choose another."
    finally:
        conn.close()


def get_questions(subject=None, question_type="diagnostic", limit=None):
    conn = get_connection()
    query = "SELECT * FROM questions WHERE question_type=?"
    params = [question_type]
    if subject:
        query += " AND subject=?"
        params.append(subject)
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_questions_for_diagnostic(subjects=None):
    """Fetch 5 questions per subject for multi-subject diagnostic."""
    conn = get_connection()
    all_q = []
    if subjects is None:
        subjects = ["Mathematics", "Science", "English", "Social Science", "Computer Science"]
    for subj in subjects:
        rows = conn.execute(
            "SELECT * FROM questions WHERE subject=? AND question_type='diagnostic' ORDER BY RANDOM() LIMIT 5",
            (subj,)
        ).fetchall()
        all_q.extend([dict(r) for r in rows])
    conn.close()
    return all_q


def get_questions_for_subject_diagnostic(subject):
    """Fetch 3 questions per topic for subject-specific diagnostic (15 total)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT topic FROM questions WHERE subject=? AND question_type='subject_diagnostic'",
        (subject,)
    ).fetchall()
    topics = [r["topic"] for r in rows]

    all_q = []
    for topic in topics:
        q_rows = conn.execute(
            """SELECT * FROM questions WHERE subject=? AND topic=? AND question_type='subject_diagnostic'
               ORDER BY RANDOM() LIMIT 3""",
            (subject, topic)
        ).fetchall()
        all_q.extend([dict(r) for r in q_rows])
    conn.close()
    return all_q


def get_practice_questions(subject, topic, limit=5):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM questions WHERE subject=? AND topic=? AND question_type='practice' ORDER BY RANDOM() LIMIT ?",
        (subject, topic, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_reassessment_questions(subject, topic, limit=5):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM questions WHERE subject=? AND topic=? AND question_type='reassessment' ORDER BY RANDOM() LIMIT ?",
        (subject, topic, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_assessment(student_id, assessment_type, subject, total_q, correct, score_pct):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO assessments (student_id, assessment_type, subject, total_questions,
                                 correct_answers, score_pct, completed_at)
        VALUES (?,?,?,?,?,?,?)
    """, (student_id, assessment_type, subject, total_q, correct, score_pct,
          datetime.now().isoformat()))
    assessment_id = c.lastrowid
    conn.commit()
    conn.close()
    return assessment_id


def save_result(student_id, assessment_id, subject, topic, score_pct, learning_status):
    conn = get_connection()
    conn.execute("""
        INSERT INTO results (student_id, assessment_id, subject, topic, score_pct, learning_status)
        VALUES (?,?,?,?,?,?)
    """, (student_id, assessment_id, subject, topic, score_pct, learning_status))
    conn.commit()
    conn.close()


def save_learning_gap(student_id, assessment_id, subject, topic, score_pct, ml_status, rank=1):
    conn = get_connection()
    conn.execute("""
        INSERT INTO learning_gaps (student_id, assessment_id, subject, topic, score_pct, ml_status, priority_rank)
        VALUES (?,?,?,?,?,?,?)
    """, (student_id, assessment_id, subject, topic, score_pct, ml_status, rank))
    conn.commit()
    conn.close()


def save_practice_attempt(student_id, subject, topic, question_id, selected, is_correct):
    conn = get_connection()
    conn.execute("""
        INSERT INTO practice_attempts (student_id, topic, subject, question_id, selected_answer, is_correct)
        VALUES (?,?,?,?,?,?)
    """, (student_id, topic, subject, question_id, selected, int(is_correct)))
    conn.commit()
    conn.close()


def save_reassessment(student_id, topic, subject, before_score, after_score):
    improvement = round(after_score - before_score, 1)
    conn = get_connection()
    conn.execute("""
        INSERT INTO reassessments (student_id, topic, subject, before_score, after_score, improvement)
        VALUES (?,?,?,?,?,?)
    """, (student_id, topic, subject, before_score, after_score, improvement))
    conn.commit()
    conn.close()


def get_student_results(student_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM results WHERE student_id=? ORDER BY recorded_at DESC",
        (student_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_multi_subject_scores(student_id):
    """Return subject-level scores from the latest multi-subject diagnostic."""
    conn = get_connection()
    assessment = conn.execute("""
        SELECT assessment_id FROM assessments
        WHERE student_id=? AND assessment_type='multi_subject'
        ORDER BY completed_at DESC LIMIT 1
    """, (student_id,)).fetchone()
    if not assessment:
        conn.close()
        return {}
    rows = conn.execute("""
        SELECT subject, score_pct FROM results
        WHERE student_id=? AND assessment_id=? AND topic IS NULL
    """, (student_id, assessment["assessment_id"])).fetchall()
    conn.close()
    return {r["subject"]: r["score_pct"] for r in rows}


def get_reassessment_history(student_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reassessments WHERE student_id=? ORDER BY completed_at DESC",
        (student_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_students():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM students ORDER BY full_name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_class_subject_scores():
    """Aggregate subject scores for teacher dashboard."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT r.subject, AVG(r.score_pct) as avg_score,
               COUNT(DISTINCT r.student_id) as student_count
        FROM results r
        WHERE r.topic IS NULL AND r.subject IS NOT NULL
        GROUP BY r.subject
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_common_learning_gaps():
    """Count most frequent weak topics across all students."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT topic, subject, COUNT(*) as frequency
        FROM learning_gaps
        WHERE topic IS NOT NULL
        GROUP BY topic, subject
        ORDER BY frequency DESC
        LIMIT 10
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_students_needing_support():
    """Students with at least one 'Needs Support' result."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT DISTINCT s.student_id, s.full_name, s.class_name, s.section,
               COUNT(CASE WHEN r.learning_status='Needs Support' THEN 1 END) as gap_count
        FROM students s
        JOIN results r ON s.student_id = r.student_id
        WHERE r.topic IS NULL
        GROUP BY s.student_id
        HAVING gap_count > 0
        ORDER BY gap_count DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_standard_questions(standard: str, subject: str = None, limit_per_subject: int = 6):
    """
    Fetch standard-wise test questions.
    If subject is given: all questions for that subject in that standard.
    Otherwise: limit_per_subject questions per subject.
    """
    conn = get_connection()
    if subject:
        rows = conn.execute(
            """SELECT * FROM questions
               WHERE question_type='standard_test' AND standard=? AND subject=?
               ORDER BY RANDOM()""",
            (str(standard), subject),
        ).fetchall()
    else:
        subjects = ["Mathematics", "Science", "English", "Social Science", "Computer Science"]
        rows_all = []
        for subj in subjects:
            r = conn.execute(
                """SELECT * FROM questions
                   WHERE question_type='standard_test' AND standard=? AND subject=?
                   ORDER BY RANDOM() LIMIT ?""",
                (str(standard), subj, limit_per_subject),
            ).fetchall()
            rows_all.extend(r)
        conn.close()
        return [dict(r) for r in rows_all]
    conn.close()
    return [dict(r) for r in rows]


def get_available_standards():
    """Return sorted list of standards that have questions."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT standard FROM questions WHERE question_type='standard_test' ORDER BY standard"
    ).fetchall()
    conn.close()
    return [r["standard"] for r in rows if r["standard"]]


def save_standard_test_result(student_id, standard, subject, total_q, correct, score_pct, topic_scores: dict):
    """Save a standard test assessment and per-topic results."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO assessments
        (student_id, assessment_type, subject, total_questions, correct_answers, score_pct, completed_at)
        VALUES (?,?,?,?,?,?,?)
    """, (student_id, f"standard_{standard}", subject or "All Subjects",
          total_q, correct, score_pct, datetime.now().isoformat()))
    assessment_id = c.lastrowid

    # Save per-topic results
    for topic, t_score in (topic_scores or {}).items():
        status = "Strong" if t_score >= 80 else ("Moderate" if t_score >= 60 else "Needs Support")
        c.execute("""
            INSERT INTO results (student_id, assessment_id, subject, topic, score_pct, learning_status)
            VALUES (?,?,?,?,?,?)
        """, (student_id, assessment_id, subject or "All Subjects", topic, t_score, status))

    conn.commit()
    conn.close()
    return assessment_id


def get_standard_test_history(student_id):
    """Return all standard-test assessments for a student."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM assessments
        WHERE student_id=? AND assessment_type LIKE 'standard_%'
        ORDER BY completed_at DESC
    """, (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_standard_wise_class_stats():
    """For teacher dashboard: average score per standard per subject."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT a.assessment_type, r.subject, AVG(r.score_pct) as avg_score,
               COUNT(DISTINCT r.student_id) as student_count
        FROM assessments a
        JOIN results r ON a.assessment_id = r.assessment_id
        WHERE a.assessment_type LIKE 'standard_%' AND r.topic IS NULL
        GROUP BY a.assessment_type, r.subject
        ORDER BY a.assessment_type, r.subject
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def run_schema_migration():
    """Add 'standard' column to existing tables if not present (safe ALTER TABLE)."""
    conn = get_connection()
    c = conn.cursor()
    # students table
    cols = [row[1] for row in c.execute("PRAGMA table_info(students)").fetchall()]
    if "standard" not in cols:
        c.execute("ALTER TABLE students ADD COLUMN standard TEXT DEFAULT '8'")
    # questions table
    cols_q = [row[1] for row in c.execute("PRAGMA table_info(questions)").fetchall()]
    if "standard" not in cols_q:
        c.execute("ALTER TABLE questions ADD COLUMN standard TEXT DEFAULT NULL")
    conn.commit()
    conn.close()


def initialize_all():
    """One-shot initializer: create schema, migrate, seed questions and demo users."""
    init_db()
    run_schema_migration()   # safe: adds columns only if missing
    seed_questions()
    seed_standard_questions()
    seed_demo_users()
    seed_sample_results()
