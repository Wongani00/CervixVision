from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    Blueprint,
    jsonify,
)
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from appPackage.auth.forms import RegistrationForm, LoginForm
from appPackage.models import User
from appPackage import db, mail
from werkzeug.security import generate_password_hash

# user management instance
auth = Blueprint("auth", __name__)


# user registration
@auth.route("/signup", methods=["POST", "GET"])
def signup():
    title = "Sign Up"
    try:
        if request.method == "POST":
            data = request.get_json()
            errors = {}

            # Validation - ensuring that all errors are strings (not arrays)
            if not data.get("f_name"):
                errors["firstname"] = "First name is required"
            else:
                try:
                    User.validate_name(data.get("f_name"), "first name")
                except AssertionError as e:
                    errors["firstname"] = str(e)

            if not data.get("surname"):
                errors["surname"] = "Surname is required"
            else:
                try:
                    User.validate_name(data.get("surname"), "surname")
                except AssertionError as e:
                    errors["surname"] = str(e)

            if not data.get("email"):
                errors["email"] = "Email is required"
            else:
                existing_user = User.query.filter_by(email=data.get("email")).first()
                if existing_user:
                    errors["email"] = "Email is already taken"
                try:
                    User.validate_email(data.get("email"))
                except AssertionError as e:
                    errors["email"] = str(e)

            if not data.get("role"):
                errors["role"] = "Role is required"
            elif data.get("role") not in [
                "doctor",
                "nurse",
                "admin",
            ]:  # Add proper role validation
                errors["role"] = "Invalid role selected"

            if not data.get("gender"):
                errors["gender"] = "Gender is required"
            elif data.get("gender") not in [
                "Male",
                "Female",
                "Other",
            ]:  # Add proper role validation
                errors["gender"] = "Invalid gender selected"

            if not data.get("password"):
                errors["password"] = "Password is required"
            else:
                try:
                    User.validate_password(data.get("password"))
                except AssertionError as e:
                    errors["password"] = str(e)

            if errors:
                return jsonify({"success": False, "errors": errors}), 400

            try:
                new_user = User(
                    f_name=data.get("f_name"),
                    surname=data.get("surname"),
                    email=data.get("email"),
                    password_hash=data.get("password"),
                    role=data.get("role"),
                    gender=data.get("gender"),
                )
                db.session.add(new_user)
                db.session.commit()

                user_full_name = f"{new_user.f_name} {new_user.surname}"
                email_sent = send_welcome_email(
                    user_email=new_user.email,
                    user_name=user_full_name,
                    user_role=new_user.role,
                )

                return (
                    jsonify(
                        {
                            "success": True,
                            "message": "Registration successful!",
                            "redirect": url_for("auth.login"),
                        }
                    ),
                    200,
                )
            except Exception as e:
                db.session.rollback()
                print(f"Error saving user: {e}")
                return (
                    jsonify(
                        {
                            "success": False,
                            "errors": {
                                "database": "An error occurred while saving user."
                            },
                        }
                    ),
                    500,
                )
    except Exception as e:
        print(f"Unexpected error during registration: {e}")
        return jsonify({"success": False, "error": str(e)})
    # GET request
    return render_template("auth/signup.html")


# user login
@auth.route("/login", methods=["POST", "GET"])
def login():
    title = "Login"
    if request.method == "POST":
        data = request.get_json()  # getting data from the json object sent via ajax
        user = User.query.filter_by(email=data["email"]).first()
        if user and user.check_password(data["password"]):
            login_user(user)
            return jsonify({"success": True, "redirect": url_for("main.home")})
        return jsonify({"success": False, "error": "Invalid username or email"})
    return render_template("auth/login.html", title=title)


def get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def send_welcome_email(user_email, user_name, user_role):
    """Send welcome email to new user upon successful registration"""
    try:
        msg = Message(
            subject="Welcome to Cervical Cancer Prediction System - Registration Successful",
            sender="noreply@gmail.com",
            recipients=[user_email],
        )

        login_url = url_for("auth.login", _external=True)

        msg.body = f"""
Dear {user_name},

Welcome to the CervixVision!

Your registration has been successfully completed. Here are your account details:
- Name: {user_name}
- Email: {user_email}
- Role: {user_role.title()}

You can now login to access the system using the following link:
{login_url}

Thank you for joining our healthcare system. We're committed to providing you with the best tools for cervical cancer prediction and prevention.

If you have any questions or need assistance, please don't hesitate to contact the support team.

Best regards,
CervixVision - Healthcare System Team
        """

        msg.html = f"""
<html>
<body>
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
        <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #28a745; margin-bottom: 10px;">Welcome to Healthcare System!</h1>
                <p style="color: #6c757d; font-size: 16px;">Registration Successful</p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
                <h3 style="color: #333; margin-bottom: 15px;">Account Details:</h3>
                <p style="margin: 8px 0; color: #555;"><strong>Name:</strong> {user_name}</p>
                <p style="margin: 8px 0; color: #555;"><strong>Email:</strong> {user_email}</p>
                <p style="margin: 8px 0; color: #555;"><strong>Role:</strong> {user_role.title()}</p>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <p style="color: #333; margin-bottom: 20px;">Your account is now ready! Click the button below to login:</p>
                <a href="{login_url}" style="background-color: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold; font-size: 16px;">Login to Your Account</a>
            </div>
            
            <div style="background-color: #e3f2fd; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h4 style="color: #1976d2; margin-bottom: 10px;">Security Information:</h4>
                <ul style="color: #555; margin: 10px 0; padding-left: 20px;">
                    <li>Keep your login credentials secure</li>
                    <li>Never share your password with anyone</li>
                    <li>Contact support if you notice any suspicious activity</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <p style="color: #6c757d; font-size: 14px;">
                    Thank you for joining our healthcare system. We're committed to providing you with the best tools for cervical cancer prediction and prevention.
                </p>
            </div>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #e9ecef;">
            
            <div style="text-align: center;">
                <p style="color: #6c757d; font-size: 12px; margin-bottom: 5px;">
                    If you have any questions or need assistance, please contact the support team.
                </p>
                <p style="color: #6c757d; font-size: 12px;">
                    Best regards,<br>
                    <strong>CervixVision</strong>
                </p>
            </div>
        </div>
    </div>
</body>
</html>
        """

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False


def send_password_reset_email(user_email, reset_token):
    """Send password reset email to user"""
    try:
        msg = Message(
            subject="Password Reset Request - CervixVision",
            sender="noreply@cervix.com",
            recipients=[user_email],
        )

        reset_url = url_for(
            "auth.reset_password_confirm", token=reset_token, _external=True
        )

        msg.body = f"""
Dear User,

You have requested to reset your password for the Cervical Cancer Prediction System.

Please click the following link to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

If you did not request this password reset, please ignore this email.

Best regards,
CervixVision
        """

        msg.html = f"""
<html>
<body>
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333; text-align: center;">Password Reset Request</h2>
        <p>Dear User,</p>
        <p>You have requested to reset your password for the Cervical Cancer Prediction System.</p>
        <div style="text-align: center; margin: 10px 0;">
            <a href="{reset_url}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
        </div>
        <p><strong>This link will expire in 1 hour for security reasons.</strong></p>
        <p>If you did not request this password reset, please ignore this email.</p>
        <hr style="margin: 10px 0;">
        <p style="color: #666; font-size: 12px;">Best regards,<br>CervixVision</p>
    </div>
</body>
</html>
        """

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


# Password reset request route
@auth.route("/reset-password", methods=["POST", "GET"])
def reset_password():
    if request.method == "POST":
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"success": False, "error": "Email is required"}), 400

        # Find user by email
        user = User.query.filter_by(email=email).first()

        if not user:
            # Don't reveal if email exists or not for security
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "If an account with this email exists, a password reset link has been sent.",
                    }
                ),
                200,
            )

        # Generate secure token
        serializer = get_serializer()
        token = serializer.dumps(user.email, salt="password-reset-salt")

        # Send email
        if send_password_reset_email(user.email, token):
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Password reset link has been sent to your email.",
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Failed to send reset email. Please try again.",
                    }
                ),
                500,
            )

    return render_template("auth/change-password.html")


# Password reset confirmation route
@auth.route("/reset-password-confirm/<token>", methods=["GET", "POST"])
def reset_password_confirm(token):
    serializer = get_serializer()

    try:
        # Verify token (expires in 1 hour)
        email = serializer.loads(token, salt="password-reset-salt", max_age=3600)
    except SignatureExpired:
        flash("The password reset link has expired. Please request a new one.", "error")
        return redirect(url_for("auth.reset_password"))
    except BadSignature:
        flash("Invalid password reset link. Please request a new one.", "error")
        return redirect(url_for("auth.reset_password"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found. Please request a new password reset.", "error")
        return redirect(url_for("auth.reset_password"))

    if request.method == "POST":
        data = request.get_json()
        new_password = data.get("password")
        confirm_password = data.get("confirm_password")

        errors = {}

        if not new_password:
            errors["password"] = "Password is required"
        else:
            try:
                User.validate_password(new_password)
            except AssertionError as e:
                errors["password"] = str(e)

        if not confirm_password:
            errors["confirm_password"] = "Please confirm your password"
        elif new_password != confirm_password:
            errors["confirm_password"] = "Passwords do not match"

        if errors:
            return jsonify({"success": False, "errors": errors}), 400

        try:
            # Update user password
            user.password_hash = generate_password_hash(
                new_password
            )  # hashing the password
            db.session.commit()

            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Password has been successfully reset!",
                        "redirect": url_for("auth.login"),
                    }
                ),
                200,
            )
        except Exception as e:
            db.session.rollback()
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "An error occurred while updating your password.",
                    }
                ),
                500,
            )

    return render_template("auth/reset-password-confirm.html", token=token)


# route for signing out
@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


# user profile information route
# @auth.route("/user-profile")
# @login_required
# def user_profile():
#     return render_template("auth/profile.html")
