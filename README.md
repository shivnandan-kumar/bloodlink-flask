# BloodLink - Blood Donor Network

BloodLink is a full-stack Flask application for blood donor matching, request verification, and emergency blood requests.

## Project Status

This project is complete from Step 1 to Step 12 and is ready for local demo, GitHub submission and interview explanation.

## Technology Stack

- Python
- Flask
- SQLite
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-Login
- Jinja Templates
- HTML
- CSS
- Bootstrap 5
- JavaScript
- Gmail SMTP
- ReportLab
- Git and GitHub

## Complete Feature List

- User registration, login and logout
- Strong password policy for registration, reset and default admin recovery
- Email OTP verification during registration
- Forgot password with secure reset link
- User dashboard
- Donor profile creation and editing
- Blood group proof upload for donors
- Blood request creation and tracking
- Doctor prescription upload for blood requests
- Admin dashboard
- Admin analytics with blood-group, request-status and donor-status insights
- Admin donor verification and rejection
- Admin blood request verification and rejection
- Emergency blood request broadcast and donor alerts
- Donor matching using blood group, pincode and city fallback
- In-app notifications
- Donation invitation, acceptance and completion flow
- Stylish PDF donation certificate download
- Request fulfillment after required units are completed
- Modern responsive UI

## Project Structure

```text
bloodlink-flask/
├── app/
│   ├── static/
│   ├── templates/
│   ├── __init__.py
│   ├── admin.py
│   ├── auth.py
│   ├── blood_requests.py
│   ├── donor.py
│   ├── donations.py
│   ├── email_verification.py
│   ├── extensions.py
│   ├── mailer.py
│   ├── matching.py
│   ├── models.py
│   ├── notifications.py
│   ├── password_reset.py
│   ├── routes.py
│   └── uploads.py
├── migrations/
├── config.py
├── run.py
├── requirements.txt
├── .env.example
├── .flaskenv
└── README.md
```

## How The App Works

1. User registers with name, email, city, pincode, blood group and password.
2. System sends an email OTP.
3. User verifies OTP and logs in.
4. User can become a donor by submitting donor details and blood group proof.
5. User can create a blood request with patient, hospital and prescription details.
6. Admin verifies donor profiles and blood requests.
7. System matches verified donors by blood group and pincode first, then city.
8. Requester invites a matched donor.
9. Donor accepts or declines the invitation.
10. Donor marks donation as completed.
11. Requester confirms the received donation.
12. Donor can download a verified PDF donation certificate.
13. Request becomes fulfilled when required units are completed.

## Main Database Models

- `User`: account, login, city, pincode, blood group and admin role
- `DonorProfile`: donor details, proof document, availability and verification status
- `BloodRequest`: patient, hospital, prescription and request status
- `Notification`: user notifications and read/unread status
- `Donation`: invitation and donation completion workflow

## Status Flow

Donor profile:

```text
Pending -> Verified
Pending -> Rejected
```

Blood request:

```text
Pending -> Verified
Pending -> Rejected
Verified -> Fulfilled
Pending/Verified -> Cancelled
```

Donation:

```text
Invited -> Accepted -> DonorCompleted -> Completed
Invited -> Declined
Invited/Accepted -> Cancelled
```

## Quick Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
flask db upgrade
python run.py
```

Open:

```text
http://127.0.0.1:8000
```

## Admin Setup

First register normally from the website. Then promote that user:

```powershell
flask promote-admin user@example.com
```

You can also create or restore a default local admin from `.env` values:

```powershell
flask create-default-admin
```

Required `.env` values:

```env
DEFAULT_ADMIN_NAME=BloodLink Admin
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=ChangeThisAdminPassword1!
DEFAULT_ADMIN_CITY=Ranchi
DEFAULT_ADMIN_PINCODE=834001
DEFAULT_ADMIN_BLOOD_GROUP=O+
```

Admin panel:

```text
http://127.0.0.1:8000/admin
```

## Email Setup

For Gmail OTP and password reset emails:

1. Enable 2-Step Verification in Gmail.
2. Create a Gmail App Password.
3. Copy `.env.example` to `.env`.
4. Add your Gmail address and App Password in `.env`.

Never commit the real `.env` file.

## Security Notes

- Passwords are stored as hashes.
- Passwords require 8+ characters, one uppercase letter, one number and one special character.
- OTP values are stored as hashes.
- Password reset links expire after 30 minutes.
- Uploaded documents are private.
- Admin routes are protected.
- `.env` is ignored by Git.

## Interview Explanation

BloodLink is a full-stack Flask project. Users can register, verify their email, login, become donors and create blood requests. Donor profiles and blood requests are verified by an admin. After verification, the system matches donors using blood group and pincode first, then falls back to the same city. The requester can invite donors and track the donation until it is completed.

The backend is built with Flask. SQLite is used as the database. Flask-SQLAlchemy is used to write database models in Python. Flask-Migrate is used to manage database changes. Flask-Login is used for login sessions. Jinja templates, Bootstrap and CSS are used for the frontend.

---

## Step-by-Step Build Notes

## Step 1

This step creates the basic Flask project structure:

- Flask app package
- Config file
- Templates folder
- Static folder
- Basic home page

## Step 2

This step adds the database foundation:

- SQLite database configuration
- Flask-SQLAlchemy setup
- Flask-Migrate setup
- User model
- First database migration

## Step 3

This step adds user authentication:

- User registration with validation
- Secure password hashing
- Login and remember-me session
- Logout
- Authentication-aware navbar

Authentication routes:

```text
/register
/login
/logout
```

## Step 4

This step adds the protected user dashboard:

- Account summary
- Registered user details
- Account status
- Empty activity state

Dashboard route:

```text
/dashboard
```

## Step 5

This step adds the donor profile module:

- Donor registration and validation
- One donor profile per user
- Donor profile view and edit
- Availability status
- Pending verification status
- Donor dashboard integration
- Private blood group proof upload
- New proof required when changing blood group
- Blood group proof required before admin verification

Donor routes:

```text
/donor/register
/donor/profile
/donor/edit
/donor/<id>/blood-group-proof
```

## Step 6

This step adds the blood request module:

- Create and validate blood requests
- List and track personal requests
- Request detail and edit pages
- Pending verification status
- Cancel request flow
- Owner-only request access
- Dashboard request activity
- Private doctor prescription upload
- PDF, JPG and PNG file validation (maximum 5 MB)
- Prescription access limited to the request owner and admin

Blood request routes:

```text
/requests
/requests/new
/requests/<id>
/requests/<id>/edit
/requests/<id>/prescription
```

## Step 7

This step adds the admin panel:

- Admin-only route protection
- Platform overview and counts
- Registered users list
- Donor profiles list
- Blood requests list
- Pending review count
- CLI command to promote an existing user

Admin routes:

```text
/admin
/admin/users
/admin/donors
/admin/requests
```

Promote a registered user:

```powershell
flask promote-admin user@example.com
```

## Step 8

This step adds donor and blood request verification:

- Admin donor review page
- Admin blood request review page
- Verify and reject POST actions
- Required rejection reason
- Reviewing admin and review timestamp
- User-visible verification outcomes
- Edit and resubmit rejected records
- Invalid second-review protection
- Prescription required before request verification

Verification routes:

```text
/admin/donors/<id>
/admin/donors/<id>/verify
/admin/donors/<id>/reject
/admin/requests/<id>
/admin/requests/<id>/verify
/admin/requests/<id>/reject
```

## Step 9

This step adds donor matching:

- Exact blood-group matching
- Pincode-first local matching
- Case-insensitive city fallback matching
- Verified donors only
- Available and medically declared donors only
- Request owner excluded from matches
- Matches available after request verification
- Requester match list and admin match preview
- Dashboard donor-available alert with contact details

Matching route:

```text
/requests/<id>/matches
```

## Step 10

This step adds persistent in-app notifications:

- Navbar bell with unread notification count
- Donor profile verified or rejected updates
- Blood request verified or rejected updates
- Matching donor available alerts
- Notification inbox ordered by newest first
- Open a notification and mark it as read
- Mark all notifications as read
- Owner-only notification access
- Duplicate matching notification protection

Notification routes:

```text
/notifications
/notifications/<id>/open
/notifications/read-all
```

## Password Recovery

The authentication system also supports secure password recovery:

- Forgot-password link on the login page
- Same response for registered and unknown email addresses
- Signed reset token that expires after 30 minutes
- Reset token becomes invalid after the password changes
- Password and confirmation validation
- Optional SMTP email delivery using environment variables

Password recovery routes:

```text
/forgot-password
/reset-password/<token>
```

For local development without SMTP, the reset link is printed in the Flask
terminal. For email delivery, copy the variable names from `.env.example` into
your private `.env` file and enter your mail provider details. Never commit the
real mail password.

## Registration Email Verification

New accounts must verify their email before login:

- Six-digit OTP sent after registration
- OTP stored as a secure hash, not plain text
- OTP expires after 10 minutes
- Maximum five incorrect attempts
- Resend OTP with a 60-second cooldown
- Unverified accounts cannot login
- Existing accounts remain verified after migration

Email verification routes:

```text
/verify-email
/verify-email/resend
```

## Step 11

This step adds the donation completion workflow:

- Requester invites a verified matched donor
- Donor accepts or declines the invitation
- Donor marks the donation completed
- Requester confirms the received donation unit
- Donor and requester can download a verified PDF donation certificate
- One confirmed donation counts as one received unit
- Request automatically becomes fulfilled after all required units are confirmed
- Remaining open invitations close after fulfillment
- Completed donor becomes unavailable until updating their profile
- Donor last-donation date updates after requester confirmation
- Status notifications for both requester and donor
- Owner-only workflow actions and fixed status transitions

Donation workflow routes:

```text
/donations
/donations/requests/<request_id>/donors/<donor_id>/invite
/donations/<id>/accept
/donations/<id>/decline
/donations/<id>/donor-complete
/donations/<id>/confirm
/donations/<id>/cancel
/donations/<id>/certificate
```

## Run Locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Open this URL in your browser:

```text
http://127.0.0.1:8000
```

## Database Commands

```powershell
flask db migrate -m "Create user model"
flask db upgrade
```
