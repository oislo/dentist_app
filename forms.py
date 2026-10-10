from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SubmitField, DateField, BooleanField,
    DecimalField, IntegerField, SelectField, SelectMultipleField, DateTimeLocalField,
    PasswordField
)
from wtforms.validators import DataRequired, InputRequired, Optional, Length, NumberRange, ValidationError

class LoginForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")

class ClientForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=200)])
    phone = StringField("Phone", validators=[Optional(), Length(max=50)])
    email = StringField("Email", validators=[Optional(), Length(max=200)])
    date_of_birth = DateField("Date of Birth", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save")

class ServiceForm(FlaskForm):
    name = StringField("Service Name", validators=[DataRequired(), Length(max=200)])
    default_price = DecimalField("Default Price", validators=[InputRequired(), NumberRange(min=0)], places=2)
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save")

class AppointmentForm(FlaskForm):
    client_id = SelectField("Client", coerce=int, validators=[DataRequired(message="Please select a client.")])

    # Optional: add multiple services on creation/edit (creates line items qty=1)
    service_ids = SelectMultipleField("Services (optional)", coerce=int, validators=[Optional()])

    start_at = DateTimeLocalField("Start", format="%Y-%m-%dT%H:%M", default=datetime.now, validators=[DataRequired()])
    end_at = DateTimeLocalField("End (optional)", format="%Y-%m-%dT%H:%M", validators=[Optional()])

    status = SelectField("Status", choices=[
        ("scheduled", "Scheduled"),
        ("completed", "Completed"),
        ("canceled", "Canceled"),
        ("no_show", "No-show"),
    ], validators=[DataRequired()])

    reason = StringField("Reason", validators=[Optional(), Length(max=255)])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save")

    def validate_end_at(self, field):
        if field.data and self.start_at.data and field.data <= self.start_at.data:
            raise ValidationError("End must be after start.")

class AppointmentBillingForm(FlaskForm):
    discount_type = SelectField("Discount Type", choices=[("amount", "Amount"), ("percent", "Percent")], validators=[DataRequired()])
    discount_value = DecimalField("Discount Value", validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    is_paid = BooleanField("Paid", default=False)
    submit = SubmitField("Save Billing")

    def validate_discount_value(self, field):
        if self.discount_type.data == "percent" and field.data is not None and field.data > 100:
            raise ValidationError("A percent discount cannot be more than 100.")

class AppointmentItemForm(FlaskForm):
    service_id = SelectField("Service", coerce=int, validators=[DataRequired()])
    quantity = IntegerField("Qty", default=1, validators=[DataRequired(), NumberRange(min=1)])
    unit_price = DecimalField("Unit Price", validators=[InputRequired(), NumberRange(min=0)], places=2)
    submit = SubmitField("Add Service")
