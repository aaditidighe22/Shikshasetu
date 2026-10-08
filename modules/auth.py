"""
ShikshaSetu AI - Authentication Module
Handles student and teacher login/registration using SQLite.
"""

import streamlit as st
from database.database import (
    get_student_by_username,
    get_teacher_by_username,
    create_student,
    hash_password,
)
from utils.helpers import set_session, get_session, info_box, STANDARD_LABELS, STANDARDS


def render_login_page():
    """Render the combined Student / Teacher login page."""
    st.markdown(
        """
        <div style="text-align:center;padding:10px 0 20px 0;">
            <h2 style="color:#1f2328;margin-bottom:4px;">🔐 Sign In to ShikshaSetu AI</h2>
            <p style="color:#57606a;">Students and teachers can log in below</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_student, tab_teacher, tab_register = st.tabs(
        ["👤 Student Login", "📊 Teacher Login", "📝 New Student? Register"]
    )

    with tab_student:
        _student_login_form()

    with tab_teacher:
        _teacher_login_form()

    with tab_register:
        _register_form()


# ─── Internal form renderers ────────────────────────────────────────────────

def _student_login_form():
    st.markdown("#### Student Login")
    with st.form("student_login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="e.g. demo")
        password = st.text_input("Password", type="password", placeholder="e.g. demo123")
        submitted = st.form_submit_button("Login as Student", use_container_width=True)

    if submitted:
        _authenticate_student(username.strip(), password)

    st.markdown(
        """
        <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;
                    padding:12px 16px;margin-top:12px;font-size:0.87em;">
            <strong>Demo Credentials:</strong><br>
            Username: <code>demo</code> &nbsp;|&nbsp; Password: <code>demo123</code><br>
            Also try: <code>student1</code> / <code>student123</code>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _teacher_login_form():
    st.markdown("#### Teacher Login")
    with st.form("teacher_login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="e.g. teacher", key="t_user")
        password = st.text_input("Password", type="password", placeholder="e.g. teacher123", key="t_pass")
        submitted = st.form_submit_button("Login as Teacher", use_container_width=True)

    if submitted:
        _authenticate_teacher(username.strip(), password)

    st.markdown(
        """
        <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;
                    padding:12px 16px;margin-top:12px;font-size:0.87em;">
            <strong>Demo Credentials:</strong><br>
            Username: <code>teacher</code> &nbsp;|&nbsp; Password: <code>teacher123</code>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _register_form():
    st.markdown("#### Create a New Student Account")
    std_options = [STANDARD_LABELS[s] for s in STANDARDS]
    with st.form("register_form", clear_on_submit=True):
        full_name = st.text_input("Full Name *", placeholder="e.g. Ananya Sharma")
        username  = st.text_input("Username *", placeholder="lowercase, no spaces")
        password  = st.text_input("Password *", type="password")
        confirm   = st.text_input("Confirm Password *", type="password")
        col1, col2, col3 = st.columns(3)
        class_name = col1.text_input("Class/Grade", placeholder="e.g. 8th")
        section    = col2.text_input("Section", placeholder="e.g. A")
        std_label  = col3.selectbox("Standard *", std_options, index=2)
        submitted  = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        if not full_name or not username or not password:
            st.error("Please fill in all required fields.")
        elif password != confirm:
            st.error("Passwords do not match.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            # Map label back to number
            std_num = STANDARDS[std_options.index(std_label)]
            ok, msg = create_student(
                username.strip(), password, full_name.strip(),
                class_name, section, standard=std_num
            )
            if ok:
                st.success(f"✅ {msg} You can now log in as a {std_label} student.")
            else:
                st.error(msg)


# ─── Auth helpers ───────────────────────────────────────────────────────────

def _authenticate_student(username, password):
    if not username or not password:
        st.error("Please enter both username and password.")
        return

    student = get_student_by_username(username)
    if student and student["password"] == hash_password(password):
        set_session("student_id",       student["student_id"])
        set_session("student_name",     student["full_name"])
        set_session("student_username", student["username"])
        set_session("student_standard", str(student.get("standard", "8")))
        set_session("student_class",    student.get("class_name", ""))
        set_session("role", "student")
        std_label = STANDARD_LABELS.get(str(student.get("standard", "8")), "")
        st.success(f"✅ Welcome back, {student['full_name']}! ({std_label})")
        st.rerun()
    else:
        st.error("❌ Invalid username or password.")


def _authenticate_teacher(username, password):
    if not username or not password:
        st.error("Please enter both username and password.")
        return

    teacher = get_teacher_by_username(username)
    if teacher and teacher["password"] == hash_password(password):
        set_session("teacher_id", teacher["teacher_id"])
        set_session("teacher_name", teacher["full_name"])
        set_session("role", "teacher")
        st.success(f"✅ Welcome, {teacher['full_name']}!")
        st.rerun()
    else:
        st.error("❌ Invalid username or password.")


def logout():
    """Clear all session state."""
    keys_to_clear = [
        "student_id", "student_name", "student_username", "role",
        "teacher_id", "teacher_name",
        "diagnostic_questions", "diagnostic_answers", "diagnostic_result",
        "subject_diag_questions", "subject_diag_answers", "subject_diag_result",
        "weak_subject", "weak_topic", "practice_done", "reassessment_done",
    ]
    for k in keys_to_clear:
        st.session_state.pop(k, None)
    st.rerun()
