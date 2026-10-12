import os
import re
import secrets
from datetime import datetime, date, timedelta, time
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
import db

app = Flask(__name__)
app.config.from_object(Config)

# -------------------------------------------------------------
# Security & CSRF Protection
# -------------------------------------------------------------
@app.before_request
def csrf_protect():
    """Ensure session has a CSRF token and validate on state-changing POST requests."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(24)
        
    if request.method == "POST":
        # Check token in form data or headers
        token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
        # Allow test client bypass if configured, otherwise require token
        if not app.config.get('TESTING') and (not token or token != session.get('csrf_token')):
            # If token is invalid or missing
            flash("Invalid or expired session security token. Please try again.", "danger")
            return redirect(request.referrer or url_for('index'))

@app.context_processor
def inject_global_data():
    """Provide common context data to all templates."""
    return {
        'csrf_token': session.get('csrf_token', ''),
        'current_user': {
            'user_id': session.get('user_id'),
            'name': session.get('user_name'),
            'email': session.get('user_email'),
            'role': session.get('user_role'),
            'doctor_id': session.get('doctor_id')
        } if 'user_id' in session else None,
        'current_year': datetime.now().year,
        'today_date': date.today().isoformat()
    }

# -------------------------------------------------------------
# Role-based Authorization Decorators
# -------------------------------------------------------------
def login_required(roles=None):
    """
    Decorator to restrict access to authenticated users and specific roles.
    roles can be a single role string (e.g. 'patient') or list (['admin', 'doctor']).
    """
    if isinstance(roles, str):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('login', next=request.path))

            user_role = session.get('user_role')
            if roles and user_role not in roles:
                flash("You are not authorized to view that page.", "danger")
                if user_role == 'patient':
                    return redirect(url_for('patient_dashboard'))
                elif user_role == 'doctor':
                    return redirect(url_for('doctor_dashboard'))
                elif user_role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -------------------------------------------------------------
# Helpers
# -------------------------------------------------------------
def is_valid_email(email):
    """Validate email format with regex."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def generate_slots(start_t, end_t, duration_minutes=30):
    """Generates time slot list strings (HH:MM) between start and end time."""
    slots = []
    # Convert time objects or strings
    if isinstance(start_t, str):
        try:
            start_t = datetime.strptime(start_t, "%H:%M:%S").time()
        except ValueError:
            start_t = datetime.strptime(start_t, "%H:%M").time()
    if isinstance(end_t, str):
        try:
            end_t = datetime.strptime(end_t, "%H:%M:%S").time()
        except ValueError:
            end_t = datetime.strptime(end_t, "%H:%M").time()

    curr_dt = datetime.combine(date.today(), start_t)
    end_dt = datetime.combine(date.today(), end_t)

    while curr_dt + timedelta(minutes=duration_minutes) <= end_dt:
        slots.append(curr_dt.strftime("%H:%M"))
        curr_dt += timedelta(minutes=duration_minutes)
    return slots

# -------------------------------------------------------------
# Public Routes
# -------------------------------------------------------------
@app.route('/')
def index():
    """Home landing page with healthcare services, specialties, and featured doctors."""
    try:
        specializations = db.query_db("SELECT * FROM specializations ORDER BY specialization_name ASC LIMIT 6")
        featured_doctors = db.query_db("""
            SELECT d.doctor_id, d.qualification, d.experience, d.consultation_fee, d.biography,
                   u.full_name, s.specialization_name
            FROM doctors d
            JOIN users u ON d.user_id = u.user_id
            JOIN specializations s ON d.specialization_id = s.specialization_id
            WHERE d.is_active = TRUE
            ORDER BY d.experience DESC
            LIMIT 4
        """)
        stats = {
            'doctors': db.query_db("SELECT COUNT(*) AS total FROM doctors WHERE is_active = TRUE", one=True)['total'],
            'patients': db.query_db("SELECT COUNT(*) AS total FROM users WHERE role = 'patient'", one=True)['total'],
            'specialties': db.query_db("SELECT COUNT(*) AS total FROM specializations", one=True)['total'],
            'appointments': db.query_db("SELECT COUNT(*) AS total FROM appointments", one=True)['total']
        }
    except Exception as e:
        app.logger.warning(f"Database error on index: {e}")
        specializations = []
        featured_doctors = []
        stats = {'doctors': 0, 'patients': 0, 'specialties': 0, 'appointments': 0}

    return render_template('index.html', specializations=specializations, featured_doctors=featured_doctors, stats=stats)

@app.route('/about')
def about():
    """About us page."""
    return render_template('contact.html', active_tab='about')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page and message submission handler."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        # Server-side validation
        if not name or not email or not subject or not message:
            flash("All fields are required. Please fill out the complete form.", "danger")
            return render_template('contact.html', name=name, email=email, subject=subject, message=message)

        if not is_valid_email(email):
            flash("Please enter a valid email address.", "danger")
            return render_template('contact.html', name=name, email=email, subject=subject, message=message)

        try:
            db.query_db(
                "INSERT INTO contact_messages (name, email, subject, message) VALUES (%s, %s, %s, %s)",
                (name, email, subject, message),
                commit=True
            )
            flash("Thank you for contacting MediConnect! Your message has been received.", "success")
            return redirect(url_for('contact'))
        except Exception as e:
            app.logger.error(f"Contact submit error: {e}")
            flash("Failed to submit message due to a server error. Please try again later.", "danger")

    return render_template('contact.html')

# -------------------------------------------------------------
# Authentication Routes
# -------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Patient self-registration page."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        dob = request.form.get('date_of_birth', '').strip()
        gender = request.form.get('gender', 'Other')
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validation
        errors = []
        if not full_name or len(full_name) < 2:
            errors.append("Please provide your full legal name.")
        if not email or not is_valid_email(email):
            errors.append("Please enter a valid email address.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if gender not in ['Male', 'Female', 'Other']:
            gender = 'Other'

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template('register.html', full_name=full_name, email=email, phone=phone, dob=dob, gender=gender)

        try:
            # Check for existing email
            existing_user = db.query_db("SELECT user_id FROM users WHERE email = %s", (email,), one=True)
            if existing_user:
                flash("An account with this email address already exists. Please log in.", "warning")
                return redirect(url_for('login'))

            # Insert new user
            pwd_hash = generate_password_hash(password)
            user_id = db.query_db(
                """INSERT INTO users (full_name, email, phone, date_of_birth, gender, password_hash, role)
                   VALUES (%s, %s, %s, %s, %s, %s, 'patient')""",
                (full_name, email, phone or None, dob or None, gender, pwd_hash),
                commit=True
            )

            # Automatically log in the user
            session.clear()
            session['csrf_token'] = secrets.token_hex(24)
            session['user_id'] = user_id
            session['user_name'] = full_name
            session['user_email'] = email
            session['user_role'] = 'patient'

            flash(f"Welcome to MediConnect, {full_name}! Your account has been created successfully.", "success")
            return redirect(url_for('patient_dashboard'))

        except Exception as e:
            app.logger.error(f"Registration error: {e}")
            flash("Could not complete registration due to a database error. Please try again.", "danger")

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Unified login for patients, doctors, and administrators."""
    if 'user_id' in session:
        role = session.get('user_role')
        if role == 'doctor':
            return redirect(url_for('doctor_dashboard'))
        elif role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('patient_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template('login.html', email=email)

        try:
            user = db.query_db("SELECT * FROM users WHERE email = %s", (email,), one=True)
            if not user or not check_password_hash(user['password_hash'], password):
                flash("Invalid email or password. Please verify your credentials.", "danger")
                return render_template('login.html', email=email)

            # Set user session
            session.clear()
            session['csrf_token'] = secrets.token_hex(24)
            session['user_id'] = user['user_id']
            session['user_name'] = user['full_name']
            session['user_email'] = user['email']
            session['user_role'] = user['role']

            # If user is a doctor, fetch and store their doctor_id
            if user['role'] == 'doctor':
                doc = db.query_db("SELECT doctor_id, is_active FROM doctors WHERE user_id = %s", (user['user_id'],), one=True)
                if doc:
                    if not doc['is_active']:
                        session.clear()
                        flash("Your doctor account has been deactivated. Please contact an administrator.", "danger")
                        return redirect(url_for('login'))
                    session['doctor_id'] = doc['doctor_id']

            flash(f"Welcome back, {user['full_name']}!", "success")

            # Redirect based on user role or 'next' param
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            else:
                return redirect(url_for('patient_dashboard'))

        except Exception as e:
            app.logger.error(f"Login error: {e}")
            flash("Database connection error during login. Please check database settings.", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logs out current user session."""
    session.clear()
    flash("You have been securely logged out.", "info")
    return redirect(url_for('login'))

# -------------------------------------------------------------
# Doctor Directory & Search
# -------------------------------------------------------------
@app.route('/doctors')
def doctors():
    """Doctor listing with search by name and filtering by specialization."""
    search_query = request.args.get('q', '').strip()
    specialization_filter = request.args.get('specialization', '').strip()

    sql = """
        SELECT d.doctor_id, d.qualification, d.experience, d.consultation_fee, d.biography, d.is_active,
               u.full_name, u.email, u.phone,
               s.specialization_id, s.specialization_name
        FROM doctors d
        JOIN users u ON d.user_id = u.user_id
        JOIN specializations s ON d.specialization_id = s.specialization_id
        WHERE d.is_active = TRUE
    """
    params = []

    if search_query:
        sql += " AND (u.full_name LIKE %s OR d.qualification LIKE %s)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    if specialization_filter:
        sql += " AND s.specialization_id = %s"
        params.append(specialization_filter)

    sql += " ORDER BY u.full_name ASC"

    try:
        doctor_list = db.query_db(sql, params)
        specializations = db.query_db("SELECT * FROM specializations ORDER BY specialization_name ASC")
    except Exception as e:
        app.logger.error(f"Doctor listing error: {e}")
        doctor_list = []
        specializations = []
        flash("Could not load doctor list from database.", "danger")

    return render_template(
        'doctors.html',
        doctors=doctor_list,
        specializations=specializations,
        search_query=search_query,
        selected_spec=specialization_filter
    )

# -------------------------------------------------------------
# Appointment Booking & Dynamic Slots
# -------------------------------------------------------------
@app.route('/api/doctor-slots')
def get_doctor_slots():
    """
    JSON API: returns available time slots for a doctor on a specific date.
    Query params: doctor_id, date (YYYY-MM-DD)
    """
    doctor_id = request.args.get('doctor_id')
    apt_date_str = request.args.get('date')

    if not doctor_id or not apt_date_str:
        return jsonify({'success': False, 'error': 'Doctor and date are required.'}), 400

    try:
        apt_date = datetime.strptime(apt_date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format (expected YYYY-MM-DD).'}), 400

    # Ensure booking is not in the past
    today = date.today()
    if apt_date < today:
        return jsonify({'success': False, 'error': 'Cannot book appointments for past dates.', 'slots': []})

    try:
        # Check doctor availability windows for that date
        availabilities = db.query_db(
            """SELECT start_time, end_time, slot_duration
               FROM doctor_availability
               WHERE doctor_id = %s AND available_date = %s AND is_available = TRUE""",
            (doctor_id, apt_date)
        )

        if not availabilities:
            return jsonify({
                'success': True,
                'slots': [],
                'message': 'No consultation slots scheduled for this doctor on selected date.'
            })

        # Get all existing non-cancelled bookings for this doctor on that date
        booked_rows = db.query_db(
            """SELECT appointment_time
               FROM appointments
               WHERE doctor_id = %s AND appointment_date = %s
                 AND status NOT IN ('Cancelled', 'Rejected')""",
            (doctor_id, apt_date)
        )
        # Format booked times as 'HH:MM'
        booked_times = set()
        for b in booked_rows:
            t = b['appointment_time']
            if isinstance(t, timedelta):
                total_seconds = int(t.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                booked_times.add(f"{hours:02d}:{minutes:02d}")
            elif isinstance(t, str):
                booked_times.add(t[:5])
            elif isinstance(t, time):
                booked_times.add(t.strftime("%H:%M"))

        # Build list of open slots across all availability windows
        all_slots = []
        now = datetime.now()

        for av in availabilities:
            s_time = av['start_time']
            e_time = av['end_time']
            dur = av['slot_duration'] or 30

            # Convert timedelta from mysql-connector if needed
            if isinstance(s_time, timedelta):
                s_tot = int(s_time.total_seconds())
                s_time = time(s_tot // 3600, (s_tot % 3600) // 60)
            if isinstance(e_time, timedelta):
                e_tot = int(e_time.total_seconds())
                e_time = time(e_tot // 3600, (e_tot % 3600) // 60)

            window_slots = generate_slots(s_time, e_time, dur)
            for slot in window_slots:
                # If date is today, exclude slots that have already passed
                if apt_date == today:
                    slot_hour, slot_min = map(int, slot.split(':'))
                    if time(slot_hour, slot_min) <= now.time():
                        continue

                is_booked = slot in booked_times
                all_slots.append({
                    'time': slot,
                    'available': not is_booked
                })

        return jsonify({'success': True, 'slots': all_slots})

    except Exception as e:
        app.logger.error(f"Error fetching slots: {e}")
        return jsonify({'success': False, 'error': 'Database error while checking slots.'}), 500

@app.route('/book-appointment', methods=['GET', 'POST'])
@login_required(roles='patient')
def book_appointment():
    """Appointment booking page and processing."""
    selected_doctor_id = request.args.get('doctor_id', type=int)

    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id', type=int)
        appointment_date_str = request.form.get('appointment_date', '').strip()
        appointment_time_str = request.form.get('appointment_time', '').strip()
        reason = request.form.get('reason', '').strip()
        patient_id = session.get('user_id')

        # Validation
        errors = []
        if not doctor_id:
            errors.append("Please select a doctor.")
        if not appointment_date_str:
            errors.append("Please select an appointment date.")
        if not appointment_time_str:
            errors.append("Please select an appointment time slot.")
        if not reason or len(reason) < 5:
            errors.append("Please provide a reason for the consultation (at least 5 characters).")

        # Validate date
        try:
            apt_date = datetime.strptime(appointment_date_str, "%Y-%m-%d").date()
            if apt_date < date.today():
                errors.append("Appointments cannot be booked for past dates.")
        except ValueError:
            errors.append("Invalid date format.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return redirect(url_for('book_appointment', doctor_id=doctor_id))

        # Check for duplicate / double-booking in transaction-safe manner
        try:
            # Format time with seconds if needed
            if len(appointment_time_str) == 5:
                formatted_time = appointment_time_str + ":00"
            else:
                formatted_time = appointment_time_str

            # Check if doctor is active
            doc = db.query_db("SELECT doctor_id FROM doctors WHERE doctor_id = %s AND is_active = TRUE", (doctor_id,), one=True)
            if not doc:
                flash("Selected doctor is not available for appointments.", "danger")
                return redirect(url_for('doctors'))

            # Check if this slot is already booked for this doctor
            existing_apt = db.query_db(
                """SELECT appointment_id FROM appointments
                   WHERE doctor_id = %s AND appointment_date = %s AND appointment_time = %s
                     AND status NOT IN ('Cancelled', 'Rejected')""",
                (doctor_id, apt_date, formatted_time),
                one=True
            )
            if existing_apt:
                flash("This time slot was just booked by another patient. Please choose another time slot.", "warning")
                return redirect(url_for('book_appointment', doctor_id=doctor_id))

            # Insert appointment
            appointment_id = db.query_db(
                """INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, status)
                   VALUES (%s, %s, %s, %s, %s, 'Pending')""",
                (patient_id, doctor_id, apt_date, formatted_time, reason),
                commit=True
            )

            flash(f"Appointment booked successfully! Your Appointment Reference ID is #{appointment_id}.", "success")
            return redirect(url_for('patient_dashboard'))

        except Exception as e:
            app.logger.error(f"Appointment booking error: {e}")
            flash("Could not book appointment due to a database error. Please try again.", "danger")
            return redirect(url_for('book_appointment', doctor_id=doctor_id))

    # GET request: load active doctors for dropdown
    try:
        doctor_list = db.query_db("""
            SELECT d.doctor_id, d.consultation_fee, d.qualification,
                   u.full_name, s.specialization_name
            FROM doctors d
            JOIN users u ON d.user_id = u.user_id
            JOIN specializations s ON d.specialization_id = s.specialization_id
            WHERE d.is_active = TRUE
            ORDER BY u.full_name ASC
        """)
    except Exception as e:
        app.logger.error(f"Error loading doctors for booking: {e}")
        doctor_list = []

    return render_template(
        'book_appointment.html',
        doctors=doctor_list,
        selected_doctor_id=selected_doctor_id
    )

# -------------------------------------------------------------
# Patient Dashboard
# -------------------------------------------------------------
@app.route('/patient/dashboard')
@login_required(roles='patient')
def patient_dashboard():
    """Displays patient profile, upcoming and historical appointments."""
    patient_id = session.get('user_id')
    try:
        user_profile = db.query_db("SELECT * FROM users WHERE user_id = %s", (patient_id,), one=True)
        appointments = db.query_db("""
            SELECT a.appointment_id, a.appointment_date, a.appointment_time, a.reason, a.status, a.created_at,
                   u.full_name AS doctor_name, u.email AS doctor_email, u.phone AS doctor_phone,
                   s.specialization_name, d.consultation_fee, d.qualification
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN users u ON d.user_id = u.user_id
            JOIN specializations s ON d.specialization_id = s.specialization_id
            WHERE a.patient_id = %s
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        """, (patient_id,))

        # Categorize
        today = date.today()
        def _to_date(val):
            if isinstance(val, date):
                return val
            if isinstance(val, str):
                try:
                    return datetime.strptime(val[:10], "%Y-%m-%d").date()
                except Exception:
                    pass
            return today

        upcoming = [apt for apt in appointments if _to_date(apt['appointment_date']) >= today and apt['status'] in ('Pending', 'Confirmed')]
        past = [apt for apt in appointments if apt not in upcoming]

    except Exception as e:
        app.logger.error(f"Patient dashboard error: {e}")
        user_profile = {}
        upcoming = []
        past = []
        flash("Could not load your dashboard data from the database.", "danger")

    return render_template(
        'patient_dashboard.html',
        user=user_profile,
        upcoming_appointments=upcoming,
        past_appointments=past
    )

@app.route('/cancel-appointment/<int:appointment_id>', methods=['POST'])
@login_required(roles=['patient', 'admin'])
def cancel_appointment(appointment_id):
    """Allows patient or admin to cancel an appointment."""
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    try:
        apt = db.query_db("SELECT * FROM appointments WHERE appointment_id = %s", (appointment_id,), one=True)
        if not apt:
            flash("Appointment not found.", "danger")
            return redirect(request.referrer or url_for('index'))

        # Security check: if patient, must be their appointment
        if user_role == 'patient' and apt['patient_id'] != user_id:
            flash("Unauthorized: You can only cancel your own appointments.", "danger")
            return redirect(url_for('patient_dashboard'))

        if apt['status'] in ('Cancelled', 'Rejected', 'Completed'):
            flash(f"Appointment cannot be cancelled as it is already marked '{apt['status']}'.", "warning")
            return redirect(request.referrer or url_for('patient_dashboard'))

        db.query_db(
            "UPDATE appointments SET status = 'Cancelled' WHERE appointment_id = %s",
            (appointment_id,),
            commit=True
        )
        flash(f"Appointment #{appointment_id} has been cancelled.", "info")

    except Exception as e:
        app.logger.error(f"Error cancelling appointment: {e}")
        flash("Database error while cancelling appointment.", "danger")

    if user_role == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('patient_dashboard'))

# -------------------------------------------------------------
# Doctor Dashboard & Availability
# -------------------------------------------------------------
@app.route('/doctor/dashboard')
@login_required(roles='doctor')
def doctor_dashboard():
    """Doctor dashboard to review bookings, update statuses, and manage schedule."""
    doctor_id = session.get('doctor_id')
    user_id = session.get('user_id')

    # If doctor_id is missing from session, fetch it
    if not doctor_id:
        doc = db.query_db("SELECT doctor_id FROM doctors WHERE user_id = %s", (user_id,), one=True)
        if doc:
            doctor_id = doc['doctor_id']
            session['doctor_id'] = doctor_id
        else:
            flash("Doctor profile not found.", "danger")
            return redirect(url_for('login'))

    try:
        doctor_info = db.query_db("""
            SELECT d.*, u.full_name, u.email, u.phone, s.specialization_name
            FROM doctors d
            JOIN users u ON d.user_id = u.user_id
            JOIN specializations s ON d.specialization_id = s.specialization_id
            WHERE d.doctor_id = %s
        """, (doctor_id,), one=True)

        appointments = db.query_db("""
            SELECT a.*, u.full_name AS patient_name, u.email AS patient_email,
                   u.phone AS patient_phone, u.gender AS patient_gender, u.date_of_birth
            FROM appointments a
            JOIN users u ON a.patient_id = u.user_id
            WHERE a.doctor_id = %s
            ORDER BY a.appointment_date ASC, a.appointment_time ASC
        """, (doctor_id,))

        availability_list = db.query_db("""
            SELECT * FROM doctor_availability
            WHERE doctor_id = %s AND available_date >= CURDATE()
            ORDER BY available_date ASC, start_time ASC
        """, (doctor_id,))

        stats = {
            'total': len(appointments),
            'pending': sum(1 for a in appointments if a['status'] == 'Pending'),
            'confirmed': sum(1 for a in appointments if a['status'] == 'Confirmed'),
            'completed': sum(1 for a in appointments if a['status'] == 'Completed')
        }

    except Exception as e:
        app.logger.error(f"Doctor dashboard error: {e}")
        doctor_info = {}
        appointments = []
        availability_list = []
        stats = {'total': 0, 'pending': 0, 'confirmed': 0, 'completed': 0}
        flash("Could not load doctor dashboard.", "danger")

    return render_template(
        'doctor_dashboard.html',
        doctor=doctor_info,
        appointments=appointments,
        availabilities=availability_list,
        stats=stats
    )

@app.route('/doctor/appointment/status/<int:appointment_id>', methods=['POST'])
@login_required(roles='doctor')
def doctor_update_status(appointment_id):
    """Doctor accepts, rejects, or completes an appointment."""
    doctor_id = session.get('doctor_id')
    new_status = request.form.get('status')

    valid_statuses = ['Confirmed', 'Rejected', 'Completed', 'Cancelled']
    if new_status not in valid_statuses:
        flash("Invalid appointment status.", "danger")
        return redirect(url_for('doctor_dashboard'))

    try:
        # Verify doctor owns this appointment
        apt = db.query_db(
            "SELECT appointment_id FROM appointments WHERE appointment_id = %s AND doctor_id = %s",
            (appointment_id, doctor_id),
            one=True
        )
        if not apt:
            flash("Unauthorized to update this appointment.", "danger")
            return redirect(url_for('doctor_dashboard'))

        db.query_db(
            "UPDATE appointments SET status = %s WHERE appointment_id = %s",
            (new_status, appointment_id),
            commit=True
        )
        flash(f"Appointment #{appointment_id} status updated to '{new_status}'.", "success")
    except Exception as e:
        app.logger.error(f"Error updating appointment status: {e}")
        flash("Failed to update status due to database error.", "danger")

    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/availability/add', methods=['POST'])
@login_required(roles='doctor')
def doctor_add_availability():
    """Doctor adds a new availability date and time slot block."""
    doctor_id = session.get('doctor_id')
    avail_date_str = request.form.get('available_date')
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')
    duration = request.form.get('slot_duration', type=int) or 30

    if not avail_date_str or not start_time_str or not end_time_str:
        flash("Please provide date, start time, and end time.", "danger")
        return redirect(url_for('doctor_dashboard'))

    try:
        avail_date = datetime.strptime(avail_date_str, "%Y-%m-%d").date()
        if avail_date < date.today():
            flash("Cannot set availability in the past.", "danger")
            return redirect(url_for('doctor_dashboard'))

        s_t = datetime.strptime(start_time_str, "%H:%M").time()
        e_t = datetime.strptime(end_time_str, "%H:%M").time()
        if s_t >= e_t:
            flash("Start time must be before end time.", "danger")
            return redirect(url_for('doctor_dashboard'))

        db.query_db(
            """INSERT INTO doctor_availability (doctor_id, available_date, start_time, end_time, slot_duration, is_available)
               VALUES (%s, %s, %s, %s, %s, TRUE)""",
            (doctor_id, avail_date, start_time_str, end_time_str, duration),
            commit=True
        )
        flash("Availability schedule added successfully!", "success")
    except Exception as e:
        app.logger.error(f"Error adding availability: {e}")
        flash("Database error while creating schedule block.", "danger")

    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/availability/delete/<int:availability_id>', methods=['POST'])
@login_required(roles='doctor')
def doctor_delete_availability(availability_id):
    """Doctor removes an availability schedule."""
    doctor_id = session.get('doctor_id')
    try:
        db.query_db(
            "DELETE FROM doctor_availability WHERE availability_id = %s AND doctor_id = %s",
            (availability_id, doctor_id),
            commit=True
        )
        flash("Availability slot removed.", "info")
    except Exception as e:
        app.logger.error(f"Error deleting availability: {e}")
        flash("Database error while removing availability slot.", "danger")

    return redirect(url_for('doctor_dashboard'))

# -------------------------------------------------------------
# Admin Dashboard & Full System Management
# -------------------------------------------------------------
@app.route('/admin/dashboard')
@login_required(roles='admin')
def admin_dashboard():
    """Admin centralized management dashboard with statistics and CRUD."""
    try:
        # KPI Counts
        total_doctors = db.query_db("SELECT COUNT(*) AS total FROM doctors", one=True)['total']
        total_patients = db.query_db("SELECT COUNT(*) AS total FROM users WHERE role = 'patient'", one=True)['total']
        total_appointments = db.query_db("SELECT COUNT(*) AS total FROM appointments", one=True)['total']
        pending_appointments = db.query_db("SELECT COUNT(*) AS total FROM appointments WHERE status = 'Pending'", one=True)['total']

        # Doctors List with details
        doctors = db.query_db("""
            SELECT d.doctor_id, d.user_id, d.qualification, d.experience, d.consultation_fee, d.biography, d.is_active,
                   u.full_name, u.email, u.phone,
                   s.specialization_id, s.specialization_name
            FROM doctors d
            JOIN users u ON d.user_id = u.user_id
            JOIN specializations s ON d.specialization_id = s.specialization_id
            ORDER BY u.full_name ASC
        """)

        # Patients List
        patients = db.query_db("""
            SELECT user_id, full_name, email, phone, date_of_birth, gender, created_at,
                   (SELECT COUNT(*) FROM appointments WHERE patient_id = users.user_id) AS total_bookings
            FROM users
            WHERE role = 'patient'
            ORDER BY created_at DESC
        """)

        # Appointments List
        appointments = db.query_db("""
            SELECT a.*, p.full_name AS patient_name, doc_u.full_name AS doctor_name, s.specialization_name
            FROM appointments a
            JOIN users p ON a.patient_id = p.user_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN users doc_u ON d.user_id = doc_u.user_id
            JOIN specializations s ON d.specialization_id = s.specialization_id
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
            LIMIT 50
        """)

        # Specializations List with doctor count
        specializations = db.query_db("""
            SELECT s.*, COUNT(d.doctor_id) AS doctor_count
            FROM specializations s
            LEFT JOIN doctors d ON s.specialization_id = d.specialization_id
            GROUP BY s.specialization_id
            ORDER BY s.specialization_name ASC
        """)

        # Contact Messages
        contact_messages = db.query_db("""
            SELECT * FROM contact_messages ORDER BY created_at DESC LIMIT 20
        """)

        # Stats breakdown for mini-chart
        status_counts = db.query_db("""
            SELECT status, COUNT(*) AS count
            FROM appointments
            GROUP BY status
        """)

    except Exception as e:
        app.logger.error(f"Admin dashboard error: {e}")
        total_doctors = total_patients = total_appointments = pending_appointments = 0
        doctors = []
        patients = []
        appointments = []
        specializations = []
        contact_messages = []
        status_counts = []
        flash("Could not load administrative data from database.", "danger")

    return render_template(
        'admin_dashboard.html',
        stats={
            'total_doctors': total_doctors,
            'total_patients': total_patients,
            'total_appointments': total_appointments,
            'pending_appointments': pending_appointments
        },
        doctors=doctors,
        patients=patients,
        appointments=appointments,
        specializations=specializations,
        contact_messages=contact_messages,
        status_counts=status_counts
    )

# Admin Doctor CRUD
@app.route('/admin/doctor/add', methods=['POST'])
@login_required(roles='admin')
def admin_add_doctor():
    """Admin creates a new doctor record (creates user + doctor profile)."""
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    specialization_id = request.form.get('specialization_id', type=int)
    qualification = request.form.get('qualification', '').strip()
    experience = request.form.get('experience', type=int) or 0
    consultation_fee = request.form.get('consultation_fee', type=float) or 50.0
    biography = request.form.get('biography', '').strip()
    password = request.form.get('password', 'Doctor@123')

    if not full_name or not email or not specialization_id or not qualification:
        flash("Full name, email, specialization, and qualification are required.", "danger")
        return redirect(url_for('admin_dashboard'))

    try:
        # Check if email exists
        if db.query_db("SELECT user_id FROM users WHERE email = %s", (email,), one=True):
            flash("User with this email already exists.", "danger")
            return redirect(url_for('admin_dashboard'))

        # Insert user
        pwd_hash = generate_password_hash(password)
        user_id = db.query_db(
            """INSERT INTO users (full_name, email, phone, password_hash, role)
               VALUES (%s, %s, %s, %s, 'doctor')""",
            (full_name, email, phone or None, pwd_hash),
            commit=True
        )

        # Insert doctor
        db.query_db(
            """INSERT INTO doctors (user_id, specialization_id, qualification, experience, consultation_fee, biography, is_active)
               VALUES (%s, %s, %s, %s, %s, %s, TRUE)""",
            (user_id, specialization_id, qualification, experience, consultation_fee, biography),
            commit=True
        )

        flash(f"Doctor {full_name} added successfully! (Default Password: {password})", "success")
    except Exception as e:
        app.logger.error(f"Error adding doctor: {e}")
        flash("Database error while adding doctor.", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/doctor/edit/<int:doctor_id>', methods=['POST'])
@login_required(roles='admin')
def admin_edit_doctor(doctor_id):
    """Admin updates an existing doctor profile."""
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    specialization_id = request.form.get('specialization_id', type=int)
    qualification = request.form.get('qualification', '').strip()
    experience = request.form.get('experience', type=int) or 0
    consultation_fee = request.form.get('consultation_fee', type=float) or 50.0
    biography = request.form.get('biography', '').strip()

    try:
        doc = db.query_db("SELECT user_id FROM doctors WHERE doctor_id = %s", (doctor_id,), one=True)
        if not doc:
            flash("Doctor not found.", "danger")
            return redirect(url_for('admin_dashboard'))

        # Update users table
        db.query_db(
            "UPDATE users SET full_name = %s, phone = %s WHERE user_id = %s",
            (full_name, phone or None, doc['user_id']),
            commit=True
        )

        # Update doctors table
        db.query_db(
            """UPDATE doctors
               SET specialization_id = %s, qualification = %s, experience = %s, consultation_fee = %s, biography = %s
               WHERE doctor_id = %s""",
            (specialization_id, qualification, experience, consultation_fee, biography, doctor_id),
            commit=True
        )
        flash("Doctor profile updated successfully.", "success")
    except Exception as e:
        app.logger.error(f"Error editing doctor: {e}")
        flash("Database error while updating doctor.", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/doctor/toggle/<int:doctor_id>', methods=['POST'])
@login_required(roles='admin')
def admin_toggle_doctor(doctor_id):
    """Admin activates or deactivates a doctor account."""
    try:
        doc = db.query_db("SELECT is_active, user_id FROM doctors WHERE doctor_id = %s", (doctor_id,), one=True)
        if not doc:
            flash("Doctor not found.", "danger")
            return redirect(url_for('admin_dashboard'))

        new_status = not doc['is_active']
        db.query_db("UPDATE doctors SET is_active = %s WHERE doctor_id = %s", (new_status, doctor_id), commit=True)
        msg = "Doctor activated." if new_status else "Doctor deactivated."
        flash(msg, "info")
    except Exception as e:
        app.logger.error(f"Error toggling doctor: {e}")
        flash("Database error while updating doctor status.", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/doctor/delete/<int:doctor_id>', methods=['POST'])
@login_required(roles='admin')
def admin_delete_doctor(doctor_id):
    """
    Admin deletes a doctor safely. If appointments exist, soft deactivates instead
    to maintain historical audit integrity.
    """
    try:
        apt_count = db.query_db("SELECT COUNT(*) AS total FROM appointments WHERE doctor_id = %s", (doctor_id,), one=True)['total']
        doc = db.query_db("SELECT user_id FROM doctors WHERE doctor_id = %s", (doctor_id,), one=True)

        if not doc:
            flash("Doctor not found.", "danger")
            return redirect(url_for('admin_dashboard'))

        if apt_count > 0:
            # Safe delete rule: Deactivate rather than delete to preserve appointment histories
            db.query_db("UPDATE doctors SET is_active = FALSE WHERE doctor_id = %s", (doctor_id,), commit=True)
            flash(f"Doctor has {apt_count} linked appointment records. Account has been safely deactivated instead of deleted to protect patient history.", "warning")
        else:
            # Delete clean
            db.query_db("DELETE FROM users WHERE user_id = %s", (doc['user_id'],), commit=True)
            flash("Doctor record removed permanently.", "success")

    except Exception as e:
        app.logger.error(f"Error deleting doctor: {e}")
        flash("Database error while removing doctor record.", "danger")

    return redirect(url_for('admin_dashboard'))

# Admin Specialization CRUD
@app.route('/admin/specialization/add', methods=['POST'])
@login_required(roles='admin')
def admin_add_specialization():
    """Admin adds a new medical specialization."""
    name = request.form.get('specialization_name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash("Specialization name is required.", "danger")
        return redirect(url_for('admin_dashboard'))

    try:
        db.query_db(
            "INSERT INTO specializations (specialization_name, description) VALUES (%s, %s)",
            (name, description),
            commit=True
        )
        flash(f"Specialization '{name}' added successfully.", "success")
    except Exception as e:
        app.logger.error(f"Error adding specialization: {e}")
        flash("Could not add specialization. Name may already exist.", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/specialization/edit/<int:spec_id>', methods=['POST'])
@login_required(roles='admin')
def admin_edit_specialization(spec_id):
    """Admin updates specialization name or description."""
    name = request.form.get('specialization_name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash("Specialization name is required.", "danger")
        return redirect(url_for('admin_dashboard'))

    try:
        db.query_db(
            "UPDATE specializations SET specialization_name = %s, description = %s WHERE specialization_id = %s",
            (name, description, spec_id),
            commit=True
        )
        flash("Specialization updated successfully.", "success")
    except Exception as e:
        app.logger.error(f"Error updating specialization: {e}")
        flash("Could not update specialization.", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/specialization/delete/<int:spec_id>', methods=['POST'])
@login_required(roles='admin')
def admin_delete_specialization(spec_id):
    """Admin deletes specialization with safe deletion rule (if no doctors assigned)."""
    try:
        doctor_count = db.query_db(
            "SELECT COUNT(*) AS total FROM doctors WHERE specialization_id = %s",
            (spec_id,),
            one=True
        )['total']

        if doctor_count > 0:
            flash(f"Cannot delete specialization: {doctor_count} doctor(s) are currently assigned to this specialization. Reassign them first.", "danger")
            return redirect(url_for('admin_dashboard'))

        db.query_db("DELETE FROM specializations WHERE specialization_id = %s", (spec_id,), commit=True)
        flash("Specialization removed successfully.", "success")
    except Exception as e:
        app.logger.error(f"Error deleting specialization: {e}")
        flash("Database error while deleting specialization.", "danger")

    return redirect(url_for('admin_dashboard'))

# Admin Appointment Status Update
@app.route('/admin/appointment/status/<int:appointment_id>', methods=['POST'])
@login_required(roles='admin')
def admin_update_appointment_status(appointment_id):
    """Admin updates status of any appointment."""
    new_status = request.form.get('status')
    valid_statuses = ['Pending', 'Confirmed', 'Rejected', 'Cancelled', 'Completed']

    if new_status not in valid_statuses:
        flash("Invalid status selected.", "danger")
        return redirect(url_for('admin_dashboard'))

    try:
        db.query_db(
            "UPDATE appointments SET status = %s WHERE appointment_id = %s",
            (new_status, appointment_id),
            commit=True
        )
        flash(f"Appointment #{appointment_id} status changed to '{new_status}'.", "success")
    except Exception as e:
        app.logger.error(f"Admin appointment status error: {e}")
        flash("Database error while updating appointment.", "danger")

    return redirect(url_for('admin_dashboard'))

# Admin Delete Contact Message
@app.route('/admin/message/delete/<int:message_id>', methods=['POST'])
@login_required(roles='admin')
def admin_delete_message(message_id):
    """Admin deletes a contact inquiry message."""
    try:
        db.query_db("DELETE FROM contact_messages WHERE message_id = %s", (message_id,), commit=True)
        flash("Contact message deleted.", "info")
    except Exception as e:
        app.logger.error(f"Error deleting message: {e}")
        flash("Could not delete message.", "danger")

    return redirect(url_for('admin_dashboard'))

# -------------------------------------------------------------
# User Profile Management
# -------------------------------------------------------------
@app.route('/profile', methods=['GET', 'POST'])
@login_required()
def profile():
    """Profile viewing and editing for all authenticated users."""
    user_id = session.get('user_id')

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        dob = request.form.get('date_of_birth', '').strip()
        gender = request.form.get('gender', 'Other')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not full_name:
            flash("Full name cannot be blank.", "danger")
            return redirect(url_for('profile'))

        if new_password:
            if len(new_password) < 6:
                flash("New password must be at least 6 characters.", "danger")
                return redirect(url_for('profile'))
            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                return redirect(url_for('profile'))

        try:
            if new_password:
                pwd_hash = generate_password_hash(new_password)
                db.query_db(
                    """UPDATE users
                       SET full_name = %s, phone = %s, date_of_birth = %s, gender = %s, password_hash = %s
                       WHERE user_id = %s""",
                    (full_name, phone or None, dob or None, gender, pwd_hash, user_id),
                    commit=True
                )
            else:
                db.query_db(
                    """UPDATE users
                       SET full_name = %s, phone = %s, date_of_birth = %s, gender = %s
                       WHERE user_id = %s""",
                    (full_name, phone or None, dob or None, gender, user_id),
                    commit=True
                )

            session['user_name'] = full_name
            flash("Profile updated successfully!", "success")
            return redirect(url_for('profile'))

        except Exception as e:
            app.logger.error(f"Profile update error: {e}")
            flash("Database error while updating profile.", "danger")

    try:
        user_data = db.query_db("SELECT * FROM users WHERE user_id = %s", (user_id,), one=True)
    except Exception as e:
        app.logger.error(f"Profile load error: {e}")
        user_data = {}

    return render_template('profile.html', user=user_data)

# -------------------------------------------------------------
# Error Handlers
# -------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, message="The page or resource you requested could not be found."), 404

@app.errorhandler(403)
def access_forbidden(e):
    return render_template('error.html', error_code=403, message="Access forbidden. You do not have permission to access this area."), 403

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, message="An internal server error occurred. Please check database connectivity."), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = Config.DEBUG
    print(f"[*] Starting CarePoint Doctor Appointment Management System on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
