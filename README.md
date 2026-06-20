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

Donor routes:

```text
/donor/register
/donor/profile
/donor/edit
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

Blood request routes:

```text
/requests
/requests/new
/requests/<id>
/requests/<id>/edit
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

Verification routes:

```text
/admin/donors/<id>
/admin/donors/<id>/verify
/admin/donors/<id>/reject
/admin/requests/<id>
/admin/requests/<id>/verify
/admin/requests/<id>/reject
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
