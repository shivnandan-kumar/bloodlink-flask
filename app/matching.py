from sqlalchemy import case, func

from app.extensions import db
from app.models import DonorProfile, User


def find_matching_donors(blood_request_record):
    normalized_city = blood_request_record.city.strip().lower()
    base_query = (
        db.select(DonorProfile)
        .join(User, DonorProfile.user_id == User.id)
        .where(
            DonorProfile.verification_status == "Verified",
            DonorProfile.is_available.is_(True),
            DonorProfile.medical_eligible.is_(True),
            User.blood_group == blood_request_record.blood_group,
            func.lower(User.city) == normalized_city,
            User.id != blood_request_record.requester_id,
        )
    )
    normalized_pincode = (blood_request_record.pincode or "").strip()
    if normalized_pincode:
        pincode_matches = db.session.scalars(
            base_query.where(User.pincode == normalized_pincode).order_by(User.name.asc())
        ).all()
        if pincode_matches:
            return pincode_matches

    if normalized_pincode:
        return db.session.scalars(
            base_query.order_by(
                case((User.pincode == normalized_pincode, 0), else_=1),
                User.name.asc(),
            )
        ).all()

    return db.session.scalars(base_query.order_by(User.name.asc())).all()


def donor_match_level(donor_profile, blood_request_record):
    if (
        blood_request_record.pincode
        and donor_profile.user.pincode
        and donor_profile.user.pincode == blood_request_record.pincode
    ):
        return "Pincode match"
    return "City match"
