from functools import wraps
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

student = Blueprint('student', __name__, url_prefix='/student')


def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        if role != 'student':
            return redirect(url_for('main.profile'))
        return f(*args, **kwargs)
    return decorated


@student.route('/dashboard')
@login_required
@student_required
def dashboard():
    return render_template('student/dashboard.html')

