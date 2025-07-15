import os


# app configurations
class Config:
    SECRET_KEY = "wuidhfw78y3r32r323ru23t3"
    SQLALCHEMY_DATABASE_URI = "sqlite:///cervical_cancer.db"
    WTF_CSRF_ENABLED = True
    TF_ENABLE_ONEDNN_OPTS = 0
    MAIL_SERVER = "smtp.googlemail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = "wonganikaunga726@gmail.com"  # os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = "lidq djoo hdue fdvm"  # os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = (
        "wonganikaunga726@gmail.com"  # os.environ.get('MAIL_DEFAULT_SENDER')
    )
