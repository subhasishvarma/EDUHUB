from functools import wraps
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

instructor = Blueprint('instructor', __name__, url_prefix='/instructor')


def instructor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        if role != 'instructor':
            return redirect(url_for('main.profile'))
        return f(*args, **kwargs)
    return decorated


@instructor.route('/dashboard')
@login_required
@instructor_required
def dashboard():
    return render_template('instructor/dashboard.html')

