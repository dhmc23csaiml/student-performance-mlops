"""
Synthetic Multi-Source Academic Dataset Generator.
Simulates:
1. Primary Historical Dataset (UCI Student Demographics & Background)
2. College ERP Attendance System Logs
3. LMS (Learning Management System / Moodle) Digital Activity Records
4. ERP Internal Assessment & Exam Marks

Injects controlled data-quality anomalies (duplicates, invalid marks, out-of-range values)
to validate the Data Quality & Rejection pipeline required by Assignment Part 1.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Ensure root is in path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import RAW_DATA_DIR

random.seed(42)

COURSES = [
    {"code": "CS101", "name": "Intro to Computer Science", "credits": 4, "dept": "Computer Science"},
    {"code": "DS201", "name": "Data Engineering Principles", "credits": 4, "dept": "Data Science"},
    {"code": "MA102", "name": "Linear Algebra & Calculus", "credits": 3, "dept": "Mathematics"},
    {"code": "SE301", "name": "Software Engineering & DevOps", "credits": 4, "dept": "Computer Science"},
]

SEMESTERS = [1, 2, 3, 4]


def generate_all_datasets(num_students: int = 600):
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[*] Generating academic records for {num_students} students across 4 sources...")

    # 1. Demographics & Background (UCI Style)
    demo_file = RAW_DATA_DIR / "uci_student_demographics.csv"
    students = []
    
    with open(demo_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "student_id", "gender", "age", "address", "famsize", "Pstatus",
            "Medu", "Fedu", "traveltime", "studytime", "failures",
            "schoolsup", "famsup", "paid", "activities", "internet", "health"
        ])

        for i in range(1, num_students + 1):
            # Standard ID format STU_10001
            stu_id = f"STU_{10000 + i}"
            gender = random.choice(["M", "F"])
            age = random.choices([17, 18, 19, 20, 21, 22, 23], weights=[0.05, 0.35, 0.30, 0.15, 0.10, 0.03, 0.02])[0]
            address = random.choice(["U", "R"])
            famsize = random.choice(["LE3", "GT3"])
            pstatus = random.choice(["T", "A"])
            medu = random.randint(0, 4)
            fedu = random.randint(0, 4)
            traveltime = random.choices([1, 2, 3, 4], weights=[0.55, 0.30, 0.10, 0.05])[0]
            studytime = random.choices([1, 2, 3, 4], weights=[0.25, 0.45, 0.20, 0.10])[0]
            failures = random.choices([0, 1, 2, 3], weights=[0.75, 0.15, 0.07, 0.03])[0]
            schoolsup = random.choice(["yes", "no"])
            famsup = random.choice(["yes", "no"])
            paid = random.choice(["yes", "no"])
            activities = random.choice(["yes", "no"])
            internet = random.choice(["yes", "no"])
            health = random.randint(1, 5)

            # Injected anomaly: unformatted ID for a couple of records
            if i == 50:
                stu_id = "10050"  # Missing prefix to test standardizer
            elif i == 51:
                age = 99  # Invalid age anomaly

            students.append(f"STU_{10000 + i}")
            writer.writerow([
                stu_id, gender, age, address, famsize, pstatus,
                medu, fedu, traveltime, studytime, failures,
                schoolsup, famsup, paid, activities, internet, health
            ])
            
    print(f"  [OK] Generated {demo_file.name}")

    # 2. College ERP Attendance System Logs
    att_file = RAW_DATA_DIR / "erp_attendance_logs.csv"
    start_date = datetime(2026, 1, 15)
    
    with open(att_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "attendance_id", "student_id", "course_code", "semester",
            "session_date", "session_type", "status"
        ])

        att_id = 1
        for stu_idx, stu_id in enumerate(students):
            # Base attendance probability: higher studytime & lower failures => better attendance
            base_prob = 0.82 + (0.05 if (stu_idx % 3 != 0) else -0.15)
            base_prob = max(0.40, min(0.98, base_prob))

            for course in COURSES:
                sem = random.choice(SEMESTERS)
                for day_offset in range(0, 30, 3):  # 10 sessions per course
                    session_date = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
                    session_type = "Lab" if (day_offset % 6 == 0) else "Lecture"
                    
                    status = "Present" if random.random() < base_prob else random.choice(["Absent", "Excused"])
                    
                    # Anomaly injection
                    if att_id == 250:
                        status = "Unknown_Status"  # Invalid status to test DQ

                    writer.writerow([
                        f"ATT_{att_id}", stu_id, course["code"], sem,
                        session_date, session_type, status
                    ])
                    att_id += 1

            # Injected duplicate record
            if stu_idx == 10:
                writer.writerow([
                    f"ATT_{att_id-1}", stu_id, COURSES[0]["code"], 1,
                    start_date.strftime("%Y-%m-%d"), "Lecture", "Present"
                ])

    print(f"  [OK] Generated {att_file.name} ({att_id} rows)")

    # 3. LMS (Learning Management System / Moodle) Logs
    lms_file = RAW_DATA_DIR / "lms_activity_submissions.csv"
    
    with open(lms_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "activity_id", "student_id", "course_code", "semester",
            "assignment_submissions", "quiz_attempts", "forum_posts",
            "lms_login_count", "learning_hours_weekly"
        ])

        for stu_idx, stu_id in enumerate(students):
            for course in COURSES:
                sem = random.choice(SEMESTERS)
                # Diligent vs struggling students
                is_struggling = (stu_idx % 5 == 0)
                
                assign_subs = random.randint(1, 4) if is_struggling else random.randint(4, 5)  # Out of 5
                quiz_attempts = random.randint(1, 3) if is_struggling else random.randint(4, 8)
                forum_posts = random.randint(0, 2) if is_struggling else random.randint(1, 10)
                logins = random.randint(10, 25) if is_struggling else random.randint(30, 80)
                weekly_hours = round(random.uniform(1.5, 4.0) if is_struggling else random.uniform(5.0, 15.0), 2)

                writer.writerow([
                    f"LMS_{stu_id}_{course['code']}", stu_id, course["code"], sem,
                    assign_subs, quiz_attempts, forum_posts, logins, weekly_hours
                ])

    print(f"  [OK] Generated {lms_file.name}")

    # 4. ERP Internal Assessment & Marks Logs
    marks_file = RAW_DATA_DIR / "erp_internal_marks.csv"
    
    with open(marks_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "mark_id", "student_id", "course_code", "semester",
            "assessment_name", "score_obtained", "max_score"
        ])

        mark_id = 1
        for stu_idx, stu_id in enumerate(students):
            is_high_risk = (stu_idx % 4 == 0)
            
            for course in COURSES:
                sem = random.choice(SEMESTERS)
                
                # 3 Continuous Assessments: Quiz (20), Midterm (30), Final (50)
                assessments = [
                    ("Quiz_1", 20, 8 if is_high_risk else 16, 4),
                    ("Midterm_Exam", 30, 12 if is_high_risk else 24, 6),
                    ("Assignment_1", 20, 9 if is_high_risk else 17, 3),
                    ("Final_Exam", 30, 11 if is_high_risk else 25, 5),
                ]
                
                for name, max_sc, mean_sc, std_sc in assessments:
                    sc = round(random.gauss(mean_sc, std_sc), 1)
                    sc = max(0.0, min(float(max_sc), sc))
                    
                    # Injected anomaly
                    if mark_id == 100:
                        sc = -15.0  # Impossible negative score
                    elif mark_id == 101:
                        sc = 150.0  # Impossible score > max_score

                    writer.writerow([
                        f"MRK_{mark_id}", stu_id, course["code"], sem,
                        name, sc, max_sc
                    ])
                    mark_id += 1

    print(f"  [OK] Generated {marks_file.name} ({mark_id} rows)")
    print("[*] Dataset generation complete. All 4 sources ready in data/raw/.\n")


if __name__ == "__main__":
    generate_all_datasets()
