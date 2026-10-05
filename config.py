import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "acc-consultation-dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "acc_consultation.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SITE_NAME = "ACC Consultation System"
