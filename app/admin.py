from functools import wraps
from datetime import datetime, timezone

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.matching import find_matching_donors
from app.models import BloodRequest, DonorProfile, User


admin = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view_function(*args, **kwargs)

    return wrapped_view


@admin.route("")
@login_required
@admin_required
def dashboard():
    stats = {
        "users": db.session.scalar(db.select(func.count()).select_from(User)),
        "donors": db.session.scalar(
            db.select(func.count()).select_from(DonorProfile)
        ),
        "requests": db.session.scalar(
            db.select(func.count()).select_from(BloodRequest)
        ),
        "pending": db.session.scalar(
            db.select(func.count())
            .select_from(DonorProfile)
            .where(DonorProfile.verification_status == "Pending")
        )
        + db.session.scalar(
            db.select(func.count())
            .select_from(BloodRequest)
            .where(BloodRequest.status == "Pending")
        ),
    }
    recent_users = db.session.scalars(
        db.select(User).order_by(User.created_at.desc()).limit(5)
    ).all()
    recent_requests = db.session.scalars(
        db.select(BloodRequest).order_by(BloodRequest.created_at.desc()).limit(5)
    ).all()
    return render_template(
        "admin_dashboard.html",
        stats=stats,
        recent_users=recent_users,
        recent_requests=recent_requests,
    )


@admin.route("/users")
@login_required
@admin_required
def users():
    users = db.session.scalars(
        db.select(User).order_by(User.created_at.desc())
    ).all()
    return render_template("admin_users.html", users=users)


@admin.route("/donors")
@login_required
@admin_required
def donors():
    donors = db.session.scalars(
        db.select(DonorProfile).order_by(DonorProfile.created_at.desc())
    ).all()
    return render_template("admin_donors.html", donors=donors)


@admin.route("/requests")
@login_required
@admin_required
def requests():
    requests = db.session.scalars(
        db.select(BloodRequest).order_by(BloodRequest.created_at.desc())
    ).all()
    return render_template("admin_requests.html", requests=requests)


def get_donor_or_404(donor_id):
    donor = db.session.get(DonorProfile, donor_id)
    if not donor:
        abort(404)
    return donor


def get_request_or_404(request_id):
    blood_request_record = db.session.get(BloodRequest, request_id)
    if not blood_request_record:
        abort(404)
    return blood_request_record


@admin.route("/donors/<int:donor_id>")
@login_required
@admin_required
def donor_detail(donor_id):
    donor = get_donor_or_404(donor_id)
    return render_template("admin_donor_detail.html", donor=donor)


@admin.route("/donors/<int:donor_id>/verify", methods=["POST"])
@login_required
@admin_required
def verify_donor(donor_id):
    donor = get_donor_or_404(donor_id)
    if donor.verification_status != "Pending":
        flash("Only pending donor profiles can be reviewed.", "warning")
        return redirect(url_for("admin.donor_detail", donor_id=donor.id))

    donor.verification_status = "Verified"
    donor.reviewed_by = current_user
    donor.reviewed_at = datetime.now(timezone.utc)
    donor.rejection_reason = None
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Donor verification could not be saved.", "danger")
    else:
        flash("Donor profile verified.", "success")
    return redirect(url_for("admin.donor_detail", donor_id=donor.id))


@admin.route("/donors/<int:donor_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_donor(donor_id):
    donor = get_donor_or_404(donor_id)
    if donor.verification_status != "Pending":
        flash("Only pending donor profiles can be reviewed.", "warning")
        return redirect(url_for("admin.donor_detail", donor_id=donor.id))

    reason = request.form.get("rejection_reason", "").strip()
    if not reason:
        flash("Rejection reason is required.", "danger")
        return redirect(url_for("admin.donor_detail", donor_id=donor.id))
    if len(reason) > 500:
        flash("Rejection reason must be 500 characters or fewer.", "danger")
        return redirect(url_for("admin.donor_detail", donor_id=donor.id))

    donor.verification_status = "Rejected"
    donor.reviewed_by = current_user
    donor.reviewed_at = datetime.now(timezone.utc)
    donor.rejection_reason = reason
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Donor rejection could not be saved.", "danger")
    else:
        flash("Donor profile rejected.", "info")
    return redirect(url_for("admin.donor_detail", donor_id=donor.id))


@admin.route("/requests/<int:request_id>")
@login_required
@admin_required
def request_detail(request_id):
    blood_request_record = get_request_or_404(request_id)
    matched_donors = (
        find_matching_donors(blood_request_record)
        if blood_request_record.status == "Verified"
        else []
    )
    return render_template(
        "admin_request_detail.html",
        blood_request_record=blood_request_record,
        matched_donors=matched_donors,
    )


@admin.route("/requests/<int:request_id>/verify", methods=["POST"])
@login_required
@admin_required
def verify_request(request_id):
    blood_request_record = get_request_or_404(request_id)
    if blood_request_record.status != "Pending":
        flash("Only pending blood requests can be reviewed.", "warning")
        return redirect(url_for("admin.request_detail", request_id=request_id))
    if not blood_request_record.prescription_filename:
        flash("A doctor prescription is required before verification.", "danger")
        return redirect(url_for("admin.request_detail", request_id=request_id))

    blood_request_record.status = "Verified"
    blood_request_record.reviewed_by = current_user
    blood_request_record.reviewed_at = datetime.now(timezone.utc)
    blood_request_record.rejection_reason = None
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Request verification could not be saved.", "danger")
    else:
        flash("Blood request verified.", "success")
    return redirect(url_for("admin.request_detail", request_id=request_id))


@admin.route("/requests/<int:request_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_request(request_id):
    blood_request_record = get_request_or_404(request_id)
    if blood_request_record.status != "Pending":
        flash("Only pending blood requests can be reviewed.", "warning")
        return redirect(url_for("admin.request_detail", request_id=request_id))

    reason = request.form.get("rejection_reason", "").strip()
    if not reason:
        flash("Rejection reason is required.", "danger")
        return redirect(url_for("admin.request_detail", request_id=request_id))
    if len(reason) > 500:
        flash("Rejection reason must be 500 characters or fewer.", "danger")
        return redirect(url_for("admin.request_detail", request_id=request_id))

    blood_request_record.status = "Rejected"
    blood_request_record.reviewed_by = current_user
    blood_request_record.reviewed_at = datetime.now(timezone.utc)
    blood_request_record.rejection_reason = reason
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Request rejection could not be saved.", "danger")
    else:
        flash("Blood request rejected.", "info")
    return redirect(url_for("admin.request_detail", request_id=request_id))
