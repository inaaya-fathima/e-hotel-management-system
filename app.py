"""
==========================================================
  E-Hotel Management System - Flask Backend
  Modularized Architecture - College Project
==========================================================
  Roles: Admin | Staff | Customer
  Author: College Project
  
  Description:
  This file is cleanly structured to easily read the
  system's configuration by importing other functions.
"""

from flask import Flask
from utils.db import init_db

# Import specific route-registration logic
from routes.main_routes import register_main_routes
from routes.customer_routes import register_customer_routes
from routes.admin_routes import register_admin_routes
from routes.staff_routes import register_staff_routes

# Initialize core Web Flask
app = Flask(__name__)
app.secret_key = 'ehotel_super_secret_college_2024_key'

# Register our organized files straight onto the app structure
register_main_routes(app)
register_customer_routes(app)
register_admin_routes(app)
register_staff_routes(app)

if __name__ == '__main__':
    # Initialize the database on startup (creates tables/loads sample data)
    init_db(app)
    
    # Run development web service
    app.run(debug=True, port=5000)
