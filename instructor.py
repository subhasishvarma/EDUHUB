from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from .models import db, Course, CourseVideo, CourseNote, CourseOnlineBook

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
    # Your ZIP admin mapping likely creates current_user.courses relationship.
    return any(c.course_id == course_id for c in getattr(current_user, "courses", []))


@instructor.route('/dashboard')
@login_required
@instructor_required
def dashboard():
    courses = getattr(current_user, "courses", [])
    return render_template('instructor/dashboard.html', courses=courses)


@instructor.route('/course/<int:course_id>')
@login_required
@instructor_required
def course_detail(course_id):
    if not _is_assigned(course_id):
        flash("You are not assigned to this course.")
        return redirect(url_for('instructor.dashboard'))

    course = Course.query.get_or_404(course_id)

    videos = CourseVideo.query.filter_by(course_id=course_id).all()
    notes = CourseNote.query.filter_by(course_id=course_id).all()
    books = CourseOnlineBook.query.filter_by(course_id=course_id).all()

    return render_template(
        'instructor/course_detail.html',
        course=course,
        videos=videos,
        notes=notes,
        books=books
    )


# ------------------ ADD VIDEO ------------------
@instructor.route('/course/<int:course_id>/videos/add', methods=['POST'])
@login_required
@instructor_required
def add_video(course_id):
    if not _is_assigned(course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    video_url = request.form.get('video_url', '').strip()
    title = request.form.get('title', '').strip()
    duration = request.form.get('duration_minutes', '').strip()

    if not video_url or not title or not duration:
        flash("All video fields are required.")
        return redirect(url_for('instructor.course_detail', course_id=course_id))

    try:
        db.session.add(CourseVideo(
            course_id=course_id,
            video_url=video_url,
            title=title,
            duration_minutes=int(duration)
        ))
        db.session.commit()
        flash("Video added successfully.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding video: {e}")

    return redirect(url_for('instructor.course_detail', course_id=course_id))


@instructor.route('/course/<int:course_id>/videos/delete', methods=['POST'])
@login_required
@instructor_required
def delete_video(course_id):
    if not _is_assigned(course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    video_url = request.form.get('video_url')
    try:
        item = CourseVideo.query.filter_by(course_id=course_id, video_url=video_url).first()
        if item:
            db.session.delete(item)
            db.session.commit()
            flash("Video deleted.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting video: {e}")

    return redirect(url_for('instructor.course_detail', course_id=course_id))


# ------------------ ADD NOTE ------------------
@instructor.route('/course/<int:course_id>/notes/add', methods=['POST'])
@login_required
@instructor_required
def add_note(course_id):
    if not _is_assigned(course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    note_url = request.form.get('note_url', '').strip()
    title = request.form.get('title', '').strip()
    fmt = request.form.get('format', 'PDF').strip()

    if not note_url or not title:
        flash("Note URL and title are required.")
        return redirect(url_for('instructor.course_detail', course_id=course_id))

    try:
        db.session.add(CourseNote(
            course_id=course_id,
            note_url=note_url,
            title=title,
            format=fmt or 'PDF'
        ))
        db.session.commit()
        flash("Note added successfully.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding note: {e}")

    return redirect(url_for('instructor.course_detail', course_id=course_id))


@instructor.route('/course/<int:course_id>/notes/delete', methods=['POST'])
@login_required
@instructor_required
def delete_note(course_id):
    if not _is_assigned(course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    note_url = request.form.get('note_url')
    try:
        item = CourseNote.query.filter_by(course_id=course_id, note_url=note_url).first()
        if item:
            db.session.delete(item)
            db.session.commit()
            flash("Note deleted.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting note: {e}")

    return redirect(url_for('instructor.course_detail', course_id=course_id))


# ------------------ ADD BOOK ------------------
@instructor.route('/course/<int:course_id>/books/add', methods=['POST'])
@login_required
@instructor_required
def add_book(course_id):
    if not _is_assigned(course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    book_url = request.form.get('book_url', '').strip()
    title = request.form.get('title', '').strip()
    page_count = request.form.get('page_count', '').strip()

    if not book_url or not title:
        flash("Book URL and title are required.")
        return redirect(url_for('instructor.course_detail', course_id=course_id))

    try:
        db.session.add(CourseOnlineBook(
            course_id=course_id,
            book_url=book_url,
            title=title,
            page_count=int(page_count) if page_count else None
        ))
        db.session.commit()
        flash("Book added successfully.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding book: {e}")

    return redirect(url_for('instructor.course_detail', course_id=course_id))


@instructor.route('/course/<int:course_id>/books/delete', methods=['POST'])
@login_required
@instructor_required
def delete_book(course_id):
    if not _is_assigned(course_id):
        flash("Unauthorized.")
        return redirect(url_for('instructor.dashboard'))

    book_url = request.form.get('book_url')
    try:
        item = CourseOnlineBook.query.filter_by(course_id=course_id, book_url=book_url).first()
        if item:
            db.session.delete(item)
            db.session.commit()
            flash("Book deleted.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting book: {e}")

    return redirect(url_for('instructor.course_detail', course_id=course_id))
