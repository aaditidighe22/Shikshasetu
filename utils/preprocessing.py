"""
ShikshaSetu AI - Preprocessing Utilities
Feature extraction and data preparation helpers for ML pipeline.
"""

import pandas as pd
import numpy as np


def build_feature_vector(
    current_score: float,
    prev_score: float = None,
    correct_answers: int = None,
    total_questions: int = 25,
    avg_time: float = 45.0,
    topic_score: float = None,
    difficulty_breakdown: dict = None,
    num_attempts: int = 1,
):
    """
    Build a feature dict compatible with the ML model.
    Fills missing values with sensible defaults derived from score_pct.
    """
    if prev_score is None:
        prev_score = max(current_score - 5.0, 0.0)
    if correct_answers is None:
        correct_answers = round(current_score / 100 * total_questions)
    incorrect_answers = total_questions - correct_answers
    if topic_score is None:
        topic_score = current_score

    diff = difficulty_breakdown or {}
    easy_pct = diff.get("easy", min(current_score + 10, 100))
    medium_pct = diff.get("medium", current_score)
    hard_pct = diff.get("hard", max(current_score - 15, 0))

    prev_improvement = current_score - prev_score

    return {
        "prev_score": round(prev_score, 2),
        "current_score": round(current_score, 2),
        "correct_answers": int(correct_answers),
        "incorrect_answers": int(incorrect_answers),
        "avg_time_per_question": round(avg_time, 2),
        "topic_score": round(topic_score, 2),
        "easy_correct_pct": round(easy_pct, 2),
        "medium_correct_pct": round(medium_pct, 2),
        "hard_correct_pct": round(hard_pct, 2),
        "num_attempts": int(num_attempts),
        "prev_improvement": round(prev_improvement, 2),
    }


def compute_difficulty_breakdown(answers: list, questions: list) -> dict:
    """
    Given a list of answers and question dicts, compute per-difficulty accuracy.
    answers: list of selected option letters ('A','B','C','D')
    questions: list of question dicts with keys 'correct_answer' and 'difficulty'
    """
    buckets = {"easy": {"c": 0, "t": 0}, "medium": {"c": 0, "t": 0}, "hard": {"c": 0, "t": 0}}
    for ans, q in zip(answers, questions):
        diff = q.get("difficulty", "medium").lower()
        if diff not in buckets:
            diff = "medium"
        buckets[diff]["t"] += 1
        if ans == q.get("correct_answer", ""):
            buckets[diff]["c"] += 1

    result = {}
    for diff, vals in buckets.items():
        result[diff] = round(vals["c"] / vals["t"] * 100, 1) if vals["t"] > 0 else 0.0
    return result


def score_answers(answers: list, questions: list) -> dict:
    """
    Score a list of MCQ answers against question correct answers.
    Returns dict with: total, correct, incorrect, score_pct, per_question
    """
    total = len(questions)
    if total == 0:
        return {"total": 0, "correct": 0, "incorrect": 0, "score_pct": 0.0, "per_question": []}

    per_q = []
    correct_count = 0
    for i, (ans, q) in enumerate(zip(answers, questions)):
        is_correct = ans == q.get("correct_answer", "")
        if is_correct:
            correct_count += 1
        per_q.append({
            "question_id": q.get("question_id"),
            "question": q.get("question"),
            "selected": ans,
            "correct_answer": q.get("correct_answer"),
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
            "topic": q.get("topic"),
            "subject": q.get("subject"),
            "difficulty": q.get("difficulty"),
        })

    score_pct = round(correct_count / total * 100, 1)
    return {
        "total": total,
        "correct": correct_count,
        "incorrect": total - correct_count,
        "score_pct": score_pct,
        "per_question": per_q,
    }


def compute_subject_scores(per_question: list) -> dict:
    """Aggregate per-question results into subject-level scores."""
    subject_data = {}
    for pq in per_question:
        subj = pq.get("subject", "Unknown")
        if subj not in subject_data:
            subject_data[subj] = {"correct": 0, "total": 0}
        subject_data[subj]["total"] += 1
        if pq["is_correct"]:
            subject_data[subj]["correct"] += 1

    return {
        subj: round(v["correct"] / v["total"] * 100, 1)
        for subj, v in subject_data.items()
        if v["total"] > 0
    }


def compute_topic_scores(per_question: list) -> dict:
    """Aggregate per-question results into topic-level scores."""
    topic_data = {}
    for pq in per_question:
        topic = pq.get("topic", "Unknown")
        if topic not in topic_data:
            topic_data[topic] = {"correct": 0, "total": 0}
        topic_data[topic]["total"] += 1
        if pq["is_correct"]:
            topic_data[topic]["correct"] += 1

    return {
        topic: round(v["correct"] / v["total"] * 100, 1)
        for topic, v in topic_data.items()
        if v["total"] > 0
    }


def classify_score(score_pct: float) -> str:
    """Rule-based learning status classification."""
    if score_pct >= 80:
        return "Strong"
    elif score_pct >= 60:
        return "Moderate"
    else:
        return "Needs Support"
