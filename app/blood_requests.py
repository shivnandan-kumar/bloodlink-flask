from datetime import date, datetime, timezone

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from app.constants import BLOOD_GROUPS, URGENCY_LEVELS
from app.extensions import db
from app.matching import donor_match_level, find_matching_donors
from app.models import BloodRequest, Donation, DonorProfile, User
from app.notifications import create_notification, notify_admins
from app.uploads import (
    UploadValidationError,
    delete_prescription,
    prescription_upload_directory,
    save_prescription,
)


blood_request = Blueprint("blood_request", __name__, url_prefix="/requests")


def validate_request_form():
    errors = []
    patient_name = request.form.get("patient_name", "").strip()
    blood_group = request.form.get("blood_group", "").strip()
    units_text = request.form.get("units_required", "").strip()
    hospital_name = request.form.get("hospital_name", "").strip()
    city = request.form.get("city", "").strip()
    pincode = "".join(
        character
        for character in request.form.get("pincode", "").strip()
        if character.isdigit()
    )
    hospital_address = request.form.get("hospital_address", "").strip()
    contact_phone = request.form.get("contact_phone", "").strip()
    needed_by_text = request.form.get("needed_by", "").strip()
    urgency = request.form.get("urgency", "").strip()
    is_emergency = request.form.get("is_emergency") == "on"
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
    if len(pincode) != 6:
        errors.append("Please enter a valid 6-digit pincode.")
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
        "pincode": pincode,
        "hospital_address": hospital_address,
        "contact_phone": normalized_phone,
        "needed_by": needed_by,
        "urgency": urgency,
        "is_emergency": is_emergency,
        "reason": reason or None,
    }


def notify_emergency_donors(blood_request_record):
    donors = db.session.scalars(
        db.select(DonorProfile)
        .join(DonorProfile.user)
        .where(
            db.func.lower(User.city) == blood_request_record.city.lower(),
            DonorProfile.user_id != blood_request_record.requester_id,
            DonorProfile.verification_status == "Verified",
            DonorProfile.is_available.is_(True),
            DonorProfile.medical_eligible.is_(True),
        )
    ).all()
    for donor_profile in donors:
        create_notification(
            user_id=donor_profile.user_id,
            title="Emergency blood request in your city",
            message=(
                f"An emergency {blood_request_record.blood_group} blood request "
                f"was submitted at {blood_request_record.hospital_name}, "
                f"{blood_request_record.city}. Admin verification is in progress."
            ),
            category="warning",
            link="/donations",
            event_key=(
                f"emergency-request-{blood_request_record.id}-"
                f"donor-{donor_profile.id}"
            ),
        )


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
            try:
                saved_name, original_name = save_prescription(
                    request.files.get("prescription")
                )
            except UploadValidationError as error:
                flash(str(error), "danger")
                return render_template(
                    "blood_request_form.html",
                    blood_groups=BLOOD_GROUPS,
                    urgency_levels=URGENCY_LEVELS,
                    blood_request_record=None,
                    page_title="Create blood request",
                    submit_label="Submit request",
                )
            blood_request_record = BloodRequest(
                requester=current_user,
                prescription_filename=saved_name,
                prescription_original_name=original_name,
                **data,
            )
            try:
                db.session.add(blood_request_record)
                db.session.flush()
                notify_admins(
                    title="New blood request needs review",
                    message=(
                        f"{current_user.name} submitted a "
                        f"{blood_request_record.blood_group} request at "
                        f"{blood_request_record.hospital_name}."
                    ),
                    category="warning" if blood_request_record.is_emergency else "review",
                    link=f"/admin/requests/{blood_request_record.id}",
                    event_key=f"blood-request-{blood_request_record.id}-submitted",
                )
                if blood_request_record.is_emergency:
                    notify_emergency_donors(blood_request_record)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                delete_prescription(saved_name)
                flash("Blood request could not be created. Please try again.", "danger")
            else:
                flash(
                    (
                        "Emergency request submitted for priority verification."
                        if blood_request_record.is_emergency
                        else "Blood request submitted for verification."
                    ),
                    "success",
                )
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
    completed_units = db.session.scalar(
        db.select(db.func.count())
        .select_from(Donation)
        .where(
            Donation.blood_request_id == request_id,
            Donation.status == "Completed",
        )
    )
    return render_template(
        "blood_request_detail.html",
        blood_request_record=blood_request_record,
        completed_units=completed_units,
    )


@blood_request.route("/<int:request_id>/prescription")
@login_required
def prescription(request_id):
    blood_request_record = db.session.get(BloodRequest, request_id)
    if not blood_request_record:
        abort(404)
    if blood_request_record.requester_id != current_user.id and not current_user.is_admin:
        abort(403)
    if not blood_request_record.prescription_filename:
        abort(404)

    return send_from_directory(
        prescription_upload_directory(),
        blood_request_record.prescription_filename,
        download_name=blood_request_record.prescription_original_name,
    )


@blood_request.route("/<int:request_id>/matches")
@login_required
def matches(request_id):
    blood_request_record = get_owned_request_or_404(request_id)
    if blood_request_record.status != "Verified":
        flash("Donor matches are available after request verification.", "warning")
        return redirect(url_for("blood_request.detail", request_id=request_id))

    donors = find_matching_donors(blood_request_record)
    invitations = db.session.scalars(
        db.select(Donation).where(Donation.blood_request_id == request_id)
    ).all()
    return render_template(
        "blood_request_matches.html",
        blood_request_record=blood_request_record,
        donors=donors,
        invitations_by_donor={
            invitation.donor_profile_id: invitation for invitation in invitations
        },
        donor_match_level=donor_match_level,
    )


@blood_request.route("/<int:request_id>/edit", methods=["GET", "POST"])
@login_required
def edit(request_id):
    blood_request_record = get_owned_request_or_404(request_id)
    if blood_request_record.status not in ("Pending", "Rejected"):
        flash("Only pending or rejected requests can be edited.", "warning")
        return redirect(url_for("blood_request.detail", request_id=request_id))

    if request.method == "POST":
        data = validate_request_form()
        if data:
            was_emergency = blood_request_record.is_emergency
            new_saved_name = None
            uploaded_file = request.files.get("prescription")
            if uploaded_file and uploaded_file.filename:
                try:
                    new_saved_name, new_original_name = save_prescription(uploaded_file)
                except UploadValidationError as error:
                    flash(str(error), "danger")
                    return redirect(
                        url_for("blood_request.edit", request_id=request_id)
                    )
            elif not blood_request_record.prescription_filename:
                flash("Doctor prescription is required.", "danger")
                return redirect(url_for("blood_request.edit", request_id=request_id))

            old_saved_name = blood_request_record.prescription_filename
            for field, value in data.items():
                setattr(blood_request_record, field, value)
            if new_saved_name:
                blood_request_record.prescription_filename = new_saved_name
                blood_request_record.prescription_original_name = new_original_name
            blood_request_record.status = "Pending"
            blood_request_record.reviewed_by_id = None
            blood_request_record.reviewed_at = None
            blood_request_record.rejection_reason = None
            try:
                if blood_request_record.is_emergency and not was_emergency:
                    notify_emergency_donors(blood_request_record)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                delete_prescription(new_saved_name)
                flash("Blood request could not be updated. Please try again.", "danger")
            else:
                if new_saved_name:
                    delete_prescription(old_saved_name)
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
        open_donations = db.session.scalars(
            db.select(Donation).where(
                Donation.blood_request_id == request_id,
                Donation.status.in_(("Invited", "Accepted")),
            )
        ).all()
        for donation_record in open_donations:
            donation_record.status = "Cancelled"
            donation_record.cancelled_at = datetime.now(timezone.utc)
            create_notification(
                user_id=donation_record.donor_profile.user_id,
                title="Donation invitation cancelled",
                message=f"The blood request for {blood_request_record.patient_name} was cancelled.",
                category="info",
                link="/donations",
                event_key=f"donation-{donation_record.id}-request-cancelled",
            )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Blood request could not be cancelled. Please try again.", "danger")
    else:
        flash("Blood request cancelled.", "info")
    return redirect(url_for("blood_request.detail", request_id=request_id))
