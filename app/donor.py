from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from app.constants import BLOOD_GROUPS
from app.extensions import db
from app.models import DonorProfile


donor = Blueprint("donor", __name__, url_prefix="/donor")
GENDERS = ("Male", "Female", "Other")


def validate_donor_form():
    errors = []
    age_text = request.form.get("age", "").strip()
    gender = request.form.get("gender", "").strip()
    phone = request.form.get("phone", "").strip()
    city = request.form.get("city", "").strip()
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
            profile = DonorProfile(
                user=current_user,
                age=data["age"],
                gender=data["gender"],
                phone=data["phone"],
                address=data["address"],
                last_donation_date=data["last_donation_date"],
                is_available=data["is_available"],
                medical_eligible=data["medical_eligible"],
            )
            current_user.city = data["city"]
            current_user.blood_group = data["blood_group"]

            try:
                db.session.add(profile)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
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


@donor.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    donor_profile = current_user.donor_profile
    if not donor_profile:
        return redirect(url_for("donor.register"))

    if request.method == "POST":
        data = validate_donor_form()
        if data:
            donor_profile.age = data["age"]
            donor_profile.gender = data["gender"]
            donor_profile.phone = data["phone"]
            donor_profile.address = data["address"]
            donor_profile.last_donation_date = data["last_donation_date"]
            donor_profile.is_available = data["is_available"]
            donor_profile.medical_eligible = data["medical_eligible"]
            donor_profile.verification_status = "Pending"
            donor_profile.reviewed_by_id = None
            donor_profile.reviewed_at = None
            donor_profile.rejection_reason = None
            current_user.city = data["city"]
            current_user.blood_group = data["blood_group"]

            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash(
                    "Donor profile could not be updated. The phone number may already be in use.",
                    "danger",
                )
            else:
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
