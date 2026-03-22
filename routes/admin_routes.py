"""
============================================================
  E-Hotel Management System — Admin Routes
  File: routes/admin_routes.py
============================================================

  These routes handle the ADMIN panel — only accessible after
  admin login. Admins can manage everything in the hotel system.

  All routes here use @admin_required to protect them.

  Pages / URLs handled here:
    /admin/login                        → Admin login page
    /admin/logout                       → Admin logout
    /admin or /admin/dashboard          → Admin dashboard (stats overview)

    Room Management:
      /admin/rooms                      → List all rooms
      /admin/rooms/add                  → Add a new room
      /admin/rooms/edit/<id>            → Edit a room
      /admin/rooms/delete/<id>          → Delete a room

    Booking Management:
      /admin/bookings                   → View all bookings
      /admin/bookings/approve/<id>      → Approve a booking
      /admin/bookings/reject/<id>       → Reject a booking
      /admin/bookings/checkout/<id>     → Mark guest as checked out

    Customer Management:
      /admin/customers                  → View all customers
      /admin/customers/delete/<id>      → Delete a customer

    Staff Management:
      /admin/staff                      → View all staff
      /admin/staff/add                  → Add a staff member
      /admin/staff/edit/<id>            → Edit staff info
      /admin/staff/delete/<id>          → Remove a staff member

    Attendance:
      /admin/attendance                 → View staff attendance records

    Billing:
      /admin/billing                    → View all bills
      /admin/billing/mark-paid/<id>     → Mark a bill as paid
      /admin/billing/add-service/<id>   → Add service charges to a bill

    Services:
      /admin/services                   → View all room service requests
      /admin/services/update/<id>       → Update service status
"""

import datetime
import sqlite3
from flask import render_template, request, redirect, url_for, session, flash
from utils.db import query_db, hash_password
from utils.auth import admin_required


def register_admin_routes(app):
    """
    Registers all admin panel routes onto the Flask app.
    Called once from app.py when the application starts.
    """

    # ----------------------------------------------------------
    # Admin Login / Logout
    # ----------------------------------------------------------

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        """
        Shows the admin login form (GET).
        Validates credentials and creates an admin session (POST).
        """
        # If already logged in as admin, go straight to dashboard
        if 'admin_id' in session:
            return redirect(url_for('admin_dashboard'))

        if request.method == 'POST':
            username = request.form['username']
            password = hash_password(request.form['password'])

            # Check if admin with this username+password exists
            admin = query_db(
                "SELECT * FROM admins WHERE username=? AND password=?",
                [username, password],
                one=True
            )

            if admin:
                # Store admin info in session
                session['admin_id']   = admin['id']
                session['admin_name'] = admin['username']
                return redirect(url_for('admin_dashboard'))

            flash('Invalid credentials. Please try again.', 'danger')

        return render_template('admin/login.html')


    @app.route('/admin/logout')
    def admin_logout():
        """
        Removes admin info from the session (logs them out).
        """
        session.pop('admin_id', None)    # Remove if exists
        session.pop('admin_name', None)
        return redirect(url_for('admin_login'))


    # ----------------------------------------------------------
    # Admin Dashboard
    # ----------------------------------------------------------

    @app.route('/admin')
    @app.route('/admin/dashboard')
    @admin_required
    def admin_dashboard():
        """
        The main admin dashboard.
        Gathers key statistics about the hotel and shows them in one place.
        Also shows the 5 most recent bookings at the bottom.
        """
        # Count statistics from the database
        total_rooms      = query_db("SELECT COUNT(*) AS c FROM rooms",                               one=True)['c']
        available_rooms  = query_db("SELECT COUNT(*) AS c FROM rooms WHERE status='Available'",      one=True)['c']
        occupied_rooms   = query_db("SELECT COUNT(*) AS c FROM rooms WHERE status='Occupied'",       one=True)['c']
        total_customers  = query_db("SELECT COUNT(*) AS c FROM users",                               one=True)['c']
        total_bookings   = query_db("SELECT COUNT(*) AS c FROM bookings",                            one=True)['c']
        pending_bookings = query_db("SELECT COUNT(*) AS c FROM bookings WHERE status='Pending'",     one=True)['c']
        pending_services = query_db("SELECT COUNT(*) AS c FROM services WHERE status='Pending'",     one=True)['c']

        # Sum of all paid bill amounts (total revenue earned)
        revenue_row    = query_db("SELECT SUM(total_amount) AS rev FROM bills WHERE payment_status='Paid'", one=True)
        total_revenue  = revenue_row['rev'] or 0  # Use 0 if no paid bills yet

        # Fetch the 5 most recent bookings (with customer name and room number)
        recent_bookings = query_db("""
            SELECT b.*, u.name AS cust_name, r.room_number
            FROM bookings b
            JOIN users u ON u.id = b.user_id
            JOIN rooms r ON r.id = b.room_id
            ORDER BY b.created_at DESC
            LIMIT 5
        """)

        return render_template(
            'admin/dashboard.html',
            total_rooms=total_rooms,
            available_rooms=available_rooms,
            occupied_rooms=occupied_rooms,
            total_customers=total_customers,
            total_bookings=total_bookings,
            pending_bookings=pending_bookings,
            pending_services=pending_services,
            total_revenue=total_revenue,
            recent_bookings=recent_bookings
        )


    # ==============================================================
    # ROOM MANAGEMENT
    # ==============================================================

    @app.route('/admin/rooms')
    @admin_required
    def admin_rooms():
        """Shows a list of ALL rooms in the hotel."""
        rooms = query_db("SELECT * FROM rooms ORDER BY room_number")
        return render_template('admin/rooms.html', rooms=rooms)


    @app.route('/admin/rooms/add', methods=['GET', 'POST'])
    @admin_required
    def admin_add_room():
        """
        Shows the 'Add Room' form (GET).
        Saves the new room to the database (POST).
        """
        if request.method == 'POST':
            query_db(
                "INSERT INTO rooms (room_number, room_type, price, status, description, image_url) VALUES (?,?,?,?,?,?)",
                [
                    request.form['room_number'],
                    request.form['room_type'],
                    request.form['price'],
                    request.form['status'],
                    request.form['description'],
                    request.form.get('image_url', '')  # Image URL is optional
                ],
                commit=True
            )
            flash('Room added successfully!', 'success')
            return redirect(url_for('admin_rooms'))

        # GET: Show the blank form (room=None means it's an 'add' form, not 'edit')
        return render_template('admin/room_form.html', room=None)


    @app.route('/admin/rooms/edit/<int:room_id>', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_room(room_id):
        """
        Shows the 'Edit Room' form pre-filled with existing data (GET).
        Updates the room record in the database (POST).
        """
        room = query_db("SELECT * FROM rooms WHERE id=?", [room_id], one=True)

        if request.method == 'POST':
            query_db(
                "UPDATE rooms SET room_number=?, room_type=?, price=?, status=?, description=?, image_url=? WHERE id=?",
                [
                    request.form['room_number'],
                    request.form['room_type'],
                    request.form['price'],
                    request.form['status'],
                    request.form['description'],
                    request.form.get('image_url', ''),
                    room_id
                ],
                commit=True
            )
            flash('Room updated successfully!', 'success')
            return redirect(url_for('admin_rooms'))

        return render_template('admin/room_form.html', room=room)


    @app.route('/admin/rooms/delete/<int:room_id>', methods=['POST'])
    @admin_required
    def admin_delete_room(room_id):
        """Deletes a room from the database."""
        query_db("DELETE FROM rooms WHERE id=?", [room_id], commit=True)
        flash('Room deleted.', 'info')
        return redirect(url_for('admin_rooms'))


    # ==============================================================
    # BOOKING MANAGEMENT
    # ==============================================================

    @app.route('/admin/bookings')
    @admin_required
    def admin_bookings():
        """
        Shows a list of ALL bookings from all customers.
        Each row includes customer name, email, and room number.
        """
        bookings = query_db("""
            SELECT b.*, u.name AS cust_name, u.email AS cust_email,
                   r.room_number, r.room_type
            FROM bookings b
            JOIN users u ON u.id = b.user_id
            JOIN rooms r ON r.id = b.room_id
            ORDER BY b.created_at DESC
        """)
        return render_template('admin/bookings.html', bookings=bookings)


    @app.route('/admin/bookings/approve/<int:booking_id>', methods=['POST'])
    @admin_required
    def admin_approve_booking(booking_id):
        """
        Approves a pending booking.
        Also marks the room as 'Occupied' so others can't book it.
        """
        booking = query_db("SELECT * FROM bookings WHERE id=?", [booking_id], one=True)
        if booking:
            query_db("UPDATE bookings SET status='Confirmed' WHERE id=?", [booking_id], commit=True)
            query_db("UPDATE rooms SET status='Occupied' WHERE id=?", [booking['room_id']], commit=True)
            flash('Booking approved!', 'success')
        return redirect(url_for('admin_bookings'))


    @app.route('/admin/bookings/reject/<int:booking_id>', methods=['POST'])
    @admin_required
    def admin_reject_booking(booking_id):
        """Rejects a pending booking."""
        query_db("UPDATE bookings SET status='Rejected' WHERE id=?", [booking_id], commit=True)
        flash('Booking rejected.', 'info')
        return redirect(url_for('admin_bookings'))


    @app.route('/admin/bookings/checkout/<int:booking_id>', methods=['POST'])
    @admin_required
    def admin_checkout(booking_id):
        """
        Marks a booking as 'Checked Out'.
        Also marks the room back to 'Available' for future bookings.
        """
        booking = query_db("SELECT * FROM bookings WHERE id=?", [booking_id], one=True)
        if booking:
            query_db("UPDATE bookings SET status='Checked Out' WHERE id=?", [booking_id], commit=True)
            query_db("UPDATE rooms SET status='Available' WHERE id=?", [booking['room_id']], commit=True)
            flash('Checkout completed. Room is now available again.', 'success')
        return redirect(url_for('admin_bookings'))


    # ==============================================================
    # CUSTOMER MANAGEMENT
    # ==============================================================

    @app.route('/admin/customers')
    @admin_required
    def admin_customers():
        """
        Shows a list of all registered customers.
        Also shows how many total bookings each customer has made.
        """
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
        """Deletes a customer account from the database."""
        query_db("DELETE FROM users WHERE id=?", [user_id], commit=True)
        flash('Customer deleted.', 'info')
        return redirect(url_for('admin_customers'))


    # ==============================================================
    # STAFF MANAGEMENT
    # ==============================================================

    @app.route('/admin/staff')
    @admin_required
    def admin_staff():
        """Shows all hotel staff members."""
        staff = query_db("SELECT * FROM staff ORDER BY name")
        return render_template('admin/staff.html', staff=staff)


    @app.route('/admin/staff/add', methods=['GET', 'POST'])
    @admin_required
    def admin_add_staff():
        """
        Shows the 'Add Staff' form (GET).
        Saves the new staff member to the database (POST).
        """
        if request.method == 'POST':
            try:
                query_db(
                    "INSERT INTO staff (name, role, contact, salary, username, password) VALUES (?,?,?,?,?,?)",
                    [
                        request.form['name'],
                        request.form['role'],
                        request.form['contact'],
                        request.form['salary'],
                        request.form['username'],
                        hash_password(request.form['password'])  # Always hash passwords!
                    ],
                    commit=True
                )
                flash('Staff member added successfully!', 'success')
                return redirect(url_for('admin_staff'))

            except sqlite3.IntegrityError:
                # This happens if the username is already taken (must be UNIQUE)
                flash('That username is already taken. Please choose another.', 'danger')

        return render_template('admin/staff_form.html', member=None)


    @app.route('/admin/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_staff(staff_id):
        """
        Shows the 'Edit Staff' form pre-filled with existing data (GET).
        Updates the staff record in the database (POST).
        Note: Password is not changed when editing staff info.
        """
        member = query_db("SELECT * FROM staff WHERE id=?", [staff_id], one=True)

        if request.method == 'POST':
            query_db(
                "UPDATE staff SET name=?, role=?, contact=?, salary=?, username=? WHERE id=?",
                [
                    request.form['name'],
                    request.form['role'],
                    request.form['contact'],
                    request.form['salary'],
                    request.form['username'],
                    staff_id
                ],
                commit=True
            )
            flash('Staff information updated!', 'success')
            return redirect(url_for('admin_staff'))

        return render_template('admin/staff_form.html', member=member)


    @app.route('/admin/staff/delete/<int:staff_id>', methods=['POST'])
    @admin_required
    def admin_delete_staff(staff_id):
        """Removes a staff member from the database."""
        query_db("DELETE FROM staff WHERE id=?", [staff_id], commit=True)
        flash('Staff member removed.', 'info')
        return redirect(url_for('admin_staff'))


    # ==============================================================
    # ATTENDANCE MANAGEMENT
    # ==============================================================

    @app.route('/admin/attendance')
    @admin_required
    def admin_attendance():
        """
        Shows staff attendance records for a selected month.

        Also shows a salary summary: how many days each staff member
        was present and what their estimated monthly pay would be.

        URL example: /admin/attendance?month=2024-03
        Default: current month
        """
        # Get month from URL parameter, defaulting to current month
        month = request.args.get('month', datetime.date.today().strftime('%Y-%m'))

        # Get all attendance records for this month (with staff name and role)
        records = query_db("""
            SELECT a.*, s.name, s.role
            FROM attendance a
            JOIN staff s ON s.id = a.staff_id
            WHERE strftime('%Y-%m', a.date) = ?
            ORDER BY a.date DESC, a.marked_at DESC
        """, [month])

        # Get salary summary: days present × salary for each staff member
        summary = query_db("""
            SELECT s.id, s.name, s.role, s.salary,
                   COUNT(a.id) AS days_present
            FROM staff s
            LEFT JOIN attendance a
                ON s.id = a.staff_id
                AND a.status = 'Present'
                AND strftime('%Y-%m', a.date) = ?
            GROUP BY s.id
        """, [month])

        return render_template(
            'admin/attendance.html',
            records=records,
            summary=summary,
            current_month=month
        )


    # ==============================================================
    # BILLING MANAGEMENT
    # ==============================================================

    @app.route('/admin/billing')
    @admin_required
    def admin_billing():
        """
        Shows all billing records.
        Also calculates total paid and total pending revenue.
        """
        bills = query_db("""
            SELECT bi.*, b.check_in, b.check_out, b.status AS booking_status,
                   u.name AS cust_name, r.room_number
            FROM bills bi
            JOIN bookings b ON b.id = bi.booking_id
            JOIN users u ON u.id = b.user_id
            JOIN rooms r ON r.id = b.room_id
            ORDER BY bi.created_at DESC
        """)

        total_paid    = query_db("SELECT SUM(total_amount) AS s FROM bills WHERE payment_status='Paid'",    one=True)['s'] or 0
        total_pending = query_db("SELECT SUM(total_amount) AS s FROM bills WHERE payment_status='Pending'", one=True)['s'] or 0

        return render_template(
            'admin/billing.html',
            bills=bills,
            total_paid=total_paid,
            total_pending=total_pending
        )


    @app.route('/admin/billing/mark-paid/<int:bill_id>', methods=['POST'])
    @admin_required
    def admin_mark_paid(bill_id):
        """Marks a specific bill as 'Paid'."""
        query_db("UPDATE bills SET payment_status='Paid' WHERE id=?", [bill_id], commit=True)
        flash('Bill marked as Paid.', 'success')
        return redirect(url_for('admin_billing'))


    @app.route('/admin/billing/add-service/<int:bill_id>', methods=['POST'])
    @admin_required
    def admin_add_service_charge(bill_id):
        """
        Adds extra service charges to an existing bill.
        Recalculates the total amount automatically.
        """
        extra_charge = float(request.form['charge'])  # The amount to add
        bill         = query_db("SELECT * FROM bills WHERE id=?", [bill_id], one=True)

        # Add the new charge to existing service charges
        new_service_charges = bill['service_charges'] + extra_charge
        new_total           = bill['room_charges'] + new_service_charges

        query_db(
            "UPDATE bills SET service_charges=?, total_amount=? WHERE id=?",
            [new_service_charges, new_total, bill_id],
            commit=True
        )
        flash(f'Service charge of ₹{extra_charge} added to bill.', 'success')
        return redirect(url_for('admin_billing'))


    # ==============================================================
    # SERVICES MANAGEMENT
    # ==============================================================

    @app.route('/admin/services')
    @admin_required
    def admin_services():
        """
        Shows all room service requests from customers.
        Includes customer name and room number for each request.
        """
        services = query_db("""
            SELECT s.*, u.name AS cust_name, r.room_number
            FROM services s
            JOIN users u ON u.id = s.user_id
            JOIN bookings b ON b.id = s.booking_id
            JOIN rooms r ON r.id = b.room_id
            ORDER BY s.created_at DESC
        """)
        return render_template('admin/services.html', services=services)


    @app.route('/admin/services/update/<int:service_id>', methods=['POST'])
    @admin_required
    def admin_update_service(service_id):
        """Updates the status of a room service request (e.g. 'In Progress', 'Completed')."""
        new_status = request.form['status']
        query_db("UPDATE services SET status=? WHERE id=?", [new_status, service_id], commit=True)
        flash('Service status updated.', 'success')
        return redirect(url_for('admin_services'))
