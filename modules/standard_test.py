"""
ShikshaSetu AI - Standard-Wise Test Module
Provides class/grade-specific diagnostic tests for Classes 6-10.
Each standard has its own question bank across all 5 subjects.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from database.database import (
    get_standard_questions,
    get_available_standards,
    save_standard_test_result,
    get_standard_test_history,
)
from utils.preprocessing import score_answers, compute_subject_scores, compute_topic_scores
from utils.helpers import (
    get_session, set_session, metric_card, render_progress_bar,
    STATUS_COLORS, STATUS_ICONS, get_status_label, fmt_pct,
    SUBJECTS, STANDARDS, STANDARD_LABELS, STANDARD_COLORS,
)
from models.train_model import predict_from_score

OPTION_LABELS = ["A", "B", "C", "D"]
OPTION_KEYS   = ["option_a", "option_b", "option_c", "option_d"]

# ─── How many questions to show per subject in the combined test ───────────────
QUESTIONS_PER_SUBJECT = 5   # 5 subjects × 5 = 25 question combined test


def render_standard_test_home():
    """
    Landing page: student selects mode (Full Standard Test / Single Subject Test),
    then selects their class standard.
    """
    student_id = get_session("student_id")
    if not student_id:
        st.warning("⚠️ Please log in to access standard-wise tests.")
        return

    student_name = get_session("student_name", "Student")
    student_std  = get_session("student_standard", "8")

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#0f172a,#1e3a8a,#3b82f6);
                    color:#fff;padding:28px 32px;border-radius:14px;margin-bottom:24px;">
            <h2 style="margin:0;font-size:1.5em;">📚 Standard-Wise Tests</h2>
            <p style="margin:8px 0 0 0;opacity:0.9;">
            Class-specific assessments aligned to the curriculum for Classes 6 – 10
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Standard-selector card grid ──────────────────────────────────────────
    st.markdown("### Select Your Class Standard")
    st.markdown(
        "<p style='color:#57606a;font-size:0.9em;'>Your registered standard is highlighted. "
        "You can also take tests for other standards.</p>",
        unsafe_allow_html=True,
    )

    cols = st.columns(5)
    std_selected = None
    for i, std in enumerate(STANDARDS):
        label  = STANDARD_LABELS[std]
        color  = STANDARD_COLORS[std]
        border = "3px solid " + color if std == student_std else "1px solid #e5e7eb"
        badge  = " ← Your Class" if std == student_std else ""
        with cols[i]:
            st.markdown(
                f"""
                <div style="background:#f7f8fa;border:{border};border-radius:12px;
                            padding:20px 12px;text-align:center;margin-bottom:8px;">
                    <div style="font-size:1.8em;font-weight:800;color:{color};">{std}</div>
                    <div style="font-size:0.8em;color:#1f2328;font-weight:600;">{label}</div>
                    <div style="font-size:0.72em;color:#57606a;">{badge}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Select {label}", key=f"std_sel_{std}", use_container_width=True):
                set_session("selected_standard", std)
                set_session("std_test_mode", None)
                set_session("std_test_questions", None)
                set_session("std_test_answers",   {})
                set_session("std_test_result",    None)
                set_session("std_subject_filter", None)
                st.rerun()

    # ── If standard is selected, show mode chooser ───────────────────────────
    selected_std = get_session("selected_standard")
    if not selected_std:
        # Pre-select student's own standard
        set_session("selected_standard", student_std)
        st.rerun()
        return

    color = STANDARD_COLORS[selected_std]
    label = STANDARD_LABELS[selected_std]

    st.markdown("---")
    st.markdown(
        f"""
        <div style="background:#f0f9ff;border:2px solid {color};border-radius:10px;
                    padding:16px 20px;margin-bottom:16px;">
            <h4 style="margin:0 0 6px 0;color:{color};">Selected: {label}</h4>
            <p style="margin:0;color:#57606a;font-size:0.9em;">
            Choose a test mode below:
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f"""
            <div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;
                        padding:16px;text-align:center;margin-bottom:8px;">
                <div style="font-size:1.5em;">📋</div>
                <div style="font-weight:700;color:#1f2328;">Full Standard Test</div>
                <div style="font-size:0.85em;color:#57606a;margin:4px 0;">
                    All 5 subjects · {QUESTIONS_PER_SUBJECT} questions each<br>
                    Total: {QUESTIONS_PER_SUBJECT * 5} questions (25)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            f"Start Full {label} Test", type="primary",
            key="full_std_test", use_container_width=True
        ):
            _start_standard_test(selected_std, subject=None)
            st.rerun()

    with col_b:
        st.markdown(
            f"""
            <div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;
                        padding:16px;text-align:center;margin-bottom:8px;">
                <div style="font-size:1.5em;">🔬</div>
                <div style="font-weight:700;color:#1f2328;">Single Subject Test</div>
                <div style="font-size:0.85em;color:#57606a;margin:4px 0;">
                    Pick one subject<br>
                    All questions for that subject
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        subject_choice = st.selectbox(
            "Choose Subject:", SUBJECTS, key="std_subj_choice"
        )
        if st.button(
            f"Start {subject_choice} Test",
            key="single_subj_test", use_container_width=True
        ):
            _start_standard_test(selected_std, subject=subject_choice)
            st.rerun()

    # ── Past results ────────────────────────────────────────────────────────
    _show_past_results(student_id)


def _start_standard_test(standard, subject=None):
    """Load questions into session and mark test as started."""
    if subject:
        questions = get_standard_questions(standard, subject=subject)
    else:
        questions = get_standard_questions(standard, limit_per_subject=QUESTIONS_PER_SUBJECT)

    set_session("selected_standard",  standard)
    set_session("std_test_mode",      "single_subject" if subject else "full")
    set_session("std_subject_filter", subject)
    set_session("std_test_questions", questions)
    set_session("std_test_answers",   {})
    set_session("std_test_result",    None)


# ─── Active test renderer ──────────────────────────────────────────────────────

def render_active_standard_test():
    """Render the in-progress standard-wise test form."""
    student_id = get_session("student_id")
    if not student_id:
        st.warning("Please log in.")
        return

    questions = get_session("std_test_questions", [])
    result    = get_session("std_test_result")
    standard  = get_session("selected_standard", "8")
    subject   = get_session("std_subject_filter")
    mode      = get_session("std_test_mode", "full")

    if not questions:
        render_standard_test_home()
        return

    if result:
        _show_standard_test_results(student_id, standard, subject, result)
        return

    label = STANDARD_LABELS.get(standard, f"Class {standard}")
    color = STANDARD_COLORS.get(standard, "#3b82d4")
    title = f"{subject} Test" if subject else "Full Standard Test"

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{color},{color}aa);color:#fff;
                    padding:24px 28px;border-radius:12px;margin-bottom:20px;">
            <h2 style="margin:0;">📚 {label} — {title}</h2>
            <p style="margin:6px 0 0 0;opacity:0.9;">
            {len(questions)} questions
            {'· All Subjects' if not subject else f'· {subject}'}
            &nbsp;|&nbsp; Answer all questions and submit
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    answers = get_session("std_test_answers", {})

    # Group by subject for display
    by_subject = {}
    for q in questions:
        by_subject.setdefault(q["subject"], []).append(q)

    subject_order = [s for s in SUBJECTS if s in by_subject]

    with st.form("std_test_form"):
        for subj in subject_order:
            subj_qs = by_subject[subj]
            st.markdown(f"### 📖 {subj}")
            st.markdown("---")
            for idx, q in enumerate(subj_qs):
                qid = q["question_id"]
                st.markdown(f"**Q{idx + 1}. {q['question']}**")
                st.markdown(_diff_badge(q["difficulty"]), unsafe_allow_html=True)

                options = {lbl: q[key] for lbl, key in zip(OPTION_LABELS, OPTION_KEYS)}
                choices = [f"{lbl}. {text}" for lbl, text in options.items()]

                prev_ans = answers.get(str(qid), "")
                default  = 0
                if prev_ans:
                    matched = [i for i, c in enumerate(choices) if c.startswith(prev_ans + ".")]
                    if matched:
                        default = matched[0]

                sel = st.radio(
                    label=f"stq_{qid}",
                    options=choices,
                    index=default,
                    key=f"stdtest_{qid}",
                    label_visibility="collapsed",
                )
                answers[str(qid)] = sel[0]
                st.markdown("<br>", unsafe_allow_html=True)

        submitted = st.form_submit_button(
            f"✅ Submit {label} {title}", use_container_width=True
        )

    set_session("std_test_answers", answers)

    if submitted:
        _process_standard_test(student_id, standard, subject, questions, answers)
        st.rerun()

    # Abandon button (outside form)
    if st.button("⬅ Back to Standard Selection", key="abandon_std"):
        for k in ["std_test_questions", "std_test_answers", "std_test_result",
                  "std_test_mode", "std_subject_filter"]:
            st.session_state.pop(k, None)
        st.rerun()


def _process_standard_test(student_id, standard, subject, questions, answers):
    """Score the test, persist results, store result in session."""
    ans_list = [answers.get(str(q["question_id"]), "A") for q in questions]
    result   = score_answers(ans_list, questions)

    subject_scores = compute_subject_scores(result["per_question"])
    topic_scores   = compute_topic_scores(result["per_question"])

    # Persist
    save_standard_test_result(
        student_id, standard,
        subject or "All Subjects",
        result["total"], result["correct"], result["score_pct"],
        topic_scores,
    )

    set_session("std_test_result", {
        "overall_score":  result["score_pct"],
        "correct":        result["correct"],
        "total":          result["total"],
        "subject_scores": subject_scores,
        "topic_scores":   topic_scores,
        "per_question":   result["per_question"],
        "standard":       standard,
        "subject":        subject,
    })


# ─── Results renderer ──────────────────────────────────────────────────────────

def _show_standard_test_results(student_id, standard, subject, result):
    label        = STANDARD_LABELS.get(standard, f"Class {standard}")
    color        = STANDARD_COLORS.get(standard, "#3b82d4")
    overall      = result["overall_score"]
    subj_scores  = result["subject_scores"]
    topic_scores = result["topic_scores"]
    overall_status, conf = predict_from_score(overall)

    title = f"{subject} Test" if subject else "Full Standard Test"
    st.markdown(f"## 🏆 {label} — {title} Results")

    # Top metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card("Overall Score", fmt_pct(overall),
                    f"Status: {overall_status}", color=STATUS_COLORS[overall_status])
    with col2:
        if subj_scores:
            best = max(subj_scores, key=subj_scores.get)
            metric_card("Best Subject", best, fmt_pct(subj_scores[best]), color="#22c55e")
        else:
            metric_card("Correct", f"{result['correct']}/{result['total']}", "", color="#22c55e")
    with col3:
        metric_card("ML Classification", overall_status,
                    f"Confidence: {conf:.0f}%", color=STATUS_COLORS[overall_status])

    st.markdown("---")

    # Subject performance chart (multi-subject test)
    if len(subj_scores) > 1:
        st.markdown("### 📊 Subject-wise Performance")
        subjs  = list(subj_scores.keys())
        scores = list(subj_scores.values())
        colors = [STATUS_COLORS[get_status_label(s)] for s in scores]
        fig = go.Figure(go.Bar(
            x=subjs, y=scores, marker_color=colors,
            text=[f"{s:.1f}%" for s in scores], textposition="outside",
            hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
        ))
        fig.add_hline(y=80, line_dash="dash", line_color="#22c55e",
                      annotation_text="Strong (80%)")
        fig.add_hline(y=60, line_dash="dash", line_color="#f59e0b",
                      annotation_text="Moderate (60%)")
        fig.update_layout(
            yaxis_range=[0, 115], yaxis_title="Score (%)",
            plot_bgcolor="#f7f8fa", paper_bgcolor="#fff",
            height=380, margin=dict(t=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Subject status table
        st.markdown("### 📋 Subject Analysis")
        rows = []
        for subj, sc in subj_scores.items():
            status_lbl, _ = predict_from_score(sc)
            rows.append({
                "Subject": subj,
                "Score":   fmt_pct(sc),
                "Status":  status_lbl,
                "Icon":    STATUS_ICONS[status_lbl],
            })
        df = pd.DataFrame(rows)
        st.dataframe(df[["Subject", "Score", "Status"]], use_container_width=True, hide_index=True)

    # Topic performance (single-subject test or topic breakdown)
    if topic_scores and (subject or len(subj_scores) == 1):
        st.markdown(f"### 🔬 Topic-wise Breakdown — {subject or list(subj_scores.keys())[0]}")
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1])
        for topic, sc in sorted_topics:
            render_progress_bar(sc, f"{STATUS_ICONS[get_status_label(sc)]} {topic}")

        # Radar chart
        if len(topic_scores) >= 3:
            topics = list(topic_scores.keys())
            vals   = list(topic_scores.values())
            fig_r  = go.Figure(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=topics + [topics[0]],
                fill="toself",
                fillcolor=f"rgba(59,130,212,0.2)",
                line=dict(color=color),
            ))
            fig_r.update_layout(
                polar=dict(radialaxis=dict(range=[0, 100])),
                showlegend=False, height=320,
                margin=dict(t=20, b=20),
                paper_bgcolor="#fff",
            )
            st.plotly_chart(fig_r, use_container_width=True)

    # ML badge
    st.markdown(
        f"""
        <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;
                    padding:10px 16px;margin:12px 0;">
            <strong>🤖 ML Classification:</strong>
            <span style="background:{STATUS_COLORS[overall_status]};color:#fff;
                         padding:2px 10px;border-radius:10px;margin-left:8px;
                         font-size:0.85em;">{overall_status}</span>
            &nbsp;<small style="color:#57606a;">(Confidence: {conf:.0f}%)</small><br>
            <small style="color:#57606a;">
            ⚠️ Prototype ML results are based on synthetic training data.
            </small>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Answer review
    with st.expander("📝 Review All Answers"):
        for i, pq in enumerate(result["per_question"]):
            icon  = "✅" if pq["is_correct"] else "❌"
            bg    = "#f0fdf4" if pq["is_correct"] else "#fef2f2"
            bord  = "#86efac" if pq["is_correct"] else "#fca5a5"
            st.markdown(
                f"""
                <div style="background:{bg};border:1px solid {bord};border-radius:8px;
                            padding:10px 14px;margin-bottom:6px;">
                    <strong>{icon} Q{i+1}. {pq['question']}</strong>
                    <span style="color:#57606a;font-size:0.85em;">
                     &nbsp;({pq['subject']} — {pq['topic']})</span><br>
                    <span style="color:#57606a;">
                    Your answer: <strong>{pq['selected']}</strong>
                    &nbsp;|&nbsp; Correct: <strong>{pq['correct_answer']}</strong>
                    </span>
                    {'<br><small style="color:#059669;">💡 '+pq["explanation"]+'</small>' if pq.get("explanation") else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("🔁 Try Another Standard Test", type="primary", use_container_width=True):
            for k in ["std_test_questions", "std_test_answers", "std_test_result",
                      "std_test_mode", "std_subject_filter", "selected_standard"]:
                st.session_state.pop(k, None)
            st.rerun()
    with col_b:
        if st.button("📋 Take Diagnostic Test", use_container_width=True):
            set_session("page", "Diagnostic Test")
            st.rerun()
    with col_c:
        if st.button("📊 View Dashboard", use_container_width=True):
            set_session("page", "Dashboard")
            st.rerun()


# ─── Past results panel ────────────────────────────────────────────────────────

def _show_past_results(student_id):
    history = get_standard_test_history(student_id)
    if not history:
        return

    st.markdown("---")
    st.markdown("### 📈 Your Standard Test History")
    rows = []
    for h in history:
        std_num = h["assessment_type"].replace("standard_", "")
        rows.append({
            "Standard":  STANDARD_LABELS.get(std_num, f"Class {std_num}"),
            "Subject":   h.get("subject", ""),
            "Score":     fmt_pct(h["score_pct"]),
            "Status":    get_status_label(h["score_pct"]),
            "Date":      (h.get("completed_at") or "")[:10],
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Progress chart
    if len(rows) > 1:
        fig = go.Figure()
        for std in STANDARDS:
            std_label = STANDARD_LABELS[std]
            std_rows  = [r for r in rows if r["Standard"] == std_label]
            if std_rows:
                fig.add_trace(go.Scatter(
                    x=[r["Date"] for r in std_rows],
                    y=[float(r["Score"].replace("%", "")) for r in std_rows],
                    mode="lines+markers",
                    name=std_label,
                    line=dict(color=STANDARD_COLORS[std]),
                ))
        fig.update_layout(
            yaxis_range=[0, 110],
            yaxis_title="Score (%)",
            xaxis_title="Date",
            title="Standard Test Score History",
            plot_bgcolor="#f7f8fa",
            paper_bgcolor="#fff",
            height=320,
            margin=dict(t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)


# ─── Entry point called from app.py ───────────────────────────────────────────

def render_standard_test_page():
    """
    Main dispatcher: if a test is in progress, show the test form;
    otherwise show the home/selector screen.
    """
    questions = get_session("std_test_questions", [])
    result    = get_session("std_test_result")
    standard  = get_session("selected_standard")

    # Show results if done
    if result and standard:
        student_id = get_session("student_id")
        subject    = get_session("std_subject_filter")
        if not student_id:
            render_standard_test_home()
            return
        _show_standard_test_results(student_id, standard, subject, result)
        return

    # Show active test if questions loaded
    if questions:
        render_active_standard_test()
        return

    # Default: home selector
    render_standard_test_home()


# ─── Helper ────────────────────────────────────────────────────────────────────

def _diff_badge(difficulty: str) -> str:
    colors = {"easy": "#22c55e", "medium": "#f59e0b", "hard": "#ef4444"}
    color  = colors.get(difficulty.lower(), "#6b7280")
    return (
        f'<span style="background:{color};color:#fff;padding:1px 8px;'
        f'border-radius:8px;font-size:0.75em;font-weight:600;'
        f'display:inline-block;margin-bottom:6px;">{difficulty.upper()}</span>'
    )
