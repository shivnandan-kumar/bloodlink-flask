from datetime import date

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

from app.constants import BLOOD_GROUPS
from app.extensions import db
from app.models import DonorProfile
from app.notifications import notify_admins
from app.uploads import (
    UploadValidationError,
    blood_group_proof_upload_directory,
    delete_blood_group_proof,
    save_blood_group_proof,
)


donor = Blueprint("donor", __name__, url_prefix="/donor")
GENDERS = ("Male", "Female", "Other")


def validate_donor_form():
    errors = []
    age_text = request.form.get("age", "").strip()
    gender = request.form.get("gender", "").strip()
    phone = request.form.get("phone", "").strip()
    city = request.form.get("city", "").strip()
    pincode = "".join(
        character
        for character in request.form.get("pincode", "").strip()
        if character.isdigit()
    )
    blood_group = request.form.get("blood_group", "").strip()
    address = request.form.get("address", "").strip()
    last_donation_text = request.form.get("last_donation_date", "").strip()
    is_available = request.form.get("is_available") == "on"
    medical_eligible = request.form.get("medical_eligible") == "on"

    try:
        age = int(age_text)
    except ValueError:
        age = 0

    if age < 18 or age > 65:
        errors.append("Age must be between 18 and 65 years.")
    if gender not in GENDERS:
        errors.append("Please select a valid gender.")

    phone_digits = "".join(character for character in phone if character.isdigit())
    if len(phone_digits) < 10 or len(phone_digits) > 15:
        errors.append("Please enter a valid phone number.")
    normalized_phone = f"+{phone_digits}" if phone.startswith("+") else phone_digits
    if not city:
        errors.append("City is required.")
    if len(pincode) != 6:
        errors.append("Please enter a valid 6-digit pincode.")
    if blood_group not in BLOOD_GROUPS:
        errors.append("Please select a valid blood group.")
    if not address:
        errors.append("Address is required.")
    if not medical_eligible:
        errors.append("Please confirm the health declaration.")

    last_donation_date = None
    if last_donation_text:
        try:
            last_donation_date = date.fromisoformat(last_donation_text)
            if last_donation_date > date.today():
                errors.append("Last donation date cannot be in the future.")
        except ValueError:
            errors.append("Please enter a valid last donation date.")

    for error in errors:
        flash(error, "danger")

    if errors:
        return None

    return {
        "age": age,
        "gender": gender,
        "phone": normalized_phone,
        "city": city,
        "pincode": pincode,
        "blood_group": blood_group,
        "address": address,
        "last_donation_date": last_donation_date,
        "is_available": is_available,
        "medical_eligible": medical_eligible,
    }


@donor.route("/register", methods=["GET", "POST"])
@login_required
def register():
    if current_user.donor_profile:
        flash("Your donor profile already exists.", "info")
        return redirect(url_for("donor.profile"))

    if request.method == "POST":
        data = validate_donor_form()
        if data:
            try:
                saved_name, original_name = save_blood_group_proof(
                    request.files.get("blood_group_proof")
                )
            except UploadValidationError as error:
                flash(str(error), "danger")
                return render_template(
                    "donor_form.html",
                    blood_groups=BLOOD_GROUPS,
                    genders=GENDERS,
                    donor_profile=None,
                    page_title="Become a donor",
                    submit_label="Submit donor profile",
                )
            profile = DonorProfile(
                user=current_user,
                age=data["age"],
                gender=data["gender"],
                phone=data["phone"],
                address=data["address"],
                last_donation_date=data["last_donation_date"],
                is_available=data["is_available"],
                medical_eligible=data["medical_eligible"],
                blood_group_proof_filename=saved_name,
                blood_group_proof_original_name=original_name,
            )
            current_user.city = data["city"]
            current_user.pincode = data["pincode"]
            current_user.blood_group = data["blood_group"]

            try:
                db.session.add(profile)
                db.session.flush()
                notify_admins(
                    title="New donor verification request",
                    message=(
                        f"{current_user.name} submitted a donor profile for "
                        "admin verification."
                    ),
                    category="review",
                    link=f"/admin/donors/{profile.id}",
                    event_key=f"donor-profile-{profile.id}-submitted",
                )
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                delete_blood_group_proof(saved_name)
                flash(
                    "Donor profile could not be saved. The phone number may already be in use.",
                    "danger",
                )
            else:
                flash("Donor profile submitted for verification.", "success")
                return redirect(url_for("donor.profile"))

    return render_template(
        "donor_form.html",
        blood_groups=BLOOD_GROUPS,
        genders=GENDERS,
        donor_profile=None,
        page_title="Become a donor",
        submit_label="Submit donor profile",
    )


@donor.route("/profile")
@login_required
def profile():
    donor_profile = current_user.donor_profile
    if not donor_profile:
        flash("Create your donor profile first.", "info")
        return redirect(url_for("donor.register"))
    return render_template("donor_profile.html", donor_profile=donor_profile)


@donor.route("/<int:donor_id>/blood-group-proof")
@login_required
def blood_group_proof(donor_id):
    donor_profile = db.session.get(DonorProfile, donor_id)
    if not donor_profile:
        abort(404)
    if donor_profile.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    if not donor_profile.blood_group_proof_filename:
        abort(404)

    return send_from_directory(
        blood_group_proof_upload_directory(),
        donor_profile.blood_group_proof_filename,
        download_name=donor_profile.blood_group_proof_original_name,
    )


@donor.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    donor_profile = current_user.donor_profile
    if not donor_profile:
        return redirect(url_for("donor.register"))

    if request.method == "POST":
        data = validate_donor_form()
        if data:
            new_saved_name = None
            uploaded_file = request.files.get("blood_group_proof")
            blood_group_changed = data["blood_group"] != current_user.blood_group
            if uploaded_file and uploaded_file.filename:
                try:
                    new_saved_name, new_original_name = save_blood_group_proof(
                        uploaded_file
                    )
                except UploadValidationError as error:
                    flash(str(error), "danger")
                    return redirect(url_for("donor.edit"))
            elif not donor_profile.blood_group_proof_filename or blood_group_changed:
                message = (
                    "Upload a new blood group proof when changing blood group."
                    if blood_group_changed
                    else "Blood group proof is required."
                )
                flash(message, "danger")
                return redirect(url_for("donor.edit"))

            old_saved_name = donor_profile.blood_group_proof_filename
            donor_profile.age = data["age"]
            donor_profile.gender = data["gender"]
            donor_profile.phone = data["phone"]
            donor_profile.address = data["address"]
            donor_profile.last_donation_date = data["last_donation_date"]
            donor_profile.is_available = data["is_available"]
            donor_profile.medical_eligible = data["medical_eligible"]
            if new_saved_name:
                donor_profile.blood_group_proof_filename = new_saved_name
                donor_profile.blood_group_proof_original_name = new_original_name
            donor_profile.verification_status = "Pending"
            donor_profile.reviewed_by_id = None
            donor_profile.reviewed_at = None
            donor_profile.rejection_reason = None
            current_user.city = data["city"]
            current_user.pincode = data["pincode"]
            current_user.blood_group = data["blood_group"]

            try:
                db.session.flush()
                notify_admins(
                    title="Donor profile needs review",
                    message=(
                        f"{current_user.name} updated donor details and needs "
                        "verification again."
                    ),
                    category="review",
                    link=f"/admin/donors/{donor_profile.id}",
                    event_key=f"donor-profile-{donor_profile.id}-resubmitted",
                )
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                delete_blood_group_proof(new_saved_name)
                flash(
                    "Donor profile could not be updated. The phone number may already be in use.",
                    "danger",
                )
            else:
                if new_saved_name:
                    delete_blood_group_proof(old_saved_name)
                flash("Donor profile updated and sent for verification.", "success")
                return redirect(url_for("donor.profile"))

    return render_template(
        "donor_form.html",
        blood_groups=BLOOD_GROUPS,
        genders=GENDERS,
        donor_profile=donor_profile,
        page_title="Edit donor profile",
        submit_label="Save changes",
    )
