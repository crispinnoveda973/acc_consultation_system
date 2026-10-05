from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from extensions import db
from models import (
    User, Consultation, Message, Setting,
    ROLE_SUPER_ADMIN, ROLE_MEDICAL_EXPERT, ROLE_STUDENT, ROLES, STATUSES,
)
from rbac import roles_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@login_required
@roles_required(ROLE_SUPER_ADMIN)
def guard():
    """Applies login_required + role check to every route in this blueprint."""
    pass


@admin_bp.route("/dashboard")
def dashboard():
    total_users = User.query.count()
    total_students = User.query.filter_by(role=ROLE_STUDENT).count()
    total_experts = User.query.filter_by(role=ROLE_MEDICAL_EXPERT).count()
    total_consultations = Consultation.query.count()
    pending = Consultation.query.filter_by(status="pending").count()
    in_progress = Consultation.query.filter_by(status="in_progress").count()
    resolved = Consultation.query.filter_by(status="resolved").count()
    recent = Consultation.query.order_by(Consultation.created_at.desc()).limit(6).all()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_students=total_students,
        total_experts=total_experts,
        total_consultations=total_consultations,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved,
        recent=recent,
    )


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------
@admin_bp.route("/users")
def users():
    role_filter = request.args.get("role", "")
    query = User.query
    if role_filter in ROLES:
        query = query.filter_by(role=role_filter)
    all_users = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users, role_filter=role_filter)


@admin_bp.route("/users/new", methods=["GET", "POST"])
def new_user():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        role = request.form.get("role", ROLE_STUDENT)
        program = request.form.get("program", "").strip()
        password = request.form.get("password", "")

        errors = []
        if not full_name or not username or not email or not password:
            errors.append("Please fill in all required fields.")
        if role not in ROLES:
            errors.append("Invalid role selected.")
        if User.query.filter_by(username=username).first():
            errors.append("Username already exists.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin/user_form.html", values=request.form, mode="new", roles=ROLES)

        user = User(full_name=full_name, username=username, email=email, role=role, program=program)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f"User '{username}' created.", "success")
        return redirect(url_for("admin.users"))

    return render_template(
        "admin/user_form.html",
        values={"full_name": "", "username": "", "email": "", "role": ROLE_STUDENT, "program": ""},
        mode="new", roles=ROLES,
    )


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        user.full_name = request.form.get("full_name", "").strip()
        user.email = request.form.get("email", "").strip()
        user.role = request.form.get("role", user.role)
        user.program = request.form.get("program", "").strip()
        user.is_active_account = request.form.get("is_active") == "on"

        new_password = request.form.get("password", "")
        if new_password:
            user.set_password(new_password)

        db.session.commit()
        flash(f"User '{user.username}' updated.", "success")
        return redirect(url_for("admin.users"))

    values = {
        "full_name": user.full_name, "username": user.username, "email": user.email,
        "role": user.role, "program": user.program or "",
        "is_active_account": user.is_active_account,
    }
    return render_template("admin/user_form.html", values=values, mode="edit", roles=ROLES, user=user)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin.users"))

    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.username}' deleted.", "info")
    return redirect(url_for("admin.users"))


# ---------------------------------------------------------------------------
# Consultations (system-wide view)
# ---------------------------------------------------------------------------
@admin_bp.route("/consultations")
def consultations():
    status_filter = request.args.get("status", "")
    query = Consultation.query
    if status_filter in STATUSES:
        query = query.filter_by(status=status_filter)
    items = query.order_by(Consultation.created_at.desc()).all()
    experts = User.query.filter_by(role=ROLE_MEDICAL_EXPERT).all()
    return render_template(
        "admin/consultations.html", consultations=items, status_filter=status_filter, experts=experts
    )


@admin_bp.route("/consultations/<int:cid>")
def consultation_detail(cid):
    consultation = Consultation.query.get_or_404(cid)
    experts = User.query.filter_by(role=ROLE_MEDICAL_EXPERT).all()
    return render_template("admin/consultation_detail.html", c=consultation, experts=experts)


@admin_bp.route("/consultations/<int:cid>/assign", methods=["POST"])
def assign_expert(cid):
    consultation = Consultation.query.get_or_404(cid)
    expert_id = request.form.get("expert_id")
    consultation.expert_id = int(expert_id) if expert_id else None
    if consultation.expert_id and consultation.status == "pending":
        consultation.status = "in_progress"
    consultation.updated_at = datetime.utcnow()
    db.session.commit()
    flash("Consultation reassigned.", "success")
    return redirect(url_for("admin.consultation_detail", cid=cid))


# ---------------------------------------------------------------------------
# System settings
# ---------------------------------------------------------------------------
@admin_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        Setting.set("site_name", request.form.get("site_name", "ACC Consultation System"))
        Setting.set("support_email", request.form.get("support_email", ""))
        Setting.set(
            "maintenance_mode", "on" if request.form.get("maintenance_mode") == "on" else "off"
        )
        flash("Settings saved.", "success")
        return redirect(url_for("admin.settings"))

    current_settings = {
        "site_name": Setting.get("site_name", "ACC Consultation System"),
        "support_email": Setting.get("support_email", "support@acc.edu"),
        "maintenance_mode": Setting.get("maintenance_mode", "off"),
    }
    return render_template("admin/settings.html", settings=current_settings)
