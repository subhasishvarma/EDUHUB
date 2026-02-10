from flask import Blueprint, render_template, Response, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import db, User, Student, Instructor

main = Blueprint('main', __name__)

@main.route('/favicon.ico')
def favicon():
    """Avoid 404 when the browser requests favicon.ico."""
    return Response(status=204)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Display and update user profile."""
    
    # Get the user object based on their role to access specific attributes
    if current_user.role == 'student':
        user = Student.query.get(current_user.user_id)
    elif current_user.role == 'instructor':
        user = Instructor.query.get(current_user.user_id)
    else:
        user = User.query.get(current_user.user_id)

    if request.method == 'POST':
        # Update common user fields
        user.first_name = request.form.get('first_name', user.first_name)
        user.last_name = request.form.get('last_name', user.last_name)
        
        # Update role-specific fields
        if user.role == 'student':
            user.age = request.form.get('age', user.age)
            user.skill_level = request.form.get('skill_level', user.skill_level)
            user.country = request.form.get('country', user.country)
        elif user.role == 'instructor':
            user.phone_number = request.form.get('phone_number', user.phone_number)
            user.bio = request.form.get('bio', user.bio)
            
        try:
            db.session.commit()
            flash('Your profile has been updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            
        return redirect(url_for('main.profile'))

    return render_template('profile.html', user=user)
