from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Enum, func

db = SQLAlchemy()

# Enums
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

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = password

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': role
    }


class Admin(User):
    __tablename__ = 'admins'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    __mapper_args__ = {'polymorphic_identity': 'admin'}


class Analyst(User):
    __tablename__ = 'analysts'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    __mapper_args__ = {'polymorphic_identity': 'analyst'}


class Student(User):
    __tablename__ = 'students'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    age = db.Column(db.Integer)
    skill_level = db.Column(db.String(50))
    country = db.Column(db.String(100))
    __mapper_args__ = {'polymorphic_identity': 'student'}


class Instructor(User):
    __tablename__ = 'instructors'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    phone_number = db.Column(db.String(20))
    bio = db.Column(db.String(500))
    __mapper_args__ = {'polymorphic_identity': 'instructor'}


# ----------------- Admin dashboard entities -----------------
class University(db.Model):
    __tablename__ = 'universities'
    uni_id = db.Column(db.Integer, primary_key=True)
    uni_name = db.Column(db.String(255), unique=True, nullable=False)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    uni_type = db.Column(db.String(50))

    courses = db.relationship(
        'Course', backref='university', lazy=True, cascade='all, delete-orphan'
    )


# Many-to-many: instructors assigned to courses
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


# Legacy Topic (keep, but you will stop using it later)
class Topic(db.Model):
    __tablename__ = 'topics'
    topic_id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(db.String(100), nullable=False)


class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    student_id = db.Column(db.Integer, db.ForeignKey('students.user_id', ondelete='CASCADE'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id', ondelete='CASCADE'), primary_key=True)

    enrollment_date = db.Column(db.Date, server_default=func.current_date())
    due_by = db.Column(db.Date)

    marks = db.Column(db.Numeric(5, 2))
    letter_grade = db.Column(db.String(5))

    student = db.relationship('Student', backref=db.backref('enrollments', lazy=True))


# ----------------- Legacy content tables (keep for now) -----------------
class CourseVideo(db.Model):
    __tablename__ = 'coursevideos'
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id', ondelete='CASCADE'), primary_key=True)
    video_url = db.Column(db.String(500), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    uploaded_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp())

    course = db.relationship('Course', backref=db.backref('videos', lazy=True, cascade='all, delete-orphan'))


class CourseNote(db.Model):
    __tablename__ = 'coursenotes'
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id', ondelete='CASCADE'), primary_key=True)
    note_url = db.Column(db.String(500), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    format = db.Column(db.String(10), default='PDF')

    course = db.relationship('Course', backref=db.backref('notes', lazy=True, cascade='all, delete-orphan'))


class CourseOnlineBook(db.Model):
    __tablename__ = 'courseonlinebooks'
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id', ondelete='CASCADE'), primary_key=True)
    book_url = db.Column(db.String(500), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    page_count = db.Column(db.Integer)

    course = db.relationship('Course', backref=db.backref('online_books', lazy=True, cascade='all, delete-orphan'))


# ==========================================================
# NEW STRUCTURE: Course -> Modules -> Topics -> Subtopics -> Contents
# ==========================================================

class CourseModule(db.Model):
    __tablename__ = 'coursemodules'
    module_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id', ondelete='CASCADE'), nullable=False)
    module_title = db.Column(db.String(255), nullable=False)
    module_order = db.Column(db.Integer, default=1)

    course = db.relationship('Course', backref=db.backref('modules', lazy=True, cascade='all, delete-orphan'))


class ModuleTopic(db.Model):
    __tablename__ = 'moduletopics'
    topic_id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('coursemodules.module_id', ondelete='CASCADE'), nullable=False)
    topic_title = db.Column(db.String(255), nullable=False)
    topic_order = db.Column(db.Integer, default=1)

    module = db.relationship('CourseModule', backref=db.backref('topics', lazy=True, cascade='all, delete-orphan'))


class TopicSubtopic(db.Model):
    __tablename__ = 'topicsubtopics'
    subtopic_id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('moduletopics.topic_id', ondelete='CASCADE'), nullable=False)
    subtopic_title = db.Column(db.String(255), nullable=False)
    subtopic_order = db.Column(db.Integer, default=1)

    topic = db.relationship('ModuleTopic', backref=db.backref('subtopics', lazy=True, cascade='all, delete-orphan'))


# Assignments attached to a specific subtopic
class SubtopicAssignment(db.Model):
    __tablename__ = 'subtopicassignments'

    assignment_id = db.Column(db.Integer, primary_key=True)
    subtopic_id = db.Column(db.Integer, db.ForeignKey('topicsubtopics.subtopic_id', ondelete='CASCADE'), nullable=False)

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp())

    subtopic = db.relationship(
        'TopicSubtopic',
        backref=db.backref('assignments', lazy=True, cascade='all, delete-orphan')
    )


# Assignments attached to a specific topic
class TopicAssignment(db.Model):
    __tablename__ = 'topicassignments'

    assignment_id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('moduletopics.topic_id', ondelete='CASCADE'), nullable=False)

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp())

    topic = db.relationship(
        'ModuleTopic',
        backref=db.backref('assignments', lazy=True, cascade='all, delete-orphan')
    )


# ✅ UPDATED: Subtopic content now supports Video / Notes / Online Book
class SubtopicContent(db.Model):
    __tablename__ = 'subtopiccontents'

    content_id = db.Column(db.Integer, primary_key=True)
    subtopic_id = db.Column(db.Integer, db.ForeignKey('topicsubtopics.subtopic_id', ondelete='CASCADE'), nullable=False)

    # video / notes / book
    content_type = db.Column(db.String(20), nullable=False)

    # common
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), nullable=False)

    # optional
    duration_minutes = db.Column(db.Integer)  # for video
    file_format = db.Column(db.String(20))    # for notes

    content_order = db.Column(db.Integer, default=1)

    subtopic = db.relationship(
        'TopicSubtopic',
        backref=db.backref('contents', lazy=True, cascade='all, delete-orphan')
    )


class DeregistrationRequest(db.Model):
    __tablename__ = 'deregistration_requests'

    request_id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey('students.user_id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id', ondelete='CASCADE'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructors.user_id', ondelete='CASCADE'), nullable=False)

    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending / approved / rejected

    created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp())
    decided_at = db.Column(db.TIMESTAMP)

    student = db.relationship('Student', backref=db.backref('deregistration_requests', lazy=True))
    course = db.relationship('Course', backref=db.backref('deregistration_requests', lazy=True))
    instructor = db.relationship('Instructor', backref=db.backref('deregistration_requests', lazy=True))