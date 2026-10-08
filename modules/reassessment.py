"""
ShikshaSetu AI - Reassessment Module
Topic-level reassessment after practice; measures before vs after improvement.
"""

import streamlit as st
import plotly.graph_objects as go
from database.database import (
    get_reassessment_questions,
    save_reassessment,
)
from utils.helpers import (
    get_session, set_session, metric_card, STATUS_COLORS, get_status_label, fmt_pct,
)
from utils.preprocessing import score_answers

OPTION_LABELS = ["A", "B", "C", "D"]
OPTION_KEYS   = ["option_a", "option_b", "option_c", "option_d"]


def render_reassessment():
    student_id = get_session("student_id")
    if not student_id:
        st.warning("⚠️ Please log in to take the reassessment.")
        return

    weak_subject = get_session("weak_subject")
    weak_topic   = get_session("weak_topic")
    before_score = get_session("weak_topic_score", 0)

    if not weak_subject or not weak_topic:
        st.info("📋 Complete the diagnostic tests and practice first to unlock the reassessment.")
        if st.button("Start Diagnostic Test", type="primary"):
            set_session("page", "Diagnostic Test")
            st.rerun()
        return

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#7c3aed,#a78bfa);color:#fff;
                    padding:24px;border-radius:12px;margin-bottom:20px;">
            <h2 style="margin:0;">🔄 Reassessment — {weak_topic}</h2>
            <p style="margin:6px 0 0 0;opacity:0.9;">
            Subject: {weak_subject} &nbsp;|&nbsp;
            Measuring your improvement after learning and practice
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Before score reminder
    st.markdown(
        f"""
        <div style="background:#fef9c3;border:1px solid #f59e0b;border-radius:8px;
                    padding:10px 16px;margin-bottom:16px;">
            📊 <strong>Before Intervention Score:</strong>
            <span style="font-size:1.1em;font-weight:700;color:#854d0e;">
            {before_score:.1f}%
            </span> &nbsp;(from your original diagnostic test)
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Show results if already done
    if get_session("reassessment_result"):
        _show_reassessment_results(weak_subject, weak_topic, before_score)
        return

    # Load questions
    if not get_session("reassessment_questions"):
        questions = get_reassessment_questions(weak_subject, weak_topic, limit=5)
        if not questions:
            st.warning(
                f"No reassessment questions found for **{weak_topic}** in **{weak_subject}**.\n\n"
                "Note: Reassessment questions are available for Computer Science → Databases."
            )
            return
        set_session("reassessment_questions", questions)
        set_session("reassessment_answers", {})

    questions = get_session("reassessment_questions")
    answers   = get_session("reassessment_answers", {})

    with st.form("reassessment_form"):
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
                label=f"rq_{qid}",
                options=choices,
                index=default,
                key=f"reassess_{qid}",
                label_visibility="collapsed",
            )
            answers[str(qid)] = selected[0]
            st.markdown("<br>", unsafe_allow_html=True)

        sub_btn = st.form_submit_button(
            "✅ Submit Reassessment", use_container_width=True
        )

    set_session("reassessment_answers", answers)

    if sub_btn:
        ans_list = [answers.get(str(q["question_id"]), "A") for q in questions]
        result   = score_answers(ans_list, questions)
        after_score = result["score_pct"]

        save_reassessment(student_id, weak_topic, weak_subject, before_score, after_score)
        set_session("reassessment_result", {
            "after_score":  after_score,
            "before_score": before_score,
            "improvement":  round(after_score - before_score, 1),
            "per_question": result["per_question"],
        })
        st.rerun()


def _show_reassessment_results(subject, topic, before_score):
    r = get_session("reassessment_result")
    after_score = r["after_score"]
    improvement = r["improvement"]
    before_status = get_status_label(before_score)
    after_status  = get_status_label(after_score)

    st.markdown(f"## 🏆 Reassessment Results — {topic}")

    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card("Before Intervention", fmt_pct(before_score), before_status,
                    color=STATUS_COLORS.get(before_status, "#ef4444"))
    with col2:
        metric_card("After Intervention", fmt_pct(after_score), after_status,
                    color=STATUS_COLORS.get(after_status, "#22c55e"))
    with col3:
        imp_color = "#22c55e" if improvement > 0 else "#ef4444"
        imp_sign  = "+" if improvement >= 0 else ""
        metric_card("Improvement", f"{imp_sign}{improvement:.1f} pp",
                    "percentage points", color=imp_color)

    # Improvement banner
    if improvement > 0:
        st.success(
            f"🎉 Congratulations! Your performance improved by **{improvement:.1f} percentage points** "
            f"in {topic}. Keep it up!"
        )
    elif improvement == 0:
        st.info("📊 Your score remained the same. Review the learning materials and try again.")
    else:
        st.warning(
            f"📚 Score decreased by {abs(improvement):.1f} pp. "
            "Don't worry — review the recommendations and practice more."
        )

    # Before vs After chart
    st.markdown("### 📊 Before vs After Performance")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Before",
        x=["Before Intervention", "After Intervention"],
        y=[before_score, after_score],
        marker_color=[STATUS_COLORS.get(before_status, "#ef4444"),
                      STATUS_COLORS.get(after_status, "#22c55e")],
        text=[f"{before_score:.1f}%", f"{after_score:.1f}%"],
        textposition="outside",
        width=0.4,
    ))
    fig.add_hline(y=80, line_dash="dash", line_color="#22c55e",
                  annotation_text="Strong (80%)", annotation_position="right")
    fig.add_hline(y=60, line_dash="dash", line_color="#f59e0b",
                  annotation_text="Moderate (60%)", annotation_position="right")
    fig.update_layout(
        yaxis_range=[0, 110],
        yaxis_title="Score (%)",
        plot_bgcolor="#f7f8fa",
        paper_bgcolor="#ffffff",
        showlegend=False,
        height=380,
        margin=dict(t=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Gauge chart for after score
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=after_score,
        delta={"reference": before_score, "suffix": " pp"},
        title={"text": f"Post-Intervention Score — {topic}"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": STATUS_COLORS.get(after_status, "#3b82d4")},
            "steps": [
                {"range": [0, 60],  "color": "#fee2e2"},
                {"range": [60, 80], "color": "#fef9c3"},
                {"range": [80, 100], "color": "#dcfce7"},
            ],
            "threshold": {
                "line": {"color": "#1f2328", "width": 3},
                "thickness": 0.8,
                "value": before_score,
            },
        },
    ))
    fig_gauge.update_layout(height=300, paper_bgcolor="#ffffff", margin=dict(t=30, b=10))
    st.plotly_chart(fig_gauge, use_container_width=True)

    # Answer review
    with st.expander("📝 Review Reassessment Answers"):
        for i, pq in enumerate(r["per_question"]):
            icon = "✅" if pq["is_correct"] else "❌"
            st.markdown(f"**{i+1}. {pq['question']}**")
            st.markdown(
                f"Your answer: **{pq['selected']}** | Correct: **{pq['correct_answer']}** {icon}"
            )
            if pq["explanation"]:
                st.caption(f"💡 {pq['explanation']}")
            st.markdown("---")

    st.markdown(
        '<p style="font-size:0.8em;color:#57606a;border-top:1px solid #e5e7eb;'
        'padding-top:8px;">⚠️ Demo disclaimer: Results are based on your actual test responses '
        "in this session. Prototype ML results use synthetic training data.</p>",
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📊 View Progress Dashboard", type="primary", use_container_width=True):
            set_session("page", "Progress")
            st.rerun()
    with col_b:
        if st.button("🔁 Retake Reassessment", use_container_width=True):
            for k in ["reassessment_questions", "reassessment_answers", "reassessment_result"]:
                st.session_state.pop(k, None)
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
