"""
============================================================
  E-Hotel Management System — Main Entry File
  File: app.py
============================================================

  This is the STARTING point of the entire web application.
  When you run this file, Flask starts a local web server.

  What this file does:
    1. Creates the Flask application object
    2. Imports and registers all route files (pages)
    3. Sets up the database when the app starts
    4. Runs the development web server

  How to run:
    python app.py
  Then open your browser at: http://localhost:5000
"""

from flask import Flask
from utils.db import init_db

# Import the route-registration functions from the routes/ folder
from routes.main_routes     import register_main_routes
from routes.customer_routes import register_customer_routes
from routes.admin_routes    import register_admin_routes
from routes.staff_routes    import register_staff_routes


# ----------------------------------------------------------
# Step 1: Create the Flask app
# ----------------------------------------------------------
app = Flask(__name__)

# Secret key is used to encrypt session cookies (login sessions).
# Change this to something random and private in a real project!
app.secret_key = 'ehotel_super_secret_college_2024_key'


# ----------------------------------------------------------
# Step 2: Register all routes (pages) onto the app
# ----------------------------------------------------------
# Each register_*_routes(app) function adds a group of URL routes.
# Think of routes as the "menu" of all pages in the app.

register_main_routes(app)      # Public pages: Home, Rooms, Room Detail
register_customer_routes(app)  # Customer pages: Login, Signup, Dashboard, Booking
register_admin_routes(app)     # Admin panel: Dashboard, Rooms, Bookings, Staff, etc.
register_staff_routes(app)     # Staff portal: Dashboard, Attendance, Service updates


# ----------------------------------------------------------
# Step 3: Start the application
# ----------------------------------------------------------
if __name__ == '__main__':
    # Initialize the database (creates tables and adds sample data)
    init_db(app)

    # debug=True gives helpful error messages during development.
    # port=5000 means the app runs at http://localhost:5000
    app.run(debug=True, port=5000)
