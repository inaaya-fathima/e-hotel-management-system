"""
E-Hotel Management System — Admin Routes
File: routes/admin_routes.py
"""

import datetime
import sqlite3
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from utils.db import query_db, hash_password
from utils.auth import admin_required

BRANCHES = [
    'E-Hotel Jaipur — City Palace Wing',
    'E-Hotel Jaipur — Maharaja Tower',
    'E-Hotel Goa — North Beach Resort',
    'E-Hotel Goa — South Cliff Retreat',
    'E-Hotel Kerala — Backwater Villas',
    'E-Hotel Himalayas — Peak View Lodge',
    'E-Hotel Varanasi — Ganga Heritage',
    'E-Hotel Mumbai — BKC Business Tower',
    'E-Hotel Mumbai — Marine Drive Grand',
    'Main Branch',
]

DESTINATIONS = ['Jaipur', 'Goa', 'Kerala', 'Himalayas', 'Varanasi', 'Mumbai', 'Main']
CATEGORIES   = ['Room', 'Hall', 'Pool', 'Package']


def register_admin_routes(app):

    # ==============================================================
    # Admin Login / Logout
    # ==============================================================

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if 'admin_id' in session:
            return redirect(url_for('admin_dashboard'))

        error    = None
        attempts = session.get('admin_login_attempts', 0)

        if request.method == 'POST':
            if attempts >= 5:
                error = 'Too many failed attempts. Please wait and try again.'
            else:
                username = request.form.get('username', '').strip()
                password = hash_password(request.form.get('password', ''))
                admin    = query_db("SELECT * FROM admins WHERE username=? AND password=?",
                                    [username, password], one=True)
                if admin:
                    session['admin_id']   = admin['id']
                    session['admin_name'] = admin['username']
                    session.pop('admin_login_attempts', None)
                    return redirect(url_for('admin_dashboard'))

                session['admin_login_attempts'] = attempts + 1
                error = 'Invalid credentials. Please try again.'

        return render_template('admin/login.html', error=error, attempts=attempts)


    @app.route('/admin/logout')
    def admin_logout():
        session.pop('admin_id', None)
        session.pop('admin_name', None)
        return redirect(url_for('admin_login'))


    # ==============================================================
    # Admin Dashboard
    # ==============================================================

    @app.route('/admin')
    @app.route('/admin/dashboard')
    @admin_required
    def admin_dashboard():
        total_rooms      = query_db("SELECT COUNT(*) AS c FROM rooms WHERE category='Room'", one=True)['c']
        available_rooms  = query_db("SELECT COUNT(*) AS c FROM rooms WHERE status='Available' AND category='Room'", one=True)['c']
        occupied_rooms   = query_db("SELECT COUNT(*) AS c FROM rooms WHERE status='Occupied' AND category='Room'", one=True)['c']
        total_halls      = query_db("SELECT COUNT(*) AS c FROM rooms WHERE category IN ('Hall','Pool','Package')", one=True)['c']
        total_customers  = query_db("SELECT COUNT(*) AS c FROM users", one=True)['c']
        total_bookings   = query_db("SELECT COUNT(*) AS c FROM bookings", one=True)['c']
        pending_bookings = query_db("SELECT COUNT(*) AS c FROM bookings WHERE status='Pending'", one=True)['c']
        pending_services = query_db("SELECT COUNT(*) AS c FROM services WHERE status='Pending'", one=True)['c']
        unread_messages  = query_db("SELECT COUNT(*) AS c FROM messages WHERE is_read=0", one=True)['c']

        revenue_row   = query_db("SELECT SUM(total_amount) AS rev FROM bills WHERE payment_status='Paid'", one=True)
        total_revenue = revenue_row['rev'] or 0

        recent_bookings = query_db("""
            SELECT b.*, u.name AS cust_name, r.room_number, r.category, r.destination, b.branch
            FROM bookings b
            JOIN users u ON u.id = b.user_id
            JOIN rooms r ON r.id = b.room_id
            ORDER BY b.created_at DESC LIMIT 6
        """)

        return render_template(
            'admin/dashboard.html',
            total_rooms=total_rooms, available_rooms=available_rooms,
            occupied_rooms=occupied_rooms, total_halls=total_halls,
            total_customers=total_customers, total_bookings=total_bookings,
            pending_bookings=pending_bookings, pending_services=pending_services,
            total_revenue=total_revenue, recent_bookings=recent_bookings,
            unread_messages=unread_messages
        )


    # ==============================================================
    # ROOM & VENUE MANAGEMENT
    # ==============================================================

    @app.route('/admin/rooms')
    @admin_required
    def admin_rooms():
        dest_filter = request.args.get('destination', '')
        cat_filter  = request.args.get('category', '')
        query       = "SELECT * FROM rooms WHERE 1=1"
        params      = []
        if dest_filter:
            query += " AND destination=?"
            params.append(dest_filter)
        if cat_filter:
            query += " AND category=?"
            params.append(cat_filter)
        query += " ORDER BY category, destination, room_number"
        rooms = query_db(query, params)
        return render_template('admin/rooms.html', rooms=rooms, destinations=DESTINATIONS,
                               categories=CATEGORIES, selected_destination=dest_filter,
                               selected_category=cat_filter)


    @app.route('/admin/rooms/add', methods=['GET', 'POST'])
    @admin_required
    def admin_add_room():
        if request.method == 'POST':
            query_db(
                "INSERT INTO rooms (room_number,room_type,price,status,description,image_url,destination,branch,capacity,category) VALUES (?,?,?,?,?,?,?,?,?,?)",
                [
                    request.form['room_number'], request.form['room_type'],
                    request.form['price'], request.form['status'],
                    request.form['description'], request.form.get('image_url', ''),
                    request.form.get('destination', 'Main'), request.form.get('branch', 'Main Branch'),
                    request.form.get('capacity', 2), request.form.get('category', 'Room'),
                ], commit=True
            )
            flash('Room/Venue added successfully!', 'success')
            return redirect(url_for('admin_rooms'))
        return render_template('admin/room_form.html', room=None, branches=BRANCHES,
                               destinations=DESTINATIONS, categories=CATEGORIES)


    @app.route('/admin/rooms/edit/<int:room_id>', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_room(room_id):
        room = query_db("SELECT * FROM rooms WHERE id=?", [room_id], one=True)
        if request.method == 'POST':
            query_db(
                "UPDATE rooms SET room_number=?,room_type=?,price=?,status=?,description=?,image_url=?,destination=?,branch=?,capacity=?,category=? WHERE id=?",
                [
                    request.form['room_number'], request.form['room_type'],
                    request.form['price'], request.form['status'],
                    request.form['description'], request.form.get('image_url', ''),
                    request.form.get('destination', 'Main'), request.form.get('branch', 'Main Branch'),
                    request.form.get('capacity', 2), request.form.get('category', 'Room'),
                    room_id
                ], commit=True
            )
            flash('Updated successfully!', 'success')
            return redirect(url_for('admin_rooms'))
        return render_template('admin/room_form.html', room=room, branches=BRANCHES,
                               destinations=DESTINATIONS, categories=CATEGORIES)


    @app.route('/admin/rooms/delete/<int:room_id>', methods=['POST'])
    @admin_required
    def admin_delete_room(room_id):
        query_db("DELETE FROM rooms WHERE id=?", [room_id], commit=True)
        flash('Room/Venue deleted.', 'info')
        return redirect(url_for('admin_rooms'))


    # ==============================================================
    # VENUES / HALLS (filtered view of rooms with category != Room)
    # ==============================================================

    @app.route('/admin/venues')
    @admin_required
    def admin_venues():
        venues = query_db(
            "SELECT * FROM rooms WHERE category IN ('Hall','Pool','Package') ORDER BY category, room_type"
        )
        return render_template('admin/venues.html', venues=venues)


    # ==============================================================
    # BOOKING MANAGEMENT
    # ==============================================================

    @app.route('/admin/bookings')
    @admin_required
    def admin_bookings():
        branch_filter = request.args.get('branch', '')
        if branch_filter:
            bookings = query_db("""
                SELECT b.*, u.name AS cust_name, u.email AS cust_email,
                       r.room_number, r.room_type, r.destination, r.category
                FROM bookings b
                JOIN users u ON u.id = b.user_id
                JOIN rooms r ON r.id = b.room_id
                WHERE b.branch = ?
                ORDER BY b.created_at DESC
            """, [branch_filter])
        else:
            bookings = query_db("""
                SELECT b.*, u.name AS cust_name, u.email AS cust_email,
                       r.room_number, r.room_type, r.destination, r.category
                FROM bookings b
                JOIN users u ON u.id = b.user_id
                JOIN rooms r ON r.id = b.room_id
                ORDER BY b.created_at DESC
            """)
        return render_template('admin/bookings.html', bookings=bookings,
                               branches=BRANCHES, selected_branch=branch_filter)


    @app.route('/admin/bookings/approve/<int:booking_id>', methods=['POST'])
    @admin_required
    def admin_approve_booking(booking_id):
        booking = query_db("SELECT * FROM bookings WHERE id=?", [booking_id], one=True)
        if booking:
            query_db("UPDATE bookings SET status='Confirmed' WHERE id=?", [booking_id], commit=True)
            query_db("UPDATE rooms SET status='Occupied' WHERE id=?", [booking['room_id']], commit=True)
            flash('Booking approved!', 'success')
        return redirect(url_for('admin_bookings'))


    @app.route('/admin/bookings/reject/<int:booking_id>', methods=['POST'])
    @admin_required
    def admin_reject_booking(booking_id):
        query_db("UPDATE bookings SET status='Rejected' WHERE id=?", [booking_id], commit=True)
        flash('Booking rejected.', 'info')
        return redirect(url_for('admin_bookings'))


    @app.route('/admin/bookings/checkout/<int:booking_id>', methods=['POST'])
    @admin_required
    def admin_checkout(booking_id):
        booking = query_db("SELECT * FROM bookings WHERE id=?", [booking_id], one=True)
        if booking:
            query_db("UPDATE bookings SET status='Checked Out' WHERE id=?", [booking_id], commit=True)
            query_db("UPDATE rooms SET status='Available' WHERE id=?", [booking['room_id']], commit=True)

            bill = query_db("SELECT * FROM bills WHERE booking_id=?", [booking_id], one=True)
            if bill:
                gst_rate   = 18.0
                subtotal   = bill['room_charges'] + bill['service_charges']
                gst_amount = round(subtotal * gst_rate / 100, 2)
                total      = subtotal + gst_amount
                query_db(
                    "UPDATE bills SET gst_rate=?,gst_amount=?,total_amount=?,is_checkout_bill=1 WHERE id=?",
                    [gst_rate, gst_amount, total, bill['id']], commit=True
                )

            flash('Checkout completed. Final bill with GST generated.', 'success')
        return redirect(url_for('admin_bookings'))


    # ==============================================================
    # CUSTOMER MANAGEMENT
    # ==============================================================

    @app.route('/admin/customers')
    @admin_required
    def admin_customers():
        customers = query_db("""
            SELECT u.*, COUNT(b.id) AS total_bookings
            FROM users u
            LEFT JOIN bookings b ON b.user_id = u.id
            GROUP BY u.id
            ORDER BY u.created_at DESC
        """)
        return render_template('admin/customers.html', customers=customers)


    @app.route('/admin/customers/delete/<int:user_id>', methods=['POST'])
    @admin_required
    def admin_delete_customer(user_id):
        query_db("DELETE FROM users WHERE id=?", [user_id], commit=True)
        flash('Customer deleted.', 'info')
        return redirect(url_for('admin_customers'))


    # ==============================================================
    # STAFF MANAGEMENT
    # ==============================================================

    @app.route('/admin/staff')
    @admin_required
    def admin_staff():
        branch_filter = request.args.get('branch', '')
        dept_filter   = request.args.get('dept', '')
        departments   = query_db("SELECT * FROM departments ORDER BY name")

        query  = "SELECT s.*, d.name AS dept_name FROM staff s LEFT JOIN departments d ON d.id = s.department_id WHERE 1=1"
        params = []
        if branch_filter:
            query += " AND s.assigned_branch=?"
            params.append(branch_filter)
        if dept_filter:
            query += " AND s.department_id=?"
            params.append(dept_filter)
        query += " ORDER BY s.assigned_branch, s.name"
        staff = query_db(query, params)

        return render_template('admin/staff.html', staff=staff, branches=BRANCHES,
                               departments=departments, selected_branch=branch_filter,
                               selected_dept=dept_filter)


    @app.route('/admin/staff/add', methods=['GET', 'POST'])
    @admin_required
    def admin_add_staff():
        departments = query_db("SELECT * FROM departments ORDER BY name")
        if request.method == 'POST':
            try:
                query_db(
                    "INSERT INTO staff (name,role,contact,salary,username,password,assigned_branch,department_id) VALUES (?,?,?,?,?,?,?,?)",
                    [
                        request.form['name'], request.form['role'],
                        request.form['contact'], request.form['salary'],
                        request.form['username'], hash_password(request.form['password']),
                        request.form.get('assigned_branch', 'Main Branch'),
                        request.form.get('department_id') or None,
                    ], commit=True
                )
                flash('Staff member added successfully!', 'success')
                return redirect(url_for('admin_staff'))
            except sqlite3.IntegrityError:
                flash('That username is already taken. Please choose another.', 'danger')
        return render_template('admin/staff_form.html', member=None, branches=BRANCHES, departments=departments)


    @app.route('/admin/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_staff(staff_id):
        member      = query_db("SELECT * FROM staff WHERE id=?", [staff_id], one=True)
        departments = query_db("SELECT * FROM departments ORDER BY name")
        if request.method == 'POST':
            query_db(
                "UPDATE staff SET name=?,role=?,contact=?,salary=?,username=?,assigned_branch=?,department_id=? WHERE id=?",
                [
                    request.form['name'], request.form['role'],
                    request.form['contact'], request.form['salary'],
                    request.form['username'], request.form.get('assigned_branch', 'Main Branch'),
                    request.form.get('department_id') or None, staff_id
                ], commit=True
            )
            flash('Staff information updated!', 'success')
            return redirect(url_for('admin_staff'))
        return render_template('admin/staff_form.html', member=member, branches=BRANCHES, departments=departments)


    @app.route('/admin/staff/delete/<int:staff_id>', methods=['POST'])
    @admin_required
    def admin_delete_staff(staff_id):
        query_db("DELETE FROM staff WHERE id=?", [staff_id], commit=True)
        flash('Staff member removed.', 'info')
        return redirect(url_for('admin_staff'))


    @app.route('/admin/staff/allocate/<int:staff_id>', methods=['POST'])
    @admin_required
    def admin_allocate_job(staff_id):
        task = request.form.get('task', '').strip()
        query_db("UPDATE staff SET current_task=? WHERE id=?", [task, staff_id], commit=True)
        flash('Job allocated successfully.', 'success')
        return redirect(url_for('admin_staff'))


    # ==============================================================
    # ATTENDANCE MANAGEMENT
    # ==============================================================

    @app.route('/admin/attendance')
    @admin_required
    def admin_attendance():
        month = request.args.get('month', datetime.date.today().strftime('%Y-%m'))

        records = query_db("""
            SELECT a.*, s.name, s.role, s.assigned_branch
            FROM attendance a
            JOIN staff s ON s.id = a.staff_id
            WHERE strftime('%Y-%m', a.date) = ?
            ORDER BY a.date DESC, a.marked_at DESC
        """, [month])

        summary = query_db("""
            SELECT s.id, s.name, s.role, s.salary, s.assigned_branch,
                   COUNT(a.id) AS days_present,
                   ROUND(s.salary / 26.0 * COUNT(a.id), 2) AS earned_salary
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.status = 'Present'
                AND strftime('%Y-%m', a.date) = ?
            GROUP BY s.id
        """, [month])

        return render_template('admin/attendance.html', records=records, summary=summary, current_month=month)


    # ==============================================================
    # BILLING MANAGEMENT
    # ==============================================================

    @app.route('/admin/billing')
    @admin_required
    def admin_billing():
        bills = query_db("""
            SELECT bi.*, b.check_in, b.check_out, b.status AS booking_status,
                   b.hotel_name, b.branch, u.name AS cust_name, r.room_number, r.destination
            FROM bills bi
            JOIN bookings b ON b.id = bi.booking_id
            JOIN users u ON u.id = b.user_id
            JOIN rooms r ON r.id = b.room_id
            ORDER BY bi.created_at DESC
        """)
        total_paid    = query_db("SELECT SUM(total_amount) AS s FROM bills WHERE payment_status='Paid'",    one=True)['s'] or 0
        total_pending = query_db("SELECT SUM(total_amount) AS s FROM bills WHERE payment_status='Pending'", one=True)['s'] or 0
        return render_template('admin/billing.html', bills=bills, total_paid=total_paid, total_pending=total_pending)


    @app.route('/admin/billing/mark-paid/<int:bill_id>', methods=['POST'])
    @admin_required
    def admin_mark_paid(bill_id):
        query_db("UPDATE bills SET payment_status='Paid' WHERE id=?", [bill_id], commit=True)
        flash('Bill marked as Paid.', 'success')
        return redirect(url_for('admin_billing'))


    @app.route('/admin/billing/add-service/<int:bill_id>', methods=['POST'])
    @admin_required
    def admin_add_service_charge(bill_id):
        extra_charge = float(request.form['charge'])
        bill         = query_db("SELECT * FROM bills WHERE id=?", [bill_id], one=True)
        new_service  = bill['service_charges'] + extra_charge
        gst_amount   = round((bill['room_charges'] + new_service) * bill['gst_rate'] / 100, 2)
        new_total    = bill['room_charges'] + new_service + gst_amount
        query_db(
            "UPDATE bills SET service_charges=?,gst_amount=?,total_amount=? WHERE id=?",
            [new_service, gst_amount, new_total, bill_id], commit=True
        )
        flash(f'Service charge of ₹{extra_charge} added to bill.', 'success')
        return redirect(url_for('admin_billing'))


    # ==============================================================
    # SERVICES MANAGEMENT
    # ==============================================================

    @app.route('/admin/services')
    @admin_required
    def admin_services():
        services = query_db("""
            SELECT s.*, u.name AS cust_name, r.room_number, b.branch,
                   st.name AS assigned_staff_name, d.name AS dept_name
            FROM services s
            JOIN users u ON u.id = s.user_id
            JOIN bookings b ON b.id = s.booking_id
            JOIN rooms r ON r.id = b.room_id
            LEFT JOIN staff st ON st.id = s.assigned_staff_id
            LEFT JOIN service_catalog sc ON sc.service_name = s.service_type
            LEFT JOIN departments d ON d.id = sc.department_id
            ORDER BY s.created_at DESC
        """)
        all_staff = query_db("SELECT id, name, role, department_id FROM staff ORDER BY name")
        return render_template('admin/services.html', services=services, all_staff=all_staff)


    @app.route('/admin/services/update/<int:service_id>', methods=['POST'])
    @admin_required
    def admin_update_service(service_id):
        new_status  = request.form['status']
        staff_id    = request.form.get('staff_id') or None
        query_db("UPDATE services SET status=?, assigned_staff_id=? WHERE id=?",
                 [new_status, staff_id, service_id], commit=True)
        flash('Service updated.', 'success')
        return redirect(url_for('admin_services'))


    # ==============================================================
    # SERVICE CATALOG
    # ==============================================================

    @app.route('/admin/service-catalog')
    @admin_required
    def admin_service_catalog():
        catalog     = query_db("""
            SELECT sc.*, d.name AS dept_name
            FROM service_catalog sc
            LEFT JOIN departments d ON d.id = sc.department_id
            ORDER BY sc.service_name
        """)
        departments = query_db("SELECT * FROM departments ORDER BY name")
        return render_template('admin/service_catalog.html', catalog=catalog, departments=departments)


    @app.route('/admin/service-catalog/update/<int:item_id>', methods=['POST'])
    @admin_required
    def admin_update_service_price(item_id):
        query_db(
            "UPDATE service_catalog SET price=?, description=?, department_id=? WHERE id=?",
            [float(request.form.get('price', 0)), request.form.get('description', ''),
             request.form.get('department_id') or None, item_id], commit=True
        )
        flash('Service price updated.', 'success')
        return redirect(url_for('admin_service_catalog'))


    @app.route('/admin/service-catalog/add', methods=['POST'])
    @admin_required
    def admin_add_service_item():
        name = request.form.get('service_name', '').strip()
        if name:
            try:
                query_db(
                    "INSERT INTO service_catalog (service_name, price, description, department_id) VALUES (?,?,?,?)",
                    [name, float(request.form.get('price', 0)), request.form.get('description', ''),
                     request.form.get('department_id') or None], commit=True
                )
                flash(f'Service "{name}" added to catalog.', 'success')
            except sqlite3.IntegrityError:
                flash('A service with that name already exists.', 'danger')
        return redirect(url_for('admin_service_catalog'))


    @app.route('/admin/service-catalog/toggle/<int:item_id>', methods=['POST'])
    @admin_required
    def admin_toggle_service(item_id):
        item = query_db("SELECT * FROM service_catalog WHERE id=?", [item_id], one=True)
        if item:
            query_db("UPDATE service_catalog SET is_active=? WHERE id=?",
                     [0 if item['is_active'] else 1, item_id], commit=True)
        return redirect(url_for('admin_service_catalog'))


    # ==============================================================
    # OFFERS MANAGEMENT
    # ==============================================================

    @app.route('/admin/offers')
    @admin_required
    def admin_offers():
        offers = query_db("SELECT * FROM offers ORDER BY is_active DESC, title")
        return render_template('admin/offers.html', offers=offers)


    @app.route('/admin/offers/add', methods=['GET', 'POST'])
    @admin_required
    def admin_add_offer():
        if request.method == 'POST':
            features = '|'.join([f.strip() for f in request.form.get('features', '').split('\n') if f.strip()])
            query_db(
                "INSERT INTO offers (title,type,description,features,image_url,price,discount_pct,valid_until,is_active) VALUES (?,?,?,?,?,?,?,?,?)",
                [
                    request.form['title'], request.form['type'],
                    request.form['description'], features,
                    request.form.get('image_url', ''),
                    float(request.form.get('price', 0)),
                    int(request.form.get('discount_pct', 0)),
                    request.form.get('valid_until') or None,
                    1 if request.form.get('is_active') else 0,
                ], commit=True
            )
            flash('Offer added!', 'success')
            return redirect(url_for('admin_offers'))
        return render_template('admin/offer_form.html', offer=None)


    @app.route('/admin/offers/edit/<int:offer_id>', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_offer(offer_id):
        offer = query_db("SELECT * FROM offers WHERE id=?", [offer_id], one=True)
        if request.method == 'POST':
            features = '|'.join([f.strip() for f in request.form.get('features', '').split('\n') if f.strip()])
            query_db(
                "UPDATE offers SET title=?,type=?,description=?,features=?,image_url=?,price=?,discount_pct=?,valid_until=?,is_active=? WHERE id=?",
                [
                    request.form['title'], request.form['type'],
                    request.form['description'], features,
                    request.form.get('image_url', ''),
                    float(request.form.get('price', 0)),
                    int(request.form.get('discount_pct', 0)),
                    request.form.get('valid_until') or None,
                    1 if request.form.get('is_active') else 0,
                    offer_id
                ], commit=True
            )
            flash('Offer updated!', 'success')
            return redirect(url_for('admin_offers'))
        return render_template('admin/offer_form.html', offer=offer)


    @app.route('/admin/offers/delete/<int:offer_id>', methods=['POST'])
    @admin_required
    def admin_delete_offer(offer_id):
        query_db("DELETE FROM offers WHERE id=?", [offer_id], commit=True)
        flash('Offer deleted.', 'info')
        return redirect(url_for('admin_offers'))


    # ==============================================================
    # MESSAGES (from contact form)
    # ==============================================================

    @app.route('/admin/messages')
    @admin_required
    def admin_messages():
        messages = query_db("""
            SELECT m.*, u.name AS user_name
            FROM messages m
            LEFT JOIN users u ON u.id = m.user_id
            ORDER BY m.created_at DESC
        """)
        return render_template('admin/messages.html', messages=messages)


    @app.route('/admin/messages/read/<int:msg_id>', methods=['POST'])
    @admin_required
    def admin_mark_message_read(msg_id):
        query_db("UPDATE messages SET is_read=1 WHERE id=?", [msg_id], commit=True)
        return redirect(url_for('admin_messages'))


    @app.route('/admin/messages/delete/<int:msg_id>', methods=['POST'])
    @admin_required
    def admin_delete_message(msg_id):
        query_db("DELETE FROM messages WHERE id=?", [msg_id], commit=True)
        flash('Message deleted.', 'info')
        return redirect(url_for('admin_messages'))


    # ==============================================================
    # VENUE ENQUIRIES (halls, lounges, meeting rooms, weddings)
    # ==============================================================

    @app.route('/admin/venue-enquiries')
    @admin_required
    def admin_venue_enquiries():
        enquiries = query_db("""
            SELECT ve.*, u.name AS user_display_name
            FROM venue_enquiries ve
            LEFT JOIN users u ON u.id = ve.user_id
            ORDER BY ve.created_at DESC
        """)
        pending_count = query_db(
            "SELECT COUNT(*) AS c FROM venue_enquiries WHERE status='Pending'", one=True
        )['c']
        return render_template('admin/venue_enquiries.html',
                               enquiries=enquiries, pending_count=pending_count)


    @app.route('/admin/venue-enquiries/update/<int:enq_id>', methods=['POST'])
    @admin_required
    def admin_update_venue_enquiry(enq_id):
        new_status = request.form.get('status', 'Pending')
        query_db("UPDATE venue_enquiries SET status=? WHERE id=?", [new_status, enq_id], commit=True)
        flash(f'Enquiry status updated to {new_status}.', 'success')
        return redirect(url_for('admin_venue_enquiries'))


    @app.route('/admin/venue-enquiries/delete/<int:enq_id>', methods=['POST'])
    @admin_required
    def admin_delete_venue_enquiry(enq_id):
        query_db("DELETE FROM venue_enquiries WHERE id=?", [enq_id], commit=True)
        flash('Venue enquiry deleted.', 'info')
        return redirect(url_for('admin_venue_enquiries'))

