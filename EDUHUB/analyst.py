from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from sqlalchemy import func

from .models import (
    db,
    Course,
    University,
    Enrollment,
    Student,
    Instructor,
    course_instructors
)

# -------------------------------------------------
# Blueprint
# -------------------------------------------------
analyst = Blueprint("analyst", __name__, url_prefix="/analyst")


def analyst_only():
    if not current_user.is_authenticated or current_user.role != "analyst":
        abort(403)


# -------------------------------------------------
# Dashboard
# -------------------------------------------------
@analyst.route("/dashboard")
@login_required
def dashboard():
    analyst_only()

    stats = {
        "students": Student.query.count(),
        "instructors": Instructor.query.count(),
        "courses": Course.query.count(),
        "enrollments": Enrollment.query.count(),
    }

    return render_template(
        "analyst/dashboard.html",
        stats=stats
    )


# -------------------------------------------------
# Course performance (ALL COURSES)
# -------------------------------------------------
@analyst.route("/courses")
@login_required
def course_analysis():
    analyst_only()

    courses = (
        db.session.query(
            Course.course_id,
            Course.course_name,
            University.uni_name,
            func.count(Enrollment.student_id).label("enrollments"),
            func.round(func.avg(Enrollment.marks), 2).label("avg_marks"),
        )
        .join(University, Course.uni_id == University.uni_id)
        .outerjoin(Enrollment, Enrollment.course_id == Course.course_id)
        .group_by(Course.course_id, University.uni_name)
        .order_by(Course.course_name)
        .all()
    )

    return render_template(
        "analyst/course_performance.html",
        courses=courses
    )


# -------------------------------------------------
# Course detail
# -------------------------------------------------
@analyst.route("/courses/<int:course_id>")
@login_required
def course_detail(course_id):
    analyst_only()

    # ---- Course summary ----
    course = (
        db.session.query(
            Course.course_name,
            University.uni_name,
            func.count(Enrollment.student_id).label("enrollments"),
            func.round(func.avg(Enrollment.marks), 2).label("avg_marks"),
            func.round(func.min(Enrollment.marks), 2).label("min_marks"),
            func.round(func.max(Enrollment.marks), 2).label("max_marks"),
        )
        .join(University, Course.uni_id == University.uni_id)
        .outerjoin(Enrollment, Enrollment.course_id == Course.course_id)
        .filter(Course.course_id == course_id)
        .group_by(Course.course_id, University.uni_name)
        .first()
    )

    # ---- Marks distribution ----
    marks_dist = (
        db.session.query(
            Enrollment.marks,
            func.count(Enrollment.student_id)
        )
        .filter(Enrollment.course_id == course_id)
        .filter(Enrollment.marks.isnot(None))
        .group_by(Enrollment.marks)
        .order_by(Enrollment.marks)
        .all()
    )

    marks = [float(m[0]) for m in marks_dist]
    counts = [m[1] for m in marks_dist]

    return render_template(
        "analyst/course_detail.html",
        course=course,
        marks=marks,
        counts=counts
    )


# -------------------------------------------------
# Instructor performance
# -------------------------------------------------
@analyst.route("/instructors")
@login_required
def instructor_performance():
    analyst_only()

    instructors = (
        db.session.query(
            Instructor.user_id,
            Instructor.first_name,
            Instructor.last_name,
            func.count(func.distinct(Course.course_id)).label("courses"),
            func.count(Enrollment.student_id).label("students"),
            func.round(func.avg(Enrollment.marks), 2).label("avg_marks"),
        )
        .join(
            course_instructors,
            course_instructors.c.instructor_id == Instructor.user_id
        )
        .join(
            Course,
            Course.course_id == course_instructors.c.course_id
        )
        .outerjoin(
            Enrollment,
            Enrollment.course_id == Course.course_id
        )
        .group_by(
            Instructor.user_id,
            Instructor.first_name,
            Instructor.last_name
        )
        .order_by(Instructor.first_name)
        .all()
    )

    return render_template(
        "analyst/instructor_performance.html",
        instructors=instructors
    )
@analyst.route("/students")
@login_required
def student_performance():
    analyst_only()

    # ---- Average marks per student (ALL subjects) ----
    students = (
        db.session.query(
            Student.user_id,
            Student.first_name,
            Student.last_name,
            func.round(func.avg(Enrollment.marks), 2).label("avg_marks")
        )
        .outerjoin(Enrollment, Enrollment.student_id == Student.user_id)
        .group_by(Student.user_id, Student.first_name, Student.last_name)
        .order_by(Student.first_name)
        .all()
    )

    # ---- Per-course marks for each student ----
    student_courses = (
        db.session.query(
            Student.user_id,
            Course.course_name,
            Enrollment.marks
        )
        .join(Enrollment, Enrollment.student_id == Student.user_id)
        .join(Course, Course.course_id == Enrollment.course_id)
        .order_by(Student.user_id, Course.course_name)
        .all()
    )

    return render_template(
        "analyst/student_performance.html",
        students=students,
        student_courses=student_courses
    )
@analyst.route("/universities")
@login_required
def university_performance():
    analyst_only()

    # ---- University summary ----
    universities = (
        db.session.query(
            University.uni_id,
            University.uni_name,
            func.count(func.distinct(Course.course_id)).label("total_courses"),
            func.count(func.distinct(Enrollment.student_id)).label("total_students"),
            func.round(func.avg(Enrollment.marks), 2).label("avg_marks")
        )
        .outerjoin(Course, Course.uni_id == University.uni_id)
        .outerjoin(Enrollment, Enrollment.course_id == Course.course_id)
        .group_by(University.uni_id, University.uni_name)
        .order_by(University.uni_name)
        .all()
    )

    # ---- Course-level details ----
    courses = (
        db.session.query(
            University.uni_id,
            Course.course_id,
            Course.course_name,
            Course.duration_weeks,
            func.count(Enrollment.student_id).label("students"),
            func.round(func.avg(Enrollment.marks), 2).label("avg_marks"),
            func.max(Enrollment.due_by).label("due_by")
        )
        .join(Course, Course.uni_id == University.uni_id)
        .outerjoin(Enrollment, Enrollment.course_id == Course.course_id)
        .group_by(
            University.uni_id,
            Course.course_id,
            Course.course_name,
            Course.duration_weeks
        )
        .order_by(Course.course_name)
        .all()
    )

    # ---- Instructors per course ----
    instructors = (
        db.session.query(
            Course.course_id,
            Instructor.first_name,
            Instructor.last_name
        )
        .join(course_instructors, course_instructors.c.instructor_id == Instructor.user_id)
        .join(Course, Course.course_id == course_instructors.c.course_id)
        .all()
    )

    return render_template(
        "analyst/university_performance.html",
        universities=universities,
        courses=courses,
        instructors=instructors
    )
