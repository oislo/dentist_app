# 🦷 Dentist Management App (Flask)

A simple **Flask-based dentist clinic management application** for managing patients, services, and appointments.  
Built as a learning / internal tool with a clean structure and room to grow.

---

## ✨ Features

- Patient management (create & list patients)
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
├── app.py # Application entry point
├── config.py # App configuration
├── extensions.py # DB & migrate initialization
│
├── models/
│ ├── init.py
│ ├── patient.py
│ ├── appointment.py
│ └── service.py
│
├── routes/
│ ├── init.py
│ └── main.py
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
cd dentist-app

python -m venv venv

Windows: venv\Scripts\activate
Linux: source venv/bin/activate

pip install -r requirements.txt

flask db upgrade

Windows: $env:FLASK_APP="app:create_app"
Linux: export FLASK_APP=app:create_app


python app.py

Follow http://127.0.0.1:5000 and voila, a simple working useful dentst app management.


## Database
Default database: SQLite created automatically in the working directory
You can switch to PostgreSQL or another DB by updating SQLALCHEMY_DATABASE_URI in config.py.





