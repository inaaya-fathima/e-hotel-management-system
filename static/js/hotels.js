document.addEventListener('DOMContentLoaded', () => {
    loadHotels();
});

async function loadHotels(query = '') {
    const container = document.getElementById('hotels-container');
    if (!container) return; // Not on the index page
    
    container.innerHTML = '<div style="text-align:center; width: 100%;"><i class="fa fa-spinner fa-spin fa-3x" style="color: var(--primary-green);"></i></div>';
    
    try {
        const response = await fetch(`/hotels/api/hotels/?search=${query}`);
        const data = await response.json();
        renderHotels(data);
    } catch (error) {
        console.error('Error fetching hotels:', error);
        container.innerHTML = '<p style="text-align:center; color: red;">Failed to load hotels. Please try again.</p>';
    }
}

function renderHotels(hotels) {
    const container = document.getElementById('hotels-container');
    container.innerHTML = '';
    
    if (hotels.length === 0) {
        container.innerHTML = '<p style="text-align:center; width:100%;">No hotels found matching your criteria.</p>';
        return;
    }

    hotels.forEach(hotel => {
        const card = document.createElement('div');
        card.className = 'hotel-card modern-card';
        card.style.display = 'flex';
        card.style.flexDirection = 'column';
        card.style.cursor = 'pointer';
        
        const imgUrl = hotel.featured_image ? hotel.featured_image : '/static/images/default_hotel.jpg';
        
        let amenitiesHtml = hotel.amenities.map(a => 
            `<span style="background: rgba(0, 255, 136, 0.1); color: var(--primary-green); padding: 5px 10px; border-radius: 20px; font-size: 0.8rem; margin-right: 5px; margin-bottom: 8px; display: inline-block; border: 1px solid var(--primary-green);">
                <i class="${a.amenity.icon || 'fa fa-check'}"></i> ${a.amenity.name}
            </span>`
        ).join('');

        card.innerHTML = `
            <div style="height: 220px; background-color:#222; border-radius: 8px; overflow:hidden; position: relative;">
                <img src="${imgUrl}" style="width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s;" alt="${hotel.name}" onmouseover="this.style.transform='scale(1.1)';" onmouseout="this.style.transform='scale(1)';">
                <div style="position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.8); padding: 5px 12px; border-radius: 20px; font-weight: bold; color: var(--primary-green); border: 1px solid var(--primary-green);">
                    <i class="fa fa-star"></i> ${hotel.rating}
                </div>
            </div>
            <div style="padding: 20px 0 10px 0; flex-grow: 1; display: flex; flex-direction: column;">
                <h3 style="color: var(--text-light); margin-bottom: 10px; font-size: 1.4rem;">
                    ${hotel.name}
                </h3>
                <p style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 15px;">
                    <i class="fa fa-map-marker-alt" style="color: var(--primary-green);"></i> ${hotel.city}
                </p>
                <div style="margin-bottom: 20px;">
                    ${amenitiesHtml}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: auto;">
                    <div style="font-size: 1.1rem; color: var(--text-light); font-weight: bold;">
                        <span style="color: #888; font-size: 0.8rem; font-weight: normal;">From</span> ₹${hotel.price_per_night || 'Contact'} 
                    </div>
                    <button class="btn-primary" onclick="viewHotel(${hotel.id})" style="padding: 10px 20px; font-size: 0.9rem; max-width: max-content; margin: 0;">Details</button>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

function viewHotel(hotelId) {
    window.location.href = `/hotel/${hotelId}`;
}
