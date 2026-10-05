from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models import User, ROLE_STUDENT, ROLE_SUPER_ADMIN, ROLE_MEDICAL_EXPERT

auth_bp = Blueprint("auth", __name__)


def redirect_for_role(role):
    if role == ROLE_SUPER_ADMIN:
        return redirect(url_for("admin.dashboard"))
    if role == ROLE_MEDICAL_EXPERT:
        return redirect(url_for("expert.dashboard"))
    return redirect(url_for("student.dashboard"))


@auth_bp.route("/", methods=["GET"])
def index():
    if current_user.is_authenticated:
        return redirect_for_role(current_user.role)
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect_for_role(current_user.role)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash("Invalid username or password.", "danger")
            return render_template("auth/login.html")

        if not user.is_active_account:
            flash("This account has been deactivated. Contact an administrator.", "danger")
            return render_template("auth/login.html")

        login_user(user)
        flash(f"Welcome back, {user.full_name}!", "success")
        return redirect_for_role(user.role)

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Self-service registration is only for Students. Admins create
    Medical Expert / Super Admin accounts from the admin panel."""
    if current_user.is_authenticated:
        return redirect_for_role(current_user.role)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        program = request.form.get("program", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []
        if not full_name or not username or not email or not password:
            errors.append("Please fill in all required fields.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if User.query.filter_by(username=username).first():
            errors.append("That username is already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("That email is already registered.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/register.html", form=request.form)

        user = User(
            username=username,
            email=email,
            full_name=full_name,
            program=program,
            role=ROLE_STUDENT,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form={})


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
