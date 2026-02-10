from functools import wraps
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from sqlalchemy import func

from .models import (
    db,
    Course,
    Student,
    Enrollment,
    CourseModule,
    ModuleTopic,
    TopicSubtopic,
    SubtopicContent,
    TopicAssignment,
    DeregistrationRequest,
)

instructor = Blueprint('instructor', __name__, url_prefix='/instructor')


def instructor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        if role != 'instructor':
            flash("Not authorized.")
            return redirect(url_for('main.profile'))
        return f(*args, **kwargs)
    return decorated


def _is_assigned(course_id: int) -> bool:
    return any(c.course_id == course_id for c in getattr(current_user, "courses", []))


@instructor.route('/dashboard')
@login_required
@instructor_required
def dashboard():
    courses = getattr(current_user, "courses", [])
    return render_template('instructor/dashboard.html', courses=courses)


# ------------------------------------------------------------
# Course page (Modules + Students)
# ------------------------------------------------------------
@instructor.route('/course/<int:course_id>')
@login_required
@instructor_required
def course_detail(course_id):
    if not _is_assigned(course_id):
        flash("You are not assigned to this course.")
        return redirect(url_for('instructor.dashboard'))

    course = Course.query.get_or_404(course_id)

    modules = (
        CourseModule.query
        .filter_by(course_id=course_id)
        .order_by(CourseModule.module_order.asc(), CourseModule.module_id.asc())
        .all()
    )

    enrollments = (
        Enrollment.query
        .filter_by(course_id=course_id)
        .join(Student, Student.user_id == Enrollment.student_id)
        .all()
    )

    tab = request.args.get('tab', 'modules')

    return render_template(
        'instructor/course_detail.html',
        course=course,
        modules=modules,
        enrollments=enrollments,
        tab=tab
    )


# ------------------------------------------------------------
# MODULES CRUD (NO ORDER INPUT: auto order)
# ------------------------------------------------------------
@instructor.route('/course/<int:course_id>/modules/add', methods=['POST'])
@login_required
@instructor_required
def add_module(course_id):
    if not _is_assigned(course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    title = request.form.get('module_title', '').strip()
    if not title:
        flash("Module title is required.")
        return redirect(url_for('instructor.course_detail', course_id=course_id, tab='modules'))

    max_order = (
        db.session.query(func.max(CourseModule.module_order))
        .filter(CourseModule.course_id == course_id)
        .scalar()
    )
    next_order = (max_order or 0) + 1

    try:
        db.session.add(CourseModule(
            course_id=course_id,
            module_title=title,
            module_order=next_order
        ))
        db.session.commit()
        flash("Module added.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding module: {e}")

    return redirect(url_for('instructor.course_detail', course_id=course_id, tab='modules'))


@instructor.route('/modules/<int:module_id>/delete', methods=['POST'])
@login_required
@instructor_required
def delete_module(module_id):
    mod = CourseModule.query.get_or_404(module_id)
    if not _is_assigned(mod.course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    try:
        db.session.delete(mod)
        db.session.commit()
        flash("Module deleted.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting module: {e}")

    return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))


# ------------------------------------------------------------
# TOPIC CRUD (NO ORDER INPUT: auto order)
# ------------------------------------------------------------
@instructor.route('/modules/<int:module_id>/topics/add', methods=['POST'])
@login_required
@instructor_required
def add_topic(module_id):
    mod = CourseModule.query.get_or_404(module_id)
    if not _is_assigned(mod.course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    title = request.form.get('topic_title', '').strip()
    if not title:
        flash("Topic title is required.")
        return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))

    max_order = (
        db.session.query(func.max(ModuleTopic.topic_order))
        .filter(ModuleTopic.module_id == module_id)
        .scalar()
    )
    next_order = (max_order or 0) + 1

    try:
        db.session.add(ModuleTopic(
            module_id=module_id,
            topic_title=title,
            topic_order=next_order
        ))
        db.session.commit()
        flash("Topic added.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding topic: {e}")

    return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))


@instructor.route('/topics/<int:topic_id>/delete', methods=['POST'])
@login_required
@instructor_required
def delete_topic(topic_id):
    t = ModuleTopic.query.get_or_404(topic_id)
    mod = CourseModule.query.get_or_404(t.module_id)
    if not _is_assigned(mod.course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    try:
        db.session.delete(t)
        db.session.commit()
        flash("Topic deleted.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting topic: {e}")

    return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))


@instructor.route('/topics/<int:topic_id>/assignments/add', methods=['POST'])
@login_required
@instructor_required
def add_assignment(topic_id):
    """Create an assignment under a specific topic."""
    t = ModuleTopic.query.get_or_404(topic_id)
    mod = CourseModule.query.get_or_404(t.module_id)

    if not _is_assigned(mod.course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    due_date_str = request.form.get('due_date', '').strip()

    if not title:
        flash("Assignment title is required.")
        return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))

    due_date_val = None
    if due_date_str:
        try:
            due_date_val = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid due date format.")
            return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))

    try:
        db.session.add(TopicAssignment(
            topic_id=topic_id,
            title=title,
            description=description or None,
            due_date=due_date_val,
        ))
        db.session.commit()
        flash("Assignment created.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating assignment: {e}")

    return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))


@instructor.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@login_required
@instructor_required
def delete_assignment(assignment_id):
    """Delete an assignment from a topic."""
    a = TopicAssignment.query.get_or_404(assignment_id)
    t = ModuleTopic.query.get_or_404(a.topic_id)
    mod = CourseModule.query.get_or_404(t.module_id)

    if not _is_assigned(mod.course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    try:
        db.session.delete(a)
        db.session.commit()
        flash("Assignment deleted.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting assignment: {e}")

    return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))


# ------------------------------------------------------------
# SUBTOPIC + FIRST CONTENT (UPDATED)
# - NO ORDER input
# - Adds Subtopic
# - Also adds a first content entry (video/notes/book) if provided
# ------------------------------------------------------------
@instructor.route('/topics/<int:topic_id>/subtopics/add', methods=['POST'])
@login_required
@instructor_required
def add_subtopic(topic_id):
    t = ModuleTopic.query.get_or_404(topic_id)
    mod = CourseModule.query.get_or_404(t.module_id)
    if not _is_assigned(mod.course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    subtopic_title = request.form.get('subtopic_title', '').strip()
    if not subtopic_title:
        flash("Subtopic title is required.")
        return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))

    # auto subtopic order
    max_st_order = (
        db.session.query(func.max(TopicSubtopic.subtopic_order))
        .filter(TopicSubtopic.topic_id == topic_id)
        .scalar()
    )
    next_st_order = (max_st_order or 0) + 1

    # optional first content
    content_type = request.form.get('content_type', '').strip()   # video/notes/book
    content_title = request.form.get('content_title', '').strip()
    url = request.form.get('url', '').strip()
    duration = request.form.get('duration_minutes', '').strip()
    file_format = request.form.get('file_format', '').strip()

    try:
        # Create subtopic first
        st = TopicSubtopic(
            topic_id=topic_id,
            subtopic_title=subtopic_title,
            subtopic_order=next_st_order
        )
        db.session.add(st)
        db.session.flush()  # get st.subtopic_id without commit

        # If user filled content type, create first content too
        if content_type:
            if content_type not in {'video', 'notes', 'book'}:
                raise ValueError("Invalid content type.")

            if not content_title:
                raise ValueError("Content title is required.")

            if not url:
                raise ValueError("URL is required.")

            dur_val = None
            fmt_val = None

            if content_type == 'video':
                if not duration:
                    raise ValueError("Minutes is required for Video.")
                dur_val = int(duration)
                if dur_val <= 0:
                    raise ValueError("Minutes must be positive.")

            if content_type == 'notes':
                fmt_val = file_format if file_format else "PDF"

            # auto content order within subtopic
            next_c_order = 1

            db.session.add(SubtopicContent(
                subtopic_id=st.subtopic_id,
                content_type=content_type,
                title=content_title,
                url=url,
                duration_minutes=dur_val,
                file_format=fmt_val,
                content_order=next_c_order
            ))

        db.session.commit()
        flash("Subtopic added." + (" Content added." if content_type else ""))

    except Exception as e:
        db.session.rollback()
        flash(f"Error adding subtopic/content: {e}")

    return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))


@instructor.route('/subtopics/<int:subtopic_id>/delete', methods=['POST'])
@login_required
@instructor_required
def delete_subtopic(subtopic_id):
    st = TopicSubtopic.query.get_or_404(subtopic_id)
    t = ModuleTopic.query.get_or_404(st.topic_id)
    mod = CourseModule.query.get_or_404(t.module_id)

    if not _is_assigned(mod.course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    try:
        db.session.delete(st)
        db.session.commit()
        flash("Subtopic deleted.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting subtopic: {e}")

    return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))


# ------------------------------------------------------------
# CONTENT CRUD (NO ORDER INPUT: auto order)
# ------------------------------------------------------------
@instructor.route('/subtopics/<int:subtopic_id>/contents/add', methods=['POST'])
@login_required
@instructor_required
def add_content(subtopic_id):
    st = TopicSubtopic.query.get_or_404(subtopic_id)
    t = ModuleTopic.query.get_or_404(st.topic_id)
    mod = CourseModule.query.get_or_404(t.module_id)

    if not _is_assigned(mod.course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    content_type = request.form.get('content_type', '').strip()
    title = request.form.get('title', '').strip()
    url = request.form.get('url', '').strip()
    duration = request.form.get('duration_minutes', '').strip()
    file_format = request.form.get('file_format', '').strip()

    if content_type not in {'video', 'notes', 'book'}:
        flash("Select Video / Notes / Online Book.")
        return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))

    if not title:
        flash("Title is required.")
        return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))

    if not url:
        flash("URL is required.")
        return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))

    dur_val = None
    fmt_val = None

    if content_type == 'video':
        if not duration:
            flash("Minutes is required for Video.")
            return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))
        try:
            dur_val = int(duration)
            if dur_val <= 0:
                raise ValueError
        except Exception:
            flash("Minutes must be a positive number.")
            return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))

    if content_type == 'notes':
        fmt_val = file_format if file_format else "PDF"

    # auto content order
    max_c_order = (
        db.session.query(func.max(SubtopicContent.content_order))
        .filter(SubtopicContent.subtopic_id == subtopic_id)
        .scalar()
    )
    next_c_order = (max_c_order or 0) + 1

    try:
        db.session.add(SubtopicContent(
            subtopic_id=subtopic_id,
            content_type=content_type,
            title=title,
            url=url,
            duration_minutes=dur_val,
            file_format=fmt_val,
            content_order=next_c_order
        ))
        db.session.commit()
        flash("Content added.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding content: {e}")

    return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))


@instructor.route('/contents/<int:content_id>/delete', methods=['POST'])
@login_required
@instructor_required
def delete_content(content_id):
    c = SubtopicContent.query.get_or_404(content_id)
    st = TopicSubtopic.query.get_or_404(c.subtopic_id)
    t = ModuleTopic.query.get_or_404(st.topic_id)
    mod = CourseModule.query.get_or_404(t.module_id)

    if not _is_assigned(mod.course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    try:
        db.session.delete(c)
        db.session.commit()
        flash("Content deleted.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting content: {e}")

    return redirect(url_for('instructor.course_detail', course_id=mod.course_id, tab='modules'))


# ------------------------------------------------------------
# STUDENTS + GRADING
# ------------------------------------------------------------
@instructor.route('/course/<int:course_id>/students/grade', methods=['POST'])
@login_required
@instructor_required
def grade_student(course_id):
    if not _is_assigned(course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    student_id = request.form.get('student_id')
    marks = request.form.get('marks', '').strip()
    letter_grade = request.form.get('letter_grade', '').strip()

    enr = Enrollment.query.filter_by(course_id=course_id, student_id=student_id).first()
    if not enr:
        flash("Enrollment not found.")
        return redirect(url_for('instructor.course_detail', course_id=course_id, tab='students'))

    try:
        enr.marks = float(marks) if marks else None
        enr.letter_grade = letter_grade or None
        db.session.commit()
        flash("Grade updated.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating grade: {e}")

    return redirect(url_for('instructor.course_detail', course_id=course_id, tab='students'))


@instructor.route('/course/<int:course_id>/students/deregister-request', methods=['POST'])
@login_required
@instructor_required
def request_deregistration(course_id):
    """Instructor requests that admin deregister a student from this course."""
    if not _is_assigned(course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    student_id = request.form.get('student_id')
    reason = request.form.get('reason', '').strip()

    if not student_id:
        flash("Student ID is required.")
        return redirect(url_for('instructor.course_detail', course_id=course_id, tab='students'))

    if not reason:
        flash("Please provide a reason for deregistration.")
        return redirect(url_for('instructor.course_detail', course_id=course_id, tab='students'))

    enr = Enrollment.query.filter_by(course_id=course_id, student_id=student_id).first()
    if not enr:
        flash("Enrollment not found.")
        return redirect(url_for('instructor.course_detail', course_id=course_id, tab='students'))

    try:
        # If there is already a pending request, just update the reason
        existing = (
            DeregistrationRequest.query
            .filter_by(student_id=student_id, course_id=course_id, status='pending')
            .first()
        )

        if existing:
            existing.reason = reason
            existing.instructor_id = current_user.user_id
        else:
            db.session.add(DeregistrationRequest(
                student_id=student_id,
                course_id=course_id,
                instructor_id=current_user.user_id,
                reason=reason,
                status='pending',
            ))

        db.session.commit()
        flash("Deregistration request sent to admin.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating deregistration request: {e}")

    return redirect(url_for('instructor.course_detail', course_id=course_id, tab='students'))
