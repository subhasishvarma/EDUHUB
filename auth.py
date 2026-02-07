from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .models import db, User, Student, Instructor, Admin, Analyst

auth = Blueprint('auth', __name__)

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    # --- Common fields ---
    email = request.form.get('email')
    username = request.form.get('username')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    password = request.form.get('password')
    role = request.form.get('role')

    # --- Check if user exists ---
    user_by_email = User.query.filter_by(email=email).first()
    user_by_username = User.query.filter_by(username=username).first()

    if user_by_email:
        flash('Email address already registered.')
        return redirect(url_for('auth.signup'))
    
    if user_by_username:
        flash('Username already taken.')
        return redirect(url_for('auth.signup'))

    # --- Create user based on role ---
    new_user = None
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    common_args = {
        'email': email,
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'password_hash': hashed_password,
        'role': role
    }

    if role == 'student':
        age = request.form.get('age')
        country = request.form.get('country')
        new_user = Student(
            **common_args,
            age=age if age else None,
            skill_level='Beginner',  # Set at signup per schema
            country=country or None
        )
    elif role == 'instructor':
        phone_number = request.form.get('phone_number')
        bio = request.form.get('bio')
        new_user = Instructor(
            **common_args,
            phone_number=phone_number,
            bio=bio
        )
    elif role == 'admin':
        new_user = Admin(**common_args)
    elif role == 'analyst':
        new_user = Analyst(**common_args)
    else:
        flash('Invalid role selected.')
        return redirect(url_for('auth.signup'))

    # --- Add to database ---
    db.session.add(new_user)
    try:
        db.session.commit()
        flash('Signup successful! Please log in.')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred during sign up: {e}')
        return redirect(url_for('auth.signup'))

    return redirect(url_for('auth.login'))


@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))
    
    login_user(user, remember=remember)

    # Redirect based on role
    role = user.role.value if hasattr(user.role, 'value') else str(user.role)
    if role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif role == 'analyst':
        return redirect(url_for('analyst.dashboard'))
    elif role == 'student':
        return redirect(url_for('student.dashboard'))
    elif role == 'instructor':
        return redirect(url_for('instructor.dashboard'))
    return redirect(url_for('main.profile'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
