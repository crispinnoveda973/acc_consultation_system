from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models import Consultation, Message, ROLE_STUDENT, PRIORITIES, STATUSES
from rbac import roles_required

student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.before_request
@login_required
@roles_required(ROLE_STUDENT)
def guard():
    pass


@student_bp.route("/dashboard")
def dashboard():
    my_consultations = Consultation.query.filter_by(student_id=current_user.id)
    stats = {
        "total": my_consultations.count(),
        "pending": my_consultations.filter_by(status="pending").count(),
        "in_progress": my_consultations.filter_by(status="in_progress").count(),
        "resolved": my_consultations.filter_by(status="resolved").count(),
    }
    recent = my_consultations.order_by(Consultation.created_at.desc()).limit(6).all()
    return render_template("student/dashboard.html", stats=stats, recent=recent)


@student_bp.route("/consultations")
def history():
    status_filter = request.args.get("status", "")
    query = Consultation.query.filter_by(student_id=current_user.id)
    if status_filter in STATUSES:
        query = query.filter_by(status=status_filter)
    items = query.order_by(Consultation.created_at.desc()).all()
    return render_template("student/history.html", consultations=items, status_filter=status_filter)


@student_bp.route("/consultations/new", methods=["GET", "POST"])
def new_consultation():
    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "normal")

        errors = []
        if not subject or not description:
            errors.append("Please provide both a subject and a description.")
        if priority not in PRIORITIES:
            priority = "normal"

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("student/new_consultation.html", form=request.form)

        consultation = Consultation(
            student_id=current_user.id,
            subject=subject,
            description=description,
            priority=priority,
        )
        db.session.add(consultation)
        db.session.commit()
        flash("Your consultation request has been submitted.", "success")
        return redirect(url_for("student.consultation_detail", cid=consultation.id))

    return render_template("student/new_consultation.html", form={})


@student_bp.route("/consultations/<int:cid>", methods=["GET", "POST"])
def consultation_detail(cid):
    consultation = Consultation.query.get_or_404(cid)
    if consultation.student_id != current_user.id:
        abort(403)

    if request.method == "POST":
        if consultation.status == "closed":
            flash("This consultation is closed and cannot accept new messages.", "warning")
            return redirect(url_for("student.consultation_detail", cid=cid))

        body = request.form.get("body", "").strip()
        if body:
            msg = Message(consultation_id=consultation.id, sender_id=current_user.id, body=body)
            db.session.add(msg)
            consultation.updated_at = datetime.utcnow()
            db.session.commit()
            flash("Message sent.", "success")
        return redirect(url_for("student.consultation_detail", cid=cid))

    return render_template("student/consultation_detail.html", c=consultation)
