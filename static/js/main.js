/**
 * E-Hotel Management System — Global JS
 * Handles: flash alerts, wishlist, star ratings, animations
 */

document.addEventListener('DOMContentLoaded', () => {

  // ── Auto-dismiss flash alerts ──────────────────────
  document.querySelectorAll('.alert').forEach(alert => {
    const close = alert.querySelector('.alert-close');
    if (close) close.addEventListener('click', () => dismissAlert(alert));
    setTimeout(() => dismissAlert(alert), 5000);
  });

  function dismissAlert(el) {
    el.style.opacity = '0';
    el.style.transform = 'translateY(-10px)';
    el.style.transition = 'all .3s ease';
    setTimeout(() => el.remove(), 300);
  }

  // ── Mobile sidebar toggle ──────────────────────────
  const toggleBtn = document.getElementById('sidebarToggle');
  const sidebar   = document.querySelector('.sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }

  // ── Hamburger nav toggle ───────────────────────────
  const hamburger = document.querySelector('.hamburger');
  const navMenu   = document.querySelector('.navbar-nav');
  if (hamburger && navMenu) {
    hamburger.addEventListener('click', () => {
      navMenu.classList.toggle('open');
      navMenu.style.display = navMenu.style.display === 'flex' ? 'none' : 'flex';
      navMenu.style.flexDirection = 'column';
      navMenu.style.position = 'absolute';
      navMenu.style.top = '70px';
      navMenu.style.left = '0';
      navMenu.style.right = '0';
      navMenu.style.background = 'var(--bg2)';
      navMenu.style.padding = '16px';
      navMenu.style.borderBottom = '1px solid var(--border)';
    });
  }

  // ── Wishlist Toggle (AJAX) ─────────────────────────
  document.querySelectorAll('.wish-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const roomId = btn.dataset.roomId;
      try {
        const res  = await fetch(`/wishlist/toggle/${roomId}`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'added') {
          btn.classList.add('active');
          btn.innerHTML = '<i class="fas fa-heart"></i>';
          showToast('Added to wishlist!', 'success');
        } else {
          btn.classList.remove('active');
          btn.innerHTML = '<i class="far fa-heart"></i>';
          showToast('Removed from wishlist.', 'info');
        }
      } catch {
        showToast('Please login to use wishlist.', 'error');
      }
    });
  });

  // ── Star Rating Input ──────────────────────────────
  const starInputs = document.querySelectorAll('.star-input');
  starInputs.forEach(wrap => {
    const labels = [...wrap.querySelectorAll('label')].reverse();
    labels.forEach((label, i) => {
      label.addEventListener('mouseenter', () => {
        labels.forEach((l, j) => {
          l.style.color = j <= i ? 'var(--warning)' : 'var(--border)';
        });
      });
    });
    wrap.addEventListener('mouseleave', updateStarDisplay.bind(null, wrap));
    wrap.querySelectorAll('input').forEach(() => {
      updateStarDisplay(wrap);
    });
  });

  function updateStarDisplay(wrap) {
    const checked = wrap.querySelector('input:checked');
    const labels  = [...wrap.querySelectorAll('label')].reverse();
    const val     = checked ? parseInt(checked.value) : 0;
    labels.forEach((l, i) => {
      l.style.color = i < val ? 'var(--warning)' : 'var(--border)';
    });
  }

  // ── Intersection Observer (scroll animations) ──────
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        e.target.style.opacity = '1';
        e.target.style.transform = 'translateY(0)';
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.room-card, .stat-card, .card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity .5s ease, transform .5s ease';
    observer.observe(el);
  });

  // ── Particles (hero section) ───────────────────────
  const particlesEl = document.querySelector('.particles');
  if (particlesEl) createParticles(particlesEl);

  // ── Active Nav Link ────────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.navbar-nav a, .sidebar-nav-item').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // ── Confirm Delete ─────────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      if (!confirm(btn.dataset.confirm || 'Are you sure?')) {
        e.preventDefault();
      }
    });
  });

  // ── Modal System ──────────────────────────────────
  document.querySelectorAll('[data-modal]').forEach(trigger => {
    trigger.addEventListener('click', () => {
      const modal = document.getElementById(trigger.dataset.modal);
      if (modal) modal.classList.add('open');
    });
  });
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) overlay.classList.remove('open');
    });
  });
  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.modal-overlay').classList.remove('open');
    });
  });

}); // END DOMContentLoaded


// ── Toast Notification ────────────────────────────────
function showToast(message, type = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const icons = { success: 'fa-check-circle', error: 'fa-times-circle', info: 'fa-info-circle', warning: 'fa-exclamation-circle' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i> ${message}`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all .3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ── Create floating particles ──────────────────────────
function createParticles(container) {
  const count = 30;
  for (let i = 0; i < count; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.style.left = Math.random() * 100 + '%';
    p.style.animationDuration = (Math.random() * 10 + 8) + 's';
    p.style.animationDelay    = (Math.random() * 8) + 's';
    p.style.width  = p.style.height = (Math.random() * 3 + 1) + 'px';
    container.appendChild(p);
  }
}

// ── Format currency ────────────────────────────────────
function formatCurrency(amount) {
  return '₹' + parseFloat(amount).toLocaleString('en-IN');
}

// ── Confirmation form submit ───────────────────────────
function confirmAndSubmit(formId, message) {
  if (confirm(message)) {
    document.getElementById(formId).submit();
  }
}
