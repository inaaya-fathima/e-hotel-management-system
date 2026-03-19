import datetime
import sqlite3
from flask import render_template, request, redirect, url_for, session, flash
from utils.db import query_db, hash_password
from utils.auth import staff_required

def register_staff_routes(app):
    """
    Registers the routes that form functionality designed solely for internal hotel employees.
    """

    @app.route('/staff/login', methods=['GET', 'POST'])
    def staff_login():
        """Handles authentication into the employee operational portal."""
        if 'staff_id' in session:
            return redirect(url_for('staff_dashboard'))
            
        if request.method == 'POST':
            username = request.form['username']
            password = hash_password(request.form['password'])
            
            member = query_db("SELECT * FROM staff WHERE username=? AND password=?",
                              [username, password], one=True)
            if member:
                session['staff_id'] = member['id']
                session['staff_name'] = member['name']
                session['staff_role'] = member['role']
                return redirect(url_for('staff_dashboard'))
            flash('Invalid credentials.', 'danger')
            
        return render_template('staff/login.html')

    @app.route('/staff/logout')
    def staff_logout():
        """Destroys actively attached staff state preventing data access."""
        session.pop('staff_id', None)
        session.pop('staff_name', None)
        session.pop('staff_role', None)
        return redirect(url_for('staff_login'))

    @app.route('/staff/dashboard')
    @staff_required
    def staff_dashboard():
        """Staff-specific dashboard for tracking tasks and recording routine checks."""
        tasks = query_db("SELECT * FROM services WHERE status != 'Completed' ORDER BY created_at DESC LIMIT 10")
        rooms = query_db("SELECT * FROM rooms ORDER BY room_number")
        
        today = datetime.date.today().isoformat()
        att = query_db("SELECT * FROM attendance WHERE staff_id=? AND date=?",
                       [session['staff_id'], today], one=True)
                       
        return render_template('staff/dashboard.html', tasks=tasks, rooms=rooms, attendance=att, today=today)

    @app.route('/staff/room/update/<int:room_id>', methods=['POST'])
    @staff_required
    def staff_update_room(room_id):
        """Enable housekeeping/maintenance checking to change room's valid state dynamically."""
        status = request.form['status']
        query_db("UPDATE rooms SET status=? WHERE id=?", [status, room_id], commit=True)
        flash(f'Room status updated to {status}.', 'success')
        return redirect(url_for('staff_dashboard'))

    @app.route('/staff/service/update/<int:service_id>', methods=['POST'])
    @staff_required
    def staff_update_service(service_id):
        """Completes and resolves task entries directly marking internal service tables."""
        status = request.form['status']
        query_db("UPDATE services SET status=? WHERE id=?", [status, service_id], commit=True)
        flash('Service request updated.', 'success')
        return redirect(url_for('staff_dashboard'))

    @app.route('/staff/attendance', methods=['POST'])
    @staff_required
    def mark_attendance():
        """Saves daily tracking checks into correct database log entry cleanly."""
        today = datetime.date.today().isoformat()
        status = request.form['status']
        sid = session['staff_id']
        
        existing = query_db("SELECT id FROM attendance WHERE staff_id=? AND date=?", [sid, today], one=True)
        if existing:
            query_db("UPDATE attendance SET status=?, marked_at=CURRENT_TIMESTAMP WHERE staff_id=? AND date=?",
                     [status, sid, today], commit=True)
        else:
            query_db("INSERT INTO attendance (staff_id,date,status,marked_at) VALUES (?,?,?,CURRENT_TIMESTAMP)",
                     [sid, today, status], commit=True)
                     
        flash(f'Attendance marked as {status}.', 'success')
        return redirect(url_for('staff_dashboard'))
