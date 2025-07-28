from sqlite3 import IntegrityError
from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    abort,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import case, func
from appPackage.models import User
from appPackage import db
from functools import wraps

user_management = Blueprint("user_management", __name__)


# function for checking user roles to enhance restriction to some pages
def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)

        return decorated_view

    return wrapper


# route for admin panel
@user_management.route("/admin-dashboard", methods=["GET", "POST"])
@login_required
@role_required("admin", "super admin")
def admin():
    title = "Admin Panel"
    # Get all counts in a single query - corrected syntax
    counts = db.session.query(
        func.sum(case((User.role.in_(["doctor", "nurse"]), 1), else_=0)).label(
            "doctor_nurse_count"
        ),
        func.sum(case((User.role.in_(["admin", "super admin"]), 1), else_=0)).label(
            "admin_superadmin_count"
        ),
        func.count(User.id).label("total_users"),
    ).first()

    # Get counts by each role
    role_counts = (
        db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
    )

    # Prepare data for template
    stats = {
        "doctor_nurse_count": counts.doctor_nurse_count or 0,
        "admin_superadmin_count": counts.admin_superadmin_count or 0,
        "total_users": counts.total_users or 0,
        "role_counts": dict(role_counts),
        "doctor_count": next(
            (count for role, count in role_counts if role == "doctor"), 0
        ),
        "nurse_count": next(
            (count for role, count in role_counts if role == "nurse"), 0
        ),
        "admin_count": next(
            (count for role, count in role_counts if role == "admin"), 0
        ),
        "super_admin_count": next(
            (count for role, count in role_counts if role == "super admin"), 0
        ),
    }

    try:
        # Get page number from request (default to 1)
        page = request.args.get("page", 1, type=int)

        # Get the paginated query
        users = User.query.paginate(page=page, per_page=5, error_out=False)

        # If requested page exceeds available pages, redirect to last page
        if page > users.pages and users.pages > 0:
            return redirect(url_for("user_management.admin", page=users.pages))

        # If there are no users and page > 1, redirect to page 1
        if users.total == 0 and page > 1:
            return redirect(url_for("user_management.admin", page=1))

    except Exception as e:
        print(f"Error in admin dashboard: {str(e)}")
        # If any error occurs, default to page 1
        users = User.query.paginate(page=1, per_page=5, error_out=False)
        flash("An error occurred while loading the admin dashboard", "error")

    return render_template(
        "user_management/admin_panel.html", title=title, users=users, stats=stats
    )


# route to delete user and Only authenticated users with admin or super admin role can delete
@user_management.route("/delete_user/<int:user_id>", methods=["POST", "GET"])
@login_required
@role_required("admin", "super admin")
def delete_user(user_id):
    target_user = User.query.get_or_404(user_id)

    # target user id
    target_user_id = target_user.id
    # current user id
    current_user_id = current_user.id
    # Prevent users from deleting themselves
    if current_user.id == target_user.id:
        abort(403)

    # Admins cannot delete super admins
    if current_user.role == "admin" and target_user.role == "super admin":
        abort(403)

    try:
        db.session.delete(target_user)
        db.session.commit()
        return redirect(url_for("user_management.admin"))
    except Exception as e:
        print("Deletion error:", e)
        abort(500)


# route for editing user details
@user_management.route("/edit/<int:user_id>", methods=["POST"])
@login_required
@role_required("admin", "super admin")
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    # Prevent regular admins from editing a super admin
    if current_user.role == "admin" and user.role == "super admin":
        abort(403)

    # You can optionally restrict that only super admins can edit super admins (even themselves or others)
    if user.role == "super admin" and current_user.role != "super admin":
        abort(403)

    firstname = request.form.get("firstname")
    surname = request.form.get("surname")
    role = request.form.get("role")
    email = request.form.get("email").strip().lower()

    try:
        # Preventing downgrading super admin by non-super admins
        if user.role == "super admin" and current_user.role != "super admin":
            abort(403)

        # Applying changes
        user.f_name = firstname
        user.surname = surname
        user.role = role
        user.email = email
        db.session.commit()

        return redirect(url_for("user_management.admin"))
    except Exception as e:
        db.session.rollback()
        raise
        abort(500)


# adding users registration
@user_management.route("/add-user", methods=["POST"])
@login_required
@role_required("admin", "super admin")
def adding_user():
    try:
        data = request.get_json()
        errors = {}

        f_name = data.get("f_name", "").strip()
        surname = data.get("surname", "").strip()
        email = data.get("email", "").strip().lower()
        role = data.get("role", "").strip()
        gender = data.get("gender", "").strip()
        password = data.get("password", "")

        # Basic field validation
        if not f_name:
            errors["firstname"] = "First name is required"
        if not surname:
            errors["surname"] = "Surname is required"
        if not email:
            errors["email"] = "Email is required"
        else:
            try:
                User.validate_email(email)
            except AssertionError as e:
                errors["email"] = str(e)
            if "email" not in errors:
                if User.query.filter(func.lower(User.email) == email).first():
                    errors["email"] = "Email is already taken"

        if not role:
            errors["role"] = "Role is required"
        elif role not in ["doctor", "nurse", "admin"]:
            errors["role"] = "Invalid role selected"

        if not gender:
            errors["gender"] = "Gender is required"
        elif gender not in ["Male", "Female", "Other"]:
            errors["gender"] = "Invalid gender selected"

        if not password:
            errors["password"] = "Password is required"
        else:
            try:
                User.validate_password(password)
            except AssertionError as e:
                errors["password"] = str(e)

        if errors:
            return jsonify({"success": False, "errors": errors}), 400

        new_user = User(
            f_name=f_name,
            surname=surname,
            email=email,
            password_hash=password,
            role=role,
            gender=gender,
        )

        db.session.add(new_user)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "User created successfully!",
                    "redirect": url_for("user_management.admin"),
                }
            ),
            201,
        )

    except IntegrityError as e:
        db.session.rollback()
        if "UNIQUE constraint failed: users.email" in str(e):
            return (
                jsonify(
                    {
                        "success": False,
                        "errors": {"email": "Email was just taken by another user"},
                    }
                ),
                400,
            )
        return (
            jsonify(
                {
                    "success": False,
                    "errors": {"database": "Database error occurred"},
                }
            ),
            500,
        )

    except Exception as e:
        db.session.rollback()
        print(f"Unexpected error: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "errors": {"system": "An unexpected error occurred"},
                }
            ),
            500,
        )
