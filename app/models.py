from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    donor_profile = db.relationship(
        "DonorProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="DonorProfile.user_id",
        uselist=False,
    )
    blood_requests = db.relationship(
        "BloodRequest",
        back_populates="requester",
        cascade="all, delete-orphan",
        foreign_keys="BloodRequest.requester_id",
        lazy="select",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class DonorProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        unique=True,
        nullable=False,
    )
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    last_donation_date = db.Column(db.Date, nullable=True)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    medical_eligible = db.Column(db.Boolean, default=False, nullable=False)
    blood_group_proof_filename = db.Column(db.String(100), nullable=True)
    blood_group_proof_original_name = db.Column(db.String(255), nullable=True)
    verification_status = db.Column(
        db.String(20),
        default="Pending",
        nullable=False,
    )
    reviewed_by_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "user.id",
            name="fk_donor_profile_reviewed_by_id_user",
        ),
        nullable=True,
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.String(500), nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship(
        "User",
        back_populates="donor_profile",
        foreign_keys=[user_id],
    )
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])

    def __repr__(self):
        return f"<DonorProfile user_id={self.user_id}>"


class BloodRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True,
    )
    patient_name = db.Column(db.String(100), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    units_required = db.Column(db.Integer, nullable=False)
    hospital_name = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    hospital_address = db.Column(db.String(255), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    needed_by = db.Column(db.Date, nullable=False)
    urgency = db.Column(db.String(20), default="Normal", nullable=False)
    reason = db.Column(db.String(500), nullable=True)
    prescription_filename = db.Column(db.String(100), nullable=True)
    prescription_original_name = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default="Pending", nullable=False)
    reviewed_by_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "user.id",
            name="fk_blood_request_reviewed_by_id_user",
        ),
        nullable=True,
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.String(500), nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    requester = db.relationship(
        "User",
        back_populates="blood_requests",
        foreign_keys=[requester_id],
    )
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])

    def __repr__(self):
        return f"<BloodRequest id={self.id} status={self.status}>"
