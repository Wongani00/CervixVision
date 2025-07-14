from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_migrate import Migrate
from flask_login import LoginManager
from appPackage.config import Config


db = SQLAlchemy()
mail = Mail()
db_migrate = Migrate()
login = LoginManager()
login.login_view = "auth.login"


# function for creating the app and initializing all the instances
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    db_migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)

    # calling and attaching blueprints to the app
    from appPackage.auth.routes import auth as auth_blueprint
    from appPackage.errors.error_handlers import errors as error_blueprint
    from appPackage.main.routes import main as main_blueprint
    from appPackage.user_management.routes import user_management as user_blueprint
    from appPackage.dashboard_APIs.api_routes import api as api_blueprint

    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(error_blueprint)
    app.register_blueprint(main_blueprint)
    app.register_blueprint(user_blueprint, url_prefix="/user-management")
    app.register_blueprint(api_blueprint)

    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, private"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return app
