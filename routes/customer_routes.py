"""
E-Hotel Management System — Customer Routes
File: routes/customer_routes.py
"""

import datetime
import sqlite3
import random
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from utils.db import query_db, hash_password
from utils.auth import login_required


def register_customer_routes(app):

    # ----------------------------------------------------------
    # Customer Login
    # ----------------------------------------------------------
    @app.route('/login', methods=['GET', 'POST'])
    def customer_login():
        if 'user_id' in session:
            return redirect(url_for('customer_dashboard'))

        if request.method == 'POST':
            email    = request.form['email']
            password = hash_password(request.form['password'])
            user = query_db("SELECT * FROM users WHERE email=? AND password=?", [email, password], one=True)
            if user:
                session['user_id']   = user['id']
                session['user_name'] = user['name']
                flash(f"Welcome back, {user['name']}!", 'success')
                return redirect(url_for('customer_dashboard'))
            flash('Invalid email or password.', 'danger')

        return render_template('auth/login.html')


    # ----------------------------------------------------------
    # Customer Sign Up
    # ----------------------------------------------------------
    @app.route('/signup', methods=['GET', 'POST'])
    def customer_signup():
        """Show signup form (GET) or process registration (POST)."""
        if 'user_id' in session:
            return redirect(url_for('customer_dashboard'))

        if request.method == 'POST':
            # --- Captcha verification ---
            user_captcha = request.form.get('captcha_answer', '').strip()
            correct      = str(session.get('captcha_answer', ''))
            if not user_captcha or user_captcha != correct:
                flash('Incorrect captcha answer. Please try again.', 'danger')
                return redirect(url_for('customer_signup'))
            session.pop('captcha_answer', None)

            name     = request.form.get('name', '').strip()
            email    = request.form.get('email', '').strip()
            phone    = request.form.get('phone', '').strip()
            password = hash_password(request.form.get('password', ''))

            if not name or not email or not password:
                flash('Please fill in all required fields.', 'danger')
                return redirect(url_for('customer_signup'))

            try:
                query_db(
                    "INSERT INTO users (name, email, phone, password) VALUES (?,?,?,?)",
                    [name, email, phone, password], commit=True
                )
                flash(f'Welcome, {name}! Your account has been created. Please login.', 'success')
                return redirect(url_for('customer_login'))
            except sqlite3.IntegrityError:
                flash('That email address is already registered.', 'danger')
                return redirect(url_for('customer_signup'))

        # GET: generate a fresh captcha challenge
        ops = ['+', '-', '×']
        op  = random.choice(ops)
        a   = random.randint(2, 15)
        b   = random.randint(1, 10)
        if op == '+':
            answer = a + b
        elif op == '-':
            a, b   = max(a, b), min(a, b)
            answer = a - b
        else:
            a, b   = random.randint(2, 9), random.randint(2, 9)
            answer = a * b

        session['captcha_answer'] = str(answer)
        captcha_question = f"{a} {op} {b}"
        return render_template('auth/signup.html', captcha_question=captcha_question)


    # ----------------------------------------------------------
    # Customer Logout
    # ----------------------------------------------------------
    @app.route('/logout')
    def customer_logout():
        session.clear()
        flash('You have been logged out successfully.', 'info')
        return redirect(url_for('index'))


    # ----------------------------------------------------------
    # Customer Dashboard
    # ----------------------------------------------------------
    @app.route('/dashboard')
    @login_required
    def customer_dashboard():
        user_id = session['user_id']

        bookings = query_db("""
            SELECT b.*, r.room_number, r.room_type, r.price, r.category, b.hotel_name, b.branch
            FROM bookings b
            JOIN rooms r ON r.id = b.room_id
            WHERE b.user_id = ?
            ORDER BY b.created_at DESC
        """, [user_id])

        wishlist = query_db("""
            SELECT r.* FROM wishlist w JOIN rooms r ON r.id = w.room_id WHERE w.user_id = ?
        """, [user_id])

        services = query_db("""
            SELECT s.*, r.room_number
            FROM services s
            JOIN bookings b ON b.id = s.booking_id
            JOIN rooms r ON r.id = b.room_id
            WHERE s.user_id = ?
            ORDER BY s.created_at DESC
        """, [user_id])

        bills = query_db("""
            SELECT bi.*, b.check_in, b.check_out, r.room_number, b.hotel_name, b.branch
            FROM bills bi
            JOIN bookings b ON b.id = bi.booking_id
            JOIN rooms r ON r.id = b.room_id
            WHERE b.user_id = ?
            ORDER BY bi.created_at DESC
        """, [user_id])

        catalog = query_db("SELECT * FROM service_catalog WHERE is_active=1 ORDER BY service_name")
        user    = query_db("SELECT * FROM users WHERE id=?", [user_id], one=True)

        return render_template(
            'customer/dashboard.html',
            bookings=bookings, wishlist=wishlist, services=services,
            bills=bills, catalog=catalog, user=user
        )


    # ----------------------------------------------------------
    # Settings — Change profile, password, delete account
    # ----------------------------------------------------------
    @app.route('/settings', methods=['GET', 'POST'])
    @login_required
    def customer_settings():
        user_id = session['user_id']
        user    = query_db("SELECT * FROM users WHERE id=?", [user_id], one=True)

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'update_profile':
                name  = request.form.get('name', '').strip()
                email = request.form.get('email', '').strip()
                phone = request.form.get('phone', '').strip()
                if not name or not email:
                    flash('Name and email are required.', 'danger')
                else:
                    try:
                        query_db(
                            "UPDATE users SET name=?, email=?, phone=? WHERE id=?",
                            [name, email, phone, user_id], commit=True
                        )
                        session['user_name'] = name
                        flash('Profile updated successfully.', 'success')
                    except sqlite3.IntegrityError:
                        flash('That email is already in use.', 'danger')

            elif action == 'change_password':
                old_pw  = hash_password(request.form.get('old_password', ''))
                new_pw  = request.form.get('new_password', '')
                confirm = request.form.get('confirm_password', '')
                if user['password'] != old_pw:
                    flash('Current password is incorrect.', 'danger')
                elif new_pw != confirm:
                    flash('New passwords do not match.', 'danger')
                elif len(new_pw) < 6:
                    flash('New password must be at least 6 characters.', 'danger')
                else:
                    query_db("UPDATE users SET password=? WHERE id=?",
                             [hash_password(new_pw), user_id], commit=True)
                    flash('Password changed successfully.', 'success')

            elif action == 'delete_account':
                confirm = request.form.get('confirm_delete', '')
                if confirm != 'DELETE':
                    flash('Please type DELETE to confirm account deletion.', 'warning')
                else:
                    query_db("DELETE FROM wishlist WHERE user_id=?", [user_id], commit=True)
                    query_db("DELETE FROM reviews WHERE user_id=?", [user_id], commit=True)
                    query_db("DELETE FROM services WHERE user_id=?", [user_id], commit=True)
                    query_db("UPDATE bookings SET user_id=NULL WHERE user_id=?", [user_id], commit=True)
                    query_db("DELETE FROM users WHERE id=?", [user_id], commit=True)
                    session.clear()
                    flash('Your account has been deleted.', 'info')
                    return redirect(url_for('index'))

            return redirect(url_for('customer_settings'))

        return render_template('customer/settings.html', user=user)


    # ----------------------------------------------------------
    # Book a Room / Hall / Experience
    # ----------------------------------------------------------
    @app.route('/book/<int:room_id>', methods=['GET', 'POST'])
    @login_required
    def book_room(room_id):
        room = query_db("SELECT * FROM rooms WHERE id=?", [room_id], one=True)

        if not room:
            flash('Room not found.', 'danger')
            return redirect(url_for('browse_rooms'))

        if room['status'] != 'Available':
            flash('This space is not available for booking right now.', 'warning')
            return redirect(url_for('room_detail', room_id=room_id))

        if request.method == 'POST':
            check_in  = request.form['check_in']
            check_out = request.form['check_out']

            ci_date = datetime.datetime.strptime(check_in,  '%Y-%m-%d')
            co_date = datetime.datetime.strptime(check_out, '%Y-%m-%d')
            nights  = (co_date - ci_date).days

            if nights <= 0:
                flash('Check-out date must be after check-in date.', 'danger')
                return render_template('customer/book_room.html', room=room)

            total_price = nights * room['price']
            hotel_name  = f"E-Hotel {room['destination']}" if room['destination'] != 'Main' else 'E-Hotel'
            branch      = room['branch'] or 'Main Branch'

            booking_id = query_db(
                "INSERT INTO bookings (user_id, room_id, check_in, check_out, total_price, status, hotel_name, branch) VALUES (?,?,?,?,?,?,?,?)",
                [session['user_id'], room_id, check_in, check_out, total_price, 'Pending', hotel_name, branch],
                commit=True
            )

            query_db(
                "INSERT INTO bills (booking_id, room_charges, service_charges, gst_rate, gst_amount, total_amount) VALUES (?,?,?,?,?,?)",
                [booking_id, total_price, 0, 18.0, 0, total_price], commit=True
            )

            flash('Booking submitted! Please wait for admin approval.', 'success')
            return redirect(url_for('booking_success', booking_id=booking_id))

        return render_template('customer/book_room.html', room=room)


    # ----------------------------------------------------------
    # Booking Success — Contact form for extra details
    # ----------------------------------------------------------
    @app.route('/booking/success/<int:booking_id>', methods=['GET', 'POST'])
    @login_required
    def booking_success(booking_id):
        booking = query_db(
            "SELECT b.*, r.room_number, r.room_type FROM bookings b JOIN rooms r ON r.id = b.room_id WHERE b.id=? AND b.user_id=?",
            [booking_id, session['user_id']], one=True
        )
        if not booking:
            return redirect(url_for('customer_dashboard'))

        if request.method == 'POST':
            details = request.form.get('details', '').strip()
            if details:
                query_db(
                    "INSERT INTO services (booking_id, user_id, service_type, description, charge) VALUES (?,?,?,?,?)",
                    [booking_id, session['user_id'], 'Further Details', details, 0], commit=True
                )
                flash('Your details have been sent to our team.', 'success')
            return redirect(url_for('customer_dashboard'))

        return render_template('customer/booking_success.html', booking=booking)


    # ----------------------------------------------------------
    # Wishlist Toggle (AJAX)
    # ----------------------------------------------------------
    @app.route('/wishlist/toggle/<int:room_id>', methods=['POST'])
    @login_required
    def toggle_wishlist(room_id):
        user_id  = session['user_id']
        existing = query_db("SELECT id FROM wishlist WHERE user_id=? AND room_id=?", [user_id, room_id], one=True)
        if existing:
            query_db("DELETE FROM wishlist WHERE user_id=? AND room_id=?", [user_id, room_id], commit=True)
            return jsonify({'status': 'removed'})
        else:
            query_db("INSERT INTO wishlist (user_id, room_id) VALUES (?,?)", [user_id, room_id], commit=True)
            return jsonify({'status': 'added'})


    # ----------------------------------------------------------
    # Submit a Review
    # ----------------------------------------------------------
    @app.route('/review/<int:room_id>', methods=['POST'])
    @login_required
    def submit_review(room_id):
        rating  = int(request.form['rating'])
        comment = request.form['comment']
        query_db(
            "INSERT INTO reviews (user_id, room_id, rating, comment) VALUES (?,?,?,?)",
            [session['user_id'], room_id, rating, comment], commit=True
        )
        flash('Your review has been submitted. Thank you!', 'success')
        return redirect(url_for('room_detail', room_id=room_id))


    # ----------------------------------------------------------
    # Request a Room Service (auto-charges from catalog)
    # ----------------------------------------------------------
    @app.route('/service/request', methods=['POST'])
    @login_required
    def request_service():
        booking_id   = request.form['booking_id']
        service_type = request.form['service_type']
        description  = request.form.get('description', '')

        catalog_item = query_db(
            "SELECT * FROM service_catalog WHERE service_name=? AND is_active=1", [service_type], one=True
        )
        charge = catalog_item['price'] if catalog_item else 0

        # Auto-assign to department staff at the booking's branch
        assigned_staff = None
        if catalog_item and catalog_item['department_id']:
            booking = query_db("SELECT branch FROM bookings WHERE id=?", [booking_id], one=True)
            if booking:
                assigned_staff = query_db(
                    "SELECT id FROM staff WHERE department_id=? AND assigned_branch=? LIMIT 1",
                    [catalog_item['department_id'], booking['branch']], one=True
                )

        staff_id = assigned_staff['id'] if assigned_staff else None

        query_db(
            "INSERT INTO services (booking_id, user_id, service_type, description, charge, assigned_staff_id) VALUES (?,?,?,?,?,?)",
            [booking_id, session['user_id'], service_type, description, charge, staff_id], commit=True
        )

        # Update bill
        if charge > 0:
            bill = query_db("SELECT * FROM bills WHERE booking_id=?", [booking_id], one=True)
            if bill:
                new_service = bill['service_charges'] + charge
                gst_amount  = round((bill['room_charges'] + new_service) * bill['gst_rate'] / 100, 2)
                new_total   = bill['room_charges'] + new_service + gst_amount
                query_db(
                    "UPDATE bills SET service_charges=?, gst_amount=?, total_amount=? WHERE id=?",
                    [new_service, gst_amount, new_total, bill['id']], commit=True
                )
            flash(f'Service request submitted. ₹{charge:.0f} has been added to your bill.', 'success')
        else:
            flash('Service request submitted successfully!', 'success')

        return redirect(url_for('customer_dashboard'))


    # ----------------------------------------------------------
    # Contact / Message Form (saved to DB + goes to admin)
    # ----------------------------------------------------------
    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        if request.method == 'POST':
            name    = request.form.get('name', '').strip()
            email   = request.form.get('email', '').strip()
            subject = request.form.get('subject', '').strip()
            body    = request.form.get('message', '').strip()
            user_id = session.get('user_id')

            if not name or not email or not body:
                flash('Please fill in all required fields.', 'danger')
            else:
                query_db(
                    "INSERT INTO messages (user_id, name, email, subject, body) VALUES (?,?,?,?,?)",
                    [user_id, name, email, subject, body], commit=True
                )
                flash('Your message has been sent to our team. We will respond within 24 hours.', 'success')
                return redirect(url_for('contact'))

        return render_template('info/contact.html')


    # ----------------------------------------------------------
    # Venue / Hall / Lounge Booking Enquiry
    # Saves to venue_enquiries table AND messages (admin sees both)
    # ----------------------------------------------------------
    @app.route('/book-venue', methods=['POST'])
    def book_venue():
        name         = request.form.get('name', '').strip()
        email        = request.form.get('email', '').strip()
        phone        = request.form.get('phone', '').strip()
        venue_type   = request.form.get('venue_type', '').strip()
        venue_option = request.form.get('venue_option', '').strip()
        event_date   = request.form.get('event_date', '').strip()
        guests       = request.form.get('guests', '0').strip()
        message      = request.form.get('message', '').strip()
        user_id      = session.get('user_id')

        if not name or not email or not event_date:
            flash('Please fill in all required fields (Name, Email, and Event Date).', 'danger')
            return redirect(request.referrer or url_for('experiences'))

        # Save to dedicated venue_enquiries table
        query_db(
            """INSERT INTO venue_enquiries
               (user_id, name, email, phone, venue_type, venue_option, event_date, guests, message)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            [user_id, name, email, phone, venue_type, venue_option, event_date, guests, message],
            commit=True
        )

        # Also mirror to messages so admin sees it in inbox
        subject = f"Venue Booking Request: {venue_type}"
        body    = (
            f"Venue: {venue_type}\n"
            f"Option: {venue_option}\n"
            f"Date: {event_date}\n"
            f"Guests: {guests}\n"
            f"Phone: {phone}\n\n"
            f"Message: {message}"
        )
        query_db(
            "INSERT INTO messages (user_id, name, email, subject, body) VALUES (?,?,?,?,?)",
            [user_id, name, email, subject, body], commit=True
        )

        flash(
            f'Your enquiry for "{venue_type}" on {event_date} has been received! '
            'Our team will contact you within 2 hours to confirm your booking.',
            'success'
        )
        # Redirect back to the page they came from
        return redirect(request.referrer or url_for('experiences'))
