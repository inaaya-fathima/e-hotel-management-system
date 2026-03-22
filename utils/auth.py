"""
============================================================
  E-Hotel Management System — Authentication Decorators
  File: utils/auth.py
============================================================

  This file provides "guard" decorators for protected routes.

  A decorator is a function that WRAPS another function.
  For example, @login_required checks if the user is logged in
  BEFORE allowing them to access a specific page.

  How it works (step-by-step):
    1. User visits a protected URL (e.g. /dashboard)
    2. @login_required runs first
    3. If the user is NOT logged in → redirect to login page
    4. If the user IS logged in → allow access to the page

  Usage in routes:
    @login_required
    def customer_dashboard():
        ...  # This code only runs if user is logged in

  Three roles are handled:
    - Customers  → use @login_required
    - Admins     → use @admin_required
    - Staff      → use @staff_required
"""

from functools import wraps
from flask import session, flash, redirect, url_for


def login_required(f):
    """
    Protects routes that require customer login.
    If the customer is not logged in, redirects to /login page.
    """
    @wraps(f)  # Keeps the original function's name and docstring
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # No customer session found → redirect to login
            flash('Please login to continue.', 'warning')
            return redirect(url_for('customer_login'))
        # Customer is logged in → run the original route function
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Protects routes that require admin login.
    If the admin is not logged in, redirects to /admin/login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            # No admin session found → redirect to admin login
            flash('Admin login required.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def staff_required(f):
    """
    Protects routes that require staff login.
    If the staff member is not logged in, redirects to /staff/login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'staff_id' not in session:
            # No staff session found → redirect to staff login
            flash('Staff login required.', 'warning')
            return redirect(url_for('staff_login'))
        return f(*args, **kwargs)
    return decorated_function
