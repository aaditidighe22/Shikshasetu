"""
ShikshaSetu AI - Practice Module
Topic-focused practice with MCQs, immediate feedback and score tracking.
"""

import streamlit as st
from database.database import (
    get_practice_questions,
    save_practice_attempt,
)
from utils.helpers import (
    get_session, set_session, metric_card, STATUS_COLORS,
    get_status_label, fmt_pct,
)

OPTION_LABELS = ["A", "B", "C", "D"]
OPTION_KEYS   = ["option_a", "option_b", "option_c", "option_d"]


def render_practice():
    student_id = get_session("student_id")
    if not student_id:
        st.warning("⚠️ Please log in to access practice questions.")
        return

    weak_subject = get_session("weak_subject")
    weak_topic   = get_session("weak_topic")

    if not weak_subject or not weak_topic:
        st.info(
            "📋 Complete the diagnostic tests first to unlock your personalized practice questions."
        )
        if st.button("Take Diagnostic Test", type="primary"):
            set_session("page", "Diagnostic Test")
            st.rerun()
        return

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#0369a1,#0ea5e9);color:#fff;
                    padding:24px;border-radius:12px;margin-bottom:20px;">
            <h2 style="margin:0;">✏️ Practice — {weak_topic}</h2>
            <p style="margin:6px 0 0 0;opacity:0.9;">
            Subject: {weak_subject} &nbsp;|&nbsp; 5 practice questions with explanations
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Load practice questions
    if not get_session("practice_questions"):
        questions = get_practice_questions(weak_subject, weak_topic, limit=5)
        if not questions:
            st.warning(
                f"No practice questions found for **{weak_topic}** in **{weak_subject}**.\n\n"
                "Tip: Practice questions are available for Computer Science → Databases. "
                "Try selecting that topic via the diagnostic flow."
            )
            return
        set_session("practice_questions", questions)
        set_session("practice_submitted", False)
        set_session("practice_answers", {})

    questions = get_session("practice_questions")
    submitted = get_session("practice_submitted", False)

    if submitted:
        _show_practice_results(student_id, weak_subject, weak_topic, questions)
        return

    # Render question form
    answers = get_session("practice_answers", {})

    with st.form("practice_form"):
        for idx, q in enumerate(questions):
            qid = q["question_id"]
            st.markdown(f"**Q{idx+1}. {q['question']}**")
            _diff_badge(q["difficulty"])

            options = {lbl: q[key] for lbl, key in zip(OPTION_LABELS, OPTION_KEYS)}
            choices = [f"{lbl}. {text}" for lbl, text in options.items()]
            default = 0
            if str(qid) in answers:
                prev = answers[str(qid)]
                matched = [i for i, c in enumerate(choices) if c.startswith(prev + ".")]
                if matched:
                    default = matched[0]

            selected = st.radio(
                label=f"pq_{qid}",
                options=choices,
                index=default,
                key=f"prac_{qid}",
                label_visibility="collapsed",
            )
            answers[str(qid)] = selected[0]
            st.markdown("<br>", unsafe_allow_html=True)

        sub_btn = st.form_submit_button("✅ Submit Practice", use_container_width=True)

    set_session("practice_answers", answers)

    if sub_btn:
        set_session("practice_submitted", True)
        st.rerun()


def _show_practice_results(student_id, subject, topic, questions):
    answers = get_session("practice_answers", {})

    correct = 0
    results = []
    for q in questions:
        qid = q["question_id"]
        selected = answers.get(str(qid), "A")
        is_correct = selected == q["correct_answer"]
        if is_correct:
            correct += 1
        results.append({**q, "selected": selected, "is_correct": is_correct})
        # Persist to DB (idempotent on rerun via session guard)

    score_pct = round(correct / len(questions) * 100, 1) if questions else 0
    status = get_status_label(score_pct)

    # Save only once per session
    if not get_session("practice_saved"):
        for r in results:
            save_practice_attempt(
                student_id, subject, topic,
                r["question_id"], r["selected"], r["is_correct"]
            )
        set_session("practice_saved", True)
        set_session("practice_score", score_pct)

    # Summary
    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card("Practice Score", fmt_pct(score_pct), status,
                    color=STATUS_COLORS.get(status, "#3b82d4"))
    with col2:
        metric_card("Correct Answers", f"{correct}/{len(questions)}", "", color="#22c55e")
    with col3:
        metric_card("Topic", topic, subject, color="#7c5cd8")

    # Detailed feedback per question
    st.markdown("### 📋 Answer Review")
    for i, r in enumerate(results):
        icon = "✅" if r["is_correct"] else "❌"
        border = "#86efac" if r["is_correct"] else "#fca5a5"
        bg     = "#f0fdf4" if r["is_correct"] else "#fef2f2"
        st.markdown(
            f"""
            <div style="background:{bg};border:1px solid {border};border-radius:8px;
                        padding:12px 16px;margin-bottom:8px;">
                <strong>{icon} Q{i+1}. {r['question']}</strong><br>
                <span style="color:#57606a;">Your answer: <strong>{r['selected']}</strong>
                &nbsp;|&nbsp; Correct: <strong>{r['correct_answer']}</strong></span><br>
                {'<span style="color:#059669;font-size:0.87em;">💡 '+r['explanation']+'</span>' if r.get('explanation') else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    if score_pct >= 80:
        st.success(f"🎉 Excellent! You scored {fmt_pct(score_pct)}. You're ready for the reassessment!")
    elif score_pct >= 60:
        st.info(f"👍 Good effort! Score: {fmt_pct(score_pct)}. Review the incorrect answers and try the reassessment.")
    else:
        st.warning(f"📚 Score: {fmt_pct(score_pct)}. Review the learning recommendations and practice again.")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("🔄 Practice Again", use_container_width=True):
            for k in ["practice_questions", "practice_submitted", "practice_answers",
                      "practice_saved", "practice_score"]:
                st.session_state.pop(k, None)
            st.rerun()
    with col_b:
        if st.button("📝 Take Reassessment", type="primary", use_container_width=True):
            set_session("page", "Reassessment")
            st.rerun()
    with col_c:
        if st.button("📚 Review Recommendations", use_container_width=True):
            set_session("page", "Personalized Learning")
            st.rerun()


def _diff_badge(difficulty: str):
    colors = {"easy": "#22c55e", "medium": "#f59e0b", "hard": "#ef4444"}
    color  = colors.get(difficulty.lower(), "#6b7280")
    st.markdown(
        f'<span style="background:{color};color:#fff;padding:1px 8px;'
        f'border-radius:8px;font-size:0.75em;font-weight:600;">'
        f'{difficulty.upper()}</span>',
        unsafe_allow_html=True,
    )
