"""
============================================================
  E-Hotel Management System — Customer Routes
  File: routes/customer_routes.py
============================================================

  These routes handle everything a CUSTOMER can do:
    - Sign up for an account
    - Login and logout
    - View their personal dashboard
    - Book a room
    - Add/remove rooms from wishlist
    - Submit a review for a room
    - Request room services

  Most routes here require the customer to be logged in.
  We use @login_required from utils/auth.py for that.

  Pages / URLs handled here:
    GET/POST /login              → Customer login page
    GET/POST /signup             → Customer registration page
    GET      /logout             → Logout and clear session
    GET      /dashboard          → Customer dashboard (bookings, wishlist, services)
    GET/POST /book/<room_id>     → Book a specific room
    POST     /wishlist/toggle/.. → Add or remove room from wishlist (AJAX)
    POST     /review/<room_id>   → Submit a rating and review
    POST     /service/request    → Submit a room service request
"""

import datetime
import sqlite3
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from utils.db import query_db, hash_password
from utils.auth import login_required


def register_customer_routes(app):
    """
    Registers all customer-related routes onto the Flask app.
    Called once from app.py when the application starts.
    """

    # ----------------------------------------------------------
    # Customer Login
    # ----------------------------------------------------------
    @app.route('/login', methods=['GET', 'POST'])
    def customer_login():
        """
        Shows the login form (GET request).
        Handles the login form submission (POST request).

        On success: stores user info in session and redirects to dashboard.
        On failure: shows an error message.
        """
        # If already logged in, skip login page and go to dashboard
        if 'user_id' in session:
            return redirect(url_for('customer_dashboard'))

        if request.method == 'POST':
            email    = request.form['email']
            password = hash_password(request.form['password'])  # Hash before comparing

            # Look up user with matching email AND hashed password
            user = query_db(
                "SELECT * FROM users WHERE email=? AND password=?",
                [email, password],
                one=True
            )

            if user:
                # Save user info in the session (like a login cookie)
                session['user_id']   = user['id']
                session['user_name'] = user['name']
                flash(f"Welcome back, {user['name']}!", 'success')
                return redirect(url_for('customer_dashboard'))

            flash('Invalid email or password.', 'danger')

        return render_template('auth/login.html')


    # ----------------------------------------------------------
    # Customer Sign Up (Registration)
    # ----------------------------------------------------------
    @app.route('/signup', methods=['GET', 'POST'])
    def customer_signup():
        """
        Shows the sign-up form (GET).
        Saves a new customer account to the database (POST).
        """
        if request.method == 'POST':
            name     = request.form['name']
            email    = request.form['email']
            phone    = request.form.get('phone', '')  # Phone is optional
            password = hash_password(request.form['password'])

            try:
                # Insert the new user into the database
                query_db(
                    "INSERT INTO users (name, email, phone, password) VALUES (?,?,?,?)",
                    [name, email, phone, password],
                    commit=True
                )
                flash('Account created successfully! Please login.', 'success')
                return redirect(url_for('customer_login'))

            except sqlite3.IntegrityError:
                # This error means the email is already registered (it must be UNIQUE)
                flash('That email address is already registered.', 'danger')

        return render_template('auth/signup.html')


    # ----------------------------------------------------------
    # Customer Logout
    # ----------------------------------------------------------
    @app.route('/logout')
    def customer_logout():
        """
        Clears the customer's session (logs them out).
        Redirects to the home page.
        """
        session.clear()
        flash('You have been logged out successfully.', 'info')
        return redirect(url_for('index'))


    # ----------------------------------------------------------
    # Customer Dashboard
    # ----------------------------------------------------------
    @app.route('/dashboard')
    @login_required  # Must be logged in to see this page
    def customer_dashboard():
        """
        The customer's personal dashboard.
        Shows their bookings, wishlist rooms, and service requests.
        """
        user_id = session['user_id']

        # Get all bookings for this customer (with room info)
        bookings = query_db("""
            SELECT b.*, r.room_number, r.room_type, r.price
            FROM bookings b
            JOIN rooms r ON r.id = b.room_id
            WHERE b.user_id = ?
            ORDER BY b.created_at DESC
        """, [user_id])

        # Get all wishlist rooms for this customer
        wishlist = query_db("""
            SELECT r.*
            FROM wishlist w
            JOIN rooms r ON r.id = w.room_id
            WHERE w.user_id = ?
        """, [user_id])

        # Get all service requests for this customer (with room number)
        services = query_db("""
            SELECT s.*, r.room_number
            FROM services s
            JOIN bookings b ON b.id = s.booking_id
            JOIN rooms r ON r.id = b.room_id
            WHERE s.user_id = ?
            ORDER BY s.created_at DESC
        """, [user_id])

        return render_template(
            'customer/dashboard.html',
            bookings=bookings,
            wishlist=wishlist,
            services=services
        )


    # ----------------------------------------------------------
    # Book a Room
    # ----------------------------------------------------------
    @app.route('/book/<int:room_id>', methods=['GET', 'POST'])
    @login_required  # Must be logged in to book
    def book_room(room_id):
        """
        Shows the booking form for a specific room (GET).
        Processes and saves the booking to the database (POST).

        Also creates a bill record automatically when booking is made.
        """
        room = query_db("SELECT * FROM rooms WHERE id=?", [room_id], one=True)

        # Safety check: make sure the room exists
        if not room:
            flash('Room not found.', 'danger')
            return redirect(url_for('browse_rooms'))

        # Check that the room is currently available
        if room['status'] != 'Available':
            flash('This room is not available for booking right now.', 'warning')
            return redirect(url_for('room_detail', room_id=room_id))

        if request.method == 'POST':
            check_in  = request.form['check_in']
            check_out = request.form['check_out']

            # Parse the dates and calculate number of nights
            ci_date = datetime.datetime.strptime(check_in,  '%Y-%m-%d')
            co_date = datetime.datetime.strptime(check_out, '%Y-%m-%d')
            nights  = (co_date - ci_date).days

            # Validate: check-out must be after check-in
            if nights <= 0:
                flash('Check-out date must be after check-in date.', 'danger')
                return render_template('customer/book_room.html', room=room)

            # Calculate the total cost: nights × price per night
            total_price = nights * room['price']

            # Save the booking record
            booking_id = query_db(
                "INSERT INTO bookings (user_id, room_id, check_in, check_out, total_price, status) VALUES (?,?,?,?,?,?)",
                [session['user_id'], room_id, check_in, check_out, total_price, 'Pending'],
                commit=True
            )

            # Also create a bill record for this booking
            query_db(
                "INSERT INTO bills (booking_id, room_charges, total_amount) VALUES (?,?,?)",
                [booking_id, total_price, total_price],
                commit=True
            )

            flash('Booking submitted! Please wait for admin approval.', 'success')
            return redirect(url_for('customer_dashboard'))

        return render_template('customer/book_room.html', room=room)


    # ----------------------------------------------------------
    # Wishlist Toggle (AJAX)
    # ----------------------------------------------------------
    @app.route('/wishlist/toggle/<int:room_id>', methods=['POST'])
    @login_required
    def toggle_wishlist(room_id):
        """
        Adds or removes a room from the customer's wishlist.

        This route is called via JavaScript (AJAX) from the room cards.
        It returns a JSON response, not an HTML page.

        Response:
          {'status': 'added'}   → Room was added to wishlist
          {'status': 'removed'} → Room was removed from wishlist
        """
        user_id = session['user_id']

        # Check if this room is already in the wishlist
        existing = query_db(
            "SELECT id FROM wishlist WHERE user_id=? AND room_id=?",
            [user_id, room_id],
            one=True
        )

        if existing:
            # Room is in wishlist → remove it
            query_db("DELETE FROM wishlist WHERE user_id=? AND room_id=?", [user_id, room_id], commit=True)
            return jsonify({'status': 'removed'})
        else:
            # Room is not in wishlist → add it
            query_db("INSERT INTO wishlist (user_id, room_id) VALUES (?,?)", [user_id, room_id], commit=True)
            return jsonify({'status': 'added'})


    # ----------------------------------------------------------
    # Submit a Room Review
    # ----------------------------------------------------------
    @app.route('/review/<int:room_id>', methods=['POST'])
    @login_required
    def submit_review(room_id):
        """
        Saves a customer's review (rating + comment) for a specific room.
        """
        rating  = int(request.form['rating'])   # Star rating: 1 to 5
        comment = request.form['comment']

        query_db(
            "INSERT INTO reviews (user_id, room_id, rating, comment) VALUES (?,?,?,?)",
            [session['user_id'], room_id, rating, comment],
            commit=True
        )

        flash('Your review has been submitted. Thank you!', 'success')
        return redirect(url_for('room_detail', room_id=room_id))


    # ----------------------------------------------------------
    # Request a Room Service
    # ----------------------------------------------------------
    @app.route('/service/request', methods=['POST'])
    @login_required
    def request_service():
        """
        Saves a room service request from a customer.
        Examples: Room Cleaning, Laundry, Food & Beverages, etc.
        """
        booking_id   = request.form['booking_id']
        service_type = request.form['service_type']
        description  = request.form.get('description', '')  # Optional extra details

        query_db(
            "INSERT INTO services (booking_id, user_id, service_type, description) VALUES (?,?,?,?)",
            [booking_id, session['user_id'], service_type, description],
            commit=True
        )

        flash('Service request submitted successfully!', 'success')
        return redirect(url_for('customer_dashboard'))
