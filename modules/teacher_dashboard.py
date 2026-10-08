"""
ShikshaSetu AI - Teacher Dashboard Module
Class-level analytics: subject performance, learning gaps, students needing support.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from database.database import (
    get_all_students,
    get_class_subject_scores,
    get_common_learning_gaps,
    get_students_needing_support,
    get_student_results,
    get_reassessment_history,
    get_latest_multi_subject_scores,
    get_standard_wise_class_stats,
    get_connection,
)
from utils.helpers import (
    get_session, set_session, metric_card, STATUS_COLORS, STATUS_ICONS,
    get_status_label, fmt_pct, SUBJECTS, STANDARDS, STANDARD_LABELS, STANDARD_COLORS,
)


def render_teacher_dashboard():
    teacher_id = get_session("teacher_id")
    if not teacher_id:
        st.warning("⚠️ Please log in as a teacher to view the class dashboard.")
        return

    teacher_name = get_session("teacher_name", "Teacher")

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#0f172a,#1e3a5f);color:#fff;
                    padding:28px;border-radius:14px;margin-bottom:24px;">
            <h2 style="margin:0;">📊 Teacher Dashboard</h2>
            <p style="margin:6px 0 0 0;opacity:0.9;font-size:1.05em;">
            Welcome, <strong>{teacher_name}</strong>!
            Monitor class performance and identify students who need support.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Class Overview",
        "📚 Subject Analysis",
        "🎯 Learning Gaps",
        "🏫 Standard-wise Analytics",
        "👤 Student Profile",
    ])

    with tab1:
        _class_overview()
    with tab2:
        _subject_analysis()
    with tab3:
        _learning_gaps()
    with tab4:
        _standard_wise_analytics()
    with tab5:
        _student_profile_view()


# ── Tab 1: Class Overview ──────────────────────────────────────────────────

def _class_overview():
    all_students     = get_all_students()
    needing_support  = get_students_needing_support()
    subject_scores   = get_class_subject_scores()
    reassessments    = _get_all_reassessments()

    total_students   = len(all_students)
    support_count    = len(needing_support)
    avg_score = (
        round(sum(r["avg_score"] for r in subject_scores) / len(subject_scores), 1)
        if subject_scores else 0
    )
    avg_improvement = (
        round(sum(r["improvement"] for r in reassessments) / len(reassessments), 1)
        if reassessments else 0
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Total Students", str(total_students), "registered", color="#3b82d4")
    with col2:
        metric_card("Need Support", str(support_count), "students", color="#ef4444")
    with col3:
        metric_card("Avg Class Score", fmt_pct(avg_score), "all subjects", color="#f59e0b")
    with col4:
        imp_sign = "+" if avg_improvement >= 0 else ""
        metric_card("Avg Improvement", f"{imp_sign}{avg_improvement:.1f} pp",
                    "post-intervention", color="#22c55e")

    # Students needing support
    if needing_support:
        st.markdown("### 🚨 Students Requiring Attention")
        rows = [
            {
                "Name": s["full_name"],
                "Class": s.get("class_name", ""),
                "Section": s.get("section", ""),
                "Subjects Needing Support": s["gap_count"],
            }
            for s in needing_support
        ]
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No student-level assessment data yet. Demo students have sample data.")

    # Progress notes
    st.markdown(
        """
        <p style="font-size:0.82em;color:#57606a;margin-top:12px;">
        ⚠️ Demo data: Sample assessment records were auto-generated for demonstration purposes.
        Real data will populate here as students complete their assessments.
        </p>
        """,
        unsafe_allow_html=True,
    )


# ── Tab 2: Subject Analysis ─────────────────────────────────────────────────

def _subject_analysis():
    subject_scores = get_class_subject_scores()
    if not subject_scores:
        st.info("No subject-level data available yet.")
        return

    st.markdown("### 📊 Class Average by Subject")
    df = pd.DataFrame(subject_scores)
    df = df.sort_values("avg_score", ascending=False)

    colors = [STATUS_COLORS[get_status_label(s)] for s in df["avg_score"]]
    fig = go.Figure(go.Bar(
        x=df["subject"],
        y=df["avg_score"],
        marker_color=colors,
        text=[f"{s:.1f}%" for s in df["avg_score"]],
        textposition="outside",
        hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=80, line_dash="dash", line_color="#22c55e",
                  annotation_text="Strong (80%)")
    fig.add_hline(y=60, line_dash="dash", line_color="#f59e0b",
                  annotation_text="Moderate (60%)")
    fig.update_layout(
        yaxis_range=[0, 115], yaxis_title="Average Score (%)",
        plot_bgcolor="#f7f8fa", paper_bgcolor="#fff",
        height=400, margin=dict(t=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Table
    table_rows = [
        {
            "Subject": r["subject"],
            "Avg Score": fmt_pct(r["avg_score"]),
            "Students": r["student_count"],
            "Status": get_status_label(r["avg_score"]),
        }
        for r in subject_scores
    ]
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)


# ── Tab 3: Learning Gaps ────────────────────────────────────────────────────

def _learning_gaps():
    gaps = get_common_learning_gaps()

    if not gaps:
        st.info("No learning gap data yet.")
        return

    st.markdown("### 🎯 Most Common Learning Gaps Across the Class")
    df = pd.DataFrame(gaps)
    df = df.sort_values("frequency", ascending=False).head(10)

    fig = go.Figure(go.Bar(
        x=df["frequency"],
        y=[f"{r['topic']} ({r['subject']})" for _, r in df.iterrows()],
        orientation="h",
        marker_color="#ef4444",
        text=df["frequency"].astype(str) + " students",
        textposition="outside",
    ))
    fig.update_layout(
        xaxis_title="Number of Students",
        plot_bgcolor="#f7f8fa",
        paper_bgcolor="#fff",
        height=400,
        margin=dict(t=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Top Learning Gaps (Ranked)")
    for i, row in enumerate(gaps[:10], 1):
        st.markdown(
            f"**{i}.** {row['topic']} *(in {row['subject']})* — "
            f"{row['frequency']} student(s)"
        )

    # Improvement overview
    reassessments = _get_all_reassessments()
    if reassessments:
        st.markdown("### 📈 Pre vs Post Intervention — Class Overview")
        rdf = pd.DataFrame(reassessments)
        avg_before = rdf["before_score"].mean()
        avg_after  = rdf["after_score"].mean()
        avg_imp    = rdf["improvement"].mean()

        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("Avg Before Score", fmt_pct(avg_before), "", color="#ef4444")
        with c2:
            metric_card("Avg After Score", fmt_pct(avg_after), "", color="#22c55e")
        with c3:
            imp_sign = "+" if avg_imp >= 0 else ""
            metric_card("Avg Improvement", f"{imp_sign}{avg_imp:.1f} pp", "", color="#3b82d4")


# ── Tab 4: Individual Student Profile ──────────────────────────────────────

def _student_profile_view():
    all_students = get_all_students()
    if not all_students:
        st.info("No students registered yet.")
        return

    names = {s["full_name"]: s["student_id"] for s in all_students}
    selected_name = st.selectbox(
        "Select a student to view their profile:", list(names.keys())
    )
    selected_id = names[selected_name]

    results = get_student_results(selected_id)
    if not results:
        st.info(f"No assessment data for {selected_name} yet.")
        return

    st.markdown(f"### 📋 Learning Profile — {selected_name}")

    # Subject scores
    subject_rows = [r for r in results if not r["topic"]]
    if subject_rows:
        df_s = pd.DataFrame([
            {
                "Subject":  r["subject"],
                "Score":    fmt_pct(r["score_pct"]),
                "Status":   r["learning_status"],
            }
            for r in subject_rows
        ])
        st.markdown("**Subject Performance**")
        st.dataframe(df_s, use_container_width=True, hide_index=True)

        subjects = [r["subject"] for r in subject_rows]
        scores   = [r["score_pct"] for r in subject_rows]
        colors   = [STATUS_COLORS.get(r["learning_status"], "#3b82d4") for r in subject_rows]
        fig = go.Figure(go.Bar(
            x=subjects, y=scores, marker_color=colors,
            text=[f"{s:.1f}%" for s in scores], textposition="outside",
        ))
        fig.update_layout(
            yaxis_range=[0, 110], yaxis_title="Score (%)",
            plot_bgcolor="#f7f8fa", paper_bgcolor="#fff",
            height=300, margin=dict(t=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Reassessment
    reassessments = get_reassessment_history(selected_id)
    if reassessments:
        rh = reassessments[0]
        st.markdown("**Reassessment Result**")
        col1, col2, col3 = st.columns(3)
        with col1:
            metric_card("Topic", rh["topic"], rh["subject"])
        with col2:
            metric_card("Before → After",
                        f"{rh['before_score']:.1f}% → {rh['after_score']:.1f}%", "")
        imp_sign = "+" if rh["improvement"] >= 0 else ""
        with col3:
            metric_card("Improvement",
                        f"{imp_sign}{rh['improvement']:.1f} pp", "",
                        color="#22c55e" if rh["improvement"] >= 0 else "#ef4444")


# ── Helper ──────────────────────────────────────────────────────────────────

def _get_all_reassessments():
    from database.database import get_connection
    conn = get_connection()
    rows = conn.execute("SELECT * FROM reassessments").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Tab 4: Standard-wise Analytics ─────────────────────────────────────────

def _standard_wise_analytics():
    st.markdown("### 🏫 Standard-wise Performance Analytics")
    st.markdown(
        "<p style='color:#57606a;font-size:0.9em;'>Performance breakdown from standard-wise tests "
        "taken by students of each class.</p>",
        unsafe_allow_html=True,
    )

    # ── Registered students per standard ──────────────────────────────────
    all_students = get_all_students()
    std_counts = {}
    for s in all_students:
        std = str(s.get("standard", "8") or "8")
        std_counts[std] = std_counts.get(std, 0) + 1

    st.markdown("#### Students Registered per Standard")
    cols = st.columns(5)
    for i, std in enumerate(STANDARDS):
        count = std_counts.get(std, 0)
        color = STANDARD_COLORS[std]
        cols[i].markdown(
            f"""
            <div style="background:#f7f8fa;border:2px solid {color};border-radius:10px;
                        padding:14px;text-align:center;">
                <div style="font-size:1.6em;font-weight:800;color:{color};">{count}</div>
                <div style="font-size:0.8em;color:#1f2328;font-weight:600;">
                    {STANDARD_LABELS[std]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Standard-test scores chart ────────────────────────────────────────
    stats = get_standard_wise_class_stats()
    if not stats:
        st.info(
            "No standard-wise test data yet. "
            "Students need to take Standard Tests (via the Standard Tests page) first."
        )
        _demo_standard_chart()
        return

    import pandas as pd
    df = pd.DataFrame(stats)
    df["standard"] = df["assessment_type"].str.replace("standard_", "")
    df["std_label"] = df["standard"].map(STANDARD_LABELS)

    st.markdown("#### Average Score per Subject by Standard")
    fig = go.Figure()
    for subj in SUBJECTS:
        subj_df = df[df["subject"] == subj]
        if subj_df.empty:
            continue
        fig.add_trace(go.Bar(
            name=subj,
            x=subj_df["std_label"],
            y=subj_df["avg_score"],
            text=[f"{v:.1f}%" for v in subj_df["avg_score"]],
            textposition="outside",
        ))
    fig.add_hline(y=80, line_dash="dash", line_color="#22c55e", annotation_text="Strong (80%)")
    fig.add_hline(y=60, line_dash="dash", line_color="#f59e0b", annotation_text="Moderate (60%)")
    fig.update_layout(
        barmode="group",
        yaxis_range=[0, 120],
        yaxis_title="Avg Score (%)",
        xaxis_title="Standard",
        plot_bgcolor="#f7f8fa",
        paper_bgcolor="#fff",
        height=420,
        margin=dict(t=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Table
    st.markdown("#### Detailed Stats Table")
    table_rows = []
    for _, row in df.iterrows():
        table_rows.append({
            "Standard":        row["std_label"],
            "Subject":         row["subject"],
            "Avg Score":       fmt_pct(row["avg_score"]),
            "Students Tested": int(row["student_count"]),
            "Status":          get_status_label(row["avg_score"]),
        })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)


def _demo_standard_chart():
    """Show a demo chart when no real standard-test data exists."""
    import pandas as pd
    st.markdown(
        """
        <div style="background:#fef9c3;border:1px solid #f59e0b;border-radius:8px;
                    padding:10px 16px;margin-bottom:12px;">
            <strong>Demo Preview</strong> — This chart shows what the standard-wise analytics
            will look like once students complete standard tests.
        </div>
        """,
        unsafe_allow_html=True,
    )
    demo_data = {
        "Class 6":  [72, 68, 75, 70, 65],
        "Class 7":  [78, 74, 80, 72, 70],
        "Class 8":  [82, 76, 78, 74, 68],
        "Class 9":  [75, 80, 72, 78, 73],
        "Class 10": [85, 82, 80, 80, 77],
    }
    fig = go.Figure()
    for subj, scores in zip(SUBJECTS, list(zip(*demo_data.values()))):
        fig.add_trace(go.Bar(
            name=subj,
            x=list(demo_data.keys()),
            y=list(scores),
            text=[f"{v}%" for v in scores],
            textposition="outside",
        ))
    fig.update_layout(
        barmode="group",
        yaxis_range=[0, 120],
        yaxis_title="Avg Score (%)",
        title="Demo: Standard-wise Subject Performance",
        plot_bgcolor="#f7f8fa",
        paper_bgcolor="#fff",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

