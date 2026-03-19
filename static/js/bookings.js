const BOOKING_API = '/bookings/api/bookings';

async function openBookingModal(hotelId, roomTypeId, roomName, pricePerNight) {
    // Verify auth
    try {
        const res = await fetch('/accounts/api/profile/');
        if(!res.ok) {
            alert('Please login to continue booking.');
            showModal('login-modal');
            return;
        }
    } catch(e) { console.error(e); }

    document.getElementById('book-hotel-id').value = hotelId;
    document.getElementById('book-room-type-id').value = roomTypeId;
    document.getElementById('book-room-name').innerText = roomName;
    document.getElementById('book-price-info').innerText = `Price: ₹${pricePerNight} / night`;
    
    // Set min date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('book-checkin').setAttribute('min', today);
    document.getElementById('book-checkout').setAttribute('min', today);

    showModal('booking-modal');
}

document.getElementById('bookingForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        hotel_id: document.getElementById('book-hotel-id').value,
        room_type_id: document.getElementById('book-room-type-id').value,
        check_in: document.getElementById('book-checkin').value,
        check_out: document.getElementById('book-checkout').value,
        num_guests: document.getElementById('book-guests').value
    };

    try {
        const res = await fetch(`${BOOKING_API}/create/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if(res.ok) {
            alert(result.message);
            // Open Payment Modal
            hideModal('booking-modal');
            document.getElementById('pay-booking-id').value = result.booking_id;
            document.getElementById('pay-amount-display').innerText = `Total: ₹${result.total_price}`;
            showModal('payment-modal');
        } else {
            alert("Booking Error: " + (result.error || JSON.stringify(result)));
        }
    } catch(err) { console.error(err); }
});

document.getElementById('paymentForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        booking_id: document.getElementById('pay-booking-id').value,
        transaction_id: 'TXN_' + Math.floor(Math.random() * 1000000000)
    };

    try {
        const res = await fetch(`${BOOKING_API}/confirm-payment/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if(res.ok) {
            alert("Payment successful! Redirecting to your dashboard...");
            window.location.href = '/dashboard';
        } else {
            alert("Payment Failed: " + result.error);
        }
    } catch(err) { console.error(err); }
});
