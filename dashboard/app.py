"""
Interactive Academic Analytics & Dropout Intervention Dashboard.
Fulfills Assignment Part 1 & Part 2 Requirements:
- 5 comprehensive views:
    1. Executive Summary & KPIs
    2. Attendance vs. Marks Correlation Analysis
    3. Subject-wise & Semester Performance Distribution
    4. High-Risk Student Watchlist & Intervention Queue
    5. Individual Student Profile & Real-Time MLOps Risk Simulator
"""

from pathlib import Path
import sys
import joblib
import numpy as np
import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import ANALYTICS_DATA_DIR, MODELS_DIR

# Page Configuration
st.set_page_config(
    page_title="Student Performance & Dropout Risk Analytics",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Sleek Dark Mode Styling
st.markdown("""
<style>
    /* Dark Theme Core Styles */
    .stApp {
        background: linear-gradient(180deg, #0B0F19 0%, #111827 100%);
        color: #F8FAFC;
    }

    /* Sleek Card Styling for Metrics */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(8px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }

    /* Metric Labels & Values */
    div[data-testid="stMetricLabel"] p {
        color: #94A3B8 !important;
        font-weight: 500;
        font-size: 0.88rem;
    }
    div[data-testid="stMetricValue"] {
        color: #F8FAFC !important;
        font-weight: 700;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* Headings Gradient */
    h1, h2, h3 {
        color: #F1F5F9;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* Styled Containers & Cards */
    .stAlert {
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.2rem;
        box-shadow: 0 4px 14px 0 rgba(79, 70, 229, 0.39);
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #4338CA 0%, #4F46E5 100%);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.5);
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    mart_file = ANALYTICS_DATA_DIR / "student_risk_mart.csv"
    if mart_file.exists():
        df = pd.read_csv(mart_file)
        return df
    else:
        st.error(f"Data mart not found at {mart_file}. Please run the ETL pipeline first!")
        return pd.DataFrame()


@st.cache_resource
def load_mlops_artifacts():
    champion_path = MODELS_DIR / "champion_model.joblib"
    preprocessor_path = MODELS_DIR / "feature_preprocessor.joblib"
    if champion_path.exists() and preprocessor_path.exists():
        model = joblib.load(champion_path)
        preproc = joblib.load(preprocessor_path)
        return model, preproc
    return None, None


df = load_data()
model, preprocessor = load_mlops_artifacts()

# Sidebar
st.sidebar.title("🎓 Academic Analytics")
st.sidebar.markdown("**Course**: Data Engineering & MLOps")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navigation Views",
    [
        "1. Executive Overview & KPIs",
        "2. Attendance vs Marks Analysis",
        "3. Subject & Semester Distribution",
        "4. High-Risk Student Watchlist",
        "5. Student Profile & MLOps Simulator",
    ],
)

if df.empty:
    st.warning("Please execute the ETL pipeline (`python etl/pipeline_runner.py`) to generate analytical tables.")
    st.stop()

# ====================================================================
# VIEW 1: EXECUTIVE OVERVIEW & KPIS
# ====================================================================
if menu == "1. Executive Overview & KPIs":
    st.title("📊 Executive Academic Analytics Overview")
    st.markdown("High-level institutional insights across student performance, engagement, and dropout vulnerability.")

    total_students = len(df)
    high_risk_count = (df["dropout_risk"] == 1).sum()
    high_risk_pct = (high_risk_count / total_students) * 100.0
    avg_att = df["attendance_percentage"].mean()
    avg_marks = df["average_internal_marks"].mean()
    avg_lms_hrs = df["avg_weekly_learning_hours"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Cohort", f"{total_students:,}")
    col2.metric("At-Risk Students", f"{high_risk_count}", f"{high_risk_pct:.1f}%", delta_color="inverse")
    col3.metric("Avg Attendance", f"{avg_att:.1f}%")
    col4.metric("Avg Internal Mark", f"{avg_marks:.1f}/100")
    col5.metric("Avg LMS Hours/Wk", f"{avg_lms_hrs:.1f} hrs")

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Cohort Risk Distribution")
        risk_counts = df["risk_category"].value_counts().reset_index()
        risk_counts.columns = ["Status", "Count"]
        st.bar_chart(risk_counts.set_index("Status"))

    with c2:
        st.subheader("Internal Assessment Score Spread")
        st.area_chart(df["average_internal_marks"])

# ====================================================================
# VIEW 2: ATTENDANCE VS. MARKS ANALYSIS
# ====================================================================
elif menu == "2. Attendance vs Marks Analysis":
    st.title("📈 Attendance vs. Academic Marks Analysis")
    st.markdown("Exploring the critical relationship between lecture presence and examination scores.")

    col1, col2 = st.columns([3, 1])

    with col2:
        st.subheader("Quadrant Filters")
        att_threshold = st.slider("Attendance Warning Threshold (%)", 50, 90, 75)
        marks_threshold = st.slider("Passing Marks Threshold (%)", 40, 75, 50)
        gender_filter = st.multiselect("Gender Filter", options=df["gender"].unique(), default=list(df["gender"].unique()))

    filtered_df = df[df["gender"].isin(gender_filter)]

    with col1:
        corr = filtered_df["attendance_percentage"].corr(filtered_df["average_internal_marks"])
        st.info(f"**Statistical Pearson Correlation:** {corr:.3f} (Indicates strong positive coupling between attendance and grades)")

        # Quadrant classification
        chart_data = filtered_df[["attendance_percentage", "average_internal_marks", "student_id"]].copy()
        st.scatter_chart(
            chart_data,
            x="attendance_percentage",
            y="average_internal_marks",
            color=None,
        )

    st.markdown("### Critical Quadrant Breakdown")
    danger_zone = filtered_df[(filtered_df["attendance_percentage"] < att_threshold) & (filtered_df["average_internal_marks"] < marks_threshold)]
    st.warning(f"🚨 **Danger Quadrant:** {len(danger_zone)} students have both sub-{att_threshold}% attendance AND sub-{marks_threshold} marks.")

# ====================================================================
# VIEW 3: SUBJECT & SEMESTER DISTRIBUTION
# ====================================================================
elif menu == "3. Subject & Semester Distribution":
    st.title("📚 Subject-wise & Semester Performance Distribution")
    st.markdown("Comparative performance analysis across curriculum modules and academic terms.")

    sub_file = ANALYTICS_DATA_DIR / "subject_performance_summary.csv"
    sem_file = ANALYTICS_DATA_DIR / "semester_performance_summary.csv"

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Course Average & Pass Rates")
        if sub_file.exists():
            sub_df = pd.read_csv(sub_file)
            st.dataframe(sub_df, use_container_width=True)
            st.bar_chart(sub_df.set_index("course_code")["course_pass_rate"])
        else:
            st.info("Subject summary table ready in analytics mart.")

    with c2:
        st.subheader("Semester Progression")
        if sem_file.exists():
            sem_df = pd.read_csv(sem_file)
            st.dataframe(sem_df, use_container_width=True)
            st.line_chart(sem_df.set_index("semester")["semester_avg_mark"])
        else:
            st.info("Semester summary table ready in analytics mart.")

# ====================================================================
# VIEW 4: HIGH-RISK STUDENT WATCHLIST
# ====================================================================
elif menu == "4. High-Risk Student Watchlist":
    st.title("🚨 High-Risk Student Early Intervention Watchlist")
    st.markdown("Actionable cohort tracking table for academic advisors and counselors.")

    col1, col2, col3 = st.columns(3)
    with col1:
        only_risk = st.checkbox("Show Only High-Risk Students", value=True)
    with col2:
        min_fail = st.selectbox("Minimum Historical Failures", [0, 1, 2, 3], index=0)
    with col3:
        search_id = st.text_input("Search Student ID", "")

    watchlist = df.copy()
    if only_risk:
        watchlist = watchlist[watchlist["dropout_risk"] == 1]
    if min_fail > 0:
        watchlist = watchlist[watchlist["failures"] >= min_fail]
    if search_id:
        watchlist = watchlist[watchlist["student_id"].str.contains(search_id, case=False, na=False)]

    columns_to_show = [
        "student_id", "gender", "age", "attendance_percentage",
        "average_internal_marks", "assignment_completion_rate",
        "avg_weekly_learning_hours", "failures", "risk_category"
    ]
    st.dataframe(watchlist[columns_to_show], use_container_width=True)

    csv_data = watchlist.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export At-Risk Cohort (CSV)",
        data=csv_data,
        file_name="high_risk_intervention_list.csv",
        mime="text/csv",
    )

# ====================================================================
# VIEW 5: STUDENT PROFILE & MLOPS INTERVENTION SIMULATOR
# ====================================================================
elif menu == "5. Student Profile & MLOps Simulator":
    st.title("🔮 Student Profile & Real-Time Intervention Simulator")
    st.markdown("Integrates the trained MLOps champion model to simulate the impact of proactive academic interventions.")

    student_list = df["student_id"].tolist()
    selected_stu = st.selectbox("Select Student Profile:", student_list)

    stu_row = df[df["student_id"] == selected_stu].iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Current Attendance", f"{stu_row['attendance_percentage']}%")
    c2.metric("Current Marks", f"{stu_row['average_internal_marks']}/100")
    c3.metric("Current Status", f"{stu_row['risk_category']}")

    st.markdown("### Proactive Intervention Simulator")
    st.markdown("Adjust parameters to test how remedial tutoring, mentoring, and attendance counseling alter predicted risk:")

    sim_col1, sim_col2 = st.columns(2)
    with sim_col1:
        sim_att = st.slider("Simulated Attendance (%)", 0.0, 100.0, float(stu_row["attendance_percentage"]))
        sim_marks = st.slider("Simulated Internal Score (%)", 0.0, 100.0, float(stu_row["average_internal_marks"]))
        sim_studytime = st.selectbox("Simulated Study Time Level (1-4)", [1, 2, 3, 4], index=int(stu_row["studytime"])-1)

    with sim_col2:
        sim_assignments = st.slider("Simulated Assignment Rate (%)", 0.0, 100.0, float(stu_row["assignment_completion_rate"]))
        sim_hours = st.slider("Weekly LMS Hours", 0.0, 30.0, float(stu_row["avg_weekly_learning_hours"]))
        sim_famsup = st.selectbox("Family/Mentorship Support", ["yes", "no"], index=0 if stu_row.get("famsup", "yes") == "yes" else 1)

    if st.button("🚀 Run Live MLOps Risk Inference", type="primary"):
        if model is not None and preprocessor is not None:
            # Build input payload
            sim_input = pd.DataFrame([{
                "age": int(stu_row["age"]),
                "studytime": int(sim_studytime),
                "failures": int(stu_row["failures"]),
                "attendance_percentage": float(sim_att),
                "average_internal_marks": float(sim_marks),
                "assignment_completion_rate": float(sim_assignments),
                "avg_weekly_learning_hours": float(sim_hours),
                "previous_score_trend": float(stu_row.get("previous_score_trend", sim_marks)),
                "gender": str(stu_row.get("gender", "M")),
                "address": str(stu_row.get("address", "U")),
                "famsize": str(stu_row.get("famsize", "GT3")),
                "Pstatus": str(stu_row.get("Pstatus", "T")),
                "schoolsup": str(stu_row.get("schoolsup", "no")),
                "famsup": str(sim_famsup),
                "paid": str(stu_row.get("paid", "no")),
                "activities": str(stu_row.get("activities", "yes")),
                "internet": str(stu_row.get("internet", "yes")),
            }])

            # Transform & Predict
            sim_trans = preprocessor.transform(sim_input)
            pred = int(model.predict(sim_trans)[0])
            prob = float(model.predict_proba(sim_trans)[0][1]) if hasattr(model, "predict_proba") else float(pred)

            st.markdown("---")
            res_col1, res_col2 = st.columns(2)
            with res_col1:
                if pred == 1:
                    st.error(f"### Predicted Outcome: HIGH DROPOUT RISK\n**Probability:** {prob*100:.1f}%")
                else:
                    st.success(f"### Predicted Outcome: LOW RISK (ON TRACK)\n**Dropout Probability:** {prob*100:.1f}%")

            with res_col2:
                st.markdown("**Intervention Prescription:**")
                if prob > 0.40:
                    st.write("⚠️ Urgent intervention recommended: Schedule mandatory 1-on-1 tutoring and peer study group.")
                else:
                    st.write("✅ Student metrics are stabilized. Routine semester advising is sufficient.")
        else:
            st.error("ML model artifacts not loaded. Ensure `python mlops/train.py` has been executed.")
