/**
 * E-Hotel — Premium Animation Engine
 * GSAP + Lenis smooth scroll + Custom cursor + Parallax + Reveal
 */

// ─────────────────────────────────────────────────────────────
// 1. PREMIUM LOADING SCREEN
// ─────────────────────────────────────────────────────────────
(function () {
  const screen = document.getElementById('loading-screen');
  if (!screen) return;
  const bar = document.getElementById('loadBar');
  const pct = document.getElementById('loadPct');
  let p = 0;

  const t = setInterval(() => {
    p = Math.min(92, p + Math.random() * 10 + 3);
    if (bar)  bar.style.width = Math.floor(p) + '%';
    if (pct)  pct.textContent  = Math.floor(p) + '%';
  }, 50);

  window.addEventListener('load', () => {
    clearInterval(t);
    if (bar) bar.style.width = '100%';
    if (pct) pct.textContent  = '100%';

    // Trigger door-open if present, else simple fade
    setTimeout(() => {
      screen.classList.add('doors-open');
      setTimeout(() => {
        screen.classList.add('fade-away');
        setTimeout(() => { screen.style.display = 'none'; }, 700);
      }, 1100);
    }, 350);
  });
})();


// ─────────────────────────────────────────────────────────────
// 2. SCROLL PROGRESS BAR
// ─────────────────────────────────────────────────────────────
(function () {
  const bar = document.getElementById('scroll-progress');
  if (!bar) return;
  window.addEventListener('scroll', () => {
    const scrollTop = window.scrollY;
    const docHeight  = document.documentElement.scrollHeight - window.innerHeight;
    const pct = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
    bar.style.width = pct + '%';
  }, { passive: true });
})();


// ─────────────────────────────────────────────────────────────
// 3. CUSTOM CURSOR
// ─────────────────────────────────────────────────────────────
// Custom cursor removed


// ─────────────────────────────────────────────────────────────
// 4. DOM READY
// ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {

  // ── 4a. Alert auto-dismiss ──────────────────────────────
  document.querySelectorAll('.alert').forEach(alertBox => {
    const closeBtn = alertBox.querySelector('.alert-close');
    if (closeBtn) closeBtn.addEventListener('click', () => dismissAlert(alertBox));
    setTimeout(() => dismissAlert(alertBox), 5000);
  });

  function dismissAlert(el) {
    el.style.opacity   = '0';
    el.style.transform = 'translateY(-10px)';
    el.style.transition = 'all 0.3s ease';
    setTimeout(() => el.remove(), 300);
  }

  // ── 4b. Mobile nav ─────────────────────────────────────
  const hamburgerBtn  = document.getElementById('hamburgerBtn');
  const mobileNav     = document.getElementById('mobileNav');
  const mobileOverlay = document.getElementById('mobileOverlay');
  const mobileClose   = document.getElementById('mobileNavClose');

  function openMobileNav()  { mobileNav?.classList.add('open');    mobileOverlay?.classList.add('open');    document.body.style.overflow = 'hidden'; }
  function closeMobileNav() { mobileNav?.classList.remove('open'); mobileOverlay?.classList.remove('open'); document.body.style.overflow = ''; }

  hamburgerBtn?.addEventListener('click', openMobileNav);
  mobileClose?.addEventListener('click',  closeMobileNav);
  mobileOverlay?.addEventListener('click', closeMobileNav);

  // ── 4c. Admin sidebar ──────────────────────────────────
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.sidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  }

  // ── 4d. Wishlist AJAX ──────────────────────────────────
  document.querySelectorAll('.wish-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      e.preventDefault(); e.stopPropagation();
      const roomId = btn.dataset.roomId;
      fetch('/wishlist/toggle/' + roomId, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
          if (data.status === 'added') {
            btn.classList.add('active');
            btn.innerHTML = '<i class="fas fa-heart"></i>';
            showToast('Added to wishlist!', 'success');
          } else {
            btn.classList.remove('active');
            btn.innerHTML = '<i class="far fa-heart"></i>';
            showToast('Removed from wishlist.', 'info');
          }
        })
        .catch(() => showToast('Please login to use the wishlist.', 'error'));
    });
  });

  // ── 4e. Star rating hover ──────────────────────────────
  document.querySelectorAll('.star-input').forEach(starGroup => {
    const labels = Array.from(starGroup.querySelectorAll('label')).reverse();
    labels.forEach((label, i) => {
      label.addEventListener('mouseenter', () => {
        labels.forEach((l, j) => { l.style.color = j <= i ? 'var(--accent)' : 'var(--border)'; });
      });
    });
    starGroup.addEventListener('mouseleave', () => updateStarDisplay(starGroup));
    starGroup.querySelectorAll('input').forEach(input => {
      input.addEventListener('change', () => updateStarDisplay(starGroup));
    });
  });

  function updateStarDisplay(starGroup) {
    const checked  = starGroup.querySelector('input:checked');
    const labels   = Array.from(starGroup.querySelectorAll('label')).reverse();
    const val      = checked ? parseInt(checked.value) : 0;
    labels.forEach((l, i) => { l.style.color = i < val ? 'var(--accent)' : 'var(--border)'; });
  }

  // ── 4f. Confirm delete ─────────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', e => {
      if (!confirm(btn.dataset.confirm || 'Are you sure?')) e.preventDefault();
    });
  });

  // ── 4g. Modal system ───────────────────────────────────
  document.querySelectorAll('[data-modal]').forEach(trigger => {
    trigger.addEventListener('click', () => {
      const modal = document.getElementById(trigger.dataset.modal);
      if (modal) { modal.classList.add('open'); }
    });
  });
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.classList.remove('open'); });
  });
  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => btn.closest('.modal-overlay')?.classList.remove('open'));
  });

  // ── 4h. Navbar shrink on scroll ────────────────────────
  const navbar = document.getElementById('mainNavbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.classList.toggle('scrolled', window.scrollY > 60);
    }, { passive: true });
  }

  // ── 4i. Navbar active link ─────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.navbar-nav > li > a, .sidebar-nav-item').forEach(link => {
    const href = link.getAttribute('href');
    if (href && (href === currentPath || (href !== '/' && currentPath.startsWith(href)))) {
      link.classList.add('active');
    }
  });

  // ── 4j. Hero particles ─────────────────────────────────
  const heroParticles = document.querySelector('.particles');
  if (heroParticles) createParticles(heroParticles);

  // ── 4k. Draggable horizontal scroll ────────────────────
  document.querySelectorAll('.h-scroll-track').forEach(track => {
    let isDown = false, startX = 0, scrollLeft = 0;
    track.addEventListener('mousedown', e => {
      isDown = true; track.style.cursor = 'grabbing';
      startX = e.pageX - track.offsetLeft;
      scrollLeft = track.scrollLeft;
    });
    track.addEventListener('mouseleave', () => { isDown = false; track.style.cursor = 'grab'; });
    track.addEventListener('mouseup',    () => { isDown = false; track.style.cursor = 'grab'; });
    track.addEventListener('mousemove',  e => {
      if (!isDown) return;
      e.preventDefault();
      const x   = e.pageX - track.offsetLeft;
      const walk = (x - startX) * 1.8;
      track.scrollLeft = scrollLeft - walk;
    });
  });

  // ── 4l. Intersection Observer for .reveal classes ──────
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale').forEach(el => {
    revealObserver.observe(el);
  });

  // ── 4m. Count-up animation ─────────────────────────────
  const countObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !entry.target.dataset.counted) {
        entry.target.dataset.counted = 'true';
        const target = parseInt(entry.target.dataset.target || entry.target.textContent);
        const suffix = entry.target.dataset.suffix || '';
        animateCount(entry.target, target, suffix);
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('.count-up').forEach(el => countObserver.observe(el));

  function animateCount(el, target, suffix) {
    const duration = 1800;
    const start = performance.now();
    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 4);
      el.textContent = Math.round(ease * target) + suffix;
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // ── 4n. Tilt effect on cards ───────────────────────────
  document.querySelectorAll('.tilt-card').forEach(card => {
    card.addEventListener('mousemove', e => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top  - rect.height / 2;
      const tiltX = (y / rect.height) * 10;
      const tiltY = -(x / rect.width) * 10;
      card.style.transform = `perspective(800px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) scale(1.02)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
      card.style.transition = 'transform 0.5s cubic-bezier(.25,.46,.45,.94)';
    });
  });


  // ─────────────────────────────────────────────────────
  // 5. GSAP + LENIS SETUP
  // ─────────────────────────────────────────────────────
  if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
    gsap.registerPlugin(ScrollTrigger);
    if (typeof ScrollToPlugin !== 'undefined') gsap.registerPlugin(ScrollToPlugin);

    // ── Lenis smooth scroll ──────────────────────────
    if (typeof Lenis !== 'undefined') {
      const lenis = new Lenis({
        duration: 1.4,
        easing: t => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        smooth: true,
        smoothTouch: false,
        touchMultiplier: 2,
      });
      function raf(time) { lenis.raf(time); requestAnimationFrame(raf); }
      requestAnimationFrame(raf);
      lenis.on('scroll', ScrollTrigger.update);
      gsap.ticker.add(time => lenis.raf(time * 1000));
      gsap.ticker.lagSmoothing(0, 0);

      // Smooth scroll for anchor links
      document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', e => {
          const target = document.querySelector(a.getAttribute('href'));
          if (target) { e.preventDefault(); lenis.scrollTo(target, { offset: -80, duration: 1.6 }); }
        });
      });
    }

    // ── Parallax hero bg ─────────────────────────────
    const heroBg = document.querySelector('.hero-bg');
    if (heroBg) {
      gsap.to(heroBg, {
        yPercent: 30,
        ease: 'none',
        scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: 1.5 }
      });
    }

    // ── Parallax + rotate images on scroll ───────────
    gsap.utils.toArray('.parallax-rotate').forEach(wrapper => {
      const img = wrapper.querySelector('img');
      if (!img) return;
      gsap.fromTo(img,
        { rotate: -4, scale: 1.1 },
        {
          rotate: 4, scale: 1.05,
          ease: 'none',
          scrollTrigger: {
            trigger: wrapper,
            start: 'top bottom',
            end: 'bottom top',
            scrub: 2
          }
        }
      );
    });

    // ── Parallax simple images ────────────────────────
    gsap.utils.toArray('.img-card img, .room-card-img img').forEach(img => {
      gsap.to(img, {
        yPercent: 12,
        ease: 'none',
        scrollTrigger: {
          trigger: img.parentElement,
          start: 'top bottom',
          end: 'bottom top',
          scrub: 1.2
        }
      });
    });

    // ── Stagger card reveals ──────────────────────────
    gsap.utils.toArray('.grid-3, .grid-4, .rooms-grid').forEach(grid => {
      const cards = grid.querySelectorAll('.card, .room-card, .img-card, .stat-card');
      if (!cards.length) return;
      gsap.from(cards, {
        y: 70, opacity: 0, duration: 0.9, stagger: 0.15,
        ease: 'power3.out',
        scrollTrigger: { trigger: grid, start: 'top 88%', toggleActions: 'play none none reverse' }
      });
    });

    // ── Horizontal slide for grid-2 ───────────────────
    gsap.utils.toArray('.grid-2').forEach(grid => {
      const children = [...grid.children];
      if (children.length < 2) return;
      gsap.from(children[0], {
        x: -60, opacity: 0, duration: 1, ease: 'power3.out',
        scrollTrigger: { trigger: grid, start: 'top 85%', toggleActions: 'play none none reverse' }
      });
      gsap.from(children[1], {
        x: 60, opacity: 0, duration: 1, delay: 0.1, ease: 'power3.out',
        scrollTrigger: { trigger: grid, start: 'top 85%', toggleActions: 'play none none reverse' }
      });
    });

    // ── Section header reveals ────────────────────────
    gsap.utils.toArray('.section-header').forEach(header => {
      gsap.from(header, {
        y: 50, opacity: 0, duration: 1, ease: 'power3.out',
        scrollTrigger: { trigger: header, start: 'top 88%', toggleActions: 'play none none reverse' }
      });
    });

    // ── Stats bar counters ────────────────────────────
    gsap.utils.toArray('.stat-card').forEach((card, i) => {
      gsap.from(card, {
        y: 40, opacity: 0, duration: 0.7, delay: i * 0.1, ease: 'power2.out',
        scrollTrigger: { trigger: card, start: 'top 92%', toggleActions: 'play none none reverse' }
      });
    });

    // ── Footer reveal ─────────────────────────────────
    const footer = document.querySelector('.footer');
    if (footer) {
      gsap.from('.footer-brand, .footer-links', {
        y: 40, opacity: 0, duration: 0.8, stagger: 0.12, ease: 'power2.out',
        scrollTrigger: { trigger: footer, start: 'top 95%', toggleActions: 'play none none reverse' }
      });
    }

    // ── SplitType headline animation (fast & classy) ──
    if (typeof SplitType !== 'undefined') {
      // Hero title — fast chars flying in from below
      document.querySelectorAll('.hero h1').forEach(el => {
        const split = new SplitType(el, { types: 'chars' });
        gsap.from(split.chars, {
          y: '110%',
          opacity: 0,
          rotateX: -80,
          duration: 0.55,
          stagger: 0.018,
          ease: 'back.out(2)',
          delay: 0.5,
        });
      });

      // Hero sub text — word by word, crisp
      document.querySelectorAll('.hero p, .hero .hero-tag').forEach(el => {
        const split = new SplitType(el, { types: 'words' });
        gsap.from(split.words, {
          y: 30, opacity: 0, duration: 0.5,
          stagger: 0.04, ease: 'power2.out', delay: 0.9,
        });
      });

      // Section headings — chars slide + fade
      document.querySelectorAll('.section-header h2').forEach(el => {
        const split = new SplitType(el, { types: 'chars' });
        gsap.from(split.chars, {
          y: '100%',
          opacity: 0,
          duration: 0.4,
          stagger: 0.015,
          ease: 'power4.out',
          scrollTrigger: {
            trigger: el,
            start: 'top 88%',
            toggleActions: 'play none none reverse'
          }
        });
      });
    }

    // ── Marquee infinite scroll ───────────────────────
    const marqueeTrack = document.querySelector('.marquee-track');
    if (marqueeTrack) {
      // Clone for seamless loop
      marqueeTrack.innerHTML += marqueeTrack.innerHTML;
    }

    // ── CTA banner parallax text ──────────────────────
    const ctaBanner = document.querySelector('[data-cta-banner]');
    if (ctaBanner) {
      gsap.from(ctaBanner.querySelectorAll('h2, p, a, .btn'), {
        y: 50, opacity: 0, duration: 0.8, stagger: 0.15, ease: 'power3.out',
        scrollTrigger: { trigger: ctaBanner, start: 'top 80%', toggleActions: 'play none none reverse' }
      });
    }

  } else {
    // Fallback
    document.querySelectorAll('.room-card, .stat-card, .card, .img-card').forEach(el => {
      el.style.opacity = '1';
    });
  }

});  // END DOMContentLoaded


// ─────────────────────────────────────────────────────────────
// 6. UTILITY FUNCTIONS
// ─────────────────────────────────────────────────────────────
function showToast(message, type) {
  type = type || 'info';
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const icons = { success: 'fa-check-circle', error: 'fa-times-circle', info: 'fa-info-circle', warning: 'fa-exclamation-circle' };
  const toast = document.createElement('div');
  toast.className = 'toast ' + type;
  toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i> ${message}`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity   = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function createParticles(container) {
  for (let i = 0; i < 24; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.style.left = (Math.random() * 100) + '%';
    p.style.animationDuration = (Math.random() * 14 + 8) + 's';
    p.style.animationDelay    = (Math.random() * 10) + 's';
    const sz = (Math.random() * 3 + 1) + 'px';
    p.style.width = sz; p.style.height = sz;
    container.appendChild(p);
  }
}

function formatCurrency(amount) {
  return '₹' + parseFloat(amount).toLocaleString('en-IN');
}

function confirmAndSubmit(formId, message) {
  if (confirm(message)) document.getElementById(formId).submit();
}
