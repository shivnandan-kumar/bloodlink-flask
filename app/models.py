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
    is_email_verified = db.Column(
        db.Boolean,
        default=False,
        server_default=db.true(),
        nullable=False,
    )
    email_otp_hash = db.Column(db.String(255), nullable=True)
    email_otp_expires_at = db.Column(db.DateTime, nullable=True)
    email_otp_sent_at = db.Column(db.DateTime, nullable=True)
    email_otp_attempts = db.Column(
        db.Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
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
    notifications = db.relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
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
    donation_count = db.Column(
        db.Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
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
    donations = db.relationship(
        "Donation",
        back_populates="donor_profile",
        lazy="select",
    )

    def __repr__(self):
        return f"<DonorProfile user_id={self.user_id}>"

    def reward_badge_title(self):
        if self.donation_count >= 5:
            return "Gold LifeSaver"
        if self.donation_count >= 3:
            return "Silver Savior"
        if self.donation_count >= 1:
            return "Bronze Hero"
        return "New Donor"

    def reward_badge_class(self):
        if self.donation_count >= 5:
            return "gold"
        if self.donation_count >= 3:
            return "silver"
        if self.donation_count >= 1:
            return "bronze"
        return "starter"


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
    donations = db.relationship(
        "Donation",
        back_populates="blood_request",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<BloodRequest id={self.id} status={self.status}>"


class Donation(db.Model):
    __table_args__ = (
        db.UniqueConstraint(
            "blood_request_id",
            "donor_profile_id",
            name="uq_donation_request_donor",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    blood_request_id = db.Column(
        db.Integer,
        db.ForeignKey("blood_request.id"),
        nullable=False,
        index=True,
    )
    donor_profile_id = db.Column(
        db.Integer,
        db.ForeignKey("donor_profile.id"),
        nullable=False,
        index=True,
    )
    status = db.Column(db.String(30), default="Invited", nullable=False, index=True)
    invited_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    responded_at = db.Column(db.DateTime, nullable=True)
    donor_completed_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    blood_request = db.relationship("BloodRequest", back_populates="donations")
    donor_profile = db.relationship("DonorProfile", back_populates="donations")

    def __repr__(self):
        return f"<Donation id={self.id} status={self.status}>"


class Notification(db.Model):
    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "event_key",
            name="uq_notification_user_event_key",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(20), default="info", nullable=False)
    link = db.Column(db.String(255), nullable=True)
    event_key = db.Column(db.String(150), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    read_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification id={self.id} user_id={self.user_id}>"
