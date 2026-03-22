"""
============================================================
  E-Hotel Management System — Public Routes
  File: routes/main_routes.py
============================================================

  These are the PUBLIC pages that anyone can visit — no login needed.

  Pages / URLs handled here:
    /              → Home page (shows featured rooms)
    /rooms         → Browse all rooms (with search and filter)
    /room/<id>     → Room detail page (info, reviews, wishlist check)
"""

from flask import render_template, request, session
from utils.db import query_db


def register_main_routes(app):
    """
    Registers all public-facing routes onto the Flask app.
    Called once from app.py when the application starts.
    """

    # ----------------------------------------------------------
    # Home Page
    # ----------------------------------------------------------
    @app.route('/')
    def index():
        """
        The home page.
        Fetches up to 8 available rooms to display as featured rooms.
        """
        rooms = query_db("SELECT * FROM rooms WHERE status='Available' LIMIT 8")
        return render_template('index.html', rooms=rooms)


    # ----------------------------------------------------------
    # Browse Rooms Page
    # ----------------------------------------------------------
    @app.route('/rooms')
    def browse_rooms():
        """
        Shows all available rooms.

        Supports two optional URL query parameters:
          ?type=Single   → Filter by room type
          ?search=cozy   → Search by room number, type, or description
        """
        room_type   = request.args.get('type', '')    # e.g. 'Single', 'Suite'
        search_term = request.args.get('search', '')  # e.g. 'city view'

        if room_type:
            # Filter rooms by type (e.g. only show Suites)
            rooms = query_db(
                "SELECT * FROM rooms WHERE status='Available' AND room_type=?",
                [room_type]
            )
        elif search_term:
            # Search rooms by keyword — % is a wildcard in SQL LIKE
            keyword = f'%{search_term}%'
            rooms = query_db(
                """SELECT * FROM rooms 
                   WHERE status='Available' AND 
                   (room_number LIKE ? OR room_type LIKE ? OR description LIKE ?)""",
                [keyword, keyword, keyword]
            )
        else:
            # No filter — show all available rooms
            rooms = query_db("SELECT * FROM rooms WHERE status='Available'")

        return render_template('rooms.html', rooms=rooms, selected_type=room_type)


    # ----------------------------------------------------------
    # Room Detail Page
    # ----------------------------------------------------------
    @app.route('/room/<int:room_id>')
    def room_detail(room_id):
        """
        Shows detailed information about a single room.

        Also loads:
          - All reviews for this room (with reviewer names)
          - Average star rating
          - Whether the logged-in customer has wishlisted this room
        """
        # Get the room by its ID
        room = query_db("SELECT * FROM rooms WHERE id=?", [room_id], one=True)

        # Get all reviews for this room, joined with user names
        reviews = query_db("""
            SELECT r.*, u.name AS user_name
            FROM reviews r
            JOIN users u ON u.id = r.user_id
            WHERE r.room_id = ?
            ORDER BY r.created_at DESC
        """, [room_id])

        # Calculate the average rating (e.g. 4.2 out of 5)
        avg_row    = query_db("SELECT AVG(rating) AS avg FROM reviews WHERE room_id=?", [room_id], one=True)
        avg_rating = avg_row['avg'] if avg_row else None

        # Check if the current customer has this room in their wishlist
        in_wishlist = False
        if 'user_id' in session:
            wishlist_entry = query_db(
                "SELECT id FROM wishlist WHERE user_id=? AND room_id=?",
                [session['user_id'], room_id],
                one=True
            )
            in_wishlist = bool(wishlist_entry)

        return render_template(
            'room_detail.html',
            room=room,
            reviews=reviews,
            avg_rating=avg_rating,
            in_wishlist=in_wishlist
        )
