from datetime import datetime, timedelta, date
from decimal import Decimal
import csv
from io import StringIO

from flask import Flask, render_template, redirect, url_for, flash, request, abort, Response
from flask_migrate import Migrate
from sqlalchemy.orm import joinedload

from config import Config
from models import db, Client, Service, Appointment, AppointmentItem
from forms import ClientForm, ServiceForm, AppointmentForm, AppointmentBillingForm, AppointmentItemForm


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    Migrate(app, db)

    # -----------------------
    # Helpers
    # -----------------------
    def get_clients_choices(include_blank=True):
        clients = Client.query.order_by(Client.full_name.asc()).all()
        choices = [(c.id, c.full_name) for c in clients]
        return ([(0, "-- Select client --")] + choices) if include_blank else choices

    def get_services_choices(active_only=True):
        q = Service.query
        if active_only:
            q = q.filter(Service.is_active.is_(True))
        services = q.order_by(Service.name.asc()).all()
        return [(s.id, s.name) for s in services]

    def calc_end(start_at: datetime, end_at: datetime | None) -> datetime:
        return end_at if end_at else start_at + timedelta(minutes=int(app.config["DEFAULT_APPOINTMENT_MINUTES"]))

    def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
        return a_start < b_end and b_start < a_end

    def find_conflict(appointment_id: int | None, start_at: datetime, end_at: datetime | None):
        new_end = calc_end(start_at, end_at)
        window_start = start_at - timedelta(days=1)
        window_end = new_end + timedelta(days=1)

        q = Appointment.query.filter(
            Appointment.status != "canceled",
            Appointment.start_at < window_end,
            Appointment.start_at >= window_start,
        )
        if appointment_id:
            q = q.filter(Appointment.id != appointment_id)

        for a in q.order_by(Appointment.start_at.asc()).all():
            if overlaps(start_at, new_end, a.start_at, calc_end(a.start_at, a.end_at)):
                return a
        return None

    def csv_response(filename: str, header: list[str], rows: list[list]):
        out = StringIO()
        w = csv.writer(out)
        w.writerow(header)
        for r in rows:
            w.writerow(r)
        data = out.getvalue()
        resp = Response(data, mimetype="text/csv; charset=utf-8")
        resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp

    @app.template_filter("money")
    def money_filter(value):
        try:
            return f"{float(value):,.2f}"
        except Exception:
            return "0.00"

    # -----------------------
    # Dashboard
    # -----------------------
    @app.get("/")
    def dashboard():
        upcoming = Appointment.query.options(joinedload(Appointment.items).joinedload(AppointmentItem.service)).filter(
            Appointment.start_at >= datetime.utcnow(),
            Appointment.status == "scheduled",
        ).order_by(Appointment.start_at.asc()).limit(8).all()

        unpaid = Appointment.query.options(joinedload(Appointment.items).joinedload(AppointmentItem.service)).filter(
            Appointment.is_paid.is_(False)
        ).order_by(Appointment.start_at.desc()).limit(8).all()

        return render_template(
            "dashboard.html",
            upcoming=upcoming,
            unpaid=unpaid,
            clients_count=Client.query.count(),
            appt_count=Appointment.query.count(),
            unpaid_count=Appointment.query.filter(Appointment.is_paid.is_(False)).count(),
        )

    # -----------------------
    # Calendar
    # -----------------------
    def start_of_week(d: date) -> date:
        return d - timedelta(days=d.weekday())  # Monday

    @app.get("/calendar")
    def calendar_week():
        day_str = request.args.get("day", "").strip()
        focus = date.today()
        if day_str:
            try:
                focus = datetime.strptime(day_str, "%Y-%m-%d").date()
            except ValueError:
                pass

        week_start = start_of_week(focus)
        days = [week_start + timedelta(days=i) for i in range(7)]
        week_end_display = week_start + timedelta(days=6)

        prev_week_day = (week_start - timedelta(days=7)).isoformat()
        next_week_day = (week_start + timedelta(days=7)).isoformat()

        week_start_dt = datetime.combine(week_start, datetime.min.time())
        week_end_dt = datetime.combine(week_start + timedelta(days=7), datetime.min.time())

        appts = Appointment.query.options(joinedload(Appointment.items).joinedload(AppointmentItem.service)).filter(
            Appointment.status != "canceled",
            Appointment.start_at >= week_start_dt,
            Appointment.start_at < week_end_dt,
        ).order_by(Appointment.start_at.asc()).all()

        by_day = {}
        for a in appts:
            by_day.setdefault(a.start_at.date(), []).append(a)

        return render_template(
            "calendar_week.html",
            week_start=week_start,
            week_end_display=week_end_display,
            days=days,
            by_day=by_day,
            prev_week_day=prev_week_day,
            next_week_day=next_week_day,
        )

    @app.get("/calendar/day")
    def calendar_day():
        day_str = request.args.get("day", "").strip()
        focus = date.today()
        if day_str:
            try:
                focus = datetime.strptime(day_str, "%Y-%m-%d").date()
            except ValueError:
                pass

        prev_day = (focus - timedelta(days=1)).isoformat()
        next_day = (focus + timedelta(days=1)).isoformat()

        day_start = datetime.combine(focus, datetime.min.time())
        day_end = day_start + timedelta(days=1)

        appts = Appointment.query.options(joinedload(Appointment.items).joinedload(AppointmentItem.service)).filter(
            Appointment.status != "canceled",
            Appointment.start_at >= day_start,
            Appointment.start_at < day_end,
        ).order_by(Appointment.start_at.asc()).all()

        return render_template("calendar_day.html", focus=focus, appts=appts, prev_day=prev_day, next_day=next_day)

    # -----------------------
    # Exports
    # -----------------------
    @app.get("/export/clients.csv")
    def export_clients():
        clients = Client.query.order_by(Client.full_name.asc()).all()
        rows = []
        for c in clients:
            dob = c.date_of_birth.strftime("%d/%m/%Y") if c.date_of_birth else ""
            rows.append([c.id, c.full_name, c.phone or "", c.email or "", dob, c.created_at])
        return csv_response("clients.csv", ["id","full_name","phone","email","date_of_birth","created_at"], rows)

    @app.get("/export/client/<int:client_id>/history.csv")
    def export_client_history(client_id: int):
        client = Client.query.get_or_404(client_id)
        appts = Appointment.query.options(joinedload(Appointment.items).joinedload(AppointmentItem.service)).filter_by(
            client_id=client.id
        ).order_by(Appointment.start_at.asc()).all()

        rows = []
        for a in appts:
            if a.items:
                for it in a.items:
                    rows.append([
                        a.id, a.start_at, a.end_at or "", a.status, "paid" if a.is_paid else "unpaid",
                        it.service.name, it.quantity, float(it.unit_price), float(it.total_price()),
                        a.discount_type, float(a.discount_value), float(a.total_due()),
                        a.reason or "", a.notes or ""
                    ])
            else:
                rows.append([
                    a.id, a.start_at, a.end_at or "", a.status, "paid" if a.is_paid else "unpaid",
                    "", "", "", "",
                    a.discount_type, float(a.discount_value), float(a.total_due()),
                    a.reason or "", a.notes or ""
                ])

        header = [
            "appointment_id","start_at","end_at","status","paid_status","service","qty","unit_price","line_total",
            "discount_type","discount_value","total_due","reason","notes"
        ]
        return csv_response(f"client_{client.id}_history.csv", header, rows)

    @app.get("/export/appointment/<int:appt_id>/invoice.csv")
    def export_appointment_invoice(appt_id: int):
        a = Appointment.query.options(joinedload(Appointment.items).joinedload(AppointmentItem.service)).get_or_404(appt_id)
        rows = [[it.service.name, it.quantity, float(it.unit_price), float(it.total_price())] for it in a.items]
        rows += [
            [],
            ["SUBTOTAL", "", "", float(a.subtotal())],
            [f"DISCOUNT ({a.discount_type})", "", "", -float(a.discount_amount())],
            ["TOTAL DUE", "", "", float(a.total_due())],
            ["PAID", "", "", "YES" if a.is_paid else "NO"],
        ]
        return csv_response(f"appointment_{a.id}_invoice.csv", ["service","qty","unit_price","line_total"], rows)

    # -----------------------
    # Clients
    # -----------------------
    @app.get("/clients")
    def clients_list():
        q = request.args.get("q", "").strip()
        query = Client.query
        if q:
            query = query.filter(Client.full_name.ilike(f"%{q}%"))
        clients = query.order_by(Client.full_name.asc()).all()
        return render_template("clients_list.html", clients=clients, q=q)

    @app.route("/clients/new", methods=["GET","POST"])
    def client_new():
        form = ClientForm()
        if form.validate_on_submit():
            client = Client(
                full_name=form.full_name.data,
                phone=form.phone.data,
                email=form.email.data,
                date_of_birth=form.date_of_birth.data,
                notes=form.notes.data,
            )
            db.session.add(client)
            db.session.commit()
            flash("Client created.", "success")
            return redirect(url_for("clients_list"))
        return render_template("client_form.html", form=form, title="New Client")

    @app.get("/clients/<int:client_id>")
    def client_detail(client_id: int):
        client = Client.query.get_or_404(client_id)
        appts = Appointment.query.options(joinedload(Appointment.items).joinedload(AppointmentItem.service)).filter_by(
            client_id=client.id
        ).order_by(Appointment.start_at.desc()).limit(100).all()
        return render_template("client_detail.html", client=client, appts=appts)

    @app.route("/clients/<int:client_id>/edit", methods=["GET","POST"])
    def client_edit(client_id: int):
        client = Client.query.get_or_404(client_id)
        form = ClientForm(obj=client)
        if form.validate_on_submit():
            client.full_name = form.full_name.data
            client.phone = form.phone.data
            client.email = form.email.data
            client.date_of_birth = form.date_of_birth.data
            client.notes = form.notes.data
            db.session.commit()
            flash("Client updated.", "success")
            return redirect(url_for("client_detail", client_id=client.id))
        return render_template("client_form.html", form=form, title="Edit Client")

    @app.post("/clients/<int:client_id>/delete")
    def client_delete(client_id: int):
        client = Client.query.get_or_404(client_id)
        db.session.delete(client)
        db.session.commit()
        flash("Client deleted.", "warning")
        return redirect(url_for("clients_list"))

    # -----------------------
    # Services
    # -----------------------
    @app.get("/services")
    def services_list():
        services = Service.query.order_by(Service.name.asc()).all()
        return render_template("services_list.html", services=services)

    @app.route("/services/new", methods=["GET","POST"])
    def service_new():
        form = ServiceForm()
        if form.validate_on_submit():
            s = Service(
                name=form.name.data.strip(),
                default_price=form.default_price.data,
                is_active=bool(form.is_active.data),
            )
            db.session.add(s)
            db.session.commit()
            flash("Service created.", "success")
            return redirect(url_for("services_list"))
        return render_template("service_form.html", form=form, title="New Service")

    @app.route("/services/<int:service_id>/edit", methods=["GET","POST"])
    def service_edit(service_id: int):
        s = Service.query.get_or_404(service_id)
        form = ServiceForm(obj=s)
        if form.validate_on_submit():
            s.name = form.name.data.strip()
            s.default_price = form.default_price.data
            s.is_active = bool(form.is_active.data)
            db.session.commit()
            flash("Service updated.", "success")
            return redirect(url_for("services_list"))
        return render_template("service_form.html", form=form, title="Edit Service")

    @app.post("/services/<int:service_id>/delete")
    def service_delete(service_id: int):
        s = Service.query.get_or_404(service_id)
        db.session.delete(s)
        db.session.commit()
        flash("Service deleted.", "warning")
        return redirect(url_for("services_list"))

    # -----------------------
    # Appointments
    # -----------------------
    @app.get("/appointments")
    def appointments_list():
        status = request.args.get("status", "").strip()
        paid = request.args.get("paid", "").strip()
        query = Appointment.query.options(joinedload(Appointment.items).joinedload(AppointmentItem.service))
        if status:
            query = query.filter(Appointment.status == status)
        if paid == "yes":
            query = query.filter(Appointment.is_paid.is_(True))
        elif paid == "no":
            query = query.filter(Appointment.is_paid.is_(False))
        appts = query.order_by(Appointment.start_at.desc()).limit(250).all()
        return render_template("appointments_list.html", appts=appts, status=status, paid=paid)

    @app.route("/appointments/new", methods=["GET","POST"])
    def appointment_new():
        form = AppointmentForm()
        form.client_id.choices = get_clients_choices(include_blank=True)
        form.service_ids.choices = get_services_choices(active_only=True)

        if request.method == "GET":
            form.client_id.data = 0
            form.service_ids.data = []

        if form.validate_on_submit():
            if form.client_id.data == 0:
                flash("Please select a client.", "warning")
                return render_template("appointment_form.html", form=form, title="New Appointment")

            conflict = find_conflict(None, form.start_at.data, form.end_at.data)
            if conflict:
                flash(f"Conflict: overlaps with {conflict.start_at} ({conflict.client.full_name}).", "warning")
                return render_template("appointment_form.html", form=form, title="New Appointment")

            appt = Appointment(
                client_id=form.client_id.data,
                start_at=form.start_at.data,
                end_at=form.end_at.data,
                status=form.status.data,
                reason=form.reason.data,
                notes=form.notes.data,
                discount_type="amount",
                discount_value=Decimal("0"),
                is_paid=False,
                paid_at=None,
            )
            db.session.add(appt)
            db.session.commit()

            # Optional: create line-items for selected services
            service_ids = form.service_ids.data or []
            if service_ids:
                services = Service.query.filter(Service.id.in_(service_ids)).all()
                for s in services:
                    db.session.add(AppointmentItem(
                        appointment_id=appt.id,
                        service_id=s.id,
                        quantity=1,
                        unit_price=s.default_price,
                    ))
                db.session.commit()

            flash("Appointment created. Manage services and billing below.", "success")
            return redirect(url_for("appointment_billing", appt_id=appt.id))

        return render_template("appointment_form.html", form=form, title="New Appointment")

    @app.route("/appointments/<int:appt_id>/edit", methods=["GET","POST"])
    def appointment_edit(appt_id: int):
        appt = Appointment.query.get_or_404(appt_id)
        form = AppointmentForm(obj=appt)
        form.client_id.choices = get_clients_choices(include_blank=True)
        form.service_ids.choices = get_services_choices(active_only=True)

        if request.method == "GET":
            form.service_ids.data = []

        if form.validate_on_submit():
            if form.client_id.data == 0:
                flash("Please select a client.", "warning")
                return render_template("appointment_form.html", form=form, title="Edit Appointment", appt=appt)

            conflict = find_conflict(appt.id, form.start_at.data, form.end_at.data)
            if conflict:
                flash(f"Conflict: overlaps with {conflict.start_at} ({conflict.client.full_name}).", "warning")
                return render_template("appointment_form.html", form=form, title="Edit Appointment", appt=appt)

            appt.client_id = form.client_id.data
            appt.start_at = form.start_at.data
            appt.end_at = form.end_at.data
            appt.status = form.status.data
            appt.reason = form.reason.data
            appt.notes = form.notes.data
            db.session.commit()

            # Optional: add more services (do not remove existing)
            service_ids = form.service_ids.data or []
            if service_ids:
                existing = {it.service_id for it in appt.items}
                services = Service.query.filter(Service.id.in_(service_ids)).all()
                for s in services:
                    if s.id not in existing:
                        db.session.add(AppointmentItem(
                            appointment_id=appt.id,
                            service_id=s.id,
                            quantity=1,
                            unit_price=s.default_price,
                        ))
                db.session.commit()

            flash("Appointment updated.", "success")
            return redirect(url_for("appointments_list"))

        return render_template("appointment_form.html", form=form, title="Edit Appointment", appt=appt)

    @app.post("/appointments/<int:appt_id>/delete")
    def appointment_delete(appt_id: int):
        appt = Appointment.query.get_or_404(appt_id)
        db.session.delete(appt)
        db.session.commit()
        flash("Appointment deleted.", "warning")
        return redirect(url_for("appointments_list"))

    # -----------------------
    # Appointment Billing (fixed multi-form + CSRF collisions)
    # -----------------------
    @app.route("/appointments/<int:appt_id>/billing", methods=["GET","POST"])
    def appointment_billing(appt_id: int):
        appt = Appointment.query.options(joinedload(Appointment.items).joinedload(AppointmentItem.service)).get_or_404(appt_id)

        billing_form = AppointmentBillingForm(prefix="bill", obj=appt)
        item_form = AppointmentItemForm(prefix="item")
        if request.method == "GET" and billing_form.discount_value.data is None:
            billing_form.discount_value.data = Decimal("0")

        # MUST set choices before validate
        item_form.service_id.choices = get_services_choices(active_only=True)

        if request.method == "GET" and item_form.service_id.choices:
            first_id = item_form.service_id.choices[0][0]
            s0 = Service.query.get(first_id)
            if s0:
                item_form.unit_price.data = s0.default_price

        form_name = request.form.get("form_name", "")

        if request.method == "POST" and form_name == "billing":
            if billing_form.validate_on_submit():
                appt.discount_type = billing_form.discount_type.data
                appt.discount_value = billing_form.discount_value.data or Decimal("0")
                appt.is_paid = bool(billing_form.is_paid.data)
                appt.paid_at = datetime.utcnow() if appt.is_paid else None
                db.session.commit()
                flash("Billing updated.", "success")
                return redirect(url_for("appointment_billing", appt_id=appt.id))
            flash(f"Billing error: {billing_form.errors}", "warning")

        if request.method == "POST" and form_name == "item":
            if item_form.validate_on_submit():
                s = Service.query.get_or_404(item_form.service_id.data)
                it = AppointmentItem(
                    appointment_id=appt.id,
                    service_id=s.id,
                    quantity=item_form.quantity.data,
                    unit_price=item_form.unit_price.data,
                )
                db.session.add(it)
                db.session.commit()
                flash("Service added.", "success")
                return redirect(url_for("appointment_billing", appt_id=appt.id))
            flash(f"Add service error: {item_form.errors}", "warning")

        return render_template("appointment_billing.html", appt=appt, billing_form=billing_form, item_form=item_form)

    @app.post("/appointments/<int:appt_id>/items/<int:item_id>/delete")
    def appointment_item_delete(appt_id: int, item_id: int):
        appt = Appointment.query.get_or_404(appt_id)
        it = AppointmentItem.query.get_or_404(item_id)
        if it.appointment_id != appt.id:
            abort(400)
        db.session.delete(it)
        db.session.commit()
        flash("Item removed.", "warning")
        return redirect(url_for("appointment_billing", appt_id=appt.id))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)
    # app.run(debug=True)
