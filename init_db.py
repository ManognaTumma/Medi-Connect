import os
import sys
import argparse
import mysql.connector
from mysql.connector import Error
from config import Config

def init_database(host=None, port=None, user=None, password=None, schema_file='schema.sql'):
    """
    Initializes the MySQL database using the schema.sql script.
    """
    host = host or Config.MYSQL_HOST
    port = port or Config.MYSQL_PORT
    user = user or Config.MYSQL_USER
    password = password if password is not None else Config.MYSQL_PASSWORD

    print(f"[*] Connecting to MySQL server at {host}:{port} as '{user}'...")

    try:
        # First connect without specifying the database so we can create it
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
    except Error as e:
        print(f"\n[!] Connection Failed: {e}")
        print("\nPlease check your credentials in .env (e.g., MYSQL_PASSWORD) or run:")
        print("  python init_db.py --password YOUR_MYSQL_PASSWORD\n")
        return False

    cursor = conn.cursor()

    if not os.path.exists(schema_file):
        print(f"[!] Schema file '{schema_file}' not found.")
        cursor.close()
        conn.close()
        return False

    print(f"[*] Reading '{schema_file}'...")
    with open(schema_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Split SQL file into executable commands by semicolon, ignoring comments
    statements = []
    current_statement = []
    for line in sql_content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith('--') or trimmed.startswith('/*'):
            continue
        current_statement.append(line)
        if trimmed.endswith(';'):
            stmt = '\n'.join(current_statement).strip()
            if stmt:
                statements.append(stmt)
            current_statement = []

    print(f"[*] Executing {len(statements)} SQL statements...")
    success_count = 0
    try:
        for stmt in statements:
            # Handle delimiter or empty
            clean_stmt = stmt.rstrip(';').strip()
            if not clean_stmt:
                continue
            cursor.execute(clean_stmt)
            success_count += 1
        
        conn.commit()
        print(f"\n[+] Database initialized successfully! ({success_count} statements executed)")
        print(f"[+] Database Name: {Config.MYSQL_DB}")
        print("\nSeed Accounts Available:")
        print("  - Admin:   admin@carepoint.com / Admin@123")
        print("  - Doctor:  sarah.jenkins@carepoint.com / Doctor@123")
        print("  - Patient: patient@carepoint.com / Patient@123")
        return True
    except Error as e:
        print(f"\n[!] Error executing statement:\n{stmt}\n[!] MySQL Error: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Initialize Doctor Appointment Management System MySQL Database")
    parser.add_argument('--host', default=None, help="MySQL Host (default from .env)")
    parser.add_argument('--port', type=int, default=None, help="MySQL Port (default 3306)")
    parser.add_argument('--user', default=None, help="MySQL User (default root)")
    parser.add_argument('--password', default=None, help="MySQL Password")
    parser.add_argument('--schema', default='schema.sql', help="Path to schema.sql")

    args = parser.parse_args()
    ok = init_database(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        schema_file=args.schema
    )
    sys.exit(0 if ok else 1)
