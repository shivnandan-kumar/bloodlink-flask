from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from app.constants import BLOOD_GROUPS, URGENCY_LEVELS
from app.extensions import db
from app.models import BloodRequest


blood_request = Blueprint("blood_request", __name__, url_prefix="/requests")


def validate_request_form():
    errors = []
    patient_name = request.form.get("patient_name", "").strip()
    blood_group = request.form.get("blood_group", "").strip()
    units_text = request.form.get("units_required", "").strip()
    hospital_name = request.form.get("hospital_name", "").strip()
    city = request.form.get("city", "").strip()
    hospital_address = request.form.get("hospital_address", "").strip()
    contact_phone = request.form.get("contact_phone", "").strip()
    needed_by_text = request.form.get("needed_by", "").strip()
    urgency = request.form.get("urgency", "").strip()
    reason = request.form.get("reason", "").strip()

    if not patient_name:
        errors.append("Patient name is required.")
    if blood_group not in BLOOD_GROUPS:
        errors.append("Please select a valid blood group.")

    try:
        units_required = int(units_text)
    except ValueError:
        units_required = 0
    if units_required < 1 or units_required > 10:
        errors.append("Units required must be between 1 and 10.")

    if not hospital_name:
        errors.append("Hospital name is required.")
    if not city:
        errors.append("City is required.")
    if not hospital_address:
        errors.append("Hospital address is required.")

    phone_digits = "".join(
        character for character in contact_phone if character.isdigit()
    )
    if len(phone_digits) < 10 or len(phone_digits) > 15:
        errors.append("Please enter a valid contact phone number.")
    normalized_phone = (
        f"+{phone_digits}" if contact_phone.startswith("+") else phone_digits
    )

    needed_by = None
    try:
        needed_by = date.fromisoformat(needed_by_text)
        if needed_by < date.today():
            errors.append("Required date cannot be in the past.")
    except ValueError:
        errors.append("Please enter a valid required date.")

    if urgency not in URGENCY_LEVELS:
        errors.append("Please select a valid urgency level.")
    if len(reason) > 500:
        errors.append("Reason must be 500 characters or fewer.")

    for error in errors:
        flash(error, "danger")

    if errors:
        return None

    return {
        "patient_name": patient_name,
        "blood_group": blood_group,
        "units_required": units_required,
        "hospital_name": hospital_name,
        "city": city,
        "hospital_address": hospital_address,
        "contact_phone": normalized_phone,
        "needed_by": needed_by,
        "urgency": urgency,
        "reason": reason or None,
    }


def get_owned_request_or_404(request_id):
    blood_request_record = db.session.get(BloodRequest, request_id)
    if not blood_request_record:
        abort(404)
    if blood_request_record.requester_id != current_user.id:
        abort(403)
    return blood_request_record


@blood_request.route("")
@login_required
def index():
    requests = db.session.scalars(
        db.select(BloodRequest)
        .where(BloodRequest.requester_id == current_user.id)
        .order_by(BloodRequest.created_at.desc())
    ).all()
    return render_template("blood_request_list.html", requests=requests)


@blood_request.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        data = validate_request_form()
        if data:
            blood_request_record = BloodRequest(
                requester=current_user,
                **data,
            )
            try:
                db.session.add(blood_request_record)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash("Blood request could not be created. Please try again.", "danger")
            else:
                flash("Blood request submitted for verification.", "success")
                return redirect(
                    url_for("blood_request.detail", request_id=blood_request_record.id)
                )

    return render_template(
        "blood_request_form.html",
        blood_groups=BLOOD_GROUPS,
        urgency_levels=URGENCY_LEVELS,
        blood_request_record=None,
        page_title="Create blood request",
        submit_label="Submit request",
    )


@blood_request.route("/<int:request_id>")
@login_required
def detail(request_id):
    blood_request_record = get_owned_request_or_404(request_id)
    return render_template(
        "blood_request_detail.html",
        blood_request_record=blood_request_record,
    )


@blood_request.route("/<int:request_id>/edit", methods=["GET", "POST"])
@login_required
def edit(request_id):
    blood_request_record = get_owned_request_or_404(request_id)
    if blood_request_record.status != "Pending":
        flash("Only pending requests can be edited.", "warning")
        return redirect(url_for("blood_request.detail", request_id=request_id))

    if request.method == "POST":
        data = validate_request_form()
        if data:
            for field, value in data.items():
                setattr(blood_request_record, field, value)
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash("Blood request could not be updated. Please try again.", "danger")
            else:
                flash("Blood request updated.", "success")
                return redirect(url_for("blood_request.detail", request_id=request_id))

    return render_template(
        "blood_request_form.html",
        blood_groups=BLOOD_GROUPS,
        urgency_levels=URGENCY_LEVELS,
        blood_request_record=blood_request_record,
        page_title="Edit blood request",
        submit_label="Save changes",
    )


@blood_request.route("/<int:request_id>/cancel", methods=["POST"])
@login_required
def cancel(request_id):
    blood_request_record = get_owned_request_or_404(request_id)
    if blood_request_record.status not in ("Pending", "Verified"):
        flash("This request cannot be cancelled.", "warning")
        return redirect(url_for("blood_request.detail", request_id=request_id))

    blood_request_record.status = "Cancelled"
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Blood request could not be cancelled. Please try again.", "danger")
    else:
        flash("Blood request cancelled.", "info")
    return redirect(url_for("blood_request.detail", request_id=request_id))

