from sqlalchemy import func

from app.extensions import db
from app.models import DonorProfile, User


def find_matching_donors(blood_request_record):
    normalized_city = blood_request_record.city.strip().lower()
    return db.session.scalars(
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
        .order_by(User.name.asc())
    ).all()

