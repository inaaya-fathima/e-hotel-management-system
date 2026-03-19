document.addEventListener('DOMContentLoaded', () => {
    const hotelId = document.getElementById('current_hotel_id').value;
    loadHotelDetails(hotelId);
});

async function loadHotelDetails(hotelId) {
    try {
        const response = await fetch(`/hotels/api/hotels/${hotelId}/`);
        if (!response.ok) throw new Error('Hotel not found');
        const hotel = await response.json();
        renderHotelInfo(hotel);
        renderHotelRooms(hotel.room_types);
    } catch (error) {
        console.error(error);
        document.getElementById('hotel-info-section').innerHTML = '<p style="color:red; text-align:center;">Failed to load hotel details.</p>';
        document.getElementById('hotel-info-section').style.display = 'block';
    }
}

function renderHotelInfo(hotel) {
    const section = document.getElementById('hotel-info-section');
    const imgUrl = hotel.featured_image ? hotel.featured_image : '/static/images/default_hotel.jpg';
    
    let amenitiesHtml = hotel.amenities.map(a => 
        `<span style="background: rgba(0, 255, 136, 0.1); color: var(--primary-green); padding: 5px 12px; border-radius: 20px; font-size: 0.9rem; margin-right: 8px; margin-bottom: 8px; display: inline-block; border: 1px solid var(--primary-green);">
            <i class="${a.amenity.icon || 'fa fa-check'}"></i> ${a.amenity.name}
        </span>`
    ).join('');

    section.innerHTML = `
        <div class="modern-card" style="display:flex; flex-wrap:wrap; gap:20px;">
            <div style="flex: 1 1 400px; height: 350px;">
                <img src="${imgUrl}" style="width:100%; height:100%; object-fit:cover; border-radius:8px;" onerror="this.src='data:image/svg+xml;charset=UTF-8,%3Csvg%20width%3D%22100%25%22%20height%3D%22100%25%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Crect%20width%3D%22100%25%22%20height%3D%22100%25%22%20fill%3D%22%23cccccc%22%2F%3E%3Ctext%20x%3D%2250%25%22%20y%3D%2250%25%22%20text-anchor%3D%22middle%22%20fill%3D%22%23fff%22%20font-size%3D%2220px%22%3ENo%20Image%3C%2Ftext%3E%3C%2Fsvg%3E'">
            </div>
            <div style="flex: 1 1 400px; padding: 10px;">
                <h1 style="color: var(--primary-green); margin-bottom: 10px; font-size: 2.5rem;">${hotel.name}</h1>
                <p style="color: var(--text-muted); font-size: 1.1rem; margin-bottom: 20px;"><i class="fa fa-map-marker-alt"></i> ${hotel.address || hotel.city}, ${hotel.city}</p>
                <div style="display:inline-block; background: rgba(0,0,0,0.8); color: var(--primary-green); border: 1px solid var(--primary-green); padding: 5px 15px; border-radius: 20px; font-weight:bold; margin-bottom: 20px;">
                    <i class="fa fa-star"></i> ${hotel.rating} / 5.0
                </div>
                <p style="line-height: 1.6; margin-bottom: 20px; color: var(--text-light);">${hotel.description}</p>
                <div>
                    <h3 style="margin-bottom: 10px; color: var(--primary-green);">Amenities</h3>
                    ${amenitiesHtml}
                </div>
                
                <div style="margin-top: 20px;">
                    <h3 style="margin-bottom: 10px; color: var(--primary-green);">Location</h3>
                    <iframe 
                        width="100%" 
                        height="200" 
                        style="border:0; border-radius: 8px;" 
                        loading="lazy" 
                        allowfullscreen 
                        src="https://www.google.com/maps/embed/v1/place?key=INITIALIZE_API_KEY_HERE&q=${encodeURIComponent(hotel.name + ', ' + hotel.city)}">
                    </iframe>
                    <small style="color:var(--text-muted);">*Map requires valid Google API key in production.</small>
                </div>
            </div>
        </div>
    `;
    section.style.display = 'block';
}

function renderHotelRooms(roomTypes) {
    const container = document.getElementById('rooms-container');
    container.innerHTML = '';

    if (!roomTypes || roomTypes.length === 0) {
        container.innerHTML = '<p style="color: var(--text-light);">No rooms available currently.</p>';
        return;
    }

    roomTypes.forEach(rt => {
        // Mock available count or use real property
        const availableCount = rt.capacity || 2; 
        
        const card = document.createElement('div');
        card.style.background = 'var(--bg-card)';
        card.style.border = '1px solid #333';
        card.style.borderRadius = '12px';
        card.style.padding = '20px';
        card.style.transition = 'transform 0.3s, border-color 0.3s';
        card.onmouseover = () => { card.style.transform = 'translateY(-5px)'; card.style.borderColor = 'var(--primary-green)'; };
        card.onmouseout = () => { card.style.transform = 'translateY(0)'; card.style.borderColor = '#333'; };
        
        card.innerHTML = `
            <h3 style="color: var(--text-light); margin-bottom: 10px; font-size: 1.5rem;">${rt.name}</h3>
            <p style="font-size: 0.95rem; color: var(--text-muted); margin-bottom: 15px; min-height: 45px;">${rt.description}</p>
            <div style="display:flex; justify-content:space-between; align-items:center; border-top: 1px solid #333; padding-top: 15px;">
                <div>
                    <span style="font-size: 1.8rem; font-weight: bold; color: var(--primary-green);">₹${rt.price_per_night}</span> <span style="font-size: 0.8rem; color:var(--text-muted);">/ night</span>
                </div>
                <div style="color: var(--text-muted);">
                    <i class="fa fa-user"></i> Max ${rt.capacity} Guests
                </div>
            </div>
            <div style="margin-top: 20px;">
                ${availableCount > 0 
                    ? `<button class="btn-primary" onclick="initiateBooking(${rt.id}, '${rt.name}', ${rt.price_per_night})">Reserve Now</button>`
                    : `<button class="btn-primary" style="background:#444; color:#888; cursor:not-allowed;" disabled>Sold Out</button>`
                }
            </div>
        `;
        container.appendChild(card);
    });
}

function initiateBooking(roomTypeId, roomName, price) {
    // We will show a booking modal and confirm the dates
    // For now we will check if user is logged in
    fetch('/accounts/api/profile/', { headers: { 'Content-Type': 'application/json' }})
        .then(res => {
            if(!res.ok) {
               alert("Please login to book a room!");
               showModal('login-modal');
               return;
            }
            // Proceed to booking modal (we'll implement this next)
            window.location.href = `/booking/new?room_type=${roomTypeId}`;
        })
        .catch(err => console.log(err));
}
