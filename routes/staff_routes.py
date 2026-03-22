"""
============================================================
  E-Hotel Management System — Staff Routes
  File: routes/staff_routes.py
============================================================

  These routes handle the STAFF portal — only accessible after
  staff login. Staff members can:
    - View their dashboard (pending service tasks + room list)
    - Update room statuses (e.g. mark as Clean/Maintenance)
    - Update service request statuses (e.g. mark as Completed)
    - Mark their daily attendance (Present / Absent)

  All routes here use @staff_required to protect them.

  Pages / URLs handled here:
    GET/POST /staff/login            → Staff login page
    GET      /staff/logout           → Staff logout
    GET      /staff/dashboard        → Staff dashboard
    POST     /staff/room/update/<id> → Update a room's status
    POST     /staff/service/update/. → Update a service request status
    POST     /staff/attendance       → Mark attendance for today
"""

import datetime
from flask import render_template, request, redirect, url_for, session, flash
from utils.db import query_db, hash_password
from utils.auth import staff_required


def register_staff_routes(app):
    """
    Registers all staff portal routes onto the Flask app.
    Called once from app.py when the application starts.
    """

    # ----------------------------------------------------------
    # Staff Login / Logout
    # ----------------------------------------------------------

    @app.route('/staff/login', methods=['GET', 'POST'])
    def staff_login():
        """
        Shows the staff login form (GET).
        Validates credentials and creates a staff session (POST).
        """
        # If staff is already logged in, go straight to dashboard
        if 'staff_id' in session:
            return redirect(url_for('staff_dashboard'))

        if request.method == 'POST':
            username = request.form['username']
            password = hash_password(request.form['password'])

            # Look up staff member with matching username+password
            member = query_db(
                "SELECT * FROM staff WHERE username=? AND password=?",
                [username, password],
                one=True
            )

            if member:
                # Store staff info in the session
                session['staff_id']   = member['id']
                session['staff_name'] = member['name']
                session['staff_role'] = member['role']
                return redirect(url_for('staff_dashboard'))

            flash('Invalid credentials. Please try again.', 'danger')

        return render_template('staff/login.html')


    @app.route('/staff/logout')
    def staff_logout():
        """
        Removes staff info from the session (logs them out).
        """
        session.pop('staff_id',   None)
        session.pop('staff_name', None)
        session.pop('staff_role', None)
        return redirect(url_for('staff_login'))


    # ----------------------------------------------------------
    # Staff Dashboard
    # ----------------------------------------------------------

    @app.route('/staff/dashboard')
    @staff_required  # Must be logged in as staff to see this page
    def staff_dashboard():
        """
        The main staff dashboard.
        Shows:
          - Pending/In-Progress service requests to complete
          - List of all rooms (to update statuses)
          - Today's attendance status for this staff member
        """
        # Get service tasks that are not yet completed (up to 10)
        tasks = query_db(
            "SELECT * FROM services WHERE status != 'Completed' ORDER BY created_at DESC LIMIT 10"
        )

        # Get all rooms (for housekeeping/status updates)
        rooms = query_db("SELECT * FROM rooms ORDER BY room_number")

        # Check if this staff member has already marked attendance today
        today           = datetime.date.today().isoformat()  # e.g. '2024-03-19'
        attendance_today = query_db(
            "SELECT * FROM attendance WHERE staff_id=? AND date=?",
            [session['staff_id'], today],
            one=True  # Returns one record or None
        )

        return render_template(
            'staff/dashboard.html',
            tasks=tasks,
            rooms=rooms,
            attendance=attendance_today,
            today=today
        )


    # ----------------------------------------------------------
    # Update Room Status
    # ----------------------------------------------------------

    @app.route('/staff/room/update/<int:room_id>', methods=['POST'])
    @staff_required
    def staff_update_room(room_id):
        """
        Lets staff update a room's status.
        Examples: 'Available', 'Maintenance', 'Cleaning'
        """
        new_status = request.form['status']
        query_db("UPDATE rooms SET status=? WHERE id=?", [new_status, room_id], commit=True)
        flash(f'Room status updated to "{new_status}".', 'success')
        return redirect(url_for('staff_dashboard'))


    # ----------------------------------------------------------
    # Update Service Request Status
    # ----------------------------------------------------------

    @app.route('/staff/service/update/<int:service_id>', methods=['POST'])
    @staff_required
    def staff_update_service(service_id):
        """
        Lets staff update the status of a service request.
        Examples: 'In Progress', 'Completed'
        """
        new_status = request.form['status']
        query_db("UPDATE services SET status=? WHERE id=?", [new_status, service_id], commit=True)
        flash('Service request status updated.', 'success')
        return redirect(url_for('staff_dashboard'))


    # ----------------------------------------------------------
    # Mark Daily Attendance
    # ----------------------------------------------------------

    @app.route('/staff/attendance', methods=['POST'])
    @staff_required
    def mark_attendance():
        """
        Allows a staff member to mark their attendance for today.

        Rules:
          - Can only be marked once per day (UNIQUE constraint on staff_id + date)
          - If already marked, it updates the existing record
          - Status options: 'Present' or 'Absent'
        """
        today      = datetime.date.today().isoformat()  # Today's date as a string
        new_status = request.form['status']              # 'Present' or 'Absent'
        staff_id   = session['staff_id']

        # Check if attendance was already marked today
        existing = query_db(
            "SELECT id FROM attendance WHERE staff_id=? AND date=?",
            [staff_id, today],
            one=True
        )

        if existing:
            # Update existing record if already marked
            query_db(
                "UPDATE attendance SET status=?, marked_at=CURRENT_TIMESTAMP WHERE staff_id=? AND date=?",
                [new_status, staff_id, today],
                commit=True
            )
        else:
            # Insert a new attendance record for today
            query_db(
                "INSERT INTO attendance (staff_id, date, status, marked_at) VALUES (?,?,?,CURRENT_TIMESTAMP)",
                [staff_id, today, new_status],
                commit=True
            )

        flash(f'Attendance marked as "{new_status}" for today.', 'success')
        return redirect(url_for('staff_dashboard'))
