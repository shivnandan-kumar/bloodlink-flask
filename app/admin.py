from functools import wraps

from flask import Blueprint, abort, render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from app.extensions import db
from app.models import BloodRequest, DonorProfile, User


admin = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view_function(*args, **kwargs)

    return wrapped_view


@admin.route("")
@login_required
@admin_required
def dashboard():
    stats = {
        "users": db.session.scalar(db.select(func.count()).select_from(User)),
        "donors": db.session.scalar(
            db.select(func.count()).select_from(DonorProfile)
        ),
        "requests": db.session.scalar(
            db.select(func.count()).select_from(BloodRequest)
        ),
        "pending": db.session.scalar(
            db.select(func.count())
            .select_from(DonorProfile)
            .where(DonorProfile.verification_status == "Pending")
        )
        + db.session.scalar(
            db.select(func.count())
            .select_from(BloodRequest)
            .where(BloodRequest.status == "Pending")
        ),
    }
    recent_users = db.session.scalars(
        db.select(User).order_by(User.created_at.desc()).limit(5)
    ).all()
    recent_requests = db.session.scalars(
        db.select(BloodRequest).order_by(BloodRequest.created_at.desc()).limit(5)
    ).all()
    return render_template(
        "admin_dashboard.html",
        stats=stats,
        recent_users=recent_users,
        recent_requests=recent_requests,
    )


@admin.route("/users")
@login_required
@admin_required
def users():
    users = db.session.scalars(
        db.select(User).order_by(User.created_at.desc())
    ).all()
    return render_template("admin_users.html", users=users)


@admin.route("/donors")
@login_required
@admin_required
def donors():
    donors = db.session.scalars(
        db.select(DonorProfile).order_by(DonorProfile.created_at.desc())
    ).all()
    return render_template("admin_donors.html", donors=donors)


@admin.route("/requests")
@login_required
@admin_required
def requests():
    requests = db.session.scalars(
        db.select(BloodRequest).order_by(BloodRequest.created_at.desc())
    ).all()
    return render_template("admin_requests.html", requests=requests)

