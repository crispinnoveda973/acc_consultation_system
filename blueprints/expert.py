from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models import Consultation, Message, User, ROLE_MEDICAL_EXPERT, STATUSES
from rbac import roles_required

expert_bp = Blueprint("expert", __name__, url_prefix="/expert")


@expert_bp.before_request
@login_required
@roles_required(ROLE_MEDICAL_EXPERT)
def guard():
    pass


@expert_bp.route("/dashboard")
def dashboard():
    my_consultations = Consultation.query.filter_by(expert_id=current_user.id)
    unassigned = Consultation.query.filter_by(expert_id=None, status="pending").order_by(
        Consultation.created_at.desc()
    ).all()

    stats = {
        "assigned": my_consultations.count(),
        "pending": my_consultations.filter_by(status="pending").count(),
        "in_progress": my_consultations.filter_by(status="in_progress").count(),
        "resolved": my_consultations.filter_by(status="resolved").count(),
        "unassigned_pool": len(unassigned),
    }
    recent = my_consultations.order_by(Consultation.updated_at.desc()).limit(6).all()

    return render_template("expert/dashboard.html", stats=stats, recent=recent, unassigned=unassigned)


@expert_bp.route("/consultations")
def consultations():
    view = request.args.get("view", "assigned")
    if view == "pool":
        items = Consultation.query.filter_by(expert_id=None, status="pending").order_by(
            Consultation.created_at.desc()
        ).all()
    else:
        status_filter = request.args.get("status", "")
        query = Consultation.query.filter_by(expert_id=current_user.id)
        if status_filter in STATUSES:
            query = query.filter_by(status=status_filter)
        items = query.order_by(Consultation.created_at.desc()).all()

    return render_template("expert/consultations.html", consultations=items, view=view)


@expert_bp.route("/consultations/<int:cid>/claim", methods=["POST"])
def claim(cid):
    consultation = Consultation.query.get_or_404(cid)
    if consultation.expert_id is not None:
        flash("This consultation has already been claimed.", "warning")
        return redirect(url_for("expert.consultations", view="pool"))

    consultation.expert_id = current_user.id
    consultation.status = "in_progress"
    consultation.updated_at = datetime.utcnow()
    db.session.commit()
    flash("Consultation claimed. You can now respond to the student.", "success")
    return redirect(url_for("expert.consultation_detail", cid=cid))


@expert_bp.route("/consultations/<int:cid>", methods=["GET", "POST"])
def consultation_detail(cid):
    consultation = Consultation.query.get_or_404(cid)
    if consultation.expert_id not in (None, current_user.id):
        abort(403)

    if request.method == "POST":
        if consultation.expert_id is None:
            consultation.expert_id = current_user.id

        body = request.form.get("body", "").strip()
        if body:
            msg = Message(consultation_id=consultation.id, sender_id=current_user.id, body=body)
            db.session.add(msg)

        new_status = request.form.get("status")
        if new_status in STATUSES:
            consultation.status = new_status

        consultation.updated_at = datetime.utcnow()
        db.session.commit()
        flash("Response sent.", "success")
        return redirect(url_for("expert.consultation_detail", cid=cid))

    return render_template("expert/consultation_detail.html", c=consultation)


@expert_bp.route("/students")
def students():
    student_ids = [
        row[0] for row in
        db.session.query(Consultation.student_id).filter_by(expert_id=current_user.id).distinct()
    ]
    my_students = User.query.filter(User.id.in_(student_ids)).all() if student_ids else []
    return render_template("expert/students.html", students=my_students)
