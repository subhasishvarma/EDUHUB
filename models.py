from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Enum

# This db object will be initialized in the main __init__.py
db = SQLAlchemy()

# Using SQLAlchemy's Enum type is better for mapping to PostgreSQL ENUM
user_role_enum = Enum('admin', 'analyst', 'student', 'instructor', name='user_role')

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, name='user_id')
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100))
    role = db.Column(user_role_enum, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    # Property for Flask-Login to use
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = password

    # Polymorphic identity for inheritance
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': role
    }

class Admin(User):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }

class Analyst(User):
    __tablename__ = 'analysts'
    id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'analyst',
    }

class Student(User):
    __tablename__ = 'students'
    id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    age = db.Column(db.Integer)
    skill_level = db.Column(db.String(50))
    country = db.Column(db.String(100))

    __mapper_args__ = {
        'polymorphic_identity': 'student',
    }

class Instructor(User):
    __tablename__ = 'instructors'
    id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    phone_number = db.Column(db.String(20))
    bio = db.Column(db.String(500))

    __mapper_args__ = {
        'polymorphic_identity': 'instructor',
    }
