# BloodLink - Blood Donor Network

BloodLink is a full-stack Flask application for blood donor matching, request verification, and emergency blood requests.

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
- Case-insensitive city matching
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
