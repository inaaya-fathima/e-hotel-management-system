import datetime
import sqlite3
from flask import render_template, request, redirect, url_for, session, flash
from utils.db import query_db, hash_password
from utils.auth import admin_required

def register_admin_routes(app):
    """
    Registers the routes securely protected globally meant exclusively for the Admin panel user.
    """

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        """Handles basic admin authentication securely."""
        if 'admin_id' in session:
            return redirect(url_for('admin_dashboard'))
            
        if request.method == 'POST':
            username = request.form['username']
            password = hash_password(request.form['password'])
            
            admin = query_db("SELECT * FROM admins WHERE username=? AND password=?",
                             [username, password], one=True)
            if admin:
                session['admin_id'] = admin['id']
                session['admin_name'] = admin['username']
                return redirect(url_for('admin_dashboard'))
            flash('Invalid credentials.', 'danger')
            
        return render_template('admin/login.html')

    @app.route('/admin/logout')
    def admin_logout():
        """Wipes active session variables safely."""
        session.pop('admin_id', None)
        session.pop('admin_name', None)
        return redirect(url_for('admin_login'))

    @app.route('/admin')
    @app.route('/admin/dashboard')
    @admin_required
    def admin_dashboard():
        """Gathers massive sets of statistical calculations representing the hotel state natively."""
        total_rooms = query_db("SELECT COUNT(*) as c FROM rooms", one=True)['c']
        available_rooms = query_db("SELECT COUNT(*) as c FROM rooms WHERE status='Available'", one=True)['c']
        occupied_rooms = query_db("SELECT COUNT(*) as c FROM rooms WHERE status='Occupied'", one=True)['c']
        total_customers = query_db("SELECT COUNT(*) as c FROM users", one=True)['c']
        total_bookings = query_db("SELECT COUNT(*) as c FROM bookings", one=True)['c']
        pending_bookings = query_db("SELECT COUNT(*) as c FROM bookings WHERE status='Pending'", one=True)['c']
        pending_services = query_db("SELECT COUNT(*) as c FROM services WHERE status='Pending'", one=True)['c']
        
        revenue_row = query_db("SELECT SUM(total_amount) as rev FROM bills WHERE payment_status='Paid'", one=True)
        total_revenue = revenue_row['rev'] or 0
        
        recent_bookings = query_db("""
            SELECT b.*, u.name as cust_name, r.room_number
            FROM bookings b 
            JOIN users u ON u.id = b.user_id
            JOIN rooms r ON r.id = b.room_id
            ORDER BY b.created_at DESC 
            LIMIT 5
        """)
        
        return render_template('admin/dashboard.html',
            total_rooms=total_rooms, available_rooms=available_rooms,
            occupied_rooms=occupied_rooms, total_customers=total_customers,
            total_bookings=total_bookings, pending_bookings=pending_bookings,
            pending_services=pending_services, total_revenue=total_revenue,
            recent_bookings=recent_bookings)

    # === ROOM MANAGEMENT ===

    @app.route('/admin/rooms')
    @admin_required
    def admin_rooms():
        """Lists each room properly formatted representing backend registration components."""
        rooms = query_db("SELECT * FROM rooms ORDER BY room_number")
        return render_template('admin/rooms.html', rooms=rooms)

    @app.route('/admin/rooms/add', methods=['GET', 'POST'])
    @admin_required
    def admin_add_room():
        if request.method == 'POST':
            query_db(
                "INSERT INTO rooms (room_number,room_type,price,status,description,image_url) VALUES (?,?,?,?,?,?)",
                [request.form['room_number'], request.form['room_type'],
                 request.form['price'], request.form['status'],
                 request.form['description'], request.form.get('image_url','')], commit=True)
            flash('Room added successfully!', 'success')
            return redirect(url_for('admin_rooms'))
        return render_template('admin/room_form.html', room=None)

    @app.route('/admin/rooms/edit/<int:room_id>', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_room(room_id):
        room = query_db("SELECT * FROM rooms WHERE id=?", [room_id], one=True)
        if request.method == 'POST':
            query_db(
                "UPDATE rooms SET room_number=?,room_type=?,price=?,status=?,description=?,image_url=? WHERE id=?",
                [request.form['room_number'], request.form['room_type'],
                 request.form['price'], request.form['status'],
                 request.form['description'], request.form.get('image_url',''), room_id], commit=True)
            flash('Room updated!', 'success')
            return redirect(url_for('admin_rooms'))
        return render_template('admin/room_form.html', room=room)

    @app.route('/admin/rooms/delete/<int:room_id>', methods=['POST'])
    @admin_required
    def admin_delete_room(room_id):
        query_db("DELETE FROM rooms WHERE id=?", [room_id], commit=True)
        flash('Room deleted.', 'info')
        return redirect(url_for('admin_rooms'))

    # === BOOKING MANAGEMENT ===

    @app.route('/admin/bookings')
    @admin_required
    def admin_bookings():
        """Fetches unified associated data tying valid histories together forming admin overviews."""
        bookings = query_db("""
            SELECT b.*, u.name as cust_name, u.email as cust_email, r.room_number, r.room_type
            FROM bookings b 
            JOIN users u ON u.id = b.user_id
            JOIN rooms r ON r.id = b.room_id
            ORDER BY b.created_at DESC
        """)
        return render_template('admin/bookings.html', bookings=bookings)

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
            flash('Checkout completed. Room is now available.', 'success')
        return redirect(url_for('admin_bookings'))

    # === CUSTOMER MANAGEMENT ===

    @app.route('/admin/customers')
    @admin_required
    def admin_customers():
        customers = query_db("""
            SELECT u.*, COUNT(b.id) as total_bookings
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

    # === STAFF MANAGEMENT ===

    @app.route('/admin/staff')
    @admin_required
    def admin_staff():
        staff = query_db("SELECT * FROM staff ORDER BY name")
        return render_template('admin/staff.html', staff=staff)

    @app.route('/admin/staff/add', methods=['GET', 'POST'])
    @admin_required
    def admin_add_staff():
        if request.method == 'POST':
            try:
                query_db(
                    "INSERT INTO staff (name,role,contact,salary,username,password) VALUES (?,?,?,?,?,?)",
                    [request.form['name'], request.form['role'],
                     request.form['contact'], request.form['salary'],
                     request.form['username'], hash_password(request.form['password'])], commit=True)
                flash('Staff member added!', 'success')
                return redirect(url_for('admin_staff'))
            except sqlite3.IntegrityError:
                flash('Username already exists.', 'danger')
        return render_template('admin/staff_form.html', member=None)

    @app.route('/admin/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_staff(staff_id):
        member = query_db("SELECT * FROM staff WHERE id=?", [staff_id], one=True)
        if request.method == 'POST':
            query_db(
                "UPDATE staff SET name=?,role=?,contact=?,salary=?,username=? WHERE id=?",
                [request.form['name'], request.form['role'],
                 request.form['contact'], request.form['salary'],
                 request.form['username'], staff_id], commit=True)
            flash('Staff updated!', 'success')
            return redirect(url_for('admin_staff'))
        return render_template('admin/staff_form.html', member=member)

    @app.route('/admin/staff/delete/<int:staff_id>', methods=['POST'])
    @admin_required
    def admin_delete_staff(staff_id):
        query_db("DELETE FROM staff WHERE id=?", [staff_id], commit=True)
        flash('Staff removed.', 'info')
        return redirect(url_for('admin_staff'))

    # === ATTENDANCE MANAGEMENT ===

    @app.route('/admin/attendance')
    @admin_required
    def admin_attendance():
        month = request.args.get('month', datetime.date.today().strftime('%Y-%m'))
        
        records = query_db("""
            SELECT a.*, s.name, s.role 
            FROM attendance a
            JOIN staff s ON s.id = a.staff_id
            WHERE strftime('%Y-%m', a.date) = ?
            ORDER BY a.date DESC, a.marked_at DESC
        """, [month])
        
        summary = query_db("""
            SELECT s.id, s.name, s.role, s.salary,
                   COUNT(a.id) as days_present
            FROM staff s
            LEFT JOIN attendance a ON s.id = a.staff_id AND a.status = 'Present' AND strftime('%Y-%m', a.date) = ?
            GROUP BY s.id
        """, [month])
        
        return render_template('admin/attendance.html', records=records, summary=summary, current_month=month)

    # === BILLING ===

    @app.route('/admin/billing')
    @admin_required
    def admin_billing():
        bills = query_db("""
            SELECT bi.*, b.check_in, b.check_out, b.status as booking_status,
                   u.name as cust_name, r.room_number
            FROM bills bi 
            JOIN bookings b ON b.id = bi.booking_id
            JOIN users u ON u.id = b.user_id
            JOIN rooms r ON r.id = b.room_id
            ORDER BY bi.created_at DESC
        """)
        total_paid = query_db("SELECT SUM(total_amount) as s FROM bills WHERE payment_status='Paid'", one=True)['s'] or 0
        total_pending = query_db("SELECT SUM(total_amount) as s FROM bills WHERE payment_status='Pending'", one=True)['s'] or 0
        
        return render_template('admin/billing.html', bills=bills,
                               total_paid=total_paid, total_pending=total_pending)

    @app.route('/admin/billing/mark-paid/<int:bill_id>', methods=['POST'])
    @admin_required
    def admin_mark_paid(bill_id):
        query_db("UPDATE bills SET payment_status='Paid' WHERE id=?", [bill_id], commit=True)
        flash('Bill marked as Paid.', 'success')
        return redirect(url_for('admin_billing'))

    @app.route('/admin/billing/add-service/<int:bill_id>', methods=['POST'])
    @admin_required
    def admin_add_service_charge(bill_id):
        charge = float(request.form['charge'])
        bill = query_db("SELECT * FROM bills WHERE id=?", [bill_id], one=True)
        
        new_svc = bill['service_charges'] + charge
        new_total = bill['room_charges'] + new_svc
        query_db("UPDATE bills SET service_charges=?, total_amount=? WHERE id=?",
                 [new_svc, new_total, bill_id], commit=True)
                 
        flash(f'Service charge of ₹{charge} added.', 'success')
        return redirect(url_for('admin_billing'))

    # === SERVICES MONITORING ===

    @app.route('/admin/services')
    @admin_required
    def admin_services():
        services = query_db("""
            SELECT s.*, u.name as cust_name, r.room_number
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
        status = request.form['status']
        query_db("UPDATE services SET status=? WHERE id=?", [status, service_id], commit=True)
        flash('Service status updated.', 'success')
        return redirect(url_for('admin_services'))
