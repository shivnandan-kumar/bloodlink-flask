from datetime import date, datetime, timezone

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.matching import find_matching_donors
from app.models import BloodRequest, Donation, DonorProfile
from app.notifications import create_notification


donation = Blueprint("donation", __name__, url_prefix="/donations")


def get_donation_or_404(donation_id):
    donation_record = db.session.get(Donation, donation_id)
    if not donation_record:
        abort(404)
    return donation_record


def get_donor_donation_or_403(donation_id):
    donation_record = get_donation_or_404(donation_id)
    donor_profile = current_user.donor_profile
    if not donor_profile or donation_record.donor_profile_id != donor_profile.id:
        abort(403)
    return donation_record


def get_requester_donation_or_403(donation_id):
    donation_record = get_donation_or_404(donation_id)
    if donation_record.blood_request.requester_id != current_user.id:
        abort(403)
    return donation_record


@donation.route("")
@login_required
def index():
    incoming = []
    if current_user.donor_profile:
        incoming = db.session.scalars(
            db.select(Donation)
            .where(Donation.donor_profile_id == current_user.donor_profile.id)
            .order_by(Donation.invited_at.desc())
        ).all()
    outgoing = db.session.scalars(
        db.select(Donation)
        .join(BloodRequest, Donation.blood_request_id == BloodRequest.id)
        .where(BloodRequest.requester_id == current_user.id)
        .order_by(Donation.invited_at.desc())
    ).all()
    return render_template(
        "donations.html",
        incoming=incoming,
        outgoing=outgoing,
    )


@donation.route(
    "/requests/<int:request_id>/donors/<int:donor_id>/invite",
    methods=["POST"],
)
@login_required
def invite(request_id, donor_id):
    blood_request_record = db.session.get(BloodRequest, request_id)
    donor_profile = db.session.get(DonorProfile, donor_id)
    if not blood_request_record or not donor_profile:
        abort(404)
    if blood_request_record.requester_id != current_user.id:
        abort(403)
    if blood_request_record.status != "Verified":
        flash("Donors can only be invited for a verified request.", "warning")
        return redirect(url_for("blood_request.detail", request_id=request_id))

    matching_ids = {donor.id for donor in find_matching_donors(blood_request_record)}
    if donor_profile.id not in matching_ids:
        flash("This donor is no longer available for matching.", "warning")
        return redirect(url_for("blood_request.matches", request_id=request_id))

    existing = db.session.scalar(
        db.select(Donation).where(
            Donation.blood_request_id == request_id,
            Donation.donor_profile_id == donor_id,
        )
    )
    if existing:
        flash("An invitation has already been sent to this donor.", "info")
        return redirect(url_for("blood_request.matches", request_id=request_id))

    donation_record = Donation(
        blood_request=blood_request_record,
        donor_profile=donor_profile,
    )
    try:
        db.session.add(donation_record)
        db.session.flush()
        create_notification(
            user_id=donor_profile.user_id,
            title="New donation invitation",
            message=(
                f"{current_user.name} invited you to donate {blood_request_record.blood_group} "
                f"blood for {blood_request_record.patient_name} at {blood_request_record.hospital_name}."
            ),
            category="match",
            link="/donations",
            event_key=f"donation-{donation_record.id}-invited",
        )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Donation invitation could not be sent.", "danger")
    else:
        flash("Donation invitation sent.", "success")
    return redirect(url_for("blood_request.matches", request_id=request_id))


@donation.route("/<int:donation_id>/accept", methods=["POST"])
@login_required
def accept(donation_id):
    donation_record = get_donor_donation_or_403(donation_id)
    if donation_record.status != "Invited":
        flash("Only a new invitation can be accepted.", "warning")
        return redirect(url_for("donation.index"))
    if donation_record.blood_request.status != "Verified":
        flash("This blood request is no longer active.", "warning")
        return redirect(url_for("donation.index"))

    donation_record.status = "Accepted"
    donation_record.responded_at = datetime.now(timezone.utc)
    try:
        create_notification(
            user_id=donation_record.blood_request.requester_id,
            title="Donor accepted your invitation",
            message=(
                f"{current_user.name} accepted the donation invitation for "
                f"{donation_record.blood_request.patient_name}."
            ),
            category="success",
            link="/donations",
            event_key=f"donation-{donation_record.id}-accepted",
        )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Donation response could not be saved.", "danger")
    else:
        flash("Invitation accepted. Contact the requester before donating.", "success")
    return redirect(url_for("donation.index"))


@donation.route("/<int:donation_id>/decline", methods=["POST"])
@login_required
def decline(donation_id):
    donation_record = get_donor_donation_or_403(donation_id)
    if donation_record.status != "Invited":
        flash("Only a new invitation can be declined.", "warning")
        return redirect(url_for("donation.index"))

    donation_record.status = "Declined"
    donation_record.responded_at = datetime.now(timezone.utc)
    try:
        create_notification(
            user_id=donation_record.blood_request.requester_id,
            title="Donor declined your invitation",
            message=(
                f"{current_user.name} is unable to donate for "
                f"{donation_record.blood_request.patient_name}."
            ),
            category="warning",
            link="/donations",
            event_key=f"donation-{donation_record.id}-declined",
        )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Donation response could not be saved.", "danger")
    else:
        flash("Invitation declined.", "info")
    return redirect(url_for("donation.index"))


@donation.route("/<int:donation_id>/donor-complete", methods=["POST"])
@login_required
def donor_complete(donation_id):
    donation_record = get_donor_donation_or_403(donation_id)
    if donation_record.status != "Accepted":
        flash("Accept the invitation before marking a donation complete.", "warning")
        return redirect(url_for("donation.index"))

    donation_record.status = "DonorCompleted"
    donation_record.donor_completed_at = datetime.now(timezone.utc)
    try:
        create_notification(
            user_id=donation_record.blood_request.requester_id,
            title="Donor marked donation complete",
            message=(
                f"{current_user.name} marked the donation for "
                f"{donation_record.blood_request.patient_name} complete. Confirm receipt now."
            ),
            category="success",
            link="/donations",
            event_key=f"donation-{donation_record.id}-donor-completed",
        )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Donation completion could not be saved.", "danger")
    else:
        flash("Donation marked complete. Waiting for requester confirmation.", "success")
    return redirect(url_for("donation.index"))


@donation.route("/<int:donation_id>/confirm", methods=["POST"])
@login_required
def confirm(donation_id):
    donation_record = get_requester_donation_or_403(donation_id)
    if donation_record.status != "DonorCompleted":
        flash("The donor must mark the donation complete first.", "warning")
        return redirect(url_for("donation.index"))

    now = datetime.now(timezone.utc)
    donation_record.status = "Completed"
    donation_record.completed_at = now
    donation_record.donor_profile.last_donation_date = date.today()
    donation_record.donor_profile.is_available = False
    try:
        db.session.flush()
        completed_units = db.session.scalar(
            db.select(db.func.count())
            .select_from(Donation)
            .where(
                Donation.blood_request_id == donation_record.blood_request_id,
                Donation.status == "Completed",
            )
        )
        request_fulfilled = completed_units >= donation_record.blood_request.units_required
        if request_fulfilled:
            donation_record.blood_request.status = "Fulfilled"
            remaining = db.session.scalars(
                db.select(Donation).where(
                    Donation.blood_request_id == donation_record.blood_request_id,
                    Donation.id != donation_record.id,
                    Donation.status.in_(("Invited", "Accepted")),
                )
            ).all()
            for other_donation in remaining:
                other_donation.status = "Cancelled"
                other_donation.cancelled_at = now
                create_notification(
                    user_id=other_donation.donor_profile.user_id,
                    title="Donation invitation closed",
                    message="The blood request has received its required confirmed units.",
                    category="info",
                    link="/donations",
                    event_key=f"donation-{other_donation.id}-fulfilled-cancelled",
                )
            create_notification(
                user_id=current_user.id,
                title="Blood request fulfilled",
                message=(
                    f"Request #{donation_record.blood_request.id} has received "
                    f"{completed_units} confirmed unit{'s' if completed_units != 1 else ''}."
                ),
                category="success",
                link=f"/requests/{donation_record.blood_request.id}",
                event_key=f"blood-request-{donation_record.blood_request.id}-fulfilled",
            )

        create_notification(
            user_id=donation_record.donor_profile.user_id,
            title="Donation confirmed",
            message=(
                f"Your donation for {donation_record.blood_request.patient_name} "
                "was confirmed by the requester. Thank you for helping."
            ),
            category="success",
            link="/donations",
            event_key=f"donation-{donation_record.id}-confirmed",
        )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Donation confirmation could not be saved.", "danger")
    else:
        message = (
            "Donation confirmed and blood request fulfilled."
            if request_fulfilled
            else f"Donation confirmed. {completed_units} unit(s) received so far."
        )
        flash(message, "success")
    return redirect(url_for("donation.index"))


@donation.route("/<int:donation_id>/cancel", methods=["POST"])
@login_required
def cancel(donation_id):
    donation_record = get_requester_donation_or_403(donation_id)
    if donation_record.status not in ("Invited", "Accepted"):
        flash("This donation invitation cannot be cancelled.", "warning")
        return redirect(url_for("donation.index"))

    donation_record.status = "Cancelled"
    donation_record.cancelled_at = datetime.now(timezone.utc)
    try:
        create_notification(
            user_id=donation_record.donor_profile.user_id,
            title="Donation invitation cancelled",
            message=(
                f"The invitation for {donation_record.blood_request.patient_name} "
                "was cancelled by the requester."
            ),
            category="info",
            link="/donations",
            event_key=f"donation-{donation_record.id}-cancelled",
        )
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash("Donation invitation could not be cancelled.", "danger")
    else:
        flash("Donation invitation cancelled.", "info")
    return redirect(url_for("donation.index"))
