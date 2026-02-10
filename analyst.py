from functools import wraps
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

analyst = Blueprint('analyst', __name__, url_prefix='/analyst')


def analyst_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        if role != 'analyst':
            return redirect(url_for('main.profile'))
        return f(*args, **kwargs)
    return decorated


@analyst.route('/dashboard')
@login_required
@analyst_required
def dashboard():
    return render_template('analyst/dashboard.html')

