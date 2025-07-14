from flask import render_template
from appPackage import db
from flask import Blueprint

# error blueprint instance
errors = Blueprint("error", __name__)


@errors.app_errorhandler(403)
def forbidden_error(e):
    return render_template("errors/403.html"), 403


@errors.app_errorhandler(404)
def not_found_error(e):
    return render_template("errors/404.html"), 404


@errors.app_errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template("errors/500.html"), 500
