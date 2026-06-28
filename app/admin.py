from functools import wraps
from datetime import datetime, timezone

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.constants import BLOOD_GROUPS
from app.extensions import db
from app.matching import donor_match_level, find_matching_donors
from app.models import BloodRequest, Donation, DonorProfile, User
from app.notifications import (
    create_notification,
    notify_matching_requests_for_donor,
    notify_request_matches,
)


admin = Blueprint("admin", __name__, url_prefix="/admin")
DONOR_STATUSES = ("Pending", "Verified", "Rejected")
REQUEST_STATUSES = ("Pending", "Verified", "Rejected", "Fulfilled", "Cancelled")


def admin_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view_function(*args, **kwargs)

    return wrapped_view


def percentage(count, total):
    if not total:
        return 0
    return round((count / total) * 100)


def build_count_rows(labels, count_map, total):
    rows = []
    for label in labels:
        count = count_map.get(label, 0)
        rows.append(
            {
                "label": label,
                "count": count,
                "percent": percentage(count, total),
            }
        )
    return rows


@admin.route("")
@login_required
@admin_required
def dashboard():
    total_users = db.session.scalar(db.select(func.count()).select_from(User)) or 0
    total_donors = (
        db.session.scalar(db.select(func.count()).select_from(DonorProfile)) or 0
    )
    total_requests = (
        db.session.scalar(db.select(func.count()).select_from(BloodRequest)) or 0
    )
    pending_donors = (
        db.session.scalar(
            db.select(func.count())
            .select_from(DonorProfile)
            .where(DonorProfile.verification_status == "Pending")
        )
        or 0
    )
    pending_requests = (
        db.session.scalar(
            db.select(func.count())
            .select_from(BloodRequest)
            .where(BloodRequest.status == "Pending")
        )
        or 0
    )
    stats = {
        "users": total_users,
        "donors": total_donors,
        "requests": total_requests,
        "pending": pending_donors + pending_requests,
    }
    blood_group_counts = dict(
        db.session.execute(
            db.select(User.blood_group, func.count(User.id))
            .group_by(User.blood_group)
        ).all()
    )
    donor_status_counts = dict(
        db.session.execute(
            db.select(DonorProfile.verification_status, func.count(DonorProfile.id))
            .group_by(DonorProfile.verification_status)
        ).all()
    )
    request_status_counts = dict(
        db.session.execute(
            db.select(BloodRequest.status, func.count(BloodRequest.id))
            .group_by(BloodRequest.status)
        ).all()
    )
    completed_donation_count = (
        db.session.scalar(
            db.select(func.count())
            .select_from(Donation)
            .where(Donation.status == "Completed")
        )
        or 0
    )
    emergency_request_count = (
        db.session.scalar(
            db.select(func.count())
            .select_from(BloodRequest)
            .where(BloodRequest.is_emergency.is_(True))
        )
        or 0
    )
    available_verified_donors = (
        db.session.scalar(
            db.select(func.count())
            .select_from(DonorProfile)
            .where(
                DonorProfile.verification_status == "Verified",
                DonorProfile.is_available.is_(True),
                DonorProfile.medical_eligible.is_(True),
            )
        )
        or 0
    )
    top_donors = db.session.scalars(
        db.select(DonorProfile)
        .join(DonorProfile.user)
        .where(DonorProfile.donation_count > 0)
        .order_by(DonorProfile.donation_count.desc(), User.name.asc())
        .limit(5)
    ).all()
    analytics = {
        "blood_groups": build_count_rows(
            BLOOD_GROUPS,
            blood_group_counts,
            max(blood_group_counts.values(), default=0),
        ),
        "donor_statuses": build_count_rows(
            DONOR_STATUSES,
            donor_status_counts,
            total_donors,
        ),
        "request_statuses": build_count_rows(
            REQUEST_STATUSES,
            request_status_counts,
            total_requests,
        ),
        "completed_donations": completed_donation_count,
        "emergency_requests": emergency_request_count,
        "available_verified_donors": available_verified_donors,
        "top_donors": top_donors,
    }
    recent_users = db.session.scalars(
        db.select(User).order_by(User.created_at.desc()).limit(5)
    ).all()
    recent_requests = db.session.scalars(
        db.select(BloodRequest)
        .order_by(BloodRequest.is_emergency.desc(), BloodRequest.created_at.desc())
        .limit(5)
    ).all()
    return render_template(
        "admin_dashboard.html",
        stats=stats,
        analytics=analytics,
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
        db.select(BloodRequest).order_by(
            BloodRequest.is_emergency.desc(),
            BloodRequest.created_at.desc(),
        )
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
    if not donor.blood_group_proof_filename:
        flash("Blood group proof is required before donor verification.", "danger")
        return redirect(url_for("admin.donor_detail", donor_id=donor.id))

    donor.verification_status = "Verified"
    donor.reviewed_by = current_user
    donor.reviewed_at = datetime.now(timezone.utc)
    donor.rejection_reason = None
    try:
        create_notification(
            user_id=donor.user_id,
            title="Donor profile verified",
            message="Your donor profile has been verified and can now appear in donor matching.",
            category="success",
            link="/donor/profile",
            event_key=f"donor-{donor.id}-verified-{donor.updated_at.isoformat()}",
        )
        notify_matching_requests_for_donor(donor)
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
        create_notification(
            user_id=donor.user_id,
            title="Donor profile needs changes",
            message=f"Your donor profile was rejected. Reason: {reason}",
            category="warning",
            link="/donor/profile",
            event_key=f"donor-{donor.id}-rejected-{donor.updated_at.isoformat()}",
        )
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
        donor_match_level=donor_match_level,
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
        create_notification(
            user_id=blood_request_record.requester_id,
            title="Blood request verified",
            message=f"Blood request #{blood_request_record.id} has been verified.",
            category="success",
            link=f"/requests/{blood_request_record.id}",
            event_key=f"blood-request-{blood_request_record.id}-verified-{blood_request_record.updated_at.isoformat()}",
        )
        notify_request_matches(
            blood_request_record,
            find_matching_donors(blood_request_record),
        )
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
        create_notification(
            user_id=blood_request_record.requester_id,
            title="Blood request needs changes",
            message=f"Blood request #{blood_request_record.id} was rejected. Reason: {reason}",
            category="warning",
            link=f"/requests/{blood_request_record.id}",
            event_key=f"blood-request-{blood_request_record.id}-rejected-{blood_request_record.updated_at.isoformat()}",
        )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Request rejection could not be saved.", "danger")
    else:
        flash("Blood request rejected.", "info")
    return redirect(url_for("admin.request_detail", request_id=request_id))
