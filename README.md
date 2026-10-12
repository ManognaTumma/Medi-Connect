# 🏥 MediConnect - Doctor Appointment Management System

MediConnect is a comprehensive, full-featured web-based Doctor Appointment Management System built with **Flask (Python)** and **MySQL**. It streamlines the appointment scheduling workflow for patients, doctors, and healthcare administrators with modern, intuitive, and responsive interfaces.

---

## 🌟 Key Features

### 👤 Patient Portal
- **User Authentication:** Secure registration and login with session management.
- **Find Doctors:** Search and filter certified doctors by specialization, experience, and fee.
- **Appointment Booking:** Real-time slot booking with date and time selection.
- **Dashboard:** View upcoming appointments, appointment history, prescriptions, and status updates.
- **Profile Management:** Update personal details, contact info, and medical history.

### 🩺 Doctor Portal
- **Doctor Dashboard:** Manage daily schedules, view incoming appointments, and patient lists.
- **Appointment Actions:** Confirm, complete, or reschedule patient appointments.
- **Prescription & Medical Notes:** Issue prescriptions, notes, and visit summaries.
- **Profile & Availability:** Set consultation timings, fees, qualifications, and specializations.

### ⚙️ Admin Dashboard
- **Analytics & Metrics:** Total patients, registered doctors, appointments booked, and revenue/stats.
- **User Management:** Manage, activate, or deactivate doctor and patient accounts.
- **Doctor Approvals:** Verify credentials and manage departmental listings.
- **Feedback & Inquiries:** Review messages submitted through the contact form.

---

## 🛠️ Technology Stack

- **Backend:** Python 3, Flask, Flask-WTF, Werkzeug
- **Database:** MySQL (via `mysql-connector-python`)
- **Frontend:** HTML5, CSS3 (Modern Glassmorphic & Clean UI), Vanilla JavaScript
- **Security:** Password hashing, CSRF protection, environment variable configuration (`python-dotenv`)

---

## 📁 Project Structure

```text
doctor_appointment_Management_System/
│
├── static/
│   ├── css/
│   │   └── style.css            # Custom CSS styling and responsive layouts
│   └── js/
│       └── script.js           # Client-side dynamic interactions and validations
│
├── templates/                  # Jinja2 HTML templates
│   ├── admin_dashboard.html    # Administrative overview & management
│   ├── base.html               # Base layout with navigation and footer
│   ├── book_appointment.html   # Appointment booking form
│   ├── contact.html            # Contact & support page
│   ├── doctor_dashboard.html   # Doctor appointment & patient management
│   ├── doctors.html            # Doctor directory and search
│   ├── error.html              # Custom error handling pages
│   ├── index.html              # Landing page
│   ├── login.html              # Authentication login
│   ├── patient_dashboard.html  # Patient appointment tracking & history
│   ├── profile.html            # User profile view and update
│   └── register.html           # User registration
│
├── .env.example                # Example environment variables template
├── .gitignore                  # Git ignore rules for environments and temporary files
├── app.py                      # Main Flask application and routing logic
├── config.py                   # Application settings & environment loaders
├── db.py                       # Database connection pooling & query helpers
├── init_db.py                  # Database initialization and sample data seeder
├── requirements.txt            # Python package dependencies
├── schema.sql                  # MySQL database schema definition
└── README.md                   # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **MySQL Server 8.0+**
- **Git**

### 2. Clone the Repository
```bash
git clone https://github.com/ManognaTumma/MediConnect.git
cd MediConnect
```

### 3. Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Setup Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Update your `.env` with your local MySQL credentials:
```ini
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=doctor_appointment_db
SECRET_KEY=your_secret_key_here
PORT=5000
```

### 6. Initialize Database
Run the initialization script to create tables and seed default admin/sample accounts:
```bash
python init_db.py
```

### 7. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://localhost:5000
```

---

## 👩‍💻 Author

- **Manogna Tumma** - [GitHub Profile](https://github.com/ManognaTumma)
