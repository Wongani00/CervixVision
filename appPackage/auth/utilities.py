from appPackage import mail
from flask_mail import Message
from flask import url_for

# from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


# def get_reset_token(self, expires_sec=1800):
#     s = Serializer(app.config["SECRET_KEY"], expires_sec)
#     return s.dumps({"user_id": self.id}).decode("utf-8")


# @staticmethod
# def verify_reset_token(token):
#     s = Serializer(app.config["SECRET_KEY"])
#     try:
#         user_id = s.loads(token)["user_id"]
#     except:
#         return None
#     return User.query.get(user_id)


# def send_reset_email(user):
#     token = user.get_reset_token()
#     msg = Message(
#         "Password Reset Request", sender="noreply@gmail.com", recipients=[user.email]
#     )
#     msg.body = f"""To reset your password, visit the following link:
#   {url_for('reset_token', token=token, _external=True)}
#   If you did not make this request, then simply ignore this email and no change"""
#     mail.send(msg)


def send_welcome_email(user_email, user_name, user_role):
    """Send welcome email to new user upon successful registration"""
    try:
        msg = Message(
            subject="Welcome to Cervical Cancer Prediction System - Registration Successful",
            # sender=os.environ.get(
            #     "MAIL_DEFAULT_SENDER", "noreply@healthcare-system.com"
            # ),
            sender="noreply@gmail.com",
            recipients=[user_email],
        )

        login_url = url_for("auth.login", _external=True)

        msg.body = f"""
        Dear {user_name},

        Welcome to the Cervical Cancer Prediction System!

        Your registration has been successfully completed. Here are your account details:
        - Name: {user_name}
        - Email: {user_email}
        - Role: {user_role.title()}

        You can now login to access the system using the following link:
        {login_url}

        Thank you for joining our healthcare system. We're committed to providing you with the best tools for cervical cancer prediction and prevention.

        If you have any questions or need assistance, please don't hesitate to contact our support team.

        Best regards,
        Healthcare System Team
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
                            If you have any questions or need assistance, please contact our support team.
                        </p>
                        <p style="color: #6c757d; font-size: 12px;">
                            Best regards,<br>
                            <strong>Healthcare System Team</strong>
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
