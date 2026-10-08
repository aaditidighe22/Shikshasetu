"""
ShikshaSetu AI — Main Application Entry Point
"From Score to Learning Gap to Improvement"

Run with:   streamlit run app.py

Aligned with SDG 4 – Quality Education
"""

import os
import sys
import streamlit as st

# ─── Path setup (allow imports from project root) ─────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ─── One-shot initialisation (DB schema + seed data + ML model) ──────────────
from database.database import initialize_all

@st.cache_resource(show_spinner=False)
def _init_app():
    """Called once per process: set up DB and train ML model if needed."""
    initialize_all()
    # Train ML model if not already saved
    model_path = os.path.join(ROOT, "models", "learning_gap_model.pkl")
    if not os.path.exists(model_path):
        try:
            from models.train_model import train_and_save_model
            train_and_save_model()
        except Exception as e:
            pass  # ML is optional; app works without it via rule-based fallback
    return True

_init_app()

# ─── Streamlit page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="ShikshaSetu AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Module imports ────────────────────────────────────────────────────────────
from utils.helpers import get_session, set_session
from modules.auth import render_login_page, logout

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Remove default Streamlit padding */
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    /* Sidebar width */
    [data-testid="stSidebar"] { min-width: 230px; }
    /* Button styles */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
    /* Dataframe text */
    .stDataFrame { font-size: 0.87em; }
    /* Tab text */
    .stTabs [data-baseweb="tab"] { font-weight: 600; }
    /* Hide Streamlit branding */
    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Sidebar ───────────────────────────────────────────────────────────────────
def _render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center;padding:12px 0 8px 0;">
                <div style="font-size:2em;">🎓</div>
                <div style="font-weight:800;font-size:1.15em;color:#1e40af;">ShikshaSetu AI</div>
                <div style="font-size:0.75em;color:#57606a;margin-top:2px;">
                    From Score to Learning Gap to Improvement
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")

        role        = get_session("role")
        student_id  = get_session("student_id")
        teacher_id  = get_session("teacher_id")

        # Auth status
        if student_id:
            from utils.helpers import STANDARD_LABELS
            std       = get_session("student_standard", "8")
            std_label = STANDARD_LABELS.get(std, f"Class {std}")
            st.markdown(
                f"<div style='background:#dcfce7;border-radius:8px;padding:8px 12px;"
                f"font-size:0.85em;margin-bottom:8px;'>👤 <strong>{get_session('student_name')}</strong><br>"
                f"<span style='color:#57606a;'>Student · {std_label}</span></div>",
                unsafe_allow_html=True,
            )
        elif teacher_id:
            st.markdown(
                f"<div style='background:#dbeafe;border-radius:8px;padding:8px 12px;"
                f"font-size:0.85em;margin-bottom:8px;'>📊 <strong>{get_session('teacher_name')}</strong><br>"
                f"<span style='color:#57606a;'>Teacher</span></div>",
                unsafe_allow_html=True,
            )

        # Navigation
        st.markdown("**Navigation**")
        pages = _get_pages(role, student_id, teacher_id)
        for page_name, icon in pages:
            if st.button(f"{icon}  {page_name}", key=f"nav_{page_name}", use_container_width=True):
                set_session("page", page_name)
                st.rerun()

        st.markdown("---")
        if student_id or teacher_id:
            if st.button("🚪 Logout", use_container_width=True):
                logout()

        st.markdown(
            """
            <div style="font-size:0.72em;color:#57606a;text-align:center;margin-top:16px;">
                Aligned with<br><strong>SDG 4 — Quality Education</strong><br>
                <span style="font-size:1.4em;">🎯</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _get_pages(role, student_id, teacher_id):
    """Return navigation items based on current user role."""
    common = [("Home", "🏠")]

    if not student_id and not teacher_id:
        return common + [("Login", "🔐"), ("About", "ℹ️")]

    if student_id:
        student_pages = [
            ("Dashboard", "📊"),
            ("Diagnostic Test", "📋"),
            ("Subject Diagnostic Test", "🔬"),
            ("Learning Profile", "🎓"),
            ("Personalized Learning", "📚"),
            ("Practice", "✏️"),
            ("Reassessment", "🔄"),
            ("Progress", "📈"),
            ("Standard Tests", "🏫"),
        ]
        return common + student_pages + [("About", "ℹ️")]

    if teacher_id:
        return common + [("Teacher Dashboard", "📊"), ("About", "ℹ️")]

    return common + [("Login", "🔐"), ("About", "ℹ️")]


# ─── Page Renderers ────────────────────────────────────────────────────────────

def render_home():
    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#1e40af,#7c5cd8,#059669);
                    color:#fff;padding:48px 32px;border-radius:16px;text-align:center;
                    margin-bottom:32px;">
            <div style="font-size:3em;margin-bottom:8px;">🎓</div>
            <h1 style="margin:0;font-size:2.4em;letter-spacing:-0.5px;">ShikshaSetu AI</h1>
            <p style="font-size:1.15em;margin:10px 0 0 0;opacity:0.9;font-style:italic;">
                "From Score to Learning Gap to Improvement"
            </p>
            <p style="margin:16px auto 0 auto;max-width:600px;opacity:0.85;font-size:0.95em;">
            An AI-powered learning platform that identifies subject and topic-level
            learning gaps and provides personalized learning recommendations
            — aligned with SDG 4: Quality Education.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Three core steps
    col1, col2, col3 = st.columns(3)
    steps = [
        ("1", "📋", "ASSESS", "Take the multi-subject diagnostic test to measure your current performance across all subjects.", "#1e40af"),
        ("2", "🔍", "IDENTIFY", "AI/ML analysis detects your weakest subject and topic-level learning gaps with personalized insights.", "#7c5cd8"),
        ("3", "📈", "IMPROVE", "Follow your personalized learning pathway, practice targeted questions, and measure your improvement.", "#059669"),
    ]
    for col, (num, icon, title, desc, color) in zip([col1, col2, col3], steps):
        col.markdown(
            f"""
            <div style="background:#f7f8fa;border:2px solid {color};border-radius:12px;
                        padding:24px;text-align:center;height:200px;">
                <div style="font-size:2.2em;">{icon}</div>
                <div style="font-weight:800;font-size:1.1em;color:{color};margin:8px 0 4px 0;">
                    STEP {num}: {title}
                </div>
                <div style="font-size:0.87em;color:#57606a;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Unique feature callout
    st.markdown(
        """
        <div style="background:#fef9c3;border:1px solid #f59e0b;border-radius:12px;
                    padding:20px 24px;margin-bottom:20px;">
            <h4 style="margin:0 0 10px 0;color:#854d0e;">🌟 Unique Feature: Two-Level Learning Gap Detection</h4>
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                <span style="background:#1e40af;color:#fff;padding:4px 14px;border-radius:8px;font-size:0.85em;">All-Subject Test</span>
                <span style="color:#57606a;">→</span>
                <span style="background:#7c5cd8;color:#fff;padding:4px 14px;border-radius:8px;font-size:0.85em;">Weak Subject Detected</span>
                <span style="color:#57606a;">→</span>
                <span style="background:#0369a1;color:#fff;padding:4px 14px;border-radius:8px;font-size:0.85em;">Subject Diagnostic</span>
                <span style="color:#57606a;">→</span>
                <span style="background:#ef4444;color:#fff;padding:4px 14px;border-radius:8px;font-size:0.85em;">Weak Topic Detected</span>
                <span style="color:#57606a;">→</span>
                <span style="background:#059669;color:#fff;padding:4px 14px;border-radius:8px;font-size:0.85em;">Personalized Learning</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # SDG badge
    st.markdown(
        """
        <div style="background:#dcfce7;border:1px solid #86efac;border-radius:10px;
                    padding:14px 20px;margin-bottom:20px;text-align:center;">
            <strong>🎯 Aligned with SDG 4 — Quality Education</strong><br>
            <span style="font-size:0.88em;color:#166534;">
            "Ensure inclusive and equitable quality education and promote
            lifelong learning opportunities for all."
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # CTA buttons
    col_a, col_b, col_c, col_d = st.columns([2, 2, 2, 1])
    with col_a:
        if st.button("🚀 Start Diagnostic Test", type="primary", use_container_width=True):
            student_id = get_session("student_id")
            if student_id:
                set_session("page", "Diagnostic Test")
            else:
                set_session("page", "Login")
            st.rerun()
    with col_b:
        if st.button("🏫 Standard-wise Tests", use_container_width=True):
            student_id = get_session("student_id")
            if student_id:
                set_session("page", "Standard Tests")
            else:
                set_session("page", "Login")
            st.rerun()
    with col_c:
        if st.button("📊 Teacher Dashboard", use_container_width=True):
            teacher_id = get_session("teacher_id")
            if teacher_id:
                set_session("page", "Teacher Dashboard")
            else:
                set_session("page", "Login")
            st.rerun()
    with col_d:
        if st.button("ℹ️ About", use_container_width=True):
            set_session("page", "About")
            st.rerun()


def render_about():
    st.markdown("## ℹ️ About ShikshaSetu AI")
    st.markdown(
        """
        ### Problem Statement
        Traditional tests only provide marks and do not clearly identify **WHY** a student
        is weak or **WHICH specific topic/concept** needs improvement.

        ### Solution
        ShikshaSetu AI uses a two-level diagnostic approach:
        1. **Multi-Subject Diagnostic** — identifies which subject needs attention
        2. **Subject-Specific Diagnostic** — pinpoints the exact topic/concept gap
        3. **ML Classification** — predicts learning status (Strong / Moderate / Needs Support)
        4. **Personalized Learning Pathway** — targeted recommendations for the weak topic
        5. **Practice + Reassessment** — measures actual improvement

        ### Technology Stack
        | Component | Technology |
        |---|---|
        | Frontend / App | Python + Streamlit |
        | ML Model | Random Forest Classifier (scikit-learn) |
        | Database | SQLite (sqlite3) |
        | Visualization | Plotly |
        | Data Processing | Pandas + NumPy |

        ### ML Methodology
        The Random Forest Classifier is trained on student performance features including:
        current score, previous score, correct/incorrect answers, difficulty breakdown,
        number of attempts, and prior improvement. It classifies learning status into:
        **Strong**, **Moderate**, or **Needs Support**.

        > ⚠️ **Important Notice**: Prototype ML results are based on synthetic/demo
        assessment data and should not be interpreted as real-world educational effectiveness.

        ### Future Scope — Agentic Personalized Learning
        The system is designed to support a future **Learning Agent** that will:
        1. Analyze the student profile autonomously
        2. Identify priority learning gaps
        3. Select and sequence learning content
        4. Generate adaptive practice questions
        5. Adjust difficulty based on performance
        6. Orchestrate the full improvement cycle

        ### SDG 4 — Quality Education
        ShikshaSetu AI directly supports SDG 4 by helping students and teachers
        identify and address learning gaps, enabling **equitable quality education**
        and **personalized learning opportunities** for all.

        ---
        **Demo Credentials**

        | Role | Username | Password |
        |---|---|---|
        | Student | `demo` | `demo123` |
        | Student | `student1` | `student123` |
        | Teacher | `teacher` | `teacher123` |
        """
    )


def render_progress_page():
    student_id = get_session("student_id")
    if not student_id:
        st.warning("⚠️ Please log in to view your progress.")
        return

    from modules.student_dashboard import render_student_dashboard
    render_student_dashboard()


def render_ai_assistant():
    """Optional AI learning assistant. Requires OPENAI_API_KEY or GOOGLE_API_KEY in env."""
    st.markdown("## 🤖 AI Learning Assistant (Optional)")

    weak_subject = get_session("weak_subject", "")
    weak_topic   = get_session("weak_topic", "")

    # Detect available API
    openai_key  = os.environ.get("OPENAI_API_KEY", "")
    google_key  = os.environ.get("GOOGLE_API_KEY", "")

    if not openai_key and not google_key:
        st.info(
            "🔒 The AI Learning Assistant is optional and requires an API key.\n\n"
            "To enable it, set `OPENAI_API_KEY` or `GOOGLE_API_KEY` in your `.env` file.\n\n"
            "The rest of ShikshaSetu AI works fully without this feature."
        )
        return

    context = f"The student's detected weak topic is **{weak_topic}** in **{weak_subject}**." \
              if weak_topic else "No specific topic detected yet."
    st.info(context)

    if "ai_chat_history" not in st.session_state:
        st.session_state["ai_chat_history"] = []

    # Display chat history
    for msg in st.session_state["ai_chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input(
        f"Ask about {weak_topic or 'any concept'} ..." if weak_topic else "Ask a learning question ..."
    )

    if user_input:
        st.session_state["ai_chat_history"].append({"role": "user", "content": user_input})

        system_prompt = (
            f"You are ShikshaSetu AI, a friendly and supportive educational assistant "
            f"for school students (Grade 6-10). "
            f"The student is struggling with {weak_topic} in {weak_subject}. "
            f"Give simple, clear, student-friendly explanations with examples. "
            f"Keep responses concise and encouraging."
        )

        try:
            if openai_key:
                _openai_chat(system_prompt, user_input)
            elif google_key:
                _google_chat(system_prompt, user_input)
        except Exception as e:
            reply = f"Sorry, I encountered an error: {str(e)[:200]}"
            st.session_state["ai_chat_history"].append({"role": "assistant", "content": reply})
            st.rerun()


def _openai_chat(system_prompt, user_input):
    import openai
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    messages = [{"role": "system", "content": system_prompt}]
    for msg in st.session_state["ai_chat_history"][-6:]:
        messages.append(msg)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=500,
    )
    reply = response.choices[0].message.content
    st.session_state["ai_chat_history"].append({"role": "assistant", "content": reply})
    st.rerun()


def _google_chat(system_prompt, user_input):
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-pro")
    prompt = f"{system_prompt}\n\nStudent: {user_input}"
    response = model.generate_content(prompt)
    reply = response.text
    st.session_state["ai_chat_history"].append({"role": "assistant", "content": reply})
    st.rerun()


# ─── Main Router ───────────────────────────────────────────────────────────────

def main():
    # Initialise default page
    if "page" not in st.session_state:
        st.session_state["page"] = "Home"

    _render_sidebar()

    page = get_session("page", "Home")

    # ── Public pages ─────────────────────────────────────────
    if page == "Home":
        render_home()
        return

    if page == "About":
        render_about()
        return

    if page == "Login":
        render_login_page()
        return

    # ── Auth guard ────────────────────────────────────────────
    student_id = get_session("student_id")
    teacher_id = get_session("teacher_id")

    if not student_id and not teacher_id:
        st.info("Please log in to access this page.")
        render_login_page()
        return

    # ── Teacher pages ─────────────────────────────────────────
    if page == "Teacher Dashboard":
        from modules.teacher_dashboard import render_teacher_dashboard
        render_teacher_dashboard()
        return

    # ── Student pages ─────────────────────────────────────────
    if not student_id:
        st.warning("This page is for students. Please log in as a student.")
        return

    if page == "Dashboard":
        from modules.student_dashboard import render_student_dashboard
        render_student_dashboard()

    elif page == "Diagnostic Test":
        from modules.diagnostic_test import render_multi_subject_test
        render_multi_subject_test()

    elif page == "Subject Diagnostic Test":
        from modules.diagnostic_test import render_subject_diagnostic_test
        render_subject_diagnostic_test()

    elif page == "Learning Profile":
        from modules.learning_analysis import render_learning_profile
        render_learning_profile()

    elif page == "Personalized Learning":
        set_session("recommendations_viewed", True)
        from modules.recommendation import render_recommendations
        render_recommendations()

    elif page == "Practice":
        from modules.practice import render_practice
        render_practice()

    elif page == "Reassessment":
        from modules.reassessment import render_reassessment
        render_reassessment()

    elif page == "Progress":
        render_progress_page()

    elif page == "Standard Tests":
        from modules.standard_test import render_standard_test_page
        render_standard_test_page()

    elif page == "AI Assistant":
        render_ai_assistant()

    else:
        render_home()


if __name__ == "__main__":
    main()
