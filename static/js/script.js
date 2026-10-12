/**
 * MediConnect Healthcare Management System - Core JavaScript
 * Handles validation, dynamic slot loading, modal interactions, and UX enhancements.
 */

document.addEventListener('DOMContentLoaded', function () {
  initMobileMenu();
  initAlertAutoDismiss();
  initIndianPhoneInputs();
  initRegistrationRoleSwitcher();
  initEditDoctorModal();
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
  // Registration Form (Patient and Doctor)
  const regForm = document.getElementById('registrationForm');
  if (regForm) {
    regForm.addEventListener('submit', function (e) {
      let isValid = true;
      clearFormErrors(regForm);

      const roleInput = regForm.querySelector('#roleInput');
      const isDoctor = roleInput && roleInput.value === 'doctor';

      const fullName = regForm.querySelector('#full_name');
      const email = regForm.querySelector('#email');
      const phone = regForm.querySelector('#phone');
      const pwd = regForm.querySelector('#password');
      const confirmPwd = regForm.querySelector('#confirm_password');

      if (!fullName.value.trim() || fullName.value.trim().length < 2) {
        showFieldError(fullName, 'Please enter your full legal name (minimum 2 characters).');
        isValid = false;
      }

      if (!validateEmail(email.value.trim())) {
        showFieldError(email, 'Please enter a valid email address.');
        isValid = false;
      }

      // Validate Indian mobile phone (+91) for both patient and doctor
      const phoneRes = validateIndianPhone(phone ? phone.value : '');
      if (!phoneRes.valid) {
        showFieldError(phone, phoneRes.message);
        isValid = false;
      }

      if (isDoctor) {
        const specSelect = regForm.querySelector('#specialization_id');
        if (!specSelect || !specSelect.value) {
          showFieldError(specSelect, 'Please select your medical specialization.');
          isValid = false;
        }

        const qual = regForm.querySelector('#qualification');
        if (!qual || !qual.value.trim()) {
          showFieldError(qual, 'Please provide your medical qualifications.');
          isValid = false;
        }
      } else {
        const dob = regForm.querySelector('#date_of_birth');
        if (dob && dob.value) {
          const birthDate = new Date(dob.value);
          const today = new Date();
          if (birthDate >= today) {
            showFieldError(dob, 'Date of birth must be in the past.');
            isValid = false;
          }
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

  // Admin Add Doctor Form (Register New Doctor Modal)
  const addDocForm = document.getElementById('adminAddDoctorForm');
  if (addDocForm) {
    addDocForm.addEventListener('submit', function (e) {
      let isValid = true;
      clearFormErrors(addDocForm);

      const fullName = addDocForm.querySelector('input[name="full_name"]');
      const email = addDocForm.querySelector('input[name="email"]');
      const phone = addDocForm.querySelector('#adminDocPhone');
      const specSelect = addDocForm.querySelector('select[name="specialization_id"]');
      const qual = addDocForm.querySelector('input[name="qualification"]');

      if (!fullName || !fullName.value.trim() || fullName.value.trim().length < 2) {
        showFieldError(fullName, 'Please enter doctor full name (min 2 characters).');
        isValid = false;
      }

      if (!email || !validateEmail(email.value.trim())) {
        showFieldError(email, 'Please enter a valid email address.');
        isValid = false;
      }

      const phoneRes = validateIndianPhone(phone ? phone.value : '');
      if (!phoneRes.valid) {
        showFieldError(phone, phoneRes.message);
        isValid = false;
      }

      if (!specSelect || !specSelect.value) {
        showFieldError(specSelect, 'Please select a specialization.');
        isValid = false;
      }

      if (!qual || !qual.value.trim()) {
        showFieldError(qual, 'Please provide doctor qualifications.');
        isValid = false;
      }

      if (!isValid) {
        e.preventDefault();
      }
    });
  }

  // Admin Edit Doctor Form
  const editDocForm = document.getElementById('adminEditDoctorForm');
  if (editDocForm) {
    editDocForm.addEventListener('submit', function (e) {
      let isValid = true;
      clearFormErrors(editDocForm);

      const fullName = editDocForm.querySelector('#editDocName');
      const phone = editDocForm.querySelector('#editDocPhone');
      const specSelect = editDocForm.querySelector('#editDocSpec');
      const qual = editDocForm.querySelector('#editDocQual');

      if (!fullName || !fullName.value.trim() || fullName.value.trim().length < 2) {
        showFieldError(fullName, 'Please enter doctor full name.');
        isValid = false;
      }

      if (phone && phone.value.trim()) {
        const phoneRes = validateIndianPhone(phone.value);
        if (!phoneRes.valid) {
          showFieldError(phone, phoneRes.message);
          isValid = false;
        }
      }

      if (!specSelect || !specSelect.value) {
        showFieldError(specSelect, 'Please select a specialization.');
        isValid = false;
      }

      if (!qual || !qual.value.trim()) {
        showFieldError(qual, 'Please provide doctor qualifications.');
        isValid = false;
      }

      if (!isValid) {
        e.preventDefault();
      }
    });
  }

  // User Profile Form
  const profileForm = document.getElementById('profileForm');
  if (profileForm) {
    profileForm.addEventListener('submit', function (e) {
      let isValid = true;
      clearFormErrors(profileForm);

      const fullName = profileForm.querySelector('#full_name');
      const phone = profileForm.querySelector('#phone');

      if (!fullName || !fullName.value.trim()) {
        showFieldError(fullName, 'Full name cannot be blank.');
        isValid = false;
      }

      if (phone && phone.classList.contains('indian-phone-field')) {
        const phoneRes = validateIndianPhone(phone.value);
        if (!phoneRes.valid) {
          showFieldError(phone, phoneRes.message);
          isValid = false;
        }
      }

      if (!isValid) {
        e.preventDefault();
      }
    });
  }

  // Appointment Booking Form
  const bookingForm = document.getElementById('appointmentBookingForm');
  if (bookingForm) {
    const docSelect = bookingForm.querySelector('#doctor_id');
    const specDetails = document.getElementById('selectedDocSpecDetails');
    const specName = document.getElementById('selectedDocSpecName');
    const specDesc = document.getElementById('selectedDocSpecDesc');

    function updateDocSpecialtyDisplay() {
      if (!docSelect || !specDetails) return;
      const opt = docSelect.options[docSelect.selectedIndex];
      if (opt && opt.getAttribute('data-spec')) {
        specName.innerText = opt.getAttribute('data-spec');
        specDesc.innerText = opt.getAttribute('data-desc') || 'Medical specialist consultation.';
        specDetails.style.display = 'block';
      } else {
        specDetails.style.display = 'none';
      }
    }

    if (docSelect) {
      docSelect.addEventListener('change', updateDocSpecialtyDisplay);
      updateDocSpecialtyDisplay();
    }

    bookingForm.addEventListener('submit', function (e) {
      let isValid = true;
      clearFormErrors(bookingForm);

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
  let container = inputElement.parentElement;
  if (container.classList.contains('phone-input-group')) {
    container = container.parentElement;
  }
  let feedback = container.querySelector('.invalid-feedback');
  if (!feedback) {
    feedback = document.createElement('div');
    feedback.className = 'invalid-feedback';
    container.appendChild(feedback);
  }
  feedback.innerText = message;
  feedback.style.display = 'block';
}

function clearFormErrors(form) {
  form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
  form.querySelectorAll('.invalid-feedback').forEach(el => {
    if (!el.classList.contains('slot-error')) el.remove();
  });
}

function validateEmail(email) {
  return /^[\w\.-]+@[\w\.-]+\.\w+$/.test(email);
}

function validatePhone(phone) {
  return /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/.test(phone);
}

function validateIndianPhone(phoneVal) {
  if (!phoneVal || !phoneVal.trim()) {
    return { valid: false, message: 'Mobile phone number is required.' };
  }
  const raw = phoneVal.trim();
  if (/[a-zA-Z]/.test(raw)) {
    return { valid: false, message: 'Phone number cannot contain letters.' };
  }
  let digits = raw.replace(/\D/g, '');
  if (digits.startsWith('91') && digits.length === 12) {
    digits = digits.slice(2);
  } else if (digits.startsWith('0') && digits.length === 11) {
    digits = digits.slice(1);
  }
  if (digits.length < 10) {
    return { valid: false, message: `Phone number is too short (${digits.length} digits). A valid Indian mobile number requires 10 digits.` };
  }
  if (digits.length > 10) {
    return { valid: false, message: `Phone number is too long (${digits.length} digits). A valid Indian mobile number requires 10 digits.` };
  }
  if (!['6', '7', '8', '9'].includes(digits.charAt(0))) {
    return { valid: false, message: 'Invalid Indian mobile number. Mobile numbers in India must start with 6, 7, 8, or 9.' };
  }
  return { valid: true, digits: digits, formatted: `+91 ${digits}` };
}

function initIndianPhoneInputs() {
  document.querySelectorAll('.indian-phone-field').forEach(input => {
    input.addEventListener('input', function () {
      let val = this.value;
      val = val.replace(/[^\d\s\-\+\(\)]/g, '');
      let digits = val.replace(/\D/g, '');
      if (digits.startsWith('91') && digits.length > 10) {
        digits = digits.slice(2);
      } else if (digits.startsWith('0') && digits.length > 10) {
        digits = digits.slice(1);
      }
      if (digits.length > 10) {
        digits = digits.slice(0, 10);
      }
      this.value = digits;

      const group = this.closest('.form-group');
      if (group) {
        const errorEl = group.querySelector('.phone-error-msg');
        if (digits.length > 0 && !['6', '7', '8', '9'].includes(digits.charAt(0))) {
          if (errorEl) {
            errorEl.innerText = 'Indian mobile numbers must start with 6, 7, 8, or 9.';
            errorEl.style.display = 'block';
          }
          this.classList.add('is-invalid');
        } else {
          if (errorEl) {
            errorEl.innerText = '';
            errorEl.style.display = 'none';
          }
          this.classList.remove('is-invalid');
        }
      }
    });

    input.addEventListener('paste', function () {
      setTimeout(() => {
        let digits = this.value.replace(/\D/g, '');
        if (digits.startsWith('91') && digits.length > 10) {
          digits = digits.slice(2);
        } else if (digits.startsWith('0') && digits.length > 10) {
          digits = digits.slice(1);
        }
        this.value = digits.slice(0, 10);
      }, 10);
    });
  });
}

function initEditDoctorModal() {
  document.querySelectorAll('.edit-doc-trigger').forEach(btn => {
    btn.addEventListener('click', function () {
      const form = document.getElementById('adminEditDoctorForm');
      if (!form) return;
      const actionUrl = this.getAttribute('data-action-url');
      if (actionUrl) form.setAttribute('action', actionUrl);

      const nameInput = document.getElementById('editDocName');
      const phoneInput = document.getElementById('editDocPhone');
      const specSelect = document.getElementById('editDocSpec');
      const qualInput = document.getElementById('editDocQual');
      const expInput = document.getElementById('editDocExp');
      const feeInput = document.getElementById('editDocFee');
      const bioInput = document.getElementById('editDocBio');

      if (nameInput) nameInput.value = this.getAttribute('data-doc-name') || '';
      let rawPhone = this.getAttribute('data-doc-phone') || '';
      let digits = rawPhone.replace(/\D/g, '');
      if (digits.startsWith('91') && digits.length > 10) digits = digits.slice(2);
      if (phoneInput) phoneInput.value = digits;
      if (specSelect) specSelect.value = this.getAttribute('data-doc-spec') || '';
      if (qualInput) qualInput.value = this.getAttribute('data-doc-qual') || '';
      if (expInput) expInput.value = this.getAttribute('data-doc-exp') || '0';
      if (feeInput) feeInput.value = this.getAttribute('data-doc-fee') || '50.00';
      if (bioInput) bioInput.value = this.getAttribute('data-doc-bio') || '';
    });
  });
}

function initRegistrationRoleSwitcher() {
  const regForm = document.getElementById('registrationForm');
  if (!regForm) return;

  const btnPatient = document.getElementById('btnRolePatient');
  const btnDoctor = document.getElementById('btnRoleDoctor');
  const roleInput = document.getElementById('roleInput');
  const doctorFields = document.getElementById('doctorFields');
  const patientFields = document.getElementById('patientFields');
  const pageTitle = document.querySelector('.form-title');
  const pageSubtitle = document.querySelector('.form-subtitle');
  const submitBtn = document.getElementById('registerSubmitBtn');
  const nameInput = document.getElementById('full_name');
  const emailInput = document.getElementById('email');
  const specSelect = document.getElementById('specialization_id');
  const qualInput = document.getElementById('qualification');

  function setRole(role) {
    if (role === 'doctor') {
      if (roleInput) roleInput.value = 'doctor';
      if (btnDoctor) {
        btnDoctor.classList.add('btn-primary');
        btnDoctor.classList.remove('btn-outline');
      }
      if (btnPatient) {
        btnPatient.classList.remove('btn-primary');
        btnPatient.classList.add('btn-outline');
      }
      if (doctorFields) doctorFields.style.display = 'block';
      if (patientFields) patientFields.style.display = 'none';
      if (pageTitle) pageTitle.textContent = 'Join as a Medical Physician';
      if (pageSubtitle) pageSubtitle.textContent = 'Register your clinical credentials to consult patients on MediConnect';
      if (submitBtn) submitBtn.textContent = 'Register as Physician';
      if (nameInput) nameInput.placeholder = 'e.g. Dr. Jane Smith';
      if (emailInput) emailInput.placeholder = 'doctor@carepoint.com';
      if (specSelect) specSelect.setAttribute('required', 'required');
      if (qualInput) qualInput.setAttribute('required', 'required');
    } else {
      if (roleInput) roleInput.value = 'patient';
      if (btnPatient) {
        btnPatient.classList.add('btn-primary');
        btnPatient.classList.remove('btn-outline');
      }
      if (btnDoctor) {
        btnDoctor.classList.remove('btn-primary');
        btnDoctor.classList.add('btn-outline');
      }
      if (doctorFields) doctorFields.style.display = 'none';
      if (patientFields) patientFields.style.display = 'block';
      if (pageTitle) pageTitle.textContent = 'Create Patient Account';
      if (pageSubtitle) pageSubtitle.textContent = 'Register to book and manage medical appointments online';
      if (submitBtn) submitBtn.textContent = 'Complete Registration';
      if (nameInput) nameInput.placeholder = 'e.g. Johnathan Doe';
      if (emailInput) emailInput.placeholder = 'patient@example.com';
      if (specSelect) specSelect.removeAttribute('required');
      if (qualInput) qualInput.removeAttribute('required');
    }
  }

  if (btnPatient) {
    btnPatient.addEventListener('click', function (e) {
      e.preventDefault();
      setRole('patient');
      if (window.history.replaceState) {
        window.history.replaceState(null, '', window.location.pathname + '?role=patient');
      }
    });
  }

  if (btnDoctor) {
    btnDoctor.addEventListener('click', function (e) {
      e.preventDefault();
      setRole('doctor');
      if (window.history.replaceState) {
        window.history.replaceState(null, '', window.location.pathname + '?role=doctor');
      }
    });
  }

  const urlParams = new URLSearchParams(window.location.search);
  const initialRole = urlParams.get('role') || (roleInput ? roleInput.value : 'patient');
  setRole(initialRole);
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
      const desc = card.getAttribute('data-desc') || '';
      const qual = card.getAttribute('data-qual') || '';

      if (name.includes(val) || spec.includes(val) || desc.includes(val) || qual.includes(val)) {
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
