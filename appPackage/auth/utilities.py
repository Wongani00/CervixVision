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

