/**
 * MediConnect Healthcare Management System - Core JavaScript
 * Handles validation, dynamic slot loading, modal interactions, and UX enhancements.
 */

document.addEventListener('DOMContentLoaded', function () {
  initMobileMenu();
  initAlertAutoDismiss();
  initFormValidations();
  initQuickFillButtons();
  initDynamicSlotLoader();
  initDoctorDirectoryFilter();
  initTabs();
  initModals();
});

/* =======================================================
   1. Mobile Navigation
   ======================================================= */
function initMobileMenu() {
  const toggleBtn = document.querySelector('.nav-toggle-btn');
  const navLinks = document.querySelector('.nav-links');

  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener('click', function () {
      navLinks.classList.toggle('open');
      const isOpen = navLinks.classList.contains('open');
      toggleBtn.setAttribute('aria-expanded', isOpen);
    });
  }
}

/* =======================================================
   2. Alert / Flash Auto-Dismiss
   ======================================================= */
function initAlertAutoDismiss() {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    // Manual close
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 250);
      });
    }

    // Auto dismiss after 6 seconds for success/info
    if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
      setTimeout(function () {
        if (alert && alert.parentElement) {
          alert.style.transition = 'opacity 0.4s ease';
          alert.style.opacity = '0';
          setTimeout(() => alert.remove(), 400);
        }
      }, 6000);
    }
  });
}

/* =======================================================
   3. Form Validation (Client-Side)
   ======================================================= */
function initFormValidations() {
  // Patient Registration Form
  const regForm = document.getElementById('registrationForm');
  if (regForm) {
    regForm.addEventListener('submit', function (e) {
      let isValid = true;
      clearFormErrors(regForm);

      const fullName = regForm.querySelector('#full_name');
      const email = regForm.querySelector('#email');
      const phone = regForm.querySelector('#phone');
      const pwd = regForm.querySelector('#password');
      const confirmPwd = regForm.querySelector('#confirm_password');
      const dob = regForm.querySelector('#date_of_birth');

      if (!fullName.value.trim() || fullName.value.trim().length < 2) {
        showFieldError(fullName, 'Please enter your full name (minimum 2 characters).');
        isValid = false;
      }

      if (!validateEmail(email.value.trim())) {
        showFieldError(email, 'Please enter a valid email address.');
        isValid = false;
      }

      if (phone && phone.value.trim() && !validatePhone(phone.value.trim())) {
        showFieldError(phone, 'Please enter a valid phone number format.');
        isValid = false;
      }

      if (dob && dob.value) {
        const birthDate = new Date(dob.value);
        const today = new Date();
        if (birthDate >= today) {
          showFieldError(dob, 'Date of birth must be in the past.');
          isValid = false;
        }
      }

      if (!pwd.value || pwd.value.length < 6) {
        showFieldError(pwd, 'Password must be at least 6 characters long.');
        isValid = false;
      }

      if (pwd.value !== confirmPwd.value) {
        showFieldError(confirmPwd, 'Passwords do not match.');
        isValid = false;
      }

      if (!isValid) {
        e.preventDefault();
      }
    });
  }

  // Appointment Booking Form
  const bookingForm = document.getElementById('appointmentBookingForm');
  if (bookingForm) {
    bookingForm.addEventListener('submit', function (e) {
      let isValid = true;
      clearFormErrors(bookingForm);

      const docSelect = bookingForm.querySelector('#doctor_id');
      const aptDate = bookingForm.querySelector('#appointment_date');
      const aptTime = bookingForm.querySelector('#appointment_time');
      const reason = bookingForm.querySelector('#reason');

      if (!docSelect || !docSelect.value) {
        showFieldError(docSelect, 'Please select a doctor.');
        isValid = false;
      }

      if (!aptDate || !aptDate.value) {
        showFieldError(aptDate, 'Please select an appointment date.');
        isValid = false;
      } else {
        const selectedDate = new Date(aptDate.value + 'T00:00:00');
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        if (selectedDate < today) {
          showFieldError(aptDate, 'Appointment date cannot be in the past.');
          isValid = false;
        }
      }

      if (!aptTime || !aptTime.value) {
        const slotBox = document.getElementById('slotContainer');
        if (slotBox) {
          let err = slotBox.querySelector('.slot-error');
          if (!err) {
            err = document.createElement('div');
            err.className = 'invalid-feedback slot-error';
            err.innerText = 'Please pick an available time slot from the list above.';
            slotBox.appendChild(err);
          }
        }
        isValid = false;
      }

      if (!reason || reason.value.trim().length < 5) {
        showFieldError(reason, 'Please specify a consultation reason (at least 5 characters).');
        isValid = false;
      }

      if (!isValid) {
        e.preventDefault();
      }
    });
  }

  // Contact Form
  const contactForm = document.getElementById('contactForm');
  if (contactForm) {
    contactForm.addEventListener('submit', function (e) {
      let isValid = true;
      clearFormErrors(contactForm);

      const name = contactForm.querySelector('#name');
      const email = contactForm.querySelector('#email');
      const subject = contactForm.querySelector('#subject');
      const message = contactForm.querySelector('#message');

      if (!name.value.trim()) {
        showFieldError(name, 'Name is required.');
        isValid = false;
      }

      if (!validateEmail(email.value.trim())) {
        showFieldError(email, 'Please enter a valid email address.');
        isValid = false;
      }

      if (!subject.value.trim()) {
        showFieldError(subject, 'Subject is required.');
        isValid = false;
      }

      if (!message.value.trim() || message.value.trim().length < 10) {
        showFieldError(message, 'Message must be at least 10 characters.');
        isValid = false;
      }

      if (!isValid) {
        e.preventDefault();
      }
    });
  }
}

function showFieldError(inputElement, message) {
  if (!inputElement) return;
  inputElement.classList.add('is-invalid');
  const parent = inputElement.parentElement;
  let feedback = parent.querySelector('.invalid-feedback');
  if (!feedback) {
    feedback = document.createElement('div');
    feedback.className = 'invalid-feedback';
    parent.appendChild(feedback);
  }
  feedback.innerText = message;
}

function clearFormErrors(form) {
  form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
  form.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
}

function validateEmail(email) {
  return /^[\w\.-]+@[\w\.-]+\.\w+$/.test(email);
}

function validatePhone(phone) {
  return /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/.test(phone);
}

/* =======================================================
   4. Quick Fill Credentials (Demo convenience)
   ======================================================= */
function initQuickFillButtons() {
  const quickBtns = document.querySelectorAll('.quick-fill-chip');
  if (!quickBtns.length) return;

  const emailInput = document.getElementById('email');
  const pwdInput = document.getElementById('password');

  quickBtns.forEach(btn => {
    btn.addEventListener('click', function () {
      const email = this.getAttribute('data-email');
      const pwd = this.getAttribute('data-password');

      if (emailInput && pwdInput) {
        emailInput.value = email;
        pwdInput.value = pwd;
        emailInput.focus();
        emailInput.classList.remove('is-invalid');
        pwdInput.classList.remove('is-invalid');
      }
    });
  });
}

/* =======================================================
   5. Dynamic Slot Loader (AJAX)
   ======================================================= */
function initDynamicSlotLoader() {
  const docSelect = document.getElementById('doctor_id');
  const dateInput = document.getElementById('appointment_date');
  const slotContainer = document.getElementById('slotContainer');
  const slotGrid = document.getElementById('slotsGrid');
  const timeHiddenInput = document.getElementById('appointment_time');

  if (!docSelect || !dateInput || !slotGrid) return;

  // Set min date on dateInput to today
  const todayStr = new Date().toISOString().split('T')[0];
  dateInput.setAttribute('min', todayStr);

  function fetchSlots() {
    const docId = docSelect.value;
    const dateVal = dateInput.value;

    // Reset selected slot
    if (timeHiddenInput) timeHiddenInput.value = '';

    if (!docId || !dateVal) {
      slotGrid.innerHTML = '<div class="slot-empty-msg">Select both a doctor and a date to view available appointment slots.</div>';
      return;
    }

    slotGrid.innerHTML = `
      <div class="slot-empty-msg" style="display:flex;align-items:center;justify-content:center;gap:0.5rem;">
        <span class="spinner" style="display:inline-block;width:18px;height:18px;border:2px solid var(--primary);border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;"></span>
        Checking doctor schedule...
      </div>
    `;

    fetch(`/api/doctor-slots?doctor_id=${encodeURIComponent(docId)}&date=${encodeURIComponent(dateVal)}`)
      .then(res => res.json())
      .then(data => {
        if (!data.success) {
          slotGrid.innerHTML = `<div class="slot-empty-msg" style="color:var(--status-cancelled);">${data.error || 'Failed to load slots.'}</div>`;
          return;
        }

        if (!data.slots || data.slots.length === 0) {
          slotGrid.innerHTML = `<div class="slot-empty-msg">${data.message || 'No available slots for this date. Please try another date or doctor.'}</div>`;
          return;
        }

        slotGrid.innerHTML = '';
        data.slots.forEach(slot => {
          const pill = document.createElement('div');
          pill.className = `slot-pill ${slot.available ? '' : 'disabled'}`;
          pill.innerText = formatTimeDisplay(slot.time);
          pill.setAttribute('data-time', slot.time);

          if (slot.available) {
            pill.addEventListener('click', function () {
              slotGrid.querySelectorAll('.slot-pill').forEach(p => p.classList.remove('selected'));
              pill.classList.add('selected');
              if (timeHiddenInput) {
                timeHiddenInput.value = slot.time;
              }
              const err = slotContainer.querySelector('.slot-error');
              if (err) err.remove();
            });
          } else {
            pill.title = 'Slot is already booked';
          }

          slotGrid.appendChild(pill);
        });
      })
      .catch(err => {
        console.error('Slot fetch error:', err);
        slotGrid.innerHTML = '<div class="slot-empty-msg" style="color:var(--status-cancelled);">Error connecting to schedule server.</div>';
      });
  }

  docSelect.addEventListener('change', fetchSlots);
  dateInput.addEventListener('change', fetchSlots);

  // If already pre-filled
  if (docSelect.value && dateInput.value) {
    fetchSlots();
  }
}

function formatTimeDisplay(timeStr) {
  // Convert 24h "14:30" to "02:30 PM"
  const [h, m] = timeStr.split(':');
  let hours = parseInt(h, 10);
  const ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12;
  hours = hours ? hours : 12;
  const hoursStr = hours < 10 ? '0' + hours : hours;
  return `${hoursStr}:${m} ${ampm}`;
}

/* =======================================================
   6. Live Search & Filter (Doctors Page)
   ======================================================= */
function initDoctorDirectoryFilter() {
  const searchInput = document.getElementById('doctorLiveSearch');
  const docCards = document.querySelectorAll('.doctor-card-item');

  if (!searchInput || !docCards.length) return;

  searchInput.addEventListener('input', function () {
    const val = this.value.toLowerCase().trim();
    docCards.forEach(card => {
      const name = card.getAttribute('data-name') || '';
      const spec = card.getAttribute('data-spec') || '';
      const qual = card.getAttribute('data-qual') || '';

      if (name.includes(val) || spec.includes(val) || qual.includes(val)) {
        card.style.display = 'flex';
      } else {
        card.style.display = 'none';
      }
    });
  });
}

/* =======================================================
   7. Tabs Component
   ======================================================= */
function initTabs() {
  const tabContainers = document.querySelectorAll('.tab-container');
  tabContainers.forEach(container => {
    const btns = container.querySelectorAll('.tab-btn');
    const panes = container.querySelectorAll('.tab-pane');

    btns.forEach(btn => {
      btn.addEventListener('click', function () {
        const targetId = this.getAttribute('data-target');

        btns.forEach(b => b.classList.remove('active'));
        panes.forEach(p => p.classList.remove('active'));

        this.classList.add('active');
        const targetPane = container.querySelector(targetId);
        if (targetPane) {
          targetPane.classList.add('active');
        }
      });
    });
  });
}

/* =======================================================
   8. Modal Dialogs
   ======================================================= */
function initModals() {
  // Open modal buttons
  document.querySelectorAll('[data-modal-target]').forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const modalId = this.getAttribute('data-modal-target');
      const modal = document.querySelector(modalId);
      if (modal) {
        // Pass any dynamic data from button attributes
        const actionUrl = this.getAttribute('data-action-url');
        const modalForm = modal.querySelector('form');
        if (actionUrl && modalForm) {
          modalForm.setAttribute('action', actionUrl);
        }

        // Prepopulate fields if present
        const titleText = this.getAttribute('data-modal-title');
        if (titleText) {
          const titleEl = modal.querySelector('.modal-title');
          if (titleEl) titleEl.innerText = titleText;
        }

        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
      }
    });
  });

  // Close buttons and backdrop clicks
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    const closeBtns = modal.querySelectorAll('.modal-close-btn, [data-modal-close]');
    closeBtns.forEach(btn => {
      btn.addEventListener('click', function () {
        closeModal(modal);
      });
    });

    modal.addEventListener('click', function (e) {
      if (e.target === modal) {
        closeModal(modal);
      }
    });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      const openModal = document.querySelector('.modal-backdrop.show');
      if (openModal) closeModal(openModal);
    }
  });
}

function closeModal(modal) {
  modal.classList.remove('show');
  document.body.style.overflow = '';
}

// Add CSS keyframe for spinner dynamically
const styleTag = document.createElement('style');
styleTag.innerHTML = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;
document.head.appendChild(styleTag);
