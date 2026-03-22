/**
 * ============================================================
 *  E-Hotel Management System — Global JavaScript
 *  File: static/js/main.js
 * ============================================================
 *
 *  This file runs on EVERY page of the website.
 *  It handles small interactive behaviors like:
 *    - Auto-dismissing flash alert messages
 *    - Mobile hamburger menu toggle
 *    - Wishlist heart button (AJAX toggle)
 *    - Star rating input hover effects
 *    - Scroll-in animations (cards fade in when visible)
 *    - Floating particles on the hero section
 *    - Confirming before delete actions
 *    - Modal popups (open/close)
 *
 *  It is loaded at the bottom of base.html, so it runs
 *  after all HTML elements are already on the page.
 */

// Wait until the entire page has loaded before running JavaScript
document.addEventListener('DOMContentLoaded', function () {


    // ----------------------------------------------------------
    // 1. Auto-dismiss flash alert messages
    // ----------------------------------------------------------
    // Flash messages (like "Booking successful!") disappear after 5 seconds.
    document.querySelectorAll('.alert').forEach(function (alertBox) {

        // Close when user clicks the X button
        var closeBtn = alertBox.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function () {
                dismissAlert(alertBox);
            });
        }

        // Auto-close after 5000 milliseconds (5 seconds)
        setTimeout(function () {
            dismissAlert(alertBox);
        }, 5000);
    });

    /**
     * Smoothly fades out and removes an alert element.
     * @param {HTMLElement} el - The alert element to dismiss
     */
    function dismissAlert(el) {
        el.style.opacity    = '0';
        el.style.transform  = 'translateY(-10px)';
        el.style.transition = 'all 0.3s ease';
        // Remove from page after the animation finishes
        setTimeout(function () { el.remove(); }, 300);
    }


    // ----------------------------------------------------------
    // 2. Mobile hamburger menu (navbar)
    // ----------------------------------------------------------
    var hamburgerBtn = document.querySelector('.hamburger');
    var navMenu      = document.querySelector('.navbar-nav');

    if (hamburgerBtn && navMenu) {
        hamburgerBtn.addEventListener('click', function () {
            // Toggle the nav menu open/closed on mobile
            var isOpen = navMenu.style.display === 'flex';
            navMenu.style.display      = isOpen ? 'none' : 'flex';
            navMenu.style.flexDirection = 'column';
            navMenu.style.position      = 'absolute';
            navMenu.style.top           = '70px';
            navMenu.style.left          = '0';
            navMenu.style.right         = '0';
            navMenu.style.background    = 'var(--bg2)';
            navMenu.style.padding       = '16px';
            navMenu.style.borderBottom  = '1px solid var(--border)';
        });
    }


    // ----------------------------------------------------------
    // 3. Admin sidebar mobile toggle
    // ----------------------------------------------------------
    var sidebarToggle = document.getElementById('sidebarToggle');
    var sidebar       = document.querySelector('.sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('open');
        });
    }


    // ----------------------------------------------------------
    // 4. Wishlist heart button (AJAX)
    // ----------------------------------------------------------
    // When a user clicks the heart button on a room card,
    // we send a request to the server to add/remove the wishlist entry.
    // The page does NOT reload — we update the button instantly.
    document.querySelectorAll('.wish-btn').forEach(function (btn) {
        btn.addEventListener('click', function (event) {
            event.preventDefault();
            event.stopPropagation(); // Don't trigger parent click events

            var roomId = btn.dataset.roomId; // Room ID from data-room-id="..."

            fetch('/wishlist/toggle/' + roomId, { method: 'POST' })
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    if (data.status === 'added') {
                        // Show filled heart
                        btn.classList.add('active');
                        btn.innerHTML = '<i class="fas fa-heart"></i>';
                        showToast('Added to wishlist!', 'success');
                    } else {
                        // Show empty heart
                        btn.classList.remove('active');
                        btn.innerHTML = '<i class="far fa-heart"></i>';
                        showToast('Removed from wishlist.', 'info');
                    }
                })
                .catch(function () {
                    showToast('Please login to use the wishlist.', 'error');
                });
        });
    });


    // ----------------------------------------------------------
    // 5. Star rating hover effects (review form)
    // ----------------------------------------------------------
    document.querySelectorAll('.star-input').forEach(function (starGroup) {
        // Get labels in reverse order (star 5 → star 1)
        var labels = Array.from(starGroup.querySelectorAll('label')).reverse();

        labels.forEach(function (label, index) {
            // Highlight stars on hover
            label.addEventListener('mouseenter', function () {
                labels.forEach(function (l, j) {
                    l.style.color = j <= index ? 'var(--warning)' : 'var(--border)';
                });
            });
        });

        // Reset to the selected star when mouse leaves
        starGroup.addEventListener('mouseleave', function () {
            updateStarDisplay(starGroup);
        });

        // Update display when a star is selected
        starGroup.querySelectorAll('input').forEach(function (input) {
            input.addEventListener('change', function () {
                updateStarDisplay(starGroup);
            });
        });
    });

    /** Updates star colors based on currently selected rating */
    function updateStarDisplay(starGroup) {
        var checkedInput = starGroup.querySelector('input:checked');
        var labels       = Array.from(starGroup.querySelectorAll('label')).reverse();
        var selectedVal  = checkedInput ? parseInt(checkedInput.value) : 0;

        labels.forEach(function (label, index) {
            label.style.color = index < selectedVal ? 'var(--warning)' : 'var(--border)';
        });
    }


    // ----------------------------------------------------------
    // 6. Scroll-in animations (cards fade up when scrolled into view)
    // ----------------------------------------------------------
    var animObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                // When element enters the viewport, make it visible
                entry.target.style.opacity   = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 }); // Trigger when 10% of the element is visible

    // Apply animation to room cards and stat cards
    document.querySelectorAll('.room-card, .stat-card, .card').forEach(function (el) {
        el.style.opacity    = '0';
        el.style.transform  = 'translateY(20px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        animObserver.observe(el);
    });


    // ----------------------------------------------------------
    // 7. Hero section floating particles
    // ----------------------------------------------------------
    var particlesContainer = document.querySelector('.particles');
    if (particlesContainer) {
        createParticles(particlesContainer);
    }


    // ----------------------------------------------------------
    // 8. Highlight the active navigation link
    // ----------------------------------------------------------
    var currentPath = window.location.pathname;
    document.querySelectorAll('.navbar-nav a, .sidebar-nav-item').forEach(function (link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });


    // ----------------------------------------------------------
    // 9. Confirm before deleting (data-confirm attribute)
    // ----------------------------------------------------------
    // Add data-confirm="Are you sure?" to any button/link to get a confirmation popup
    document.querySelectorAll('[data-confirm]').forEach(function (btn) {
        btn.addEventListener('click', function (event) {
            var message = btn.dataset.confirm || 'Are you sure?';
            if (!confirm(message)) {
                event.preventDefault(); // Cancel the action if user clicks "Cancel"
            }
        });
    });


    // ----------------------------------------------------------
    // 10. Modal system (open/close popups)
    // ----------------------------------------------------------

    // Open modal when clicking a trigger element with data-modal="modal-id"
    document.querySelectorAll('[data-modal]').forEach(function (trigger) {
        trigger.addEventListener('click', function () {
            var modalId = trigger.dataset.modal;
            var modal   = document.getElementById(modalId);
            if (modal) modal.classList.add('open');
        });
    });

    // Close modal when clicking outside the modal box
    document.querySelectorAll('.modal-overlay').forEach(function (overlay) {
        overlay.addEventListener('click', function (event) {
            if (event.target === overlay) {
                overlay.classList.remove('open');
            }
        });
    });

    // Close modal when clicking the X (close) button
    document.querySelectorAll('.modal-close').forEach(function (closeBtn) {
        closeBtn.addEventListener('click', function () {
            closeBtn.closest('.modal-overlay').classList.remove('open');
        });
    });

}); // END DOMContentLoaded


// ============================================================
// UTILITY FUNCTIONS (available globally on every page)
// ============================================================

/**
 * Shows a small toast notification in the bottom-right corner.
 *
 * @param {string} message - The text to show
 * @param {string} type - 'success', 'error', 'info', or 'warning'
 *
 * Example:
 *   showToast('Room added to wishlist!', 'success');
 */
function showToast(message, type) {
    type = type || 'info';

    // Create the toast container if it doesn't exist yet
    var container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // Icon based on type
    var icons = {
        success: 'fa-check-circle',
        error:   'fa-times-circle',
        info:    'fa-info-circle',
        warning: 'fa-exclamation-circle'
    };

    // Create the toast element
    var toast = document.createElement('div');
    toast.className = 'toast ' + type;
    toast.innerHTML = '<i class="fas ' + (icons[type] || icons.info) + '"></i> ' + message;
    container.appendChild(toast);

    // Fade out and remove after 3.5 seconds
    setTimeout(function () {
        toast.style.opacity    = '0';
        toast.style.transform  = 'translateX(20px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(function () { toast.remove(); }, 300);
    }, 3500);
}


/**
 * Creates floating particle dots for the hero section background.
 * @param {HTMLElement} container - The element to put particles in
 */
function createParticles(container) {
    for (var i = 0; i < 30; i++) {
        var particle = document.createElement('div');
        particle.className          = 'particle';
        particle.style.left             = (Math.random() * 100) + '%';
        particle.style.animationDuration = (Math.random() * 10 + 8) + 's';
        particle.style.animationDelay    = (Math.random() * 8) + 's';
        var size = (Math.random() * 3 + 1) + 'px';
        particle.style.width  = size;
        particle.style.height = size;
        container.appendChild(particle);
    }
}


/**
 * Formats a number as Indian Rupee currency.
 * @param {number} amount - The number to format
 * @returns {string} e.g. '₹2,500'
 */
function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toLocaleString('en-IN');
}


/**
 * Shows a confirmation popup and submits a form if the user confirms.
 *
 * @param {string} formId   - The ID of the form element to submit
 * @param {string} message  - The confirmation message to show
 *
 * Example (in HTML):
 *   <button onclick="confirmAndSubmit('deleteForm', 'Delete this room?')">Delete</button>
 */
function confirmAndSubmit(formId, message) {
    if (confirm(message)) {
        document.getElementById(formId).submit();
    }
}
