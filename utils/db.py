"""
============================================================
  E-Hotel Management System — Database Helper
  File: utils/db.py
============================================================

  This file handles EVERYTHING related to the database.
  We use SQLite — a simple file-based database (hotel.db).

  What this file provides:
    - get_db()       → Opens a database connection
    - close_db()     → Closes the connection when the request ends
    - query_db()     → Runs any SQL query (SELECT, INSERT, UPDATE, DELETE)
    - hash_password()→ Converts plain text password to a secure hash
    - init_db()      → Creates all tables and seeds default data
"""

import sqlite3
import os
import hashlib
from flask import g  # Flask's 'g' stores data for the current request


# ----------------------------------------------------------
# Database File Path
# ----------------------------------------------------------
# We find the project root folder, then look for 'hotel.db' there.
# os.path.abspath ensures we get the full path even on different systems.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE  = os.path.join(BASE_DIR, 'hotel.db')


# ----------------------------------------------------------
# Connection Management
# ----------------------------------------------------------

def get_db():
    """
    Opens a connection to the SQLite database.

    Flask's 'g' object is a temporary storage for the current request.
    We reuse the same connection within a single request for efficiency.
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        # row_factory lets us access columns by name (e.g. row['email'])
        # instead of by index (e.g. row[2])
        db.row_factory = sqlite3.Row
    return db


def close_db(exception):
    """
    Closes the database connection at the end of each request.
    Flask calls this automatically when a request finishes.
    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# ----------------------------------------------------------
# Query Helper
# ----------------------------------------------------------

def query_db(query, args=(), one=False, commit=False):
    """
    A simple helper to run any SQL query.

    Parameters:
        query  - The SQL string to run (use ? as placeholder for values)
        args   - A list or tuple of values to safely substitute for ? marks
        one    - If True, returns only the first row (for single lookups)
        commit - If True, saves changes to the database (for INSERT/UPDATE/DELETE)

    Returns:
        - For SELECT: a list of rows (or one row if one=True)
        - For INSERT with commit=True: the ID of the newly inserted row

    Example usage:
        # Get all available rooms
        rooms = query_db("SELECT * FROM rooms WHERE status='Available'")

        # Get one user by email
        user = query_db("SELECT * FROM users WHERE email=?", [email], one=True)

        # Insert a new booking
        new_id = query_db("INSERT INTO bookings ... VALUES (?,?,?)", [v1,v2,v3], commit=True)
    """
    db  = get_db()
    cur = db.execute(query, args)

    if commit:
        # Save changes (used for INSERT, UPDATE, DELETE)
        db.commit()
        return cur.lastrowid  # Returns the auto-generated ID of the new row

    # Fetch results for SELECT queries
    rows = cur.fetchall()
    if one:
        return rows[0] if rows else None  # Return one result or None
    return rows  # Return all results


# ----------------------------------------------------------
# Password Security
# ----------------------------------------------------------

def hash_password(password):
    """
    Converts a plain text password into a secure SHA-256 hash.

    We never store passwords as plain text — only their hashed version.
    When a user logs in, we hash their input and compare it to the stored hash.

    Example:
        hash_password("admin123") → "240be518..." (a long hex string)
    """
    return hashlib.sha256(password.encode()).hexdigest()


# ----------------------------------------------------------
# Database Initialization
# ----------------------------------------------------------

def init_db(app):
    """
    Creates all database tables (if they don't exist yet) and
    inserts some default/sample data so the app works immediately.

    This is called once when app.py starts.

    Tables created:
        - users     → Customer accounts
        - admins    → Admin accounts
        - staff     → Hotel staff members
        - rooms     → Hotel rooms
        - bookings  → Room booking records
        - bills     → Billing/invoice records
        - services  → Room service requests
        - reviews   → Customer room reviews
        - wishlist  → Rooms saved by customers
        - attendance → Staff daily attendance
    """
    with app.app_context():
        db = get_db()

        # Create all tables using a multi-line SQL script
        db.executescript('''
            PRAGMA foreign_keys = ON;

            -- USERS: Customers who register on the website
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                email       TEXT UNIQUE NOT NULL,
                phone       TEXT,
                password    TEXT NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- ADMINS: Hotel administrator accounts
            CREATE TABLE IF NOT EXISTS admins (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT UNIQUE NOT NULL,
                password    TEXT NOT NULL
            );

            -- STAFF: Hotel employees (receptionists, housekeeping, etc.)
            CREATE TABLE IF NOT EXISTS staff (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                role        TEXT NOT NULL,
                contact     TEXT,
                salary      REAL DEFAULT 0,
                username    TEXT UNIQUE NOT NULL,
                password    TEXT NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- ROOMS: Individual hotel rooms
            CREATE TABLE IF NOT EXISTS rooms (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                room_number TEXT UNIQUE NOT NULL,
                room_type   TEXT NOT NULL,
                price       REAL NOT NULL,
                status      TEXT DEFAULT 'Available',
                description TEXT,
                image_url   TEXT
            );

            -- BOOKINGS: Customer room reservation records
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

            -- BILLS: Invoice/billing records linked to bookings
            CREATE TABLE IF NOT EXISTS bills (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id      INTEGER REFERENCES bookings(id),
                room_charges    REAL DEFAULT 0,
                service_charges REAL DEFAULT 0,
                total_amount    REAL DEFAULT 0,
                payment_status  TEXT DEFAULT 'Pending',
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- SERVICES: Room service requests from customers
            CREATE TABLE IF NOT EXISTS services (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id   INTEGER REFERENCES bookings(id),
                user_id      INTEGER REFERENCES users(id),
                service_type TEXT NOT NULL,
                description  TEXT,
                status       TEXT DEFAULT 'Pending',
                created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- REVIEWS: Customer reviews and ratings for rooms
            CREATE TABLE IF NOT EXISTS reviews (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER REFERENCES users(id),
                room_id    INTEGER REFERENCES rooms(id),
                rating     INTEGER NOT NULL,
                comment    TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- WISHLIST: Rooms that customers have saved/liked
            CREATE TABLE IF NOT EXISTS wishlist (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                room_id INTEGER REFERENCES rooms(id),
                UNIQUE(user_id, room_id)  -- Each customer can wishlist a room only once
            );

            -- ATTENDANCE: Daily attendance records for staff
            CREATE TABLE IF NOT EXISTS attendance (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id  INTEGER REFERENCES staff(id),
                date      DATE NOT NULL,
                status    TEXT DEFAULT 'Present',
                marked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(staff_id, date)  -- One attendance record per staff per day
            );
        ''')
        db.commit()

        # If the 'marked_at' column is missing from an older database, add it
        try:
            db.execute("ALTER TABLE attendance ADD COLUMN marked_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            db.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists, nothing to do


        # ----------------------------------------------------------
        # Seed Default Data (only if the tables are empty)
        # ----------------------------------------------------------

        # Create the default admin account (if no admin exists yet)
        existing_admin = db.execute("SELECT id FROM admins WHERE username='admin'").fetchone()
        if not existing_admin:
            db.execute("INSERT INTO admins (username, password) VALUES (?, ?)",
                       ('admin', hash_password('admin123')))

        # Add sample rooms (if no rooms exist yet)
        room_count = db.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
        if room_count == 0:
            sample_rooms = [
                ('101', 'Single', 1200, 'Available', 'Cozy single room with city view',
                 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=600'),
                ('102', 'Double', 2200, 'Available', 'Spacious double room for couples',
                 'https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=600'),
                ('103', 'Deluxe', 3500, 'Available', 'Deluxe room with premium amenities',
                 'https://images.unsplash.com/photo-1591088398332-8a7791972843?w=600'),
                ('201', 'Suite',  6000, 'Available', 'Luxury suite with jacuzzi & balcony',
                 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600'),
            ]
            db.executemany(
                "INSERT INTO rooms (room_number, room_type, price, status, description, image_url) VALUES (?,?,?,?,?,?)",
                sample_rooms
            )

        # Add sample staff members (if no staff exists yet)
        staff_count = db.execute("SELECT COUNT(*) FROM staff").fetchone()[0]
        if staff_count == 0:
            sample_staff = [
                ('Ravi Kumar',  'Receptionist', '9876543210', 25000, 'ravi',  hash_password('ravi123')),
                ('Priya Singh', 'Housekeeping', '9876543211', 18000, 'priya', hash_password('priya123')),
            ]
            db.executemany(
                "INSERT INTO staff (name, role, contact, salary, username, password) VALUES (?,?,?,?,?,?)",
                sample_staff
            )

        db.commit()
