from flask import Flask
from flask_login import LoginManager
from .models import db, User


def create_app():
    app = Flask(__name__)

    @app.template_filter("enum_display")
    def enum_display(v):
        if v is None:
            return ""
        s = getattr(v, "value", str(v))
        return s.replace("_", " ").title()

<<<<<<< HEAD
    # ✅ ADD THIS FILTER
    @app.template_filter("role_value")
    def role_value(v):
        if v is None:
            return ""
        return getattr(v, "value", str(v))

    # --- Configuration ---
    app.config['SECRET_KEY'] = 'a_very_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://23CS30019:23CS30019@10.5.18.103:5432/23CS30019'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

=======
    # --- Configuration ---
    app.config['SECRET_KEY'] = 'a_very_secret_key' # Replace with a real secret key
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://23CS30019:23CS30019@10.5.18.103:5432/23CS30019'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- Initialize Extensions ---
>>>>>>> b43b4c6 (Add auth, student dashboard, and templates)
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

<<<<<<< HEAD
=======
    # --- Blueprints ---
>>>>>>> b43b4c6 (Add auth, student dashboard, and templates)
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    from .student import student as student_blueprint
    app.register_blueprint(student_blueprint)

    from .instructor import instructor as instructor_blueprint
    app.register_blueprint(instructor_blueprint)

    from .analyst import analyst as analyst_blueprint
    app.register_blueprint(analyst_blueprint)

<<<<<<< HEAD
=======
    # with app.app_context():
    #     db.create_all()

>>>>>>> b43b4c6 (Add auth, student dashboard, and templates)
    return app
