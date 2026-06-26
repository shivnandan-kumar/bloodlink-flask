from datetime import datetime, timezone

from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app.extensions import db
from app.matching import find_matching_donors
from app.models import BloodRequest, Notification


notifications = Blueprint("notifications", __name__, url_prefix="/notifications")


def create_notification(
    user_id,
    title,
    message,
    category="info",
    link=None,
    event_key=None,
):
    if event_key:
        existing = db.session.scalar(
            db.select(Notification).where(
                Notification.user_id == user_id,
                Notification.event_key == event_key,
            )
        )
        if existing:
            return existing

    notification = Notification(
        user_id=user_id,
        title=title[:120],
        message=message[:500],
        category=category,
        link=link[:255] if link else None,
        event_key=event_key[:150] if event_key else None,
    )
    db.session.add(notification)
    return notification


def notify_request_matches(blood_request_record, donors):
    if not donors:
        return None
    donor_count = len(donors)
    return create_notification(
        user_id=blood_request_record.requester_id,
        title="Matching donor available",
        message=(
            f"{donor_count} verified donor"
            f"{'s are' if donor_count != 1 else ' is'} available for "
            f"request #{blood_request_record.id} in {blood_request_record.city}."
        ),
        category="match",
        link=f"/requests/{blood_request_record.id}/matches",
        event_key=f"blood-request-{blood_request_record.id}-match-found",
    )


def notify_matching_requests_for_donor(donor):
    if not donor.is_available or not donor.medical_eligible:
        return

    matching_requests = db.session.scalars(
        db.select(BloodRequest).where(
            BloodRequest.status == "Verified",
            BloodRequest.blood_group == donor.user.blood_group,
            func.lower(BloodRequest.city) == donor.user.city.strip().lower(),
            BloodRequest.requester_id != donor.user_id,
        )
    ).all()
    for blood_request_record in matching_requests:
        if donor in find_matching_donors(blood_request_record):
            notify_request_matches(blood_request_record, [donor])


def get_owned_notification_or_404(notification_id):
    notification = db.session.get(Notification, notification_id)
    if not notification:
        abort(404)
    if notification.user_id != current_user.id:
        abort(403)
    return notification


@notifications.route("")
@login_required
def index():
    user_notifications = db.session.scalars(
        db.select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    ).all()
    return render_template(
        "notifications.html",
        notifications=user_notifications,
    )


@notifications.route("/<int:notification_id>/open", methods=["POST"])
@login_required
def open_notification(notification_id):
    notification = get_owned_notification_or_404(notification_id)
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        db.session.commit()

    destination = notification.link or url_for("notifications.index")
    if not destination.startswith("/") or destination.startswith("//"):
        destination = url_for("notifications.index")
    return redirect(destination)


@notifications.route("/read-all", methods=["POST"])
@login_required
def read_all():
    unread_notifications = db.session.scalars(
        db.select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    ).all()
    read_time = datetime.now(timezone.utc)
    for notification in unread_notifications:
        notification.is_read = True
        notification.read_at = read_time
    db.session.commit()

    destination = request.form.get("next", "")
    if not destination.startswith("/") or destination.startswith("//"):
        destination = url_for("notifications.index")
    return redirect(destination)
