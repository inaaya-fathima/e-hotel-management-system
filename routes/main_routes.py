"""
============================================================
  E-Hotel Management System — Public Routes
  File: routes/main_routes.py
============================================================
"""

from flask import render_template, request, session, redirect, url_for, flash
from utils.db import query_db


def register_main_routes(app):

    @app.route('/')
    def index():
        rooms = query_db("SELECT * FROM rooms WHERE status='Available' LIMIT 8")
        return render_template('index.html', rooms=rooms)


    @app.route('/rooms')
    def browse_rooms():
        room_type   = request.args.get('type', '')
        search_term = request.args.get('search', '')
        destination = request.args.get('destination', '')

        if not destination and not search_term:
            flash("Please select a destination first to view available stays and experiences.", "info")
            return redirect(url_for('destinations'))

        if destination and room_type:
            rooms = query_db(
                "SELECT * FROM rooms WHERE status='Available' AND destination=? AND room_type=?",
                [destination, room_type]
            )
        elif destination:
            rooms = query_db(
                "SELECT * FROM rooms WHERE status='Available' AND destination=?",
                [destination]
            )
        else:
            keyword = f'%{search_term}%'
            rooms = query_db(
                """SELECT * FROM rooms
                   WHERE status='Available' AND
                   (room_number LIKE ? OR room_type LIKE ? OR description LIKE ? OR destination LIKE ? OR branch LIKE ?)""",
                [keyword, keyword, keyword, keyword, keyword]
            )

        destinations = query_db("SELECT DISTINCT destination FROM rooms WHERE destination IS NOT NULL ORDER BY destination")

        return render_template(
            'rooms.html',
            rooms=rooms,
            selected_type=room_type,
            selected_destination=destination,
            destinations=destinations
        )


    @app.route('/room/<int:room_id>')
    def room_detail(room_id):
        room = query_db("SELECT * FROM rooms WHERE id=?", [room_id], one=True)
        if not room:
            flash("Room or Experience not found.", "danger")
            return redirect(url_for('destinations'))

        reviews = query_db("""
            SELECT r.*, u.name AS user_name
            FROM reviews r
            JOIN users u ON u.id = r.user_id
            WHERE r.room_id = ?
            ORDER BY r.created_at DESC
        """, [room_id])

        avg_row    = query_db("SELECT AVG(rating) AS avg FROM reviews WHERE room_id=?", [room_id], one=True)
        avg_rating = avg_row['avg'] if avg_row else None

        in_wishlist = False
        if 'user_id' in session:
            wishlist_entry = query_db(
                "SELECT id FROM wishlist WHERE user_id=? AND room_id=?",
                [session['user_id'], room_id], one=True
            )
            in_wishlist = bool(wishlist_entry)

        return render_template(
            'room_detail.html',
            room=room,
            reviews=reviews,
            avg_rating=avg_rating,
            in_wishlist=in_wishlist
        )


    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/destinations')
    def destinations():
        return render_template('destinations.html')

    @app.route('/offers')
    def offers():
        offers_data = query_db("SELECT * FROM offers WHERE is_active=1")
        return render_template('offers.html', offers=offers_data)


    @app.route('/offer/<int:offer_id>')
    def offer_detail(offer_id):
        offer = query_db("SELECT * FROM offers WHERE id=?", [offer_id], one=True)
        if not offer:
            flash("Offer not found.", "danger")
            return redirect(url_for('offers'))
        return render_template('offer_detail.html', offer=offer)


    @app.route('/sustainability')
    def sustainability():
        return render_template('info/sustainability.html')

    @app.route('/careers')
    def careers():
        return render_template('info/careers.html')

    @app.route('/travel-stories')
    def travel_stories():
        return render_template('info/travel_stories.html')

    @app.route('/our-story')
    def our_story():
        return render_template('info/our_story.html')

    @app.route('/our-team')
    def our_team():
        return render_template('info/our_team.html')

    @app.route('/awards')
    def awards():
        return render_template('info/awards.html')

    # --- EXPERIENCES EXTRA PAGES ---
    @app.route('/experiences')
    def experiences():
        return render_template('experiences.html')

    @app.route('/experiences/dining')
    def exp_dining():
        return render_template('experiences/dining.html')

    @app.route('/experiences/meetings')
    def exp_meetings():
        return render_template('experiences/meetings.html')

    @app.route('/experiences/wedding')
    def exp_wedding():
        return render_template('experiences/wedding.html')

    @app.route('/experiences/business-lounge')
    def exp_business_lounge():
        return render_template('experiences/business_lounge.html')
