# ACC Consultation System

A full-stack web application for managing campus health/medical consultations
between **Students**, **Medical Experts**, and a **Super Admin**, built with
Flask, SQLite, and vanilla HTML/CSS/JS.

## Tech Stack

- **Backend:** Python 3 + Flask, Flask-SQLAlchemy, Flask-Login
- **Frontend:** Server-rendered Jinja2 templates, vanilla CSS + JavaScript (no build step)
- **Database:** SQLite (file-based, zero configuration)

## Features

- Role-based access control (RBAC) with three roles:
  - **Super Admin** — manage all users, view/reassign every consultation, system settings
  - **Medical Expert** — claim unassigned consultations, respond to assigned students, view their student list
  - **Student** — submit consultation requests, message assigned experts, view their own history
- Session-based authentication (Flask-Login) with hashed passwords (Werkzeug)
- Role-aware redirects after login; every route is protected by a `roles_required` decorator
- Consultation threading (message history per consultation), status (pending / in progress / resolved / closed) and priority (low / normal / high / urgent) tracking
- Responsive, chroma-styled UI (teal / purple / orange gradient palette)
- SQLite schema + seed script with ready-to-use demo accounts

## Project Structure

```
acc_consultation_system/
├── app.py                  # Application factory & entrypoint
├── config.py                # Config (secret key, DB URI)
├── extensions.py             # db / login_manager singletons
├── models.py                 # User, Consultation, Message, Setting models
├── rbac.py                   # roles_required() decorator
├── init_db.py                 # DB schema creation + seed data script
├── requirements.txt
├── blueprints/
│   ├── auth.py                # /login /register /logout
│   ├── admin.py                # /admin/* (Super Admin)
│   ├── expert.py               # /expert/* (Medical Expert)
│   └── student.py              # /student/* (Student)
├── templates/
│   ├── base.html                # Shared sidebar/topbar shell
│   ├── auth/ (login.html, register.html)
│   ├── admin/ (dashboard, users, user_form, consultations, consultation_detail, settings)
│   ├── expert/ (dashboard, consultations, consultation_detail, students)
│   ├── student/ (dashboard, new_consultation, history, consultation_detail)
│   └── errors/error.html
└── static/
    ├── css/style.css           # Chroma theme (teal/purple/orange)
    └── js/main.js               # Flash dismiss, confirm dialogs
```

## Database Schema

| Table         | Key Columns                                                                 |
|---------------|------------------------------------------------------------------------------|
| `users`       | id, username, email, password_hash, full_name, role, program, is_active_account, created_at |
| `consultations` | id, student_id (FK→users), expert_id (FK→users, nullable), subject, description, status, priority, created_at, updated_at |
| `messages`    | id, consultation_id (FK→consultations), sender_id (FK→users), body, created_at |
| `settings`    | id, key, value                                                              |

`role` is one of `super_admin`, `medical_expert`, `student`.
`status` is one of `pending`, `in_progress`, `resolved`, `closed`.
`priority` is one of `low`, `normal`, `high`, `urgent`.

## Setup & Run Instructions

### 1. Prerequisites
- Python 3.9+ installed
- `pip` available on your PATH

### 2. Create and activate a virtual environment

```bash
cd acc_consultation_system

# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize the database (creates tables + sample data)

```bash
python init_db.py
```

This creates `acc_consultation.db` in the project root and seeds it with
demo accounts and sample consultations. To wipe and reseed at any point:

```bash
python init_db.py --reset
```

### 5. Run the development server

```bash
python app.py
```

The app will be available at **http://127.0.0.1:5000**. You'll land on the
login page automatically.

### 6. Log in with a demo account

| Role            | Username    | Password    |
|-----------------|-------------|-------------|
| Super Admin     | `admin`     | `admin123`  |
| Medical Expert  | `dr.santos` | `expert123` |
| Medical Expert  | `dr.lim`    | `expert123` |
| Student         | `jdoe`      | `student123`|
| Student         | `mgarcia`   | `student123`|
| Student         | `rcruz`     | `student123`|

New students can also self-register at `/register`. Medical Expert and
Super Admin accounts must be created by an admin from **Manage Users**.

## Notes for Production Use

This project is configured for local development (`debug=True`, a default
`SECRET_KEY`). Before deploying:

1. Set a strong, unique `SECRET_KEY` via the `SECRET_KEY` environment variable.
2. Disable debug mode and run behind a production WSGI server (e.g. `gunicorn app:app`).
3. Consider moving from SQLite to PostgreSQL/MySQL for concurrent production traffic.
4. Serve static files via a CDN/reverse proxy (e.g. Nginx) rather than Flask directly.
5. Add HTTPS termination and set `SESSION_COOKIE_SECURE = True`.

## Design / Color Palette

The UI uses a vibrant "chroma" theme defined as CSS variables in
`static/css/style.css`:

- Teal `#14B8A6` (`--teal`)
- Purple `#8B5CF6` (`--purple`)
- Orange `#F97316` (`--orange`)
- Dark navy sidebar gradient `#171A2E → #221B3D → #2C1B3B`

These combine into a brand gradient (`--gradient-brand`) used across
buttons, avatars, and accent bars for a cohesive, modern, energetic look.
