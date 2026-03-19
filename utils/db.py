import sqlite3
import os
import hashlib
from flask import g

# Compute the path to 'hotel.db' intelligently
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(BASE_DIR, 'hotel.db')

def get_db():
    """Returns a connection to the database. Uses Flask `g` (global) element to reuse connections."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # This allows us to access columns by name like a dictionary
    return db

def close_db(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False, commit=False):
    """
    Helper function to run SQL queries. Easy to read and prevents code-duplication.
    - query:  The SQL string
    - args:   Tuple of arguments for the query (prevents SQL injection)
    - one:    If True, returns only the first row
    - commit: If True, saves changes to database (used for INSERT/UPDATE/DELETE)
    """
    db = get_db()
    cur = db.execute(query, args)
    if commit:
        db.commit()
        return cur.lastrowid
    rv = cur.fetchall()
    if one:
        return rv[0] if rv else None
    else:
        return rv

def hash_password(password):
    """Simple password hashing feature for security."""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db(app):
    """Creates the database tables and inserts some initial sample data."""
    with app.app_context():
        db = get_db()
        db.executescript('''
            PRAGMA foreign_keys = ON;
            
            -- USERS
            CREATE TABLE IF NOT EXISTS users (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT NOT NULL,
                email     TEXT UNIQUE NOT NULL,
                phone     TEXT,
                password  TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- ADMIN
            CREATE TABLE IF NOT EXISTS admins (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );

            -- STAFF
            CREATE TABLE IF NOT EXISTS staff (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                role       TEXT NOT NULL,
                contact    TEXT,
                salary     REAL DEFAULT 0,
                username   TEXT UNIQUE NOT NULL,
                password   TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- ROOMS
            CREATE TABLE IF NOT EXISTS rooms (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                room_number TEXT UNIQUE NOT NULL,
                room_type   TEXT NOT NULL,
                price       REAL NOT NULL,
                status      TEXT DEFAULT 'Available',
                description TEXT,
                image_url   TEXT
            );

            -- BOOKINGS
            CREATE TABLE IF NOT EXISTS bookings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER REFERENCES users(id),
                room_id     INTEGER REFERENCES rooms(id),
                check_in    DATE NOT NULL,
                check_out   DATE NOT NULL,
                total_price REAL NOT NULL,
                status      TEXT DEFAULT 'Pending',
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- BILLS
            CREATE TABLE IF NOT EXISTS bills (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id    INTEGER REFERENCES bookings(id),
                room_charges  REAL DEFAULT 0,
                service_charges REAL DEFAULT 0,
                total_amount  REAL DEFAULT 0,
                payment_status TEXT DEFAULT 'Pending',
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- ROOM SERVICES
            CREATE TABLE IF NOT EXISTS services (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id  INTEGER REFERENCES bookings(id),
                user_id     INTEGER REFERENCES users(id),
                service_type TEXT NOT NULL,
                description TEXT,
                status      TEXT DEFAULT 'Pending',
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- REVIEWS
            CREATE TABLE IF NOT EXISTS reviews (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER REFERENCES users(id),
                room_id    INTEGER REFERENCES rooms(id),
                rating     INTEGER NOT NULL,
                comment    TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- WISHLIST
            CREATE TABLE IF NOT EXISTS wishlist (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                room_id INTEGER REFERENCES rooms(id),
                UNIQUE(user_id, room_id)
            );

            -- ATTENDANCE
            CREATE TABLE IF NOT EXISTS attendance (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id   INTEGER REFERENCES staff(id),
                date       DATE NOT NULL,
                status     TEXT DEFAULT 'Present',
                marked_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(staff_id, date)
            );
        ''')
        db.commit()

        # Update schema dynamically if 'marked_at' was missing from old tables
        try:
            db.execute("ALTER TABLE attendance ADD COLUMN marked_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            db.commit()
        except sqlite3.OperationalError:
            pass

        # === DATA SEEDING ===
        # Create default admin if not existing
        existing_admin = db.execute("SELECT id FROM admins WHERE username='admin'").fetchone()
        if not existing_admin:
            db.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('admin', hash_password('admin123')))

        # Create default rooms if empty
        r_count = db.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
        if r_count == 0:
            rooms = [
                ('101', 'Single',  1200, 'Available', 'Cozy single room with city view', 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=600'),
                ('102', 'Double',  2200, 'Available', 'Spacious double room for couples', 'https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=600'),
                ('103', 'Deluxe',  3500, 'Available', 'Deluxe room with premium amenities', 'https://images.unsplash.com/photo-1591088398332-8a7791972843?w=600'),
                ('201', 'Suite',   6000, 'Available', 'Luxury suite with jacuzzi & balcony', 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600'),
            ]
            db.executemany("INSERT INTO rooms (room_number, room_type, price, status, description, image_url) VALUES (?,?,?,?,?,?)", rooms)

        # Create default staff if empty
        s_count = db.execute("SELECT COUNT(*) FROM staff").fetchone()[0]
        if s_count == 0:
            staffs = [
                ('Ravi Kumar', 'Receptionist',  '9876543210', 25000, 'ravi', hash_password('ravi123')),
                ('Priya Singh', 'Housekeeping', '9876543211', 18000, 'priya', hash_password('priya123')),
            ]
            db.executemany("INSERT INTO staff (name, role, contact, salary, username, password) VALUES (?,?,?,?,?,?)", staffs)

        db.commit()
