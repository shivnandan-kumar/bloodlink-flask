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
