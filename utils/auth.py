from functools import wraps
from flask import session, flash, redirect, url_for

def login_required(f):
    """
    Decorator function to enforce customer login access on specific routes.
    If the customer is not logged in, they are redirected to the customer login screen.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('customer_routes.customer_login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """
    Decorator function to enforce admin access on specific routes.
    If the admin is not logged in, they are redirected to the admin login screen.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Admin login required.', 'warning')
            return redirect(url_for('admin_routes.admin_login'))
        return f(*args, **kwargs)
    return decorated

def staff_required(f):
    """
    Decorator function to enforce staff access on specific routes.
    If the staff is not logged in, they are redirected to the staff login screen.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'staff_id' not in session:
            flash('Staff login required.', 'warning')
            return redirect(url_for('staff_routes.staff_login'))
        return f(*args, **kwargs)
    return decorated
