from flask import render_template, request, session
from utils.db import query_db

def register_main_routes(app):
    """
    Registers the public-facing pages that anyone can view.
    """

    @app.route('/')
    def index():
        """Home page showing some sample available rooms."""
        rooms = query_db("SELECT * FROM rooms WHERE status='Available' LIMIT 8")
        return render_template('index.html', rooms=rooms)

    @app.route('/rooms')
    def browse_rooms():
        """Page to browse all available rooms with optional search and type filters."""
        room_type = request.args.get('type', '')
        search = request.args.get('search', '')

        if room_type:
            rooms = query_db("SELECT * FROM rooms WHERE status='Available' AND room_type=?", [room_type])
        elif search:
            search_term = f'%{search}%'
            rooms = query_db(
                "SELECT * FROM rooms WHERE status='Available' AND (room_number LIKE ? OR room_type LIKE ? OR description LIKE ?)",
                [search_term, search_term, search_term]
            )
        else:
            rooms = query_db("SELECT * FROM rooms WHERE status='Available'")
            
        return render_template('rooms.html', rooms=rooms, selected_type=room_type)

    @app.route('/room/<int:room_id>')
    def room_detail(room_id):
        """Details of a specific room, along with past customer reviews and wishlist info."""
        room = query_db("SELECT * FROM rooms WHERE id=?", [room_id], one=True)
        
        # Get all reviews corresponding to the targeted room
        reviews = query_db("""
            SELECT r.*, u.name as user_name 
            FROM reviews r
            JOIN users u ON u.id = r.user_id 
            WHERE r.room_id = ?
            ORDER BY r.created_at DESC
        """, [room_id])
        
        # Calculate the average review score (max 5)
        avg_rating_row = query_db("SELECT AVG(rating) as avg FROM reviews WHERE room_id=?", [room_id], one=True)
        avg_rating = avg_rating_row['avg'] if avg_rating_row else None
        
        # Check if the room exists inside the current customer's wishlist
        in_wishlist = False
        if 'user_id' in session:
            w = query_db("SELECT id FROM wishlist WHERE user_id=? AND room_id=?", 
                         [session['user_id'], room_id], one=True)
            in_wishlist = bool(w)
            
        return render_template('room_detail.html', room=room, reviews=reviews,
                               avg_rating=avg_rating, in_wishlist=in_wishlist)
