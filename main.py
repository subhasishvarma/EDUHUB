from flask import Blueprint, render_template, Response
from flask_login import login_required, current_user

main = Blueprint('main', __name__)

@main.route('/favicon.ico')
def favicon():
    """Avoid 404 when the browser requests favicon.ico."""
    return Response(status=204)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)
