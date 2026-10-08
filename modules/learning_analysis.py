"""
ShikshaSetu AI - Learning Analysis Module
Combines subject scores, topic scores, and ML predictions into a student learning profile.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from utils.helpers import (
    get_session, set_session, section_header, metric_card, render_progress_bar,
    STATUS_COLORS, STATUS_ICONS, get_status_label, fmt_pct, SUBJECTS, TOPICS_MAP,
)
from models.train_model import predict_from_score


def render_learning_profile():
    student_id = get_session("student_id")
    if not student_id:
        st.warning("⚠️ Please log in to view your learning profile.")
        return

    diag = get_session("diagnostic_result")
    subj_diag = get_session("subject_diag_result")

    if not diag:
        st.info("📋 You haven't taken the Multi-Subject Diagnostic Test yet.")
        if st.button("Take Diagnostic Test Now", type="primary"):
            set_session("page", "Diagnostic Test")
            st.rerun()
        return

    subject_scores = diag["subject_scores"]
    overall = diag["overall_score"]
    weakest_subject = diag.get("weakest_subject", "")
    student_name = get_session("student_name", "Student")

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#1e40af,#7c5cd8);color:#fff;
                    padding:24px;border-radius:12px;margin-bottom:20px;">
            <h2 style="margin:0;">🎓 Learning Profile — {student_name}</h2>
            <p style="margin:6px 0 0 0;opacity:0.9;">
            Comprehensive subject and topic analysis with AI classification
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Overall status
    overall_status, conf = predict_from_score(overall)
    color = STATUS_COLORS[overall_status]
    icon  = STATUS_ICONS[overall_status]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Overall Score", fmt_pct(overall), "Multi-Subject Test", color=color)
    with col2:
        metric_card("Learning Status", f"{icon} {overall_status}", f"ML confidence: {conf:.0f}%", color=color)
    best = max(subject_scores, key=subject_scores.get)
    with col3:
        metric_card("Strongest Subject", best, fmt_pct(subject_scores[best]), color="#22c55e")
    with col4:
        metric_card("Priority Subject", weakest_subject,
                    fmt_pct(subject_scores.get(weakest_subject, 0)), color="#ef4444")

    st.markdown("---")

    # Subject performance chart
    _render_subject_chart(subject_scores)

    # Subject-level status table
    st.markdown("### 📋 Subject-Level Analysis")
    rows = []
    for subj in SUBJECTS:
        score = subject_scores.get(subj, 0)
        status, _ = predict_from_score(score)
        rows.append({"Subject": subj, "Score": fmt_pct(score), "Status": status})
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Topic-level analysis (if subject diagnostic done)
    if subj_diag:
        st.markdown("---")
        _render_topic_analysis(subj_diag)

    # Weak subject alert
    st.markdown("---")
    weak_topic = get_session("weak_topic")
    if weak_topic:
        _render_gap_summary(weakest_subject, weak_topic, subj_diag)
    else:
        st.markdown(
            f"""
            <div style="background:#fef9c3;border:1px solid #f59e0b;border-radius:10px;
                        padding:16px 20px;margin:8px 0;">
                <h4 style="margin:0 0 6px 0;color:#854d0e;">📌 Next Step</h4>
                <p style="margin:0;color:#1f2328;">
                Take the <strong>{weakest_subject} Topic Diagnostic Test</strong>
                to discover your exact learning gap.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"🔬 Take {weakest_subject} Diagnostic Test", type="primary"):
            set_session("page", "Subject Diagnostic Test")
            st.rerun()


def _render_subject_chart(subject_scores: dict):
    st.markdown("### 📊 Subject Performance Overview")
    subjects = list(subject_scores.keys())
    scores   = list(subject_scores.values())
    colors   = [STATUS_COLORS[get_status_label(s)] for s in scores]

    fig = go.Figure(
        go.Bar(
            x=subjects,
            y=scores,
            marker_color=colors,
            text=[f"{s:.1f}%" for s in scores],
            textposition="outside",
            hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
        )
    )
    fig.add_hline(y=80, line_dash="dash", line_color="#22c55e",
                  annotation_text="Strong (80%)", annotation_position="right")
    fig.add_hline(y=60, line_dash="dash", line_color="#f59e0b",
                  annotation_text="Moderate (60%)", annotation_position="right")
    fig.update_layout(
        yaxis_range=[0, 110],
        yaxis_title="Score (%)",
        xaxis_title="Subject",
        plot_bgcolor="#f7f8fa",
        paper_bgcolor="#ffffff",
        margin=dict(t=20, b=20),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_topic_analysis(subj_diag: dict):
    subject     = subj_diag["subject"]
    topic_scores = subj_diag["topic_scores"]
    weakest_t   = subj_diag["weakest_topic"]

    st.markdown(f"### 🔬 {subject} — Topic Analysis")
    col1, col2 = st.columns([3, 2])

    with col1:
        topics  = list(topic_scores.keys())
        scores  = list(topic_scores.values())
        colors  = [STATUS_COLORS[get_status_label(s)] for s in scores]
        fig = go.Figure(go.Bar(
            x=scores, y=topics, orientation="h",
            marker_color=colors,
            text=[f"{s:.1f}%" for s in scores],
            textposition="outside",
            hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
        ))
        fig.add_vline(x=80, line_dash="dash", line_color="#22c55e")
        fig.add_vline(x=60, line_dash="dash", line_color="#f59e0b")
        fig.update_layout(
            xaxis_range=[0, 115],
            xaxis_title="Score (%)",
            plot_bgcolor="#f7f8fa",
            paper_bgcolor="#ffffff",
            margin=dict(t=10, b=10),
            height=320,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Topic Rankings**")
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        for rank, (topic, score) in enumerate(sorted_topics, 1):
            status = get_status_label(score)
            icon   = STATUS_ICONS[status]
            st.markdown(
                f"**{rank}.** {topic}  \n"
                f"{icon} {score:.1f}% — *{status}*"
            )

    # Radar chart
    if len(topic_scores) >= 3:
        topics = list(topic_scores.keys())
        vals   = list(topic_scores.values())
        fig_r  = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=topics + [topics[0]],
            fill="toself",
            fillcolor="rgba(124,92,216,0.2)",
            line=dict(color="#7c5cd8"),
        ))
        fig_r.update_layout(
            polar=dict(radialaxis=dict(range=[0, 100])),
            showlegend=False,
            height=320,
            margin=dict(t=20, b=20),
            paper_bgcolor="#ffffff",
        )
        st.plotly_chart(fig_r, use_container_width=True)


def _render_gap_summary(weak_subject, weak_topic, subj_diag):
    topic_score = (subj_diag.get("topic_scores") or {}).get(weak_topic, 0) if subj_diag else 0
    ml_status, conf = predict_from_score(topic_score)

    st.markdown("### 🎯 Learning Gap Summary")
    st.markdown(
        f"""
        <div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:12px;padding:20px;">
            <h4 style="margin:0 0 12px 0;color:#991b1b;">Priority Learning Gap Detected</h4>
            <table style="width:100%;border-collapse:collapse;font-size:0.9em;">
                <tr><td style="padding:4px 8px;color:#57606a;width:40%;">Priority Subject</td>
                    <td style="padding:4px 8px;font-weight:600;">{weak_subject}</td></tr>
                <tr><td style="padding:4px 8px;color:#57606a;">Priority Topic</td>
                    <td style="padding:4px 8px;font-weight:600;">{weak_topic}</td></tr>
                <tr><td style="padding:4px 8px;color:#57606a;">Topic Score</td>
                    <td style="padding:4px 8px;font-weight:600;">{topic_score:.1f}%</td></tr>
                <tr><td style="padding:4px 8px;color:#57606a;">ML Learning Status</td>
                    <td style="padding:4px 8px;">
                        <span style="background:{STATUS_COLORS.get(ml_status,'#6b7280')};color:#fff;
                                     padding:2px 10px;border-radius:10px;font-size:0.85em;">
                            {ml_status}
                        </span>
                    </td></tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📚 Get Learning Recommendations", type="primary", use_container_width=True):
            set_session("page", "Personalized Learning")
            st.rerun()
    with col_b:
        if st.button("✏️ Practice Questions", use_container_width=True):
            set_session("page", "Practice")
            st.rerun()
