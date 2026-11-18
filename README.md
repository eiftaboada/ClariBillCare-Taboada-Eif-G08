# ClariBill Care – Project Development 1 (Account Feature)

Full-stack Django (templates for the frontend) with a PostgreSQL / Supabase database.

## Account Feature
- **Registration** – `/register/` with required fields, valid/unique email, unique username, matching passwords, hashed passwords (Django auth) and success/error messages.
- **Login / Logout** – `/login/`, `/logout/` (POST). Invalid credentials show an error. Protected pages redirect logged-out users to the login page.
- **Role-based dashboards** – two roles: **Patient** (`/dashboard/patient/`) and **Billing Staff** (`/dashboard/staff/`). `/dashboard/` sends each user to their own dashboard; opening the other role's dashboard returns 403.
- **Profile** – `/profile/` and `/profile/edit/` (name, email, contact number, profile photo). Users can only see and edit their own profile.

## Setup
```bash
python -m venv venv
venv\Scripts\activate            # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env           # macOS/Linux: cp .env.example .env  -> then fill in your values
```
Create the database in PostgreSQL (or use your Supabase connection details in `.env`; set `DB_SSLMODE=require` for Supabase), then:
```bash
python manage.py migrate
python manage.py createsuperuser   # superusers are created as Billing Staff
python manage.py runserver
```
Open http://127.0.0.1:8000/ . Run the tests with `python manage.py test`.

Public registration always creates **Patient** accounts. Billing Staff accounts are created with `createsuperuser` or in `/admin/`.
