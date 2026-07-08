# BloodLink - Blood Donor Network

BloodLink is a full-stack Flask web application for managing blood donors, blood requests, admin verification, donor matching, donation tracking, notifications and PDF donation certificates.

The project is built as a practical resume-level application, not only a basic CRUD project. It includes authentication, secure document uploads, admin workflows, pincode-based matching, analytics and a complete donation completion flow.

## Project Highlights

- User can register, verify email with OTP, login and logout.
- User can act as both donor and requester from the same account.
- Donor can upload blood-group proof and submit profile for admin verification.
- Requester can create blood requests with doctor prescription upload.
- Admin can verify or reject donors and blood requests.
- Matching first checks blood group and pincode, then falls back to city.
- Emergency blood requests are highlighted and notify available donors.
- In-app notifications track verification and donation updates.
- Requester can invite donors and confirm completed donations.
- Donor rewards grow after confirmed donations.
- Completed donations generate a stylish PDF certificate.
- Admin dashboard includes analytics for blood groups, request status, donor status, emergency requests and top donors.

## Tech Stack

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

## Screenshots

Add screenshots here before posting on LinkedIn or sharing the GitHub repo:

```text
docs/screenshots/homepage.png
docs/screenshots/dashboard.png
docs/screenshots/admin-analytics.png
docs/screenshots/donor-matching.png
docs/screenshots/donation-certificate.png
```

Recommended screenshots:

- Homepage with modern BloodLink hero section
- User dashboard
- Admin analytics dashboard
- Blood request matching page
- Donation activity page
- PDF certificate preview

## Main Features

### Authentication

- Register, login and logout
- Strong password policy
- Email OTP verification
- Forgot-password flow with secure reset link
- Remember-me login support

### Donor Module

- Donor profile creation and editing
- Blood-group proof upload
- Availability status
- Medical declaration
- Admin verification or rejection
- Donor reward badge based on confirmed donations

### Blood Request Module

- Create, edit, cancel and track requests
- Doctor prescription upload
- Emergency request flag
- Request status tracking
- Owner-only request access

### Admin Module

- Protected admin dashboard
- Admin-only route access
- Donor verification
- Blood request verification
- Rejection reason tracking
- Analytics dashboard
- Default admin recovery command

### Matching System

- Exact blood group matching
- Pincode-first local matching
- City fallback matching
- Verified donors only
- Available and medically eligible donors only
- Request owner excluded from matching

### Donation Workflow

- Requester invites matched donor
- Donor accepts or declines invitation
- Donor marks donation as completed
- Requester confirms received donation
- Request becomes fulfilled after required units are confirmed
- Donor receives a PDF certificate after completion

## Project Structure

```text
bloodlink-flask/
|-- app/
|   |-- static/
|   |   |-- css/
|   |   |-- images/
|   |-- templates/
|   |-- __init__.py
|   |-- admin.py
|   |-- auth.py
|   |-- blood_requests.py
|   |-- certificates.py
|   |-- donor.py
|   |-- donations.py
|   |-- email_verification.py
|   |-- extensions.py
|   |-- mailer.py
|   |-- matching.py
|   |-- models.py
|   |-- notifications.py
|   |-- password_reset.py
|   |-- routes.py
|   |-- security.py
|   |-- uploads.py
|-- migrations/
|-- config.py
|-- run.py
|-- requirements.txt
|-- .env.example
|-- .flaskenv
|-- README.md
```

## How The App Works

1. User registers with name, email, city, pincode, blood group and password.
2. System sends a 6-digit email OTP.
3. User verifies OTP and logs in.
4. User can become a donor by submitting donor details and blood-group proof.
5. User can create a blood request with patient, hospital and prescription details.
6. Admin verifies donor profiles and blood requests.
7. System matches donors by blood group and pincode first, then city.
8. Requester invites a matched donor.
9. Donor accepts or declines the invitation.
10. Donor marks the donation completed.
11. Requester confirms the received donation.
12. Donation count increases and reward badge updates.
13. Donor can download a verified PDF certificate.
14. Request becomes fulfilled when required units are completed.

## Database Models

- `User`: account, login, city, pincode, blood group, email verification and admin role
- `DonorProfile`: donor details, proof document, availability, eligibility, rewards and verification status
- `BloodRequest`: patient, hospital, prescription, emergency flag and request status
- `Donation`: invitation, donor response and donation completion workflow
- `Notification`: in-app user notifications and read status

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

## Local Setup

Create and activate virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create environment file:

```powershell
copy .env.example .env
```

Apply migrations:

```powershell
flask db upgrade
```

Run the application:

```powershell
python run.py
```

Open:

```text
http://127.0.0.1:8000
```

## Admin Setup

Promote an existing user:

```powershell
flask promote-admin user@example.com
```

Create or restore default admin from `.env`:

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
4. Add Gmail SMTP values in `.env`.

Never commit the real `.env` file.

## Security Features

- Passwords are stored as hashes.
- Passwords require minimum 8 characters, one uppercase letter, one number and one special character.
- OTP values are stored as hashes.
- Password reset links expire after 30 minutes.
- Uploaded documents are private.
- Admin routes are protected.
- `.env` is ignored by Git.

## Important Routes

Authentication:

```text
/register
/login
/logout
/verify-email
/forgot-password
/reset-password/<token>
```

User and donor:

```text
/dashboard
/donor/register
/donor/profile
/donor/edit
```

Blood requests:

```text
/requests
/requests/new
/requests/<id>
/requests/<id>/matches
```

Admin:

```text
/admin
/admin/users
/admin/donors
/admin/requests
```

Donation workflow:

```text
/donations
/donations/requests/<request_id>/donors/<donor_id>/invite
/donations/<id>/accept
/donations/<id>/decline
/donations/<id>/donor-complete
/donations/<id>/confirm
/donations/<id>/cancel
/donations/<id>/certificate
/donations/<id>/chat
/donations/<id>/chat/messages
```

## Interview Explanation

BloodLink is a full-stack Flask application for connecting blood requesters with verified donors. A user can register, verify email, login, become a donor and also create blood requests. Donor profiles and blood requests are reviewed by an admin. After verification, the system matches donors using blood group and pincode first, then city fallback. The requester can invite donors, coordinate through private chat and track the donation workflow until completion. After confirmation, the donor reward count increases and a PDF certificate can be downloaded.

The backend is built with Flask. SQLite stores the data. Flask-SQLAlchemy is used for models and queries. Flask-Migrate manages database migrations. Flask-Login handles sessions. Jinja templates, Bootstrap, JavaScript and custom CSS build the frontend. ReportLab is used to generate PDF certificates. Gmail SMTP is used for OTP and password reset emails.

## Resume Bullet Points

- Built a full-stack blood donor network using Flask, SQLite, SQLAlchemy, Jinja and Bootstrap.
- Implemented secure authentication with OTP email verification, password hashing and password reset.
- Designed admin verification workflows for donor profiles and blood requests.
- Added pincode-first donor matching with city fallback using SQLAlchemy queries.
- Built donation invitation and completion workflow with in-app notifications.
- Added private AJAX chat between requester and donor after donation acceptance.
- Generated professional PDF donation certificates using ReportLab.
- Created an admin analytics dashboard using aggregate database queries and CSS charts.

## Future Improvements

- Deploy on Render or Railway.
- Add Google OAuth login.
- Add SMS alerts for emergency requests.
- Add map-based distance matching.
- Add automated tests with pytest.
