import logging
import mysql.connector
from mysql.connector import Error, pooling
from config import Config

logger = logging.getLogger(__name__)

# Connection pool holder
_pool = None

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
    
    # Fallback to direct connection
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
    """Verifies MySQL connectivity and database existence."""
    try:
        conn = get_db_connection()
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            return True, "Connected successfully."
    except Error as e:
        return False, str(e)
    return False, "Unknown connection error."

def query_db(query, args=(), one=False, commit=False):
    """
    Executes a parameterized SQL query safely.
    - If commit=True: commits transaction and returns (lastrowid, rowcount).
    - If commit=False: returns list of dict rows or single dict row if one=True.
    """
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
    except Error as e:
        if conn and commit:
            try:
                conn.rollback()
            except Exception:
                pass
        logger.error(f"Database query error: {e} | Query: {query} | Args: {args}")
        raise e
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

def execute_transaction(queries_with_args):
    """
    Executes a sequence of queries inside a single database transaction.
    queries_with_args is a list of tuples: [(query1, args1), (query2, args2), ...]
    Returns True on success, rolls back and raises on failure.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        for query, args in queries_with_args:
            cursor.execute(query, args)
        conn.commit()
        return True
    except Error as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        logger.error(f"Transaction failed: {e}")
        raise e
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
