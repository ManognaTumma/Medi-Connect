import os
import re
import logging
import sqlite3
import tempfile
import mysql.connector
from mysql.connector import Error, pooling
from config import Config

logger = logging.getLogger(__name__)

# Connection pool holder
_pool = None
_use_sqlite = False
_sqlite_initialized = False

def get_sqlite_path():
    """Returns the filesystem path for the SQLite database fallback."""
    custom_path = os.environ.get('SQLITE_DB_PATH')
    if custom_path:
        return custom_path
    # On Vercel or read-only cloud environments, /tmp is writable
    if os.environ.get('VERCEL') or not os.access(os.getcwd(), os.W_OK):
        return os.path.join(tempfile.gettempdir(), 'medi_connect.db')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'doctor_appointment.sqlite3')

def init_sqlite_db(conn):
    """Initializes schema and seed records in SQLite if tables do not exist."""
    global _sqlite_initialized
    if _sqlite_initialized:
        return

    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        date_of_birth TEXT,
        gender TEXT DEFAULT 'Other',
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'patient',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS specializations (
        specialization_id INTEGER PRIMARY KEY AUTOINCREMENT,
        specialization_name TEXT NOT NULL UNIQUE,
        description TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        specialization_id INTEGER NOT NULL,
        qualification TEXT NOT NULL,
        experience INTEGER NOT NULL DEFAULT 0,
        consultation_fee REAL NOT NULL DEFAULT 50.00,
        biography TEXT,
        is_active INTEGER NOT NULL DEFAULT 1
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        reason TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctor_availability (
        availability_id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL,
        available_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        slot_duration INTEGER NOT NULL DEFAULT 30,
        is_available INTEGER NOT NULL DEFAULT 1
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contact_messages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed 15 specializations
    specs = [
        (1, 'Cardiologist', 'Heart and blood vessel specialist.'),
        (2, 'Neurologist', 'Brain, spine, nerves, and nervous system specialist.'),
        (3, 'Pediatrician', "Infants, children, and adolescents' physician."),
        (4, 'Dermatologist', 'Skin, hair, and nail specialist.'),
        (5, 'Orthopedist (Orthopedic Surgeon)', 'Bones, joints, muscles, and musculoskeletal system specialist.'),
        (6, 'Gynecologist/Obstetrician', "Women's reproductive health and pregnancy specialist."),
        (7, 'Dentist', 'Teeth and jaw bone specialist.'),
        (8, 'Ophthalmologist', 'Eye and vision specialist.'),
        (9, 'Anesthesiologist', 'Pain management and anesthesia specialist during surgery.'),
        (10, 'Endocrinologist', 'Hormone imbalances, diabetes, and thyroid disease specialist.'),
        (11, 'Gastroenterologist', 'Digestive system and stomach specialist.'),
        (12, 'Hematologist', 'Blood and bone marrow specialist.'),
        (13, 'Oncologist', 'Cancer diagnosis and treatment specialist.'),
        (14, 'Nephrologist', 'Kidney care and kidney disease specialist.'),
        (15, 'Psychiatrist', 'Mental health and emotional disorders specialist.')
    ]
    cursor.executemany("INSERT OR REPLACE INTO specializations (specialization_id, specialization_name, description) VALUES (?, ?, ?)", specs)

    # Seed initial accounts if users table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_hash = "scrypt:32768:8:1$8foPf0WMisD30TmQ$dd186102cf40f055360c9bceb624e3d26e398a591a3721311bc4e004881a70cb561ebf0f5fd9ec47c3a6deb2f1de2bd8d1351389cb5bd0d7dacb208fde0b86e8"
        doc_hash = "scrypt:32768:8:1$X672wTZ1ybALXtjV$35e11992d6b7ffc649c9e10d46a3f3fa60d067f4a6288a967f83c3e2ee1a521f319435c2ac4c15b3afe30f22679d773cb3a8cd1be23edd488c1f79753acfb97e"
        pat_hash = "scrypt:32768:8:1$oNQQlC37JiXFsAUA$795f805bae9523a172648e9a4fcf32893b5e02eaac01b68c77cd1271707592ae26cbc5926688809cf4287981b0519cf5d64b22426fb924af9256dffd411616e8"

        users_seed = [
            (1, 'System Administrator', 'admin@carepoint.com', '+91 9876500001', '1985-06-15', 'Male', admin_hash, 'admin'),
            (2, 'Dr. Sarah Jenkins', 'sarah.jenkins@carepoint.com', '+91 9876500002', '1980-03-22', 'Female', doc_hash, 'doctor'),
            (3, 'Dr. Michael Chen', 'michael.chen@carepoint.com', '+91 9876500003', '1978-11-09', 'Male', doc_hash, 'doctor'),
            (4, 'Dr. Emily Rodriguez', 'emily.rodriguez@carepoint.com', '+91 9876500004', '1986-07-14', 'Female', doc_hash, 'doctor'),
            (5, 'Dr. David Patel', 'david.patel@carepoint.com', '+91 9876500005', '1982-09-30', 'Male', doc_hash, 'doctor'),
            (6, 'John Doe', 'patient@carepoint.com', '+91 9876500006', '1992-04-18', 'Male', pat_hash, 'patient'),
        ]
        cursor.executemany("INSERT INTO users (user_id, full_name, email, phone, date_of_birth, gender, password_hash, role) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", users_seed)

        docs_seed = [
            (1, 2, 1, 'MD (Cardiology), FACC - Harvard Medical School', 14, 120.00, 'Senior interventional cardiologist with over 14 years of clinical experience specializing in preventive heart health and arrhythmias.', 1),
            (2, 3, 2, 'MD, PhD (Neurology) - Johns Hopkins University', 16, 150.00, 'Board-certified neurologist specializing in neuro-muscular disorders, headache management, and stroke rehabilitation.', 1),
            (3, 4, 3, 'MD (Pediatrics), FAAP - Stanford University', 9, 90.00, 'Compassionate pediatrician devoted to child wellness, developmental milestones, preventive care, and pediatric nutrition.', 1),
            (4, 5, 4, 'MBBS, MD (Dermatology) - Mayo Clinic', 11, 110.00, 'Expert clinical dermatologist offering treatment for eczema, psoriasis, acne therapy, and preventive skin screening.', 1),
        ]
        cursor.executemany("INSERT INTO doctors (doctor_id, user_id, specialization_id, qualification, experience, consultation_fee, biography, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", docs_seed)

    conn.commit()
    cursor.close()
    _sqlite_initialized = True

def get_sqlite_connection():
    """Creates an active SQLite connection configured with dict row factory."""
    db_path = get_sqlite_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_sqlite_db(conn)
    return conn

def get_connection_pool():
    """Initializes or returns the MySQL connection pool."""
    global _pool
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="doctor_app_pool",
                pool_size=5,
                pool_reset_session=True,
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                autocommit=False
            )
        except Error as e:
            logger.warning(f"Connection pooling could not be initialized: {e}")
            return None
    return _pool

def get_db_connection():
    """Returns an active MySQL database connection."""
    pool = get_connection_pool()
    if pool:
        try:
            return pool.get_connection()
        except Error as e:
            logger.warning(f"Failed to get connection from pool, falling back to direct connection: {e}")

    # Direct connection
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci',
        autocommit=False
    )

def check_db_connection():
    """Verifies database connectivity (MySQL or SQLite fallback)."""
    global _use_sqlite
    if not _use_sqlite:
        try:
            conn = get_db_connection()
            if conn and conn.is_connected():
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                conn.close()
                return True, "Connected to MySQL successfully."
        except Exception as e:
            logger.info(f"MySQL unavailable ({e}). Automatically using SQLite fallback.")
            _use_sqlite = True

    try:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return True, "Connected to SQLite fallback successfully."
    except Exception as e:
        return False, str(e)

def _query_sqlite(query, args=(), one=False, commit=False):
    """Executes a query on SQLite fallback database."""
    conn = get_sqlite_connection()
    cursor = conn.cursor()

    # Convert MySQL parameter placeholder %s to SQLite ?
    sql = query.replace('%s', '?')

    try:
        cursor.execute(sql, args)
        if commit:
            conn.commit()
            last_id = cursor.lastrowid
            row_count = cursor.rowcount
            return last_id if last_id else row_count

        rows = cursor.fetchall()
        result = [dict(r) for r in rows]
        return (result[0] if result else None) if one else result
    finally:
        cursor.close()
        conn.close()

def _execute_transaction_sqlite(queries_with_args):
    """Executes a transaction on SQLite fallback database."""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    try:
        for query, args in queries_with_args:
            sql = query.replace('%s', '?')
            cursor.execute(sql, args)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"SQLite transaction failed: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

def query_db(query, args=(), one=False, commit=False):
    """
    Executes a parameterized SQL query safely.
    Attempts MySQL first; if MySQL is unavailable (e.g. cloud/Vercel), seamlessly uses SQLite fallback.
    - If commit=True: commits transaction and returns (lastrowid, rowcount).
    - If commit=False: returns list of dict rows or single dict row if one=True.
    """
    global _use_sqlite
    if not _use_sqlite:
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, args)

            if commit:
                conn.commit()
                last_id = cursor.lastrowid
                row_count = cursor.rowcount
                return last_id if last_id else row_count

            result = cursor.fetchall()
            return (result[0] if result else None) if one else result
        except (Error, Exception) as e:
            logger.warning(f"MySQL query error or unavailable ({e}). Automatically switching to SQLite fallback...")
            _use_sqlite = True
            if conn and commit:
                try:
                    conn.rollback()
                except Exception:
                    pass
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    return _query_sqlite(query, args, one, commit)

def execute_transaction(queries_with_args):
    """
    Executes a sequence of queries inside a single database transaction.
    Attempts MySQL first; if unavailable, seamlessly executes on SQLite fallback.
    """
    global _use_sqlite
    if not _use_sqlite:
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            for query, args in queries_with_args:
                cursor.execute(query, args)
            conn.commit()
            return True
        except (Error, Exception) as e:
            logger.warning(f"MySQL transaction error ({e}). Switching to SQLite fallback...")
            _use_sqlite = True
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    return _execute_transaction_sqlite(queries_with_args)
