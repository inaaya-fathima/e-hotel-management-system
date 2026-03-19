// Configuration
const API_URL = '/accounts/api';

// Utility: Setup CSRF for fetch requests
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Modal Mgt
function showModal(id) {
    document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none');
    document.getElementById(id).style.display = 'flex';
}
function hideModal(id) { document.getElementById(id).style.display = 'none'; }
function switchModal(closeId, openId) { hideModal(closeId); showModal(openId); }

// Close modals when clicking outside
window.addEventListener('click', (e) => {
    if(e.target.classList.contains('modal-overlay')) {
        e.target.style.display = 'none';
    }
});

// Handle Login Success (Redirect to dashboard / Reload)
function handleLoginSuccess(username) {
    document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none');
    updateNavState(true);
    // Optionally reload to update UI completely natively
    // window.location.reload();
}

// Signup Submission
document.getElementById('signupForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        username: document.getElementById('reg-username').value,
        email: document.getElementById('reg-email').value,
        phone: document.getElementById('reg-phone').value,
        password: document.getElementById('reg-password').value
    };
    
    try {
        const res = await fetch(`${API_URL}/register/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if(res.ok) {
            alert(`Registration successful. Your OTP is (Dev Mode): ${result.otp_debug}`);
            document.getElementById('otp-username').value = data.username;
            switchModal('signup-modal', 'otp-modal');
        } else {
            alert("Error: " + JSON.stringify(result));
        }
    } catch(err) { console.error(err); }
});

// Login Submission
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        username: document.getElementById('login-username').value,
        password: document.getElementById('login-password').value
    };
    try {
        const res = await fetch(`${API_URL}/login/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if(res.ok) {
            if(result.requires_otp) {
                alert(`OTP Sent! (Dev Mode): ${result.otp_debug}`);
                document.getElementById('otp-username').value = data.username;
                switchModal('login-modal', 'otp-modal');
            } else {
                handleLoginSuccess(result.user.username);
            }
        } else {
            alert("Login Failed: " + (result.error || "Invalid Credentials"));
        }
    } catch(err) { console.error(err); }
});

// OTP Submission
document.getElementById('otpForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        username: document.getElementById('otp-username').value,
        otp_code: document.getElementById('otp-code').value
    };
    try {
        const res = await fetch(`${API_URL}/verify-otp/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if(res.ok) {
            handleLoginSuccess(result.user.username);
        } else {
            alert("OTP Verification Failed: " + result.error);
        }
    } catch(err) { console.error(err); }
});

// Logout
async function logoutUser() {
    await fetch(`${API_URL}/logout/`, {method: 'POST', headers: {'X-CSRFToken': getCSRFToken()}});
    updateNavState(false);
    window.location.reload();
}

function updateNavState(isLoggedIn) {
    if(isLoggedIn) {
        document.getElementById('nav-login').style.display = 'none';
        document.getElementById('nav-signup').style.display = 'none';
        document.getElementById('nav-my-bookings').style.display = 'block';
        document.getElementById('nav-logout').style.display = 'block';
    } else {
        document.getElementById('nav-login').style.display = 'block';
        document.getElementById('nav-signup').style.display = 'block';
        document.getElementById('nav-my-bookings').style.display = 'none';
        document.getElementById('nav-logout').style.display = 'none';
    }
}
