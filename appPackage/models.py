from datetime import datetime
import re
from wsgiref import validate
from appPackage import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# managing user sessions
@login.user_loader
def loadUser(id):
    return User.query.get(int(id))


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String(120), nullable=False)
    surname = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="user")
    gender = db.Column(db.String(10), nullable=True)  # Optional field
    date_joined = db.Column(db.DateTime, default=datetime.now())
    # created_by = db.Column(
    #     db.Integer,
    #     db.ForeignKey("users.id"),
    #     nullable=True,
    #     default="self_registration",
    # )

    # creator = db.relationship("User", remote_side=[id], backref="created_users")
    predictions = db.relationship(
        "Prediction", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    feedbacks = db.relationship(
        "Feedback", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def __init__(self, f_name, surname, email, password_hash, role, gender):
        self.f_name = f_name
        self.surname = surname
        self.email = email
        self.password_hash = generate_password_hash(password_hash)
        self.role = role
        self.gender = gender

    @staticmethod
    def validate_name(name, field_name="Name"):
        """Validating the username"""
        if not name or len(name) < 3:
            raise AssertionError("name must be at least 3 characters long")
        if not re.match(r"^[a-zA-Z0-9_]+$", name):
            raise AssertionError(
                "name can only contain letters, numbers, and underscores"
            )
        # Check if username already exists in the database
        # existing_user = User.query.filter_by(username=username).first()
        # if existing_user:
        #     raise AssertionError("Username is already taken")
        # return name

    @staticmethod
    def validate_email(email):
        """Email validation"""
        if not email:
            raise AssertionError("Email is required")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise AssertionError("Invalid email format")
        # Check if email already exists in the database
        # existing_email = User.query.filter_by(email=email).first()
        # if existing_email:
        #     raise AssertionError("Email is already registered")
        return email

    @staticmethod
    def validate_password(password):
        if not re.search(
            r"^(?=.*?[0-9])(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[^0-9A-Za-z]).{8,32}$",
            password,
        ):
            raise AssertionError(
                "Atleast 8 characters, including a number, Capital letter and special caharacters"
            )
        return password

    # checking user password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Prediction(db.Model):
    __tablename__ = "predictions"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    image_path = db.Column(db.String(200))
    predicted_class = db.Column(db.String(100))
    confidence = db.Column(db.Float)
    ood_status = db.Column(db.String(20))
    true_label = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now())
    # user who made the prediction
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # relationship with Appointment model
    appointment = db.relationship("Appointment", backref="prediction", uselist=False)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    next_screening_date = db.Column(db.Date)
    prediction_id = db.Column(db.Integer, db.ForeignKey("predictions.id"))


class Feedback(db.Model):
    __tablename__ = "feedbacks"
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.now())
