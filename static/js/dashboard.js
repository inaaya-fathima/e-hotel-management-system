document.addEventListener('DOMContentLoaded', () => {
    loadUserProfile();
    loadUserBookings();
});

async function loadUserProfile() {
    try {
        const res = await fetch('/accounts/api/profile/');
        if (!res.ok) {
            window.location.href = '/'; // Redirect to home if not logged in
            return;
        }
        const user = await res.json();
        
        const container = document.getElementById('profile-container');
        container.innerHTML = `
            <p><strong>Name:</strong> ${user.first_name || ''} ${user.last_name || ''}</p>
            <p><strong>Username:</strong> ${user.username}</p>
            <p><strong>Email:</strong> ${user.email}</p>
            <p><strong>Phone:</strong> ${user.phone || 'N/A'}</p>
            <p><strong>Address:</strong> ${user.address || 'N/A'}</p>
        `;
    } catch(err) { console.error(err); }
}

async function loadUserBookings() {
    try {
        const res = await fetch('/bookings/api/bookings/my-bookings/');
        const container = document.getElementById('bookings-container');
        
        if (!res.ok) {
            container.innerHTML = '<p style="color:red;">Error loading bookings.</p>';
            return;
        }
        const bookings = await res.json();
        
        if (bookings.length === 0) {
            container.innerHTML = '<p>You have no recent bookings.</p>';
            return;
        }

        let html = '<table style="width: 100%; border-collapse: collapse;">';
        html += '<tr style="background: rgba(0,255,136,0.1); text-align: left; color: var(--primary-green); border-bottom: 2px solid #333;">';
        html += '<th style="padding: 15px 10px;">Booking ID</th>';
        html += '<th style="padding: 15px 10px;">Hotel</th>';
        html += '<th style="padding: 15px 10px;">Check In/Out</th>';
        html += '<th style="padding: 15px 10px;">Status</th>';
        html += '<th style="padding: 15px 10px;">Price</th>';
        html += '</tr>';

        bookings.forEach(b => {
            const statusColor = b.status === 'CONFIRMED' ? 'var(--primary-green)' : (b.status === 'CANCELLED' ? '#ff4d4d' : 'orange');
            html += `<tr style="border-bottom: 1px solid #333; transition: background 0.3s;" onmouseover="this.style.background='rgba(255,255,255,0.05)'" onmouseout="this.style.background='transparent'">
                <td style="padding: 15px 10px;">#${b.id}</td>
                <td style="padding: 15px 10px;">${b.hotel_name}<br><small style="color: var(--text-muted);">Room: ${b.room_number}</small></td>
                <td style="padding: 15px 10px;">${b.check_in} <br><small style="color: var(--text-muted);">to</small> ${b.check_out}</td>
                <td style="padding: 15px 10px; color: ${statusColor}; font-weight: bold;">${b.status}</td>
                <td style="padding: 15px 10px;">₹${b.total_price}</td>
            </tr>`;
        });
        
        html += '</table>';
        container.innerHTML = html;
        
    } catch(err) { console.error(err); }
}
