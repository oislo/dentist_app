# 🦷 Dentist Management App (Flask)

A simple **Flask-based dentist clinic management application** for managing patients, services, and appointments.  
Built as a learning / internal tool with a clean structure and room to grow.

---

## ✨ Features

- Client (patient) management
- Password-protected: one shared password, set with `APP_PASSWORD`
- Appointment scheduling
- Service catalog
- SQLite database (easy local setup)
- Flask + SQLAlchemy ORM
- Flask-Migrate for database migrations
- Clean project structure (app factory pattern)

---

## 🛠 Tech Stack

- **Python 3.10+**
- **Flask**
- **Flask-SQLAlchemy**
- **Flask-Migrate (Alembic)**
- **SQLite** (default, easily replaceable)
- **Jinja2 templates**

---

## 📂 Project Structure

dentist_app/
│
├── app.py # Application factory and all routes
├── config.py # App configuration (environment variables)
├── models.py # Client, Service, Appointment, AppointmentItem
├── forms.py # WTForms forms and validation
│
├── templates/
│ └── *.html
│
├── migrations/ # Alembic migrations
├── requirements.txt
├── .gitignore
└── README.md

---

## 🚀 Getting Started


git clone https://github.com/oislo/dentist_app.git
cd dentist_app

python -m venv venv

Windows: venv\Scripts\activate
Linux: source venv/bin/activate

pip install -r requirements.txt

flask db upgrade

Windows: $env:FLASK_APP="app:create_app"
Linux: export FLASK_APP=app:create_app

Set the login password (required, the app stays locked without it):

Windows: $env:APP_PASSWORD="choose-a-password"
Linux: export APP_PASSWORD="choose-a-password"


python app.py

Follow http://127.0.0.1:5000 and voila, a simple working useful dentst app management.


## Configuration

All settings are environment variables:

- `APP_PASSWORD` (required): the shared password for the login page.
- `SECRET_KEY` (optional): signs the session cookie. If unset, a random key is generated once and saved to `instance/secret_key`.
- `DATABASE_URL` (optional): defaults to a local SQLite file.
- `DEFAULT_APPOINTMENT_MINUTES` (optional): assumed length of an appointment with no end time, default 30.

The app serves plain HTTP. If it is reachable from outside your own machine, put it behind HTTPS.

## Database
Default database: SQLite created automatically in the working directory
You can switch to PostgreSQL or another DB by setting the `DATABASE_URL` environment variable.





