"""
ShikshaSetu AI - Student Dashboard Module
Comprehensive student-level progress, charts, and learning profile summary.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from database.database import (
    get_student_results,
    get_latest_multi_subject_scores,
    get_reassessment_history,
)
from utils.helpers import (
    get_session, set_session, metric_card, render_progress_bar,
    STATUS_COLORS, STATUS_ICONS, get_status_label, fmt_pct, SUBJECTS,
)
from models.train_model import predict_from_score


def render_student_dashboard():
    student_id = get_session("student_id")
    if not student_id:
        st.warning("⚠️ Please log in to view your dashboard.")
        return

    student_name = get_session("student_name", "Student")
    diag         = get_session("diagnostic_result")
    subj_diag    = get_session("subject_diag_result")
    weak_subject = get_session("weak_subject")
    weak_topic   = get_session("weak_topic")
    topic_score  = get_session("weak_topic_score", 0)
    practice_score = get_session("practice_score")
    reassessment_r = get_session("reassessment_result")

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#1e40af,#7c5cd8);color:#fff;
                    padding:28px;border-radius:14px;margin-bottom:24px;">
            <h2 style="margin:0;">🎓 Student Dashboard</h2>
            <p style="margin:6px 0 0 0;opacity:0.9;font-size:1.05em;">
            Welcome, <strong>{student_name}</strong>!
            Track your learning journey and measure your improvement.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not diag:
        st.info("You haven't taken the diagnostic test yet.")
        if st.button("🚀 Start Diagnostic Test", type="primary"):
            set_session("page", "Diagnostic Test")
            st.rerun()
        return

    # ── Key metrics ────────────────────────────────────────────────────────
    subject_scores = diag["subject_scores"]
    overall        = diag["overall_score"]
    overall_status, conf = predict_from_score(overall)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Overall Score", fmt_pct(overall),
                    f"{overall_status} ({conf:.0f}% conf.)",
                    color=STATUS_COLORS[overall_status])
    best = max(subject_scores, key=subject_scores.get)
    with col2:
        metric_card("Strongest Subject", best, fmt_pct(subject_scores[best]), color="#22c55e")
    with col3:
        ws = weak_subject or min(subject_scores, key=subject_scores.get)
        metric_card("Priority Subject", ws, fmt_pct(subject_scores.get(ws, 0)), color="#f59e0b")
    with col4:
        if weak_topic:
            metric_card("Priority Learning Gap", weak_topic,
                        f"{topic_score:.1f}%", color="#ef4444")
        else:
            metric_card("Priority Subject", ws, "Take subject test →", color="#ef4444")

    st.markdown("---")

    # ── Subject chart ──────────────────────────────────────────────────────
    st.markdown("### 📊 Subject Performance")
    subjects = list(subject_scores.keys())
    scores   = list(subject_scores.values())
    colors   = [STATUS_COLORS[get_status_label(s)] for s in scores]

    fig = go.Figure(go.Bar(
        x=subjects, y=scores, marker_color=colors,
        text=[f"{s:.1f}%" for s in scores], textposition="outside",
        hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=80, line_dash="dash", line_color="#22c55e", annotation_text="Strong (80%)")
    fig.add_hline(y=60, line_dash="dash", line_color="#f59e0b", annotation_text="Moderate (60%)")
    fig.update_layout(
        yaxis_range=[0, 110], yaxis_title="Score (%)",
        plot_bgcolor="#f7f8fa", paper_bgcolor="#fff",
        height=380, margin=dict(t=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Topic chart (if subject diag done) ────────────────────────────────
    if subj_diag:
        st.markdown(f"### 🔬 {subj_diag['subject']} — Topic Performance")
        t_scores = subj_diag["topic_scores"]
        t_names  = list(t_scores.keys())
        t_vals   = list(t_scores.values())
        t_colors = [STATUS_COLORS[get_status_label(v)] for v in t_vals]

        fig2 = go.Figure(go.Bar(
            x=t_vals, y=t_names, orientation="h",
            marker_color=t_colors,
            text=[f"{v:.1f}%" for v in t_vals], textposition="outside",
        ))
        fig2.add_vline(x=80, line_dash="dash", line_color="#22c55e")
        fig2.add_vline(x=60, line_dash="dash", line_color="#f59e0b")
        fig2.update_layout(
            xaxis_range=[0, 115], xaxis_title="Score (%)",
            plot_bgcolor="#f7f8fa", paper_bgcolor="#fff",
            height=320, margin=dict(t=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Reassessment improvement chart ────────────────────────────────────
    reassessment_history = get_reassessment_history(student_id)
    if reassessment_history:
        st.markdown("### 📈 Reassessment Progress")
        rh = reassessment_history[0]  # latest
        before = rh["before_score"]
        after  = rh["after_score"]
        imp    = rh["improvement"]
        topic  = rh["topic"]

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=["Before Intervention", "After Intervention"],
            y=[before, after],
            marker_color=[STATUS_COLORS[get_status_label(before)],
                          STATUS_COLORS[get_status_label(after)]],
            text=[f"{before:.1f}%", f"{after:.1f}%"],
            textposition="outside",
            width=0.35,
        ))
        fig3.add_hline(y=80, line_dash="dash", line_color="#22c55e")
        fig3.add_hline(y=60, line_dash="dash", line_color="#f59e0b")
        fig3.update_layout(
            title=f"Improvement in {topic}",
            yaxis_range=[0, 110], yaxis_title="Score (%)",
            plot_bgcolor="#f7f8fa", paper_bgcolor="#fff",
            showlegend=False, height=380,
        )
        st.plotly_chart(fig3, use_container_width=True)

        imp_sign = "+" if imp >= 0 else ""
        imp_col  = "#22c55e" if imp > 0 else "#ef4444"
        st.markdown(
            f'<p style="text-align:center;font-size:1.1em;">Performance changed by '
            f'<strong style="color:{imp_col};">{imp_sign}{imp:.1f} percentage points</strong>'
            f' in {topic}</p>',
            unsafe_allow_html=True,
        )

    # ── Progress checklist ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ✅ Learning Journey Progress")

    steps = [
        ("Multi-Subject Diagnostic Test", bool(diag)),
        ("Subject Diagnostic Test", bool(subj_diag)),
        ("Weak Topic Identified", bool(weak_topic)),
        ("Personalized Learning Plan Viewed", bool(get_session("recommendations_viewed"))),
        ("Practice Completed", practice_score is not None),
        ("Reassessment Completed", bool(reassessment_r or reassessment_history)),
    ]
    for label, done in steps:
        icon = "✅" if done else "⭕"
        color = "#22c55e" if done else "#d1d5db"
        st.markdown(
            f'<div style="background:#f7f8fa;border:1px solid {color};border-radius:8px;'
            f'padding:8px 16px;margin-bottom:6px;">{icon} {label}</div>',
            unsafe_allow_html=True,
        )

    # ── Quick navigation ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🧭 Quick Navigation")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("📋 Diagnostic Test", use_container_width=True):
            set_session("page", "Diagnostic Test")
            st.rerun()
    with c2:
        if st.button("📚 Recommendations", use_container_width=True):
            set_session("page", "Personalized Learning")
            st.rerun()
    with c3:
        if st.button("✏️ Practice", use_container_width=True):
            set_session("page", "Practice")
            st.rerun()
    with c4:
        if st.button("🔄 Reassessment", use_container_width=True):
            set_session("page", "Reassessment")
            st.rerun()
