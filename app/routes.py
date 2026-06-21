from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.matching import find_matching_donors


main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/dashboard")
@login_required
def dashboard():
    active_request_count = sum(
        blood_request.status in ("Pending", "Verified")
        for blood_request in current_user.blood_requests
    )
    matched_request_summaries = []
    verified_requests = sorted(
        (
            blood_request
            for blood_request in current_user.blood_requests
            if blood_request.status == "Verified"
        ),
        key=lambda blood_request: blood_request.created_at,
        reverse=True,
    )
    for blood_request in verified_requests:
        donors = find_matching_donors(blood_request)
        if donors:
            matched_request_summaries.append(
                {
                    "request": blood_request,
                    "donors": donors,
                }
            )

    return render_template(
        "dashboard.html",
        user=current_user,
        active_request_count=active_request_count,
        matched_request_summaries=matched_request_summaries,
    )
