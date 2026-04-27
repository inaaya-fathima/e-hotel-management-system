"""
E-Hotel Management System — Database Helper
File: utils/db.py
"""

import sqlite3
import os
import hashlib
from flask import g

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE  = os.path.join(BASE_DIR, 'hotel.db')


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False, commit=False):
    db  = get_db()
    cur = db.execute(query, args)
    if commit:
        db.commit()
        return cur.lastrowid
    rows = cur.fetchall()
    return rows[0] if (one and rows) else (None if one else rows)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db(app):
    with app.app_context():
        db = get_db()

        db.executescript('''
            PRAGMA foreign_keys = ON;

            -- USERS
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                email       TEXT UNIQUE NOT NULL,
                phone       TEXT,
                password    TEXT NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- ADMINS
            CREATE TABLE IF NOT EXISTS admins (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT UNIQUE NOT NULL,
                password    TEXT NOT NULL
            );

            -- DEPARTMENTS (new: links staff to a service type)
            CREATE TABLE IF NOT EXISTS departments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT UNIQUE NOT NULL,
                description TEXT
            );

            -- STAFF
            CREATE TABLE IF NOT EXISTS staff (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                role            TEXT NOT NULL,
                contact         TEXT,
                salary          REAL DEFAULT 0,
                username        TEXT UNIQUE NOT NULL,
                password        TEXT NOT NULL,
                assigned_branch TEXT DEFAULT 'Main Branch',
                department_id   INTEGER REFERENCES departments(id),
                current_task    TEXT,
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- ROOMS (with destination + branch)
            CREATE TABLE IF NOT EXISTS rooms (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                room_number TEXT UNIQUE NOT NULL,
                room_type   TEXT NOT NULL,
                price       REAL NOT NULL,
                status      TEXT DEFAULT 'Available',
                description TEXT,
                image_url   TEXT,
                destination TEXT DEFAULT 'Main',
                branch      TEXT DEFAULT 'Main Branch',
                capacity    INTEGER DEFAULT 2,
                category    TEXT DEFAULT 'Room'
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
                hotel_name  TEXT DEFAULT 'E-Hotel',
                branch      TEXT DEFAULT 'Main Branch',
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- BILLS
            CREATE TABLE IF NOT EXISTS bills (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id      INTEGER REFERENCES bookings(id),
                room_charges    REAL DEFAULT 0,
                service_charges REAL DEFAULT 0,
                gst_rate        REAL DEFAULT 18.0,
                gst_amount      REAL DEFAULT 0,
                total_amount    REAL DEFAULT 0,
                payment_status  TEXT DEFAULT 'Pending',
                is_checkout_bill INTEGER DEFAULT 0,
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- SERVICE CATALOG
            CREATE TABLE IF NOT EXISTS service_catalog (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name    TEXT UNIQUE NOT NULL,
                price           REAL NOT NULL DEFAULT 0,
                description     TEXT,
                department_id   INTEGER REFERENCES departments(id),
                is_active       INTEGER DEFAULT 1
            );

            -- SERVICES (guest requests)
            CREATE TABLE IF NOT EXISTS services (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id   INTEGER REFERENCES bookings(id),
                user_id      INTEGER REFERENCES users(id),
                service_type TEXT NOT NULL,
                description  TEXT,
                charge       REAL DEFAULT 0,
                status       TEXT DEFAULT 'Pending',
                assigned_staff_id INTEGER REFERENCES staff(id),
                created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
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
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id  INTEGER REFERENCES staff(id),
                date      DATE NOT NULL,
                status    TEXT DEFAULT 'Present',
                marked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(staff_id, date)
            );

            -- OFFERS (admin-managed, now with booking_room_id)
            CREATE TABLE IF NOT EXISTS offers (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                title          TEXT NOT NULL,
                type           TEXT NOT NULL,
                description    TEXT,
                features       TEXT,
                image_url      TEXT,
                price          REAL DEFAULT 0,
                discount_pct   INTEGER DEFAULT 0,
                valid_until    DATE,
                is_active      INTEGER DEFAULT 1
            );

            -- MESSAGES (contact form & user queries)
            CREATE TABLE IF NOT EXISTS messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER REFERENCES users(id),
                name       TEXT NOT NULL,
                email      TEXT NOT NULL,
                subject    TEXT,
                body       TEXT NOT NULL,
                is_read    INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            -- VENUE ENQUIRIES (halls, lounges, meeting rooms, weddings)
            CREATE TABLE IF NOT EXISTS venue_enquiries (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER REFERENCES users(id),
                name         TEXT NOT NULL,
                email        TEXT NOT NULL,
                phone        TEXT,
                venue_type   TEXT NOT NULL,
                venue_option TEXT,
                event_date   DATE NOT NULL,
                guests       INTEGER DEFAULT 0,
                message      TEXT,
                status       TEXT DEFAULT 'Pending',
                created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        db.commit()

        # ── Run safe migrations for older DB schemas ──
        migrations = [
            "ALTER TABLE attendance ADD COLUMN marked_at DATETIME DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE rooms ADD COLUMN destination TEXT DEFAULT 'Main'",
            "ALTER TABLE rooms ADD COLUMN branch TEXT DEFAULT 'Main Branch'",
            "ALTER TABLE rooms ADD COLUMN capacity INTEGER DEFAULT 2",
            "ALTER TABLE rooms ADD COLUMN category TEXT DEFAULT 'Room'",
            "ALTER TABLE bookings ADD COLUMN hotel_name TEXT DEFAULT 'E-Hotel'",
            "ALTER TABLE bookings ADD COLUMN branch TEXT DEFAULT 'Main Branch'",
            "ALTER TABLE bills ADD COLUMN gst_rate REAL DEFAULT 18.0",
            "ALTER TABLE bills ADD COLUMN gst_amount REAL DEFAULT 0",
            "ALTER TABLE bills ADD COLUMN is_checkout_bill INTEGER DEFAULT 0",
            "ALTER TABLE services ADD COLUMN charge REAL DEFAULT 0",
            "ALTER TABLE services ADD COLUMN assigned_staff_id INTEGER",
            "ALTER TABLE staff ADD COLUMN assigned_branch TEXT DEFAULT 'Main Branch'",
            "ALTER TABLE staff ADD COLUMN department_id INTEGER",
            "ALTER TABLE staff ADD COLUMN current_task TEXT",
            "ALTER TABLE service_catalog ADD COLUMN department_id INTEGER",
            "ALTER TABLE offers ADD COLUMN price REAL DEFAULT 0",
            "ALTER TABLE offers ADD COLUMN discount_pct INTEGER DEFAULT 0",
            "ALTER TABLE offers ADD COLUMN valid_until DATE",
        ]
        for sql in migrations:
            try:
                db.execute(sql)
                db.commit()
            except sqlite3.OperationalError:
                pass  # Column already exists

        # ── Seed default admin ──
        if not db.execute("SELECT id FROM admins WHERE username='admin'").fetchone():
            db.execute("INSERT INTO admins (username, password) VALUES (?, ?)",
                       ('admin', hash_password('admin123')))

        # ── Seed demo guest user ──
        # Login credentials: demo@ehotel.com / demo1234
        if not db.execute("SELECT id FROM users WHERE email='demo@ehotel.com'").fetchone():
            db.execute(
                "INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)",
                ('Demo Guest', 'demo@ehotel.com', '9000000001', hash_password('demo1234'))
            )
            db.commit()

        # ── Seed departments ──
        if db.execute("SELECT COUNT(*) FROM departments").fetchone()[0] == 0:
            depts = [
                ('Housekeeping',   'Room cleaning, laundry, and amenities'),
                ('Food & Beverage','In-room dining and beverage service'),
                ('Concierge',      'Guest services, airport transfers, wake-up calls'),
                ('Wellness',       'Spa, gym, and wellness treatments'),
                ('Events',         'Party halls, weddings, and conferences'),
                ('Maintenance',    'Repairs and maintenance requests'),
            ]
            db.executemany("INSERT INTO departments (name, description) VALUES (?,?)", depts)
            db.commit()

        # ── Seed service catalog (linked to departments) ──
        if db.execute("SELECT COUNT(*) FROM service_catalog").fetchone()[0] == 0:
            dept = {row['name']: row['id'] for row in db.execute("SELECT id, name FROM departments")}
            catalog = [
                ('Room Cleaning',          200,  'Full room cleaning and bed-making service',    dept.get('Housekeeping')),
                ('Laundry',                350,  'Wash, dry and fold up to 5 garments',          dept.get('Housekeeping')),
                ('Extra Towels/Amenities', 100,  'Extra set of towels, toiletries, and amenities', dept.get('Housekeeping')),
                ('Food & Beverages',       500,  'In-room dining order (base charge)',            dept.get('Food & Beverage')),
                ('Maintenance',            0,    'Maintenance and repair request (no charge)',    dept.get('Maintenance')),
                ('Wake-up Call',           0,    'Scheduled wake-up call (complimentary)',        dept.get('Concierge')),
                ('Airport Transfer',       800,  'Hotel car pick-up or drop at airport',          dept.get('Concierge')),
                ('Spa & Wellness',         1200, 'In-room spa or wellness session',               dept.get('Wellness')),
                ('Event Setup Assistance', 500,  'Help with event/party setup and decorations',   dept.get('Events')),
                ('Further Details',        0,    'Further booking details and special requests',  dept.get('Concierge')),
                ('Other',                  0,    'Custom service request — priced on request',    None),
            ]
            db.executemany(
                "INSERT INTO service_catalog (service_name, price, description, department_id) VALUES (?,?,?,?)",
                catalog
            )
            db.commit()

        # ── Seed rooms ──
        if db.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] == 0:
            rooms = [
                # Jaipur
                ('J101', 'Heritage Single',    1800, 'Available', 'Royal single room with Rajasthani frescoes.',
                 'https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=600', 'Jaipur', 'E-Hotel Jaipur — City Palace Wing', 1, 'Room'),
                ('J102', 'Heritage Double',    3200, 'Available', 'Spacious double room with hand-carved furniture.',
                 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=600', 'Jaipur', 'E-Hotel Jaipur — City Palace Wing', 2, 'Room'),
                ('J201', 'Royal Suite',        7500, 'Available', 'Opulent suite with marble bath and butler service.',
                 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600', 'Jaipur', 'E-Hotel Jaipur — Maharaja Tower', 2, 'Room'),
                # Goa
                ('G101', 'Beach View Single',  2200, 'Available', 'Bright single room steps from the beach.',
                 'https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=600', 'Goa', 'E-Hotel Goa — North Beach Resort', 1, 'Room'),
                ('G102', 'Pool-Side Double',   3800, 'Available', 'Double room with direct pool access.',
                 'https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=600', 'Goa', 'E-Hotel Goa — North Beach Resort', 2, 'Room'),
                ('G201', 'Ocean Suite',        8500, 'Available', 'Panoramic ocean-view suite with private plunge pool.',
                 'https://images.unsplash.com/photo-1540541338537-1220059dddf3?w=600', 'Goa', 'E-Hotel Goa — South Cliff Retreat', 2, 'Room'),
                # Kerala
                ('K101', 'Garden Single',      1600, 'Available', 'Cosy single room surrounded by coconut groves.',
                 'https://images.unsplash.com/photo-1591088398332-8a7791972843?w=600', 'Kerala', 'E-Hotel Kerala — Backwater Villas', 1, 'Room'),
                ('K201', 'Lake-View Suite',    6200, 'Available', 'Traditional Kerala teak suite with lake views.',
                 'https://images.unsplash.com/photo-1587985064135-0366536eab42?w=600', 'Kerala', 'E-Hotel Kerala — Backwater Villas', 2, 'Room'),
                # Himalayas
                ('H101', 'Mountain Single',    2000, 'Available', 'Cosy room with Himalayan peak views and fireplace.',
                 'https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=600', 'Himalayas', 'E-Hotel Himalayas — Peak View Lodge', 1, 'Room'),
                ('H201', 'Alpine Suite',       5500, 'Available', 'Log-cabin suite with mountain panoramas and hot tub.',
                 'https://images.unsplash.com/photo-1519974719765-e6559eac2575?w=600', 'Himalayas', 'E-Hotel Himalayas — Peak View Lodge', 2, 'Room'),
                # Varanasi
                ('V101', 'Ganga View Single',  1900, 'Available', 'Serene room with direct views of the holy Ganges.',
                 'https://images.unsplash.com/photo-1561361058-c24cecae35ca?w=600', 'Varanasi', 'E-Hotel Varanasi — Ganga Heritage', 1, 'Room'),
                ('V201', 'Heritage Suite',     5000, 'Available', 'Grand heritage suite overlooking Manikarnika Ghat.',
                 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600', 'Varanasi', 'E-Hotel Varanasi — Ganga Heritage', 2, 'Room'),
                # Mumbai
                ('M101', 'City View Single',   2500, 'Available', 'Modern room with sweeping Mumbai skyline views.',
                 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600', 'Mumbai', 'E-Hotel Mumbai — BKC Business Tower', 1, 'Room'),
                ('M201', 'Skyline Penthouse',  9500, 'Available', 'Opulent penthouse with a private rooftop pool.',
                 'https://images.unsplash.com/photo-1549294413-26f195200c16?w=600', 'Mumbai', 'E-Hotel Mumbai — Marine Drive Grand', 2, 'Room'),
                # Halls & Venues
                ('H-PARTY', 'Party Hall',             45000,  'Available', 'Grand Maharaja Ballroom, up to 600 guests, full AV.',
                 'https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=600', 'Main', 'Main Branch', 600, 'Hall'),
                ('H-CONF',  'Conference Room',         15000,  'Available', 'High-tech conference room with 4K projectors.',
                 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=600', 'Main', 'Main Branch', 50, 'Hall'),
                ('H-BSLN',  'Business Lounge',          3000,  'Available', 'Premium lounge with fast Wi-Fi and printing.',
                 'https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=600', 'Main', 'Main Branch', 30, 'Hall'),
                ('H-WED',   'Wedding Venue',           150000, 'Available', 'Complete wedding venue with bridal suite.',
                 'https://images.unsplash.com/photo-1511285560929-80b456fea0bc?w=600', 'Main', 'Main Branch', 500, 'Hall'),
                ('H-POOL',  'Infinity Pool (Private)',   5000,  'Available', 'Exclusive private infinity pool access with cabana.',
                 'https://images.unsplash.com/photo-1582610116397-edb318620f90?w=600', 'Main', 'Main Branch', 10, 'Pool'),
                ('H-DWS',   'Dining with Stay',        12000,  'Available', 'Luxury suite stay with 5-course private dining.',
                 'https://images.unsplash.com/photo-1544148103-0773bf10d330?w=600', 'Main', 'Main Branch', 2, 'Package'),
            ]
            db.executemany(
                "INSERT INTO rooms (room_number,room_type,price,status,description,image_url,destination,branch,capacity,category) VALUES (?,?,?,?,?,?,?,?,?,?)",
                rooms
            )
            db.commit()

        # ── Seed offers ──
        if db.execute("SELECT COUNT(*) FROM offers").fetchone()[0] == 0:
            sample_offers = [
                ('Weekend Getaway',     'Leisure',
                 'Escape the week with our premium weekend package — breakfast, pool access, and late checkout.',
                 '2 Nights Stay|Daily Breakfast|Infinity Pool Access|Late Check-out (2 PM)|Welcome Fruit Basket',
                 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600', 8000, 15, None),
                ('Family Holidays',     'Family',
                 'Create lasting memories with family-friendly activities, kid menus, and spacious rooms.',
                 'Family Suite Stay|Buffet Breakfast|Kids Activities & Club|Guided City Tour|Complimentary Cots',
                 'https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=600', 12000, 10, None),
                ('Seasonal Escapes',    'Seasonal',
                 'Special seasonal packages tied to festivals and holidays — Diwali, New Year\'s, and more.',
                 'Festive Décor|Special Dining Events|Cultural Experiences|Complimentary Gifting|Exclusive Rates',
                 'https://images.unsplash.com/photo-1519974719765-e6559eac2575?w=600', 6500, 20, None),
                ('Corporate Rates',     'Business',
                 'Preferred rates for business travelers and corporate accounts with dedicated concierge support.',
                 'Negotiated Corporate Rates|Business Centre Access|Express Check-in/out|Account Manager',
                 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600', 5000, 25, None),
                ('Long Stay Discounts', 'Long Stay',
                 'Extended stay offers with significant savings — perfect for remote workers.',
                 'Up to 30% off 7+ nights|Weekly & Monthly Plans|Kitchenette|Complimentary Laundry',
                 'https://images.unsplash.com/photo-1540541338537-1220059dddf3?w=600', 4500, 30, None),
            ]
            db.executemany(
                "INSERT INTO offers (title,type,description,features,image_url,price,discount_pct,valid_until) VALUES (?,?,?,?,?,?,?,?)",
                sample_offers
            )
            db.commit()

        # ── Seed staff ──
        if db.execute("SELECT COUNT(*) FROM staff").fetchone()[0] == 0:
            dept = {row['name']: row['id'] for row in db.execute("SELECT id, name FROM departments")}
            sample_staff = [
                ('Ravi Kumar',  'Receptionist', '9876543210', 25000, 'ravi',  hash_password('ravi123'),  'E-Hotel Jaipur — City Palace Wing',        dept.get('Concierge')),
                ('Priya Singh', 'Housekeeping', '9876543211', 18000, 'priya', hash_password('priya123'), 'E-Hotel Goa — North Beach Resort',          dept.get('Housekeeping')),
                ('Arjun Mehta', 'Manager',      '9876543212', 40000, 'arjun', hash_password('arjun123'), 'E-Hotel Kerala — Backwater Villas',         dept.get('Concierge')),
                ('Sunita Rao',  'Concierge',    '9876543213', 22000, 'sunita',hash_password('sunita123'),'E-Hotel Mumbai — BKC Business Tower',       dept.get('Concierge')),
                ('Dev Sharma',  'Events Staff', '9876543214', 20000, 'dev',   hash_password('dev123'),   'Main Branch',                               dept.get('Events')),
                ('Anita Nair',  'Spa Therapist','9876543215', 21000, 'anita', hash_password('anita123'), 'Main Branch',                               dept.get('Wellness')),
            ]
            db.executemany(
                "INSERT INTO staff (name,role,contact,salary,username,password,assigned_branch,department_id) VALUES (?,?,?,?,?,?,?,?)",
                sample_staff
            )
            db.commit()

        db.commit()
