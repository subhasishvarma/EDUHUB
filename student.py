from functools import wraps
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)
from flask_login import login_required, current_user
from sqlalchemy import func

from .models import db, Student, Course, Enrollment, University


student = Blueprint("student", __name__, url_prefix="/student")


def student_required(f):
    """Decorator to ensure only students can access these routes."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        role = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )
        if role != "student":
            return redirect(url_for("main.profile"))
        return f(*args, **kwargs)

    return decorated


@student.route("/dashboard")
@login_required
@student_required
def dashboard():
    """Student dashboard showing enrolled courses and student info."""

    # Get student's enrolled courses with course and university details
    enrolled_courses = (
        db.session.query(Course, Enrollment, University)
        .join(Enrollment, Course.course_id == Enrollment.course_id)
        .join(University, Course.uni_id == University.uni_id)
        .filter(Enrollment.student_id == current_user.user_id)
        .all()
    )

    # Get student object for additional info
    student_info = Student.query.get(current_user.user_id)

    return render_template(
        "student/dashboard.html",
        enrolled_courses=enrolled_courses,
        student=student_info,
    )


@student.route("/grades")
@login_required
@student_required
def grades():
    """View all grades for enrolled courses."""

    # Get enrollments with course details and grades
    enrollments = (
        db.session.query(Course, Enrollment, University)
        .join(Enrollment, Course.course_id == Enrollment.course_id)
        .join(University, Course.uni_id == University.uni_id)
        .filter(Enrollment.student_id == current_user.user_id)
        .all()
    )

    # Calculate GPA (assuming grades are out of 100)
    total_grades = 0
    count = 0
    for course, enrollment, university in enrollments:
        if enrollment.grade:
            total_grades += float(enrollment.grade)
            count += 1

    gpa = round(total_grades / count, 2) if count > 0 else 0

    return render_template(
        "student/grades.html",
        enrollments=enrollments,
        gpa=gpa,
    )


@student.route("/explore-courses")
@login_required
@student_required
def explore_courses():
    """Browse all available courses and enroll."""

    # Get all courses with university details
    all_courses = (
        db.session.query(Course, University)
        .join(University, Course.uni_id == University.uni_id)
        .all()
    )

    # Get list of course IDs the student is already enrolled in
    enrolled_course_ids = (
        db.session.query(Enrollment.course_id)
        .filter(Enrollment.student_id == current_user.user_id)
        .all()
    )
    enrolled_course_ids = [cid[0] for cid in enrolled_course_ids]

    return render_template(
        "student/explore_courses.html",
        all_courses=all_courses,
        enrolled_course_ids=enrolled_course_ids,
    )


@student.route("/enroll/<int:course_id>", methods=["POST"])
@login_required
@student_required
def enroll(course_id):
    """Enroll in a course."""

    # Check if course exists
    course = Course.query.get(course_id)
    if not course:
        flash("Course not found.")
        return redirect(url_for("student.explore_courses"))

    # Check if already enrolled
    existing_enrollment = Enrollment.query.filter_by(
        student_id=current_user.user_id,
        course_id=course_id,
    ).first()

    if existing_enrollment:
        flash("You are already enrolled in this course.")
        return redirect(url_for("student.explore_courses"))

    # Create new enrollment
    new_enrollment = Enrollment(
        student_id=current_user.user_id,
        course_id=course_id,
    )

    db.session.add(new_enrollment)
    try:
        db.session.commit()
        flash(f"Successfully enrolled in {course.course_name}!")
    except Exception as e:
        db.session.rollback()
        flash(f"Error enrolling in course: {str(e)}")

    return redirect(url_for("student.dashboard"))


@student.route("/unenroll/<int:course_id>", methods=["POST"])
@login_required
@student_required
def unenroll(course_id):
    """Unenroll from a course."""

    enrollment = Enrollment.query.filter_by(
        student_id=current_user.user_id,
        course_id=course_id,
    ).first()

    if not enrollment:
        flash("You are not enrolled in this course.")
        return redirect(url_for("student.dashboard"))

    db.session.delete(enrollment)
    try:
        db.session.commit()
        flash("Successfully unenrolled from course.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error unenrolling: {str(e)}")

    return redirect(url_for("student.dashboard"))


@student.route("/course/<int:course_id>")
@login_required
@student_required
def course_detail(course_id):
    """View details of an enrolled course."""

    # Check if student is enrolled
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.user_id,
        course_id=course_id,
    ).first()

    if not enrollment:
        flash("You must be enrolled in this course to view it.")
        return redirect(url_for("student.explore_courses"))

    # Get course with all details
    course = Course.query.get(course_id)
    university = University.query.get(course.uni_id)

    # Get course materials
    videos = course.videos
    notes = course.notes
    books = course.online_books
    instructors = course.instructors

    # Get topics and textbooks
    topics = course.topics
    textbooks = course.textbooks

    return render_template(
        "student/course_detail.html",
        course=course,
        university=university,
        enrollment=enrollment,
        videos=videos,
        notes=notes,
        books=books,
        instructors=instructors,
        topics=topics,
        textbooks=textbooks,
    )

