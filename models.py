from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False, index=True)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(200), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    appointments = db.relationship("Appointment", backref="client", cascade="all, delete-orphan")

class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True, index=True)
    default_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)

    start_at = db.Column(db.DateTime, nullable=False, index=True)
    end_at = db.Column(db.DateTime, nullable=True)

    status = db.Column(db.String(30), nullable=False, default="scheduled")
    reason = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Billing (per appointment)
    discount_type = db.Column(db.String(10), nullable=False, default="amount")  # amount or percent
    discount_value = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    is_paid = db.Column(db.Boolean, default=False, nullable=False)
    paid_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    items = db.relationship("AppointmentItem", backref="appointment", cascade="all, delete-orphan")

    def subtotal(self) -> float:
        return float(sum([it.total_price() for it in self.items]))

    def discount_amount(self) -> float:
        subtotal = self.subtotal()
        if self.discount_type == "percent":
            amount = subtotal * (float(self.discount_value) / 100.0)
        else:
            amount = float(self.discount_value)
        # A discount can never be negative or larger than the subtotal.
        return min(subtotal, max(0.0, amount))

    def total_due(self) -> float:
        return max(0.0, self.subtotal() - self.discount_amount())

    def services_summary(self) -> str:
        return ", ".join([f"{it.service_name} x{it.quantity}" for it in self.items])

class AppointmentItem(db.Model):
    __tablename__ = "appointment_items"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id"), nullable=False)

    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    service = db.relationship("Service")

    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    @property
    def service_name(self) -> str:
        # Older databases can hold items whose service was deleted.
        return self.service.name if self.service else "(deleted service)"

    def total_price(self) -> float:
        return float(self.quantity) * float(self.unit_price)
