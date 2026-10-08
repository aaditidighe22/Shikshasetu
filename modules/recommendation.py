"""
ShikshaSetu AI - Recommendation Module
Generates personalized learning pathways for identified weak topics.
"""

import streamlit as st
from utils.helpers import get_session, set_session, section_header, STATUS_COLORS

# ─── Learning pathways per subject/topic ──────────────────────────────────────
# Each entry: list of step strings for the student to follow.

LEARNING_PATHS = {
    # Mathematics
    ("Mathematics", "Arithmetic"): {
        "overview": "Build number sense: counting, place value, and the four operations.",
        "steps": [
            "Review number place value (ones, tens, hundreds, thousands)",
            "Practice addition and subtraction with carrying and borrowing",
            "Understand multiplication tables up to 12×12",
            "Practice long division with remainders",
            "Solve multi-step word problems using all four operations",
            "Practice percentage calculations (%, of, increase/decrease)",
            "Take reassessment to confirm mastery",
        ],
        "resources": [
            "Khan Academy – Arithmetic",
            "NCERT Class 7 – Numbers and Operations",
            "Practice with mental math exercises daily",
        ],
    },
    ("Mathematics", "Fractions"): {
        "overview": "Understand parts of a whole and operations with fractions.",
        "steps": [
            "Understand numerator and denominator — what they mean",
            "Learn equivalent fractions (e.g., 1/2 = 2/4 = 4/8)",
            "Learn to convert between mixed numbers and improper fractions",
            "Practice addition and subtraction of like fractions",
            "Practice addition and subtraction of unlike fractions (find LCM)",
            "Practice multiplication and division of fractions",
            "Solve word problems involving fractions",
            "Take reassessment",
        ],
        "resources": ["Khan Academy – Fractions", "NCERT Class 6-7 Maths"],
    },
    ("Mathematics", "Algebra"): {
        "overview": "Use letters to represent unknown quantities and solve equations.",
        "steps": [
            "Understand variables and constants in algebraic expressions",
            "Learn to simplify expressions by collecting like terms",
            "Evaluate expressions by substituting values",
            "Solve one-variable linear equations (e.g., 2x + 3 = 11)",
            "Understand and apply the distributive property",
            "Translate word problems into algebraic equations",
            "Practice equations with negative numbers",
            "Take reassessment",
        ],
        "resources": ["Khan Academy – Algebra Basics", "NCERT Class 8 Maths – Algebraic Expressions"],
    },
    ("Mathematics", "Geometry"): {
        "overview": "Understand shapes, angles, area, and perimeter.",
        "steps": [
            "Learn types of angles: acute, right, obtuse, straight, reflex",
            "Understand properties of triangles (angles sum to 180°)",
            "Learn area formulas: rectangle, square, triangle, circle",
            "Learn perimeter formulas for common shapes",
            "Understand the Pythagorean theorem",
            "Practice identifying 2D and 3D shapes",
            "Solve geometry word problems",
            "Take reassessment",
        ],
        "resources": ["Khan Academy – Geometry", "NCERT Class 7-8 Maths"],
    },
    ("Mathematics", "Linear Equations"): {
        "overview": "Solve equations with one or two variables representing straight-line relationships.",
        "steps": [
            "Review algebraic expressions and variables",
            "Solve simple one-step equations (add/subtract/multiply/divide)",
            "Solve two-step equations (e.g., 2x + 5 = 13)",
            "Learn to check solutions by substitution",
            "Understand slope-intercept form y = mx + c",
            "Graph linear equations on a coordinate plane",
            "Solve systems of two linear equations",
            "Take reassessment",
        ],
        "resources": ["Khan Academy – Linear Equations", "NCERT Class 8-9 Maths"],
    },
    # Science
    ("Science", "Matter"): {
        "overview": "Understand the three states of matter and their properties.",
        "steps": [
            "Learn the definition of matter and its properties",
            "Study the three states: solid, liquid, gas",
            "Understand particle arrangement in each state",
            "Learn about changes of state: melting, boiling, condensation, freezing",
            "Understand sublimation and deposition",
            "Learn about physical vs chemical properties",
            "Practice classifying materials by state",
            "Take reassessment",
        ],
        "resources": ["NCERT Science Class 6-8", "Khan Academy – States of Matter"],
    },
    ("Science", "Force and Motion"): {
        "overview": "Understand Newton's laws and how forces affect movement.",
        "steps": [
            "Understand what a force is (push/pull) and its units (Newton)",
            "Learn Newton's First Law: Law of Inertia",
            "Learn Newton's Second Law: F = ma",
            "Learn Newton's Third Law: Action-Reaction",
            "Understand speed, velocity, and acceleration",
            "Learn about gravity and its effects",
            "Practice solving force and motion problems",
            "Take reassessment",
        ],
        "resources": ["NCERT Science Class 9", "Khan Academy – Forces and Newton's Laws"],
    },
    ("Science", "Energy"): {
        "overview": "Explore kinetic, potential, and other forms of energy.",
        "steps": [
            "Define energy and its SI unit (Joule)",
            "Learn types: kinetic, potential, thermal, chemical, electrical",
            "Understand the Law of Conservation of Energy",
            "Learn about energy transformation examples",
            "Study renewable vs non-renewable energy sources",
            "Understand power and its unit (Watt)",
            "Solve simple energy calculation problems",
            "Take reassessment",
        ],
        "resources": ["NCERT Science Class 9", "Khan Academy – Work, Energy, Power"],
    },
    ("Science", "Human Body"): {
        "overview": "Learn about the human body's organ systems.",
        "steps": [
            "Learn about cells as the basic unit of life",
            "Study the digestive system and its organs",
            "Study the circulatory system: heart, blood, vessels",
            "Study the respiratory system: lungs, breathing",
            "Learn about the nervous system: brain, spinal cord, nerves",
            "Study the skeletal and muscular systems",
            "Understand the endocrine and excretory systems",
            "Take reassessment",
        ],
        "resources": ["NCERT Science Class 8-10", "Khan Academy – Human Biology"],
    },
    ("Science", "Environment"): {
        "overview": "Understand ecosystems, biodiversity, and environmental challenges.",
        "steps": [
            "Learn about ecosystems and food chains/webs",
            "Understand biodiversity and its importance",
            "Learn about the water, carbon, and nitrogen cycles",
            "Study causes and effects of pollution (air, water, soil)",
            "Understand the greenhouse effect and global warming",
            "Learn about deforestation and conservation",
            "Study sustainable development and SDGs",
            "Take reassessment",
        ],
        "resources": ["NCERT Science Class 8-10", "WWF – Environmental Education"],
    },
    # English
    ("English", "Grammar"): {
        "overview": "Master the building blocks of correct English sentences.",
        "steps": [
            "Review the 8 parts of speech: noun, pronoun, verb, adjective, adverb, preposition, conjunction, interjection",
            "Practice identifying subjects and predicates",
            "Learn tenses: simple present, past, future + continuous/perfect forms",
            "Understand active vs passive voice",
            "Practice correct use of articles (a, an, the)",
            "Learn subject-verb agreement rules",
            "Identify and correct common grammar errors",
            "Take reassessment",
        ],
        "resources": ["BBC Learning English", "NCERT English Grammar Book"],
    },
    ("English", "Vocabulary"): {
        "overview": "Build your word power with synonyms, antonyms, and word usage.",
        "steps": [
            "Learn 10 new words daily using context",
            "Practice using a dictionary and thesaurus",
            "Study common prefixes and suffixes (un-, re-, -ful, -less)",
            "Practice synonym and antonym exercises",
            "Learn commonly confused words (their/there/they're)",
            "Use new words in sentences for reinforcement",
            "Read passages and identify unfamiliar words",
            "Take reassessment",
        ],
        "resources": ["Merriam-Webster Word of the Day", "Wordsmith.org"],
    },
    ("English", "Reading Comprehension"): {
        "overview": "Improve your ability to understand and analyse written passages.",
        "steps": [
            "Read actively: preview, read, review (SQ3R method)",
            "Practice finding the main idea and supporting details",
            "Learn to identify the author's purpose and tone",
            "Practice making inferences from context",
            "Study literary devices: simile, metaphor, personification",
            "Answer comprehension questions using text evidence",
            "Practice reading different genres (fiction, non-fiction, poetry)",
            "Take reassessment",
        ],
        "resources": ["ReadWorks.org", "NCERT Literature Books"],
    },
    ("English", "Sentence Formation"): {
        "overview": "Construct clear, correct, and varied sentences.",
        "steps": [
            "Understand simple, compound, and complex sentences",
            "Practice joining sentences using conjunctions (and, but, because, although)",
            "Learn about dependent and independent clauses",
            "Avoid run-on sentences and sentence fragments",
            "Practice varying sentence beginnings",
            "Learn direct and indirect speech",
            "Edit sentences for clarity and correctness",
            "Take reassessment",
        ],
        "resources": ["Purdue OWL – Sentence Structure", "NCERT English Grammar"],
    },
    ("English", "Writing"): {
        "overview": "Develop clear, structured, and effective writing skills.",
        "steps": [
            "Learn the structure: introduction, body, conclusion",
            "Practice writing effective topic sentences",
            "Learn to support ideas with evidence and examples",
            "Study paragraph coherence and transitions",
            "Practice different writing types: narrative, descriptive, persuasive, expository",
            "Learn formal vs informal letter writing",
            "Review and edit your drafts for grammar and clarity",
            "Take reassessment",
        ],
        "resources": ["Writing Forward Blog", "NCERT Writing Skills Books"],
    },
    # Social Science
    ("Social Science", "History"): {
        "overview": "Understand key historical events, timelines, and their significance.",
        "steps": [
            "Create a timeline of major historical periods",
            "Study key events in Indian independence",
            "Understand the causes and effects of the World Wars",
            "Learn about ancient civilizations (Indus Valley, Mesopotamia, Egypt)",
            "Study the impact of colonialism on India",
            "Understand the Constitution of India and its formation",
            "Practice map-based historical questions",
            "Take reassessment",
        ],
        "resources": ["NCERT History Books Class 8-10", "IGNOU History Materials"],
    },
    ("Social Science", "Geography"): {
        "overview": "Understand physical and human geography concepts.",
        "steps": [
            "Learn to read political and physical maps",
            "Study landforms: mountains, rivers, plateaus, plains",
            "Understand climate zones and seasons",
            "Learn about Indian rivers, mountains, and plains",
            "Study natural resources: water, minerals, forests",
            "Understand population distribution and migration",
            "Learn about human settlements and urbanisation",
            "Take reassessment",
        ],
        "resources": ["NCERT Geography Class 8-10", "National Geographic Education"],
    },
    ("Social Science", "Civics"): {
        "overview": "Understand democracy, government, and citizenship in India.",
        "steps": [
            "Learn the structure of India's government: legislative, executive, judiciary",
            "Study the Constitution: preamble, fundamental rights, duties",
            "Understand how Parliament works: Lok Sabha, Rajya Sabha",
            "Learn about the role of the judiciary and Supreme Court",
            "Study elections, voting, and the Election Commission",
            "Understand Panchayati Raj and local governance",
            "Learn about international organisations: UN, WHO, UNESCO",
            "Take reassessment",
        ],
        "resources": ["NCERT Political Science Class 8-10", "Constitution of India"],
    },
    ("Social Science", "Economics"): {
        "overview": "Understand basic economic concepts and India's economy.",
        "steps": [
            "Learn basic concepts: wants, needs, goods, services",
            "Understand the three sectors: primary, secondary, tertiary",
            "Learn about money, banking, and credit",
            "Study GDP, GNP, and economic development",
            "Understand inflation and its effects",
            "Learn about poverty, employment, and inequality in India",
            "Study globalisation and international trade",
            "Take reassessment",
        ],
        "resources": ["NCERT Economics Class 9-10", "RBI Publication – Financial Literacy"],
    },
    ("Social Science", "Environment"): {
        "overview": "Learn about environmental challenges and sustainable development.",
        "steps": [
            "Understand natural resources and their types",
            "Study environmental degradation: deforestation, desertification, pollution",
            "Learn about climate change: causes, effects, solutions",
            "Understand sustainable development and the SDGs",
            "Study environmental laws and policies in India",
            "Learn about biodiversity hotspots and conservation",
            "Explore India's environmental initiatives",
            "Take reassessment",
        ],
        "resources": ["NCERT Geography/Science Class 9-10", "UNEP Education Materials"],
    },
    # Computer Science
    ("Computer Science", "Computer Basics"): {
        "overview": "Understand the fundamental components of a computer system.",
        "steps": [
            "Learn the basic components: CPU, RAM, ROM, storage, I/O devices",
            "Understand the difference between hardware and software",
            "Learn about operating systems (Windows, Linux, macOS)",
            "Understand binary numbers and why computers use them",
            "Learn about input devices (keyboard, mouse) and output devices (monitor, printer)",
            "Understand file systems and folder organisation",
            "Learn basic shortcuts and computer operations",
            "Take reassessment",
        ],
        "resources": ["GCF Global – Computer Basics", "NCERT Computer Science Class 8-9"],
    },
    ("Computer Science", "Programming Fundamentals"): {
        "overview": "Learn the core concepts of programming using Python.",
        "steps": [
            "Understand what a program is and how it works",
            "Learn about variables, data types (int, float, string, bool)",
            "Practice input/output: input() and print() in Python",
            "Learn arithmetic and comparison operators",
            "Understand conditional statements: if, elif, else",
            "Learn loops: for loop and while loop",
            "Understand functions: defining and calling",
            "Take reassessment",
        ],
        "resources": ["Python.org Tutorial", "W3Schools Python", "NCERT CS Class 11"],
    },
    ("Computer Science", "Algorithms"): {
        "overview": "Understand how to solve problems step by step efficiently.",
        "steps": [
            "Understand what an algorithm is and its properties",
            "Learn to write pseudocode and flowcharts",
            "Study linear search and binary search",
            "Learn bubble sort, selection sort, insertion sort",
            "Understand time complexity: O(1), O(n), O(log n), O(n²)",
            "Learn recursion basics with simple examples",
            "Practice algorithm design for common problems",
            "Take reassessment",
        ],
        "resources": ["Khan Academy – Algorithms", "CS50 – Introduction to CS"],
    },
    ("Computer Science", "Databases"): {
        "overview": "Understand database concepts and basic SQL queries.",
        "steps": [
            "Understand what a database is and why it is used",
            "Learn about tables, rows, and columns",
            "Understand primary key and foreign key concepts",
            "Learn basic SQL: CREATE TABLE, INSERT INTO, SELECT",
            "Practice WHERE clause to filter data",
            "Learn ORDER BY to sort results",
            "Practice simple JOIN operations",
            "Take reassessment",
        ],
        "resources": ["W3Schools SQL Tutorial", "SQLiteOnline.com", "NCERT CS Class 11"],
    },
    ("Computer Science", "Networking"): {
        "overview": "Understand how computers communicate over networks.",
        "steps": [
            "Learn what a computer network is and its types (LAN, WAN, MAN)",
            "Understand the client-server model",
            "Learn about IP addresses and how they work",
            "Understand DNS: how domain names are resolved",
            "Learn about HTTP/HTTPS and web communication",
            "Understand network devices: router, switch, hub, modem",
            "Learn about network security basics: firewalls, encryption",
            "Take reassessment",
        ],
        "resources": ["Khan Academy – Internet", "Cisco Networking Basics", "NCERT CS Class 11"],
    },
}


def get_learning_path(subject: str, topic: str) -> dict:
    """Return the learning path for a subject-topic pair or a generic fallback."""
    key = (subject, topic)
    if key in LEARNING_PATHS:
        return LEARNING_PATHS[key]
    # Generic fallback
    return {
        "overview": f"Improve your understanding of {topic} in {subject}.",
        "steps": [
            f"Review the basic concepts of {topic}",
            f"Read your textbook chapter on {topic}",
            f"Watch a video explanation of {topic}",
            f"Solve at least 10 practice questions on {topic}",
            f"Discuss any doubts about {topic} with your teacher",
            "Take the reassessment to measure your improvement",
        ],
        "resources": [
            f"NCERT {subject} textbook",
            "Khan Academy",
            "Your school notes",
        ],
    }


def render_recommendations():
    student_id  = get_session("student_id")
    if not student_id:
        st.warning("⚠️ Please log in to view your personalized learning recommendations.")
        return

    weak_subject = get_session("weak_subject")
    weak_topic   = get_session("weak_topic")
    topic_score  = get_session("weak_topic_score", 0)

    if not weak_subject:
        st.info("📋 Complete the Multi-Subject Diagnostic Test first to get personalized recommendations.")
        if st.button("Take Diagnostic Test", type="primary"):
            set_session("page", "Diagnostic Test")
            st.rerun()
        return

    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#059669,#10b981);color:#fff;
                    padding:24px;border-radius:12px;margin-bottom:20px;">
            <h2 style="margin:0;">📚 Personalized Learning Recommendations</h2>
            <p style="margin:6px 0 0 0;opacity:0.9;">
            Your AI-generated learning pathway based on detected gaps
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not weak_topic:
        st.markdown(
            f"""
            <div style="background:#fef9c3;border:1px solid #f59e0b;border-radius:10px;
                        padding:16px 20px;margin-bottom:16px;">
                <h4 style="margin:0 0 8px 0;color:#854d0e;">📌 Detected Gap: Subject Level</h4>
                <p style="margin:0;color:#1f2328;">
                Priority Subject: <strong>{weak_subject}</strong><br>
                Take the subject diagnostic test to identify the specific topic gap.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"🔬 Take {weak_subject} Diagnostic Test", type="primary"):
            set_session("page", "Subject Diagnostic Test")
            st.rerun()
        return

    path = get_learning_path(weak_subject, weak_topic)

    # Gap banner
    st.markdown(
        f"""
        <div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:10px;
                    padding:16px 20px;margin-bottom:16px;">
            <table style="width:100%;"><tr>
                <td><strong>🎯 Detected Gap</strong></td>
                <td style="font-weight:700;font-size:1.1em;">{weak_topic}</td>
                <td><strong>Subject</strong></td>
                <td style="font-weight:700;">{weak_subject}</td>
                <td><strong>Current Score</strong></td>
                <td><span style="background:#ef4444;color:#fff;padding:2px 10px;
                           border-radius:10px;">{topic_score:.1f}%</span></td>
            </tr></table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Overview
    st.markdown(
        f"""
        <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;
                    padding:14px 18px;margin-bottom:16px;">
            <strong>📌 Learning Overview</strong><br>
            <span style="color:#1f2328;">{path['overview']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Steps
    st.markdown("### 🗺️ Your Recommended Learning Path")
    for i, step in enumerate(path["steps"], 1):
        is_last = step.lower().startswith("take reassessment")
        icon = "🔄" if is_last else "📖"
        bg = "#f0fdf4" if is_last else "#f7f8fa"
        border = "#86efac" if is_last else "#e5e7eb"
        st.markdown(
            f"""
            <div style="background:{bg};border:1px solid {border};border-radius:8px;
                        padding:10px 16px;margin-bottom:6px;display:flex;align-items:center;">
                <span style="background:#3b82f6;color:#fff;border-radius:50%;
                             width:24px;height:24px;display:inline-flex;align-items:center;
                             justify-content:center;font-size:0.75em;font-weight:700;
                             margin-right:12px;flex-shrink:0;">{i}</span>
                <span>{icon} {step}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Resources
    if path.get("resources"):
        st.markdown("### 📖 Recommended Resources")
        for res in path["resources"]:
            st.markdown(f"• {res}")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("✏️ Go to Practice Questions", type="primary", use_container_width=True):
            set_session("page", "Practice")
            st.rerun()
    with col_b:
        if st.button("📊 View My Learning Profile", use_container_width=True):
            set_session("page", "Learning Profile")
            st.rerun()
