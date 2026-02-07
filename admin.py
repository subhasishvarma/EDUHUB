from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from .models import db, User, Student, Instructor, Admin, Analyst, University, Course, Topic, Enrollment

admin = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to restrict access to admin users only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        if role != 'admin':
            return redirect(url_for('main.profile'))
        return f(*args, **kwargs)
    return decorated


def _safe_count(model, default=0):
    """Safely count model rows; return default if table missing or query fails."""
    try:
        return model.query.count()
    except Exception:
        return default


def _safe_query(query_fn, default=None):
    """Run a query and return default on failure."""
    try:
        return query_fn()
    except Exception:
        return default if default is not None else []


@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Stats - wrap in safe calls in case some tables don't exist yet
    stats = {
        'total_users': _safe_count(User),
        'total_students': _safe_count(Student),
        'total_instructors': _safe_count(Instructor),
        'total_admins': _safe_count(Admin),
        'total_analysts': _safe_count(Analyst),
        'total_universities': _safe_count(University),
        'total_courses': _safe_count(Course),
        'total_enrollments': _safe_count(Enrollment),
        'total_topics': _safe_count(Topic),
    }

    return render_template(
        'admin/dashboard.html',
        stats=stats,
    )


@admin.route('/students', methods=['GET', 'POST'])
@login_required
@admin_required
def students():
    items = _safe_query(lambda: Student.query.all(), default=[])
    if request.method == 'POST' and request.form.get('action') == 'delete':
        sid = request.form.get('student_id')
        if sid and sid != str(current_user.id):
            try:
                student = Student.query.get(int(sid))
                if student:
                    uid = student.id
                    db.session.delete(student)
                    user = User.query.get(uid)
                    if user:
                        db.session.delete(user)
                    db.session.commit()
                    flash('Student removed successfully.')
                else:
                    flash('Student not found.')
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {e}')
            return redirect(url_for('admin.students'))
        elif sid == str(current_user.id):
            flash('You cannot remove yourself.')
            return redirect(url_for('admin.students'))
    if request.method == 'POST' and request.form.get('action') == 'add':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        age = request.form.get('age')
        country = request.form.get('country')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
        elif User.query.filter_by(username=username).first():
            flash('Username already taken.')
        elif username and email and password and first_name:
            try:
                hashed = generate_password_hash(password, method='pbkdf2:sha256')
                s = Student(
                    username=username, email=email, password_hash=hashed,
                    first_name=first_name, last_name=last_name or None,
                    age=int(age) if age else None, skill_level='Beginner',
                    country=country or None, role='student'
                )
                db.session.add(s)
                db.session.commit()
                flash('Student added successfully.')
                return redirect(url_for('admin.students'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {e}')
        else:
            flash('Username, email, password, and first name are required.')
    return render_template('admin/students.html', items=items)


@admin.route('/instructors', methods=['GET', 'POST'])
@login_required
@admin_required
def instructors():
    items = _safe_query(lambda: Instructor.query.all(), default=[])
    if request.method == 'POST' and request.form.get('action') == 'delete':
        iid = request.form.get('instructor_id')
        if iid and iid != str(current_user.id):
            try:
                instructor = Instructor.query.get(int(iid))
                if instructor:
                    uid = instructor.id
                    db.session.delete(instructor)
                    user = User.query.get(uid)
                    if user:
                        db.session.delete(user)
                    db.session.commit()
                    flash('Instructor removed successfully.')
                else:
                    flash('Instructor not found.')
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {e}')
            return redirect(url_for('admin.instructors'))
        elif iid == str(current_user.id):
            flash('You cannot remove yourself.')
            return redirect(url_for('admin.instructors'))
    if request.method == 'POST' and request.form.get('action') == 'add':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone_number = request.form.get('phone_number')
        bio = request.form.get('bio')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
        elif User.query.filter_by(username=username).first():
            flash('Username already taken.')
        elif username and email and password and first_name:
            try:
                hashed = generate_password_hash(password, method='pbkdf2:sha256')
                i = Instructor(
                    username=username, email=email, password_hash=hashed,
                    first_name=first_name, last_name=last_name or None,
                    phone_number=phone_number or None, bio=bio or None,
                    role='instructor'
                )
                db.session.add(i)
                db.session.commit()
                flash('Instructor added successfully.')
                return redirect(url_for('admin.instructors'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {e}')
        else:
            flash('Username, email, password, and first name are required.')
    return render_template('admin/instructors.html', items=items)


@admin.route('/courses', methods=['GET', 'POST'])
@login_required
@admin_required
def courses():
    items = _safe_query(lambda: Course.query.all(), default=[])
    universities = _safe_query(lambda: University.query.all(), default=[])
    instructors_list = _safe_query(lambda: Instructor.query.all(), default=[])
    if request.method == 'POST' and request.form.get('action') == 'delete':
        cid = request.form.get('course_id')
        if cid:
            try:
                course = Course.query.get(int(cid))
                if course:
                    db.session.delete(course)
                    db.session.commit()
                    flash('Course removed successfully.')
                else:
                    flash('Course not found.')
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {e}')
            return redirect(url_for('admin.courses'))
    if request.method == 'POST' and request.form.get('action') == 'add_instructor':
        cid = request.form.get('course_id')
        iid = request.form.get('instructor_id')
        if cid and iid:
            try:
                course = Course.query.get(int(cid))
                instructor = Instructor.query.get(int(iid))
                if course and instructor and instructor not in course.instructors:
                    course.instructors.append(instructor)
                    db.session.commit()
                    flash('Instructor added to course.')
                elif course and instructor and instructor in course.instructors:
                    flash('Instructor is already assigned to this course.')
                else:
                    flash('Course or instructor not found.')
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {e}')
            return redirect(url_for('admin.courses'))
    if request.method == 'POST' and request.form.get('action') == 'remove_instructor':
        cid = request.form.get('course_id')
        iid = request.form.get('instructor_id')
        if cid and iid:
            try:
                course = Course.query.get(int(cid))
                instructor = Instructor.query.get(int(iid))
                if course and instructor and instructor in course.instructors:
                    course.instructors.remove(instructor)
                    db.session.commit()
                    flash('Instructor removed from course.')
                else:
                    flash('Course or instructor not found, or not assigned.')
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {e}')
            return redirect(url_for('admin.courses'))
    if request.method == 'POST' and request.form.get('action') == 'add':
        course_name = request.form.get('course_name')
        duration_weeks = request.form.get('duration_weeks')
        c_type = request.form.get('c_type')
        uni_id = request.form.get('uni_id')
        if not course_name or not uni_id:
            flash('Course name and university are required.')
        elif Course.query.filter_by(course_name=course_name).first():
            flash('Course name already exists.')
        else:
            try:
                c = Course(
                    course_name=course_name,
                    duration_weeks=int(duration_weeks) if duration_weeks else None,
                    c_type=c_type if c_type in ('degree', 'diploma', 'certificate') else None,
                    uni_id=int(uni_id)
                )
                db.session.add(c)
                db.session.commit()
                flash('Course added successfully.')
                return redirect(url_for('admin.courses'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {e}')
    return render_template('admin/courses.html', items=items, universities=universities, instructors_list=instructors_list)


@admin.route('/universities', methods=['GET', 'POST'])
@login_required
@admin_required
def universities():
    items = _safe_query(lambda: University.query.all(), default=[])
    if request.method == 'POST' and request.form.get('action') == 'delete':
        uid = request.form.get('uni_id')
        if uid:
            try:
                uni = University.query.get(int(uid))
                if uni:
                    db.session.delete(uni)
                    db.session.commit()
                    flash('University removed successfully.')
                else:
                    flash('University not found.')
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {e}')
            return redirect(url_for('admin.universities'))
    if request.method == 'POST' and request.form.get('action') == 'add':
        uni_name = request.form.get('uni_name')
        city = request.form.get('city')
        country = request.form.get('country')
        uni_type = request.form.get('uni_type')
        if not uni_name:
            flash('University name is required.')
        elif University.query.filter_by(uni_name=uni_name).first():
            flash('University name already exists.')
        else:
            try:
                u = University(
                    uni_name=uni_name,
                    city=city or None,
                    country=country or None,
                    uni_type=uni_type or None
                )
                db.session.add(u)
                db.session.commit()
                flash('University added successfully.')
                return redirect(url_for('admin.universities'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {e}')
    return render_template('admin/universities.html', items=items)


@admin.route('/enrollments', methods=['GET', 'POST'])
@login_required
@admin_required
def enrollments():
    enrollments_list = _safe_query(
        lambda: db.session.query(Enrollment, Course, Student)
        .join(Course, Enrollment.course_id == Course.course_id)
        .join(Student, Enrollment.student_id == Student.id)
        .order_by(Enrollment.enrollment_date.desc())
        .all(),
        default=[]
    )
    students = _safe_query(lambda: Student.query.all(), default=[])
    courses = _safe_query(lambda: Course.query.all(), default=[])
    if request.method == 'POST' and request.form.get('action') == 'delete':
        sid = request.form.get('student_id')
        cid = request.form.get('course_id')
        if sid and cid:
            try:
                enr = Enrollment.query.filter_by(student_id=int(sid), course_id=int(cid)).first()
                if enr:
                    db.session.delete(enr)
                    db.session.commit()
                    flash('Enrollment removed (student dropped from course).')
                else:
                    flash('Enrollment not found.')
            except Exception as e:
                db.session.rollback()
                flash(f'Error: {e}')
            return redirect(url_for('admin.enrollments'))
    if request.method == 'POST' and request.form.get('action') == 'add':
        student_id = request.form.get('student_id')
        course_id = request.form.get('course_id')
        grade = request.form.get('grade')
        due_by = request.form.get('due_by')
        if not student_id or not course_id:
            flash('Student and course are required.')
        elif Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first():
            flash('This enrollment already exists.')
        else:
            try:
                e = Enrollment(
                    student_id=int(student_id),
                    course_id=int(course_id),
                    grade=float(grade) if grade else None,
                    due_by=due_by if due_by else None
                )
                db.session.add(e)
                db.session.commit()
                flash('Enrollment added successfully.')
                return redirect(url_for('admin.enrollments'))
            except Exception as ex:
                db.session.rollback()
                flash(f'Error: {ex}')
    return render_template(
        'admin/enrollments.html',
        items=enrollments_list,
        students=students,
        courses=courses,
    )
