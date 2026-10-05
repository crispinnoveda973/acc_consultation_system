from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db

# ---------------------------------------------------------------------------
# Role constants
# ---------------------------------------------------------------------------
ROLE_SUPER_ADMIN = "super_admin"
ROLE_MEDICAL_EXPERT = "medical_expert"
ROLE_STUDENT = "student"

ROLES = [ROLE_SUPER_ADMIN, ROLE_MEDICAL_EXPERT, ROLE_STUDENT]

STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_RESOLVED = "resolved"
STATUS_CLOSED = "closed"

STATUSES = [STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_RESOLVED, STATUS_CLOSED]

PRIORITIES = ["low", "normal", "high", "urgent"]


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(30), nullable=False, default=ROLE_STUDENT)
    program = db.Column(db.String(150))  # e.g. course/department for students, specialty for experts
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    consultations_as_student = db.relationship(
        "Consultation", foreign_keys="Consultation.student_id", backref="student", lazy="dynamic"
    )
    consultations_as_expert = db.relationship(
        "Consultation", foreign_keys="Consultation.expert_id", backref="expert", lazy="dynamic"
    )
    messages = db.relationship("Message", backref="sender", lazy="dynamic")

    # Flask-Login requires is_active; we alias to our own column
    @property
    def is_active(self):
        return self.is_active_account

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def role_label(self):
        return {
            ROLE_SUPER_ADMIN: "Super Admin",
            ROLE_MEDICAL_EXPERT: "Medical Expert",
            ROLE_STUDENT: "Student",
        }.get(self.role, self.role)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Consultation(db.Model):
    __tablename__ = "consultations"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    expert_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default=STATUS_PENDING)
    priority = db.Column(db.String(20), nullable=False, default="normal")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = db.relationship(
        "Message", backref="consultation", lazy="dynamic",
        order_by="Message.created_at", cascade="all, delete-orphan"
    )

    def status_label(self):
        return self.status.replace("_", " ").title()

    def __repr__(self):
        return f"<Consultation #{self.id} {self.subject!r}>"


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey("consultations.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Setting(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)

    @staticmethod
    def get(key, default=None):
        row = Setting.query.filter_by(key=key).first()
        return row.value if row else default

    @staticmethod
    def set(key, value):
        row = Setting.query.filter_by(key=key).first()
        if row:
            row.value = value
        else:
            row = Setting(key=key, value=value)
            db.session.add(row)
        db.session.commit()
