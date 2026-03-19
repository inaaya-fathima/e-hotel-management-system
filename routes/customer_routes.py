import datetime
import sqlite3
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from utils.db import query_db, hash_password
from utils.auth import login_required

def register_customer_routes(app):
    """
    Registers the routes specifically related to logged-in customers.
    """

    @app.route('/login', methods=['GET', 'POST'])
    def customer_login():
        """Customer authentication page."""
        if 'user_id' in session:
            return redirect(url_for('customer_dashboard'))
            
        if request.method == 'POST':
            email = request.form['email']
            password = hash_password(request.form['password'])
            
            user = query_db("SELECT * FROM users WHERE email=? AND password=?", [email, password], one=True)
            if user:
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                flash(f"Welcome back, {user['name']}!", 'success')
                return redirect(url_for('customer_dashboard'))
            flash('Invalid email or password.', 'danger')
            
        return render_template('auth/login.html')

    @app.route('/signup', methods=['GET', 'POST'])
    def customer_signup():
        """Creates a new customer account."""
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            phone = request.form.get('phone', '')
            password = hash_password(request.form['password'])
            
            try:
                query_db("INSERT INTO users (name,email,phone,password) VALUES (?,?,?,?)", 
                         [name, email, phone, password], commit=True)
                flash('Account created! Please login.', 'success')
                return redirect(url_for('customer_login'))
            except sqlite3.IntegrityError:
                flash('Email is already registered.', 'danger')
                
        return render_template('auth/signup.html')

    @app.route('/logout')
    def customer_logout():
        """Logs out the customer."""
        session.clear()
        flash('Logged out successfully.', 'info')
        return redirect(url_for('index'))

    @app.route('/dashboard')
    @login_required
    def customer_dashboard():
        """Customer portal showing past and present bookings, wishlist, and service requests."""
        uid = session['user_id']
        
        bookings = query_db("""
            SELECT b.*, r.room_number, r.room_type, r.price
            FROM bookings b 
            JOIN rooms r ON r.id = b.room_id
            WHERE b.user_id = ? 
            ORDER BY b.created_at DESC
        """, [uid])
        
        wishlist = query_db("""
            SELECT r.* 
            FROM wishlist w 
            JOIN rooms r ON r.id = w.room_id
            WHERE w.user_id = ?
        """, [uid])
        
        services = query_db("""
            SELECT s.*, r.room_number 
            FROM services s
            JOIN bookings b ON b.id = s.booking_id
            JOIN rooms r ON r.id = b.room_id
            WHERE s.user_id = ? 
            ORDER BY s.created_at DESC
        """, [uid])
        
        return render_template('customer/dashboard.html', 
                               bookings=bookings, wishlist=wishlist, services=services)

    @app.route('/book/<int:room_id>', methods=['GET', 'POST'])
    @login_required
    def book_room(room_id):
        """Processes a simple room booking from the customer."""
        room = query_db("SELECT * FROM rooms WHERE id=?", [room_id], one=True)
        if not room:
            flash('Room not found.', 'danger')
            return redirect(url_for('browse_rooms'))
            
        if room['status'] != 'Available':
            flash('This room is currently not available for booking.', 'warning')
            return redirect(url_for('room_detail', room_id=room_id))

        if request.method == 'POST':
            check_in = request.form['check_in']
            check_out = request.form['check_out']
            
            # Verify the intended duration forms a positive integer
            ci_date = datetime.datetime.strptime(check_in, '%Y-%m-%d')
            co_date = datetime.datetime.strptime(check_out, '%Y-%m-%d')
            days = (co_date - ci_date).days
            
            if days <= 0:
                flash('Check-out date must be after check-in date.', 'danger')
                return render_template('customer/book_room.html', room=room)
                
            total_price = days * room['price']
            
            # Save Booking mapping User + Room together
            booking_id = query_db(
                "INSERT INTO bookings (user_id, room_id, check_in, check_out, total_price, status) VALUES (?,?,?,?,?,?)",
                [session['user_id'], room_id, check_in, check_out, total_price, 'Pending'], 
                commit=True
            )
            
            # Bind a new Invoice matching exactly against the newly submitted booking
            query_db("INSERT INTO bills (booking_id, room_charges, total_amount) VALUES (?,?,?)",
                     [booking_id, total_price, total_price], commit=True)
                     
            flash('Booking request has been submitted! Waiting for Admin approval.', 'success')
            return redirect(url_for('customer_dashboard'))
            
        return render_template('customer/book_room.html', room=room)

    @app.route('/wishlist/toggle/<int:room_id>', methods=['POST'])
    @login_required
    def toggle_wishlist(room_id):
        """AJAX handled logic routing adding/toggling wishlist tracking states."""
        uid = session['user_id']
        existing = query_db("SELECT id FROM wishlist WHERE user_id=? AND room_id=?", [uid, room_id], one=True)
        
        if existing:
            query_db("DELETE FROM wishlist WHERE user_id=? AND room_id=?", [uid, room_id], commit=True)
            return jsonify({'status': 'removed'})
        else:
            query_db("INSERT INTO wishlist (user_id, room_id) VALUES (?,?)", [uid, room_id], commit=True)
            return jsonify({'status': 'added'})

    @app.route('/review/<int:room_id>', methods=['POST'])
    @login_required
    def submit_review(room_id):
        """Processes submitted public review feedbacks mapping safely into the database."""
        rating  = int(request.form['rating'])
        comment = request.form['comment']
        
        query_db("INSERT INTO reviews (user_id, room_id, rating, comment) VALUES (?,?,?,?)",
                 [session['user_id'], room_id, rating, comment], commit=True)
        flash('Your review has been successfully submitted!', 'success')
        return redirect(url_for('room_detail', room_id=room_id))

    @app.route('/service/request', methods=['POST'])
    @login_required
    def request_service():
        """Permits active guest sessions safely requesting services towards linked backend accounts."""
        booking_id = request.form['booking_id']
        service_type = request.form['service_type']
        description = request.form.get('description', '')
        
        query_db("INSERT INTO services (booking_id, user_id, service_type, description) VALUES (?,?,?,?)",
                 [booking_id, session['user_id'], service_type, description], commit=True)
        flash('Service request submitted successfully!', 'success')
        return redirect(url_for('customer_dashboard'))
