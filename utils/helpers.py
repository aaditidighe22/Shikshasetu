"""
ShikshaSetu AI - General Helpers
Shared constants, formatting utilities and UI helper functions.
"""

import streamlit as st
from typing import Optional

# ─── Standards / Subject / Topic Metadata ─────────────────────────────────────

STANDARDS = ["6", "7", "8", "9", "10"]

STANDARD_LABELS = {
    "6":  "Class 6",
    "7":  "Class 7",
    "8":  "Class 8",
    "9":  "Class 9",
    "10": "Class 10",
}

STANDARD_COLORS = {
    "6":  "#0ea5e9",
    "7":  "#8b5cf6",
    "8":  "#f59e0b",
    "9":  "#10b981",
    "10": "#ef4444",
}

SUBJECTS = [
    "Mathematics",
    "Science",
    "English",
    "Social Science",
    "Computer Science",
]

TOPICS_MAP = {
    "Mathematics":      ["Arithmetic", "Fractions", "Algebra", "Geometry", "Linear Equations"],
    "Science":          ["Matter", "Force and Motion", "Energy", "Human Body", "Environment"],
    "English":          ["Grammar", "Vocabulary", "Reading Comprehension", "Sentence Formation", "Writing"],
    "Social Science":   ["History", "Geography", "Civics", "Economics", "Environment"],
    "Computer Science": ["Computer Basics", "Programming Fundamentals", "Algorithms", "Databases", "Networking"],
}

STATUS_COLORS = {
    "Strong":        "#22c55e",   # green
    "Moderate":      "#f59e0b",   # amber
    "Needs Support": "#ef4444",   # red
}

STATUS_ICONS = {
    "Strong":        "✅",
    "Moderate":      "⚠️",
    "Needs Support": "🔴",
}


# ─── Score formatting ──────────────────────────────────────────────────────────

def fmt_pct(val: float) -> str:
    return f"{val:.1f}%"


def status_badge(status: str) -> str:
    """Return an HTML badge for learning status."""
    color = STATUS_COLORS.get(status, "#6b7280")
    icon = STATUS_ICONS.get(status, "")
    return (
        f'<span style="background:{color};color:#fff;padding:3px 10px;'
        f'border-radius:12px;font-size:0.8em;font-weight:600;">'
        f'{icon} {status}</span>'
    )


def get_status_label(score_pct: float) -> str:
    if score_pct >= 80:
        return "Strong"
    elif score_pct >= 60:
        return "Moderate"
    else:
        return "Needs Support"


def score_color(score_pct: float) -> str:
    if score_pct >= 80:
        return "#22c55e"
    elif score_pct >= 60:
        return "#f59e0b"
    else:
        return "#ef4444"


# ─── Streamlit UI helpers ─────────────────────────────────────────────────────

def metric_card(label: str, value: str, sub: str = "", color: str = "#3b82d4"):
    """Render a styled metric card using st.markdown."""
    st.markdown(
        f"""
        <div style="background:#f7f8fa;border:1px solid #e5e7eb;border-radius:10px;
                    padding:16px 20px;margin-bottom:8px;border-left:4px solid {color};">
            <div style="font-size:0.78em;color:#57606a;font-weight:600;text-transform:uppercase;
                        letter-spacing:0.05em;">{label}</div>
            <div style="font-size:1.6em;font-weight:700;color:#1f2328;margin:4px 0;">{value}</div>
            <div style="font-size:0.82em;color:#57606a;">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div style="margin:16px 0 8px 0;">
            <h3 style="margin:0;color:#1f2328;font-size:1.25em;">{title}</h3>
            {'<p style="margin:2px 0 0 0;color:#57606a;font-size:0.88em;">'+subtitle+'</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_box(text: str, kind: str = "info"):
    colors = {
        "info":    ("#dbeafe", "#1e40af"),
        "success": ("#dcfce7", "#166534"),
        "warning": ("#fef9c3", "#854d0e"),
        "error":   ("#fee2e2", "#991b1b"),
    }
    bg, fg = colors.get(kind, colors["info"])
    st.markdown(
        f'<div style="background:{bg};color:{fg};padding:12px 16px;border-radius:8px;'
        f'margin:8px 0;font-size:0.9em;">{text}</div>',
        unsafe_allow_html=True,
    )


def render_progress_bar(pct: float, label: str = ""):
    color = score_color(pct)
    st.markdown(
        f"""
        <div style="margin:4px 0;">
            <div style="display:flex;justify-content:space-between;font-size:0.85em;color:#1f2328;">
                <span>{label}</span><span style="font-weight:600;">{pct:.1f}%</span>
            </div>
            <div style="background:#e5e7eb;border-radius:6px;height:10px;margin-top:2px;">
                <div style="background:{color};width:{min(pct,100)}%;height:10px;border-radius:6px;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── Session-state helpers ─────────────────────────────────────────────────────

def get_session(key, default=None):
    return st.session_state.get(key, default)


def set_session(key, value):
    st.session_state[key] = value


def clear_session_keys(*keys):
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]


def is_logged_in() -> bool:
    return bool(get_session("student_id") or get_session("teacher_id"))


def require_student_login():
    if not get_session("student_id"):
        st.warning("⚠️ Please log in as a student to access this feature.")
        st.stop()
