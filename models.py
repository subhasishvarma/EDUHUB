from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Enum, func

# This db object will be initialized in the main __init__.py
db = SQLAlchemy()

# Using SQLAlchemy's Enum type is better for mapping to PostgreSQL ENUM
user_role_enum = Enum('admin', 'analyst', 'student', 'instructor', name='user_role')
course_type_enum = Enum('degree', 'diploma', 'certificate', name='course_type')

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100))
    role = db.Column(user_role_enum, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    def get_id(self):
        return self.user_id

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
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }

class Analyst(User):
    __tablename__ = 'analysts'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'analyst',
    }

class Student(User):
    __tablename__ = 'students'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    age = db.Column(db.Integer)
    skill_level = db.Column(db.String(50))
    country = db.Column(db.String(100))

    __mapper_args__ = {
        'polymorphic_identity': 'student',
    }

class Instructor(User):
    __tablename__ = 'instructors'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    phone_number = db.Column(db.String(20))
    bio = db.Column(db.String(500))

    __mapper_args__ = {
        'polymorphic_identity': 'instructor',
    }


# --- Other schema entities for admin dashboard ---
class University(db.Model):
    __tablename__ = 'universities'
    uni_id = db.Column(db.Integer, primary_key=True)
    uni_name = db.Column(db.String(255), unique=True, nullable=False)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    uni_type = db.Column(db.String(50))
    courses = db.relationship('Course', backref='university', lazy=True, cascade='all, delete-orphan')


# Many-to-many: instructors assigned to courses (admin adds teachers to a course)
course_instructors = db.Table(
    'course_instructors',
    db.Column('course_id', db.Integer, db.ForeignKey('courses.course_id', ondelete='CASCADE'), primary_key=True),
    db.Column('instructor_id', db.Integer, db.ForeignKey('instructors.user_id', ondelete='CASCADE'), primary_key=True),
)


class Course(db.Model):
    __tablename__ = 'courses'
    course_id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(255), unique=True, nullable=False)
    duration_weeks = db.Column(db.Integer)
    c_type = db.Column(course_type_enum)
    uni_id = db.Column(db.Integer, db.ForeignKey('universities.uni_id', ondelete='CASCADE'), nullable=False)
    enrollments = db.relationship('Enrollment', backref='course', lazy=True, cascade='all, delete-orphan')
    instructors = db.relationship(
        'Instructor',
        secondary=course_instructors,
        backref=db.backref('courses', lazy=True),
        lazy=True,
    )


class Topic(db.Model):
    __tablename__ = 'topics'
    topic_id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(db.String(100), nullable=False)


class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    student_id = db.Column(db.Integer, db.ForeignKey('students.user_id', ondelete='CASCADE'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id', ondelete='CASCADE'), primary_key=True)
    enrollment_date = db.Column(db.Date, server_default=func.current_date())
    grade = db.Column(db.Numeric(5, 2))
    due_by = db.Column(db.Date)
