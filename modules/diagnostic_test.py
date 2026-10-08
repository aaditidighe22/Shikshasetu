"""
ShikshaSetu AI - Diagnostic Test Module
Level-1 Multi-Subject Test and Level-2 Subject-Specific Diagnostic Test.
"""

import streamlit as st
from database.database import (
    get_questions_for_diagnostic,
    get_questions_for_subject_diagnostic,
    save_assessment,
    save_result,
    save_learning_gap,
)
from utils.preprocessing import score_answers, compute_subject_scores, compute_topic_scores
from utils.helpers import (
    get_session, set_session, section_header, info_box,
    render_progress_bar, SUBJECTS, STATUS_ICONS, STATUS_COLORS,
    get_status_label, fmt_pct, metric_card,
)
from models.train_model import predict_from_score


OPTION_LABELS = ["A", "B", "C", "D"]
OPTION_KEYS   = ["option_a", "option_b", "option_c", "option_d"]


# ──────────────────────────────────────────────────────────────────────────────
# LEVEL 1 — MULTI-SUBJECT DIAGNOSTIC TEST
# ──────────────────────────────────────────────────────────────────────────────

def render_multi_subject_test():
    student_id = get_session("student_id")
    if not student_id:
        st.warning("⚠️ Please log in to take the diagnostic test.")
        return

    # If already completed, show results
    if get_session("diagnostic_result"):
        _show_multi_subject_results()
        return

    # Load / initialise questions
    if not get_session("diagnostic_questions"):
        questions = get_questions_for_diagnostic()
        if not questions:
            st.error("No diagnostic questions found. Please ensure the database is initialised.")
            return
        set_session("diagnostic_questions", questions)
        set_session("diagnostic_answers", {})

    questions = get_session("diagnostic_questions")
    answers   = get_session("diagnostic_answers", {})

    # Header
    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#1e40af,#3b82f6);color:#fff;
                    padding:24px;border-radius:12px;margin-bottom:20px;">
            <h2 style="margin:0;font-size:1.4em;">📋 Multi-Subject Diagnostic Test</h2>
            <p style="margin:6px 0 0 0;opacity:0.9;">5 subjects × 5 questions = 25 questions total</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Group questions by subject
    subjects_order = SUBJECTS
    by_subject = {}
    for q in questions:
        subj = q["subject"]
        by_subject.setdefault(subj, []).append(q)

    # Show questions subject by subject
    with st.form("multi_diag_form"):
        for subj in subjects_order:
            subj_qs = by_subject.get(subj, [])
            if not subj_qs:
                continue
            st.markdown(f"### 📚 {subj}")
            st.markdown("---")
            for idx, q in enumerate(subj_qs):
                qid = q["question_id"]
                st.markdown(f"**Q{idx+1}. {q['question']}**")
                difficulty_badge = _difficulty_badge(q["difficulty"])
                st.markdown(difficulty_badge, unsafe_allow_html=True)

                options = {lbl: q[key] for lbl, key in zip(OPTION_LABELS, OPTION_KEYS)}
                choices = [f"{lbl}. {text}" for lbl, text in options.items()]
                default_idx = 0
                if str(qid) in answers:
                    prev = answers[str(qid)]
                    matched = [i for i, c in enumerate(choices) if c.startswith(prev + ".")]
                    if matched:
                        default_idx = matched[0]

                selected = st.radio(
                    label=f"q_{qid}",
                    options=choices,
                    index=default_idx,
                    key=f"diag_{qid}",
                    label_visibility="collapsed",
                )
                answers[str(qid)] = selected[0]  # store just the letter
                st.markdown("<br>", unsafe_allow_html=True)

        submitted = st.form_submit_button(
            "✅ Submit Diagnostic Test", use_container_width=True
        )

    if submitted:
        _process_multi_subject_results(student_id, questions, answers)
        st.rerun()


def _process_multi_subject_results(student_id, questions, answers):
    ans_list = [answers.get(str(q["question_id"]), "A") for q in questions]
    result   = score_answers(ans_list, questions)
    subject_scores = compute_subject_scores(result["per_question"])

    # Save overall assessment
    assessment_id = save_assessment(
        student_id, "multi_subject", None,
        result["total"], result["correct"], result["score_pct"]
    )

    # Save per-subject results + detect learning status via ML
    for subj, score in subject_scores.items():
        ml_status, _ = predict_from_score(score)
        save_result(student_id, assessment_id, subj, None, score, ml_status)

    # Determine weakest subject
    weakest_subject = min(subject_scores, key=subject_scores.get)
    weakest_score   = subject_scores[weakest_subject]
    ml_status, conf = predict_from_score(weakest_score)
    save_learning_gap(student_id, assessment_id, weakest_subject, None, weakest_score, ml_status, 1)

    # Store in session
    set_session("diagnostic_result", {
        "assessment_id": assessment_id,
        "overall_score": result["score_pct"],
        "correct":       result["correct"],
        "total":         result["total"],
        "subject_scores": subject_scores,
        "per_question":  result["per_question"],
        "weakest_subject": weakest_subject,
    })
    set_session("weak_subject", weakest_subject)


def _show_multi_subject_results():
    result = get_session("diagnostic_result")
    subject_scores = result["subject_scores"]
    weakest = result["weakest_subject"]
    overall = result["overall_score"]
    overall_status = get_status_label(overall)

    st.markdown("## 📊 Diagnostic Test Results")

    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card("Overall Score", fmt_pct(overall), f"Status: {overall_status}",
                    color=STATUS_COLORS[overall_status])
    with col2:
        best_subj = max(subject_scores, key=subject_scores.get)
        metric_card("Strongest Subject", best_subj, fmt_pct(subject_scores[best_subj]),
                    color="#22c55e")
    with col3:
        metric_card("Priority Subject", weakest, fmt_pct(subject_scores[weakest]),
                    color="#ef4444")

    st.markdown("### Subject-wise Performance")
    for subj in SUBJECTS:
        score = subject_scores.get(subj, 0)
        status = get_status_label(score)
        icon = STATUS_ICONS[status]
        render_progress_bar(score, f"{icon} {subj}")

    # Weak subject alert
    st.markdown(
        f"""
        <div style="background:#fef9c3;border:1px solid #f59e0b;border-radius:10px;
                    padding:16px 20px;margin:16px 0;">
            <h4 style="margin:0 0 8px 0;color:#854d0e;">🔍 Learning Gap Identified</h4>
            <p style="margin:0;color:#1f2328;">
            Your diagnostic assessment indicates that <strong>{weakest}</strong>
            ({fmt_pct(subject_scores[weakest])}) requires additional attention.
            </p>
            <p style="margin:8px 0 0 0;color:#57606a;font-size:0.9em;">
            Take the <strong>{weakest} Topic Diagnostic Test</strong> to identify the exact learning gap.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button(f"🔬 Take {weakest} Diagnostic Test", type="primary", use_container_width=True):
            set_session("page", "Subject Diagnostic Test")
            st.rerun()
    with col_b:
        if st.button("🔁 Retake Multi-Subject Test", use_container_width=True):
            for k in ["diagnostic_questions", "diagnostic_answers", "diagnostic_result"]:
                st.session_state.pop(k, None)
            st.rerun()

    # Detailed answer review
    with st.expander("📝 Review Answers"):
        for i, pq in enumerate(result["per_question"]):
            icon = "✅" if pq["is_correct"] else "❌"
            with st.container():
                st.markdown(f"**{i+1}. {pq['question']}** &nbsp;({pq['subject']} — {pq['topic']})")
                st.markdown(
                    f"Your answer: **{pq['selected']}** &nbsp;|&nbsp; "
                    f"Correct: **{pq['correct_answer']}** &nbsp; {icon}"
                )
                if pq["explanation"]:
                    st.caption(f"💡 {pq['explanation']}")
                st.markdown("---")


# ──────────────────────────────────────────────────────────────────────────────
# LEVEL 2 — SUBJECT-SPECIFIC DIAGNOSTIC TEST
# ──────────────────────────────────────────────────────────────────────────────

def render_subject_diagnostic_test():
    student_id = get_session("student_id")
    if not student_id:
        st.warning("⚠️ Please log in to take the subject diagnostic test.")
        return

    weak_subject = get_session("weak_subject")
    if not weak_subject:
        st.info("📋 Please complete the Multi-Subject Diagnostic Test first to identify your weak subject.")
        if st.button("Go to Diagnostic Test"):
            set_session("page", "Diagnostic Test")
            st.rerun()
        return

    if get_session("subject_diag_result"):
        _show_subject_diag_results(weak_subject)
        return

    if not get_session("subject_diag_questions"):
        questions = get_questions_for_subject_diagnostic(weak_subject)
        if not questions:
            st.error(f"No subject-diagnostic questions found for {weak_subject}.")
            return
        set_session("subject_diag_questions", questions)
        set_session("subject_diag_answers", {})

    questions = get_session("subject_diag_questions")
    answers   = get_session("subject_diag_answers", {})

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#7c5cd8,#a78bfa);color:#fff;
                    padding:24px;border-radius:12px;margin-bottom:20px;">
            <h2 style="margin:0;font-size:1.4em;">🔬 {weak_subject} — Topic Diagnostic Test</h2>
            <p style="margin:6px 0 0 0;opacity:0.9;">5 topics × 3 questions = 15 questions total</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Group by topic
    by_topic = {}
    for q in questions:
        by_topic.setdefault(q["topic"], []).append(q)

    with st.form("subject_diag_form"):
        for topic, t_qs in by_topic.items():
            st.markdown(f"### 📌 {topic}")
            st.markdown("---")
            for idx, q in enumerate(t_qs):
                qid = q["question_id"]
                st.markdown(f"**Q{idx+1}. {q['question']}**")
                st.markdown(_difficulty_badge(q["difficulty"]), unsafe_allow_html=True)

                options = {lbl: q[key] for lbl, key in zip(OPTION_LABELS, OPTION_KEYS)}
                choices = [f"{lbl}. {text}" for lbl, text in options.items()]
                default_idx = 0
                if str(qid) in answers:
                    prev = answers[str(qid)]
                    matched = [i for i, c in enumerate(choices) if c.startswith(prev + ".")]
                    if matched:
                        default_idx = matched[0]

                selected = st.radio(
                    label=f"sq_{qid}",
                    options=choices,
                    index=default_idx,
                    key=f"sdiag_{qid}",
                    label_visibility="collapsed",
                )
                answers[str(qid)] = selected[0]
                st.markdown("<br>", unsafe_allow_html=True)

        submitted = st.form_submit_button(
            f"✅ Submit {weak_subject} Diagnostic Test", use_container_width=True
        )

    if submitted:
        _process_subject_diag_results(student_id, weak_subject, questions, answers)
        st.rerun()


def _process_subject_diag_results(student_id, subject, questions, answers):
    ans_list = [answers.get(str(q["question_id"]), "A") for q in questions]
    result   = score_answers(ans_list, questions)
    topic_scores = compute_topic_scores(result["per_question"])

    prev_result = get_session("diagnostic_result") or {}
    subject_score = (prev_result.get("subject_scores") or {}).get(subject, result["score_pct"])

    assessment_id = save_assessment(
        student_id, "subject_diagnostic", subject,
        result["total"], result["correct"], result["score_pct"]
    )

    # Save topic results
    for topic, t_score in topic_scores.items():
        ml_status, _ = predict_from_score(t_score)
        save_result(student_id, assessment_id, subject, topic, t_score, ml_status)

    # Weakest topic
    weakest_topic = min(topic_scores, key=topic_scores.get)
    weakest_score = topic_scores[weakest_topic]
    ml_status, conf = predict_from_score(weakest_score)
    save_learning_gap(student_id, assessment_id, subject, weakest_topic, weakest_score, ml_status, 1)

    set_session("subject_diag_result", {
        "assessment_id": assessment_id,
        "subject":       subject,
        "overall_score": result["score_pct"],
        "topic_scores":  topic_scores,
        "weakest_topic": weakest_topic,
        "weakest_score": weakest_score,
        "ml_status":     ml_status,
        "ml_confidence": conf,
        "per_question":  result["per_question"],
    })
    set_session("weak_topic", weakest_topic)
    set_session("weak_topic_score", weakest_score)


def _show_subject_diag_results(subject):
    result = get_session("subject_diag_result")
    topic_scores = result["topic_scores"]
    weakest = result["weakest_topic"]
    ml_status = result["ml_status"]
    conf = result["ml_confidence"]

    st.markdown(f"## 📊 {subject} — Topic Analysis Results")

    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card("Subject Score", fmt_pct(result["overall_score"]),
                    f"ML Status: {ml_status}", color=STATUS_COLORS.get(ml_status, "#3b82d4"))
    with col2:
        best_topic = max(topic_scores, key=topic_scores.get)
        metric_card("Strongest Topic", best_topic, fmt_pct(topic_scores[best_topic]),
                    color="#22c55e")
    with col3:
        metric_card("Priority Learning Gap", weakest, fmt_pct(result["weakest_score"]),
                    color="#ef4444")

    st.markdown("### Topic-wise Performance")
    sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1])
    for topic, score in sorted_topics:
        status = get_status_label(score)
        render_progress_bar(score, f"{STATUS_ICONS[status]} {topic}")

    # ML Badge
    st.markdown(
        f"""
        <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;
                    padding:14px 18px;margin:12px 0;">
            <strong>🤖 ML Classification:</strong>
            <span style="background:{STATUS_COLORS.get(ml_status,'#6b7280')};color:#fff;
                         padding:2px 10px;border-radius:10px;margin-left:8px;
                         font-size:0.85em;">{ml_status}</span>
            &nbsp;<small style="color:#57606a;">(Confidence: {conf:.0f}%)</small>
            <p style="margin:6px 0 0 0;font-size:0.85em;color:#57606a;">
            ⚠️ Prototype ML results are based on synthetic/demo assessment data.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Gap alert
    st.markdown(
        f"""
        <div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:10px;
                    padding:16px 20px;margin:12px 0;">
            <h4 style="margin:0 0 8px 0;color:#991b1b;">🎯 Priority Learning Gap Identified</h4>
            <p style="margin:0;color:#1f2328;">
            Based on your performance, <strong>{weakest}</strong>
            ({fmt_pct(result['weakest_score'])}) is your priority learning gap.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📚 View Learning Recommendations", type="primary", use_container_width=True):
            set_session("page", "Personalized Learning")
            st.rerun()
    with col_b:
        if st.button("🔁 Retake Subject Diagnostic", use_container_width=True):
            for k in ["subject_diag_questions", "subject_diag_answers", "subject_diag_result"]:
                st.session_state.pop(k, None)
            st.rerun()

    with st.expander("📝 Review Answers"):
        for i, pq in enumerate(result["per_question"]):
            icon = "✅" if pq["is_correct"] else "❌"
            st.markdown(f"**{i+1}. {pq['question']}** &nbsp;({pq['topic']})")
            st.markdown(
                f"Your answer: **{pq['selected']}** &nbsp;|&nbsp; Correct: **{pq['correct_answer']}** {icon}"
            )
            if pq["explanation"]:
                st.caption(f"💡 {pq['explanation']}")
            st.markdown("---")


def _difficulty_badge(difficulty: str) -> str:
    colors = {"easy": "#22c55e", "medium": "#f59e0b", "hard": "#ef4444"}
    color  = colors.get(difficulty.lower(), "#6b7280")
    return (
        f'<span style="background:{color};color:#fff;padding:1px 8px;'
        f'border-radius:8px;font-size:0.75em;font-weight:600;margin-bottom:6px;'
        f'display:inline-block;">{difficulty.upper()}</span>'
    )
