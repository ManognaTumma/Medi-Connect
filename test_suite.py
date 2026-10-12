import re
import unittest
from app import app, validate_and_normalize_indian_phone
import db

class SystemVerificationTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_all_15_specializations_in_database(self):
        """1. Verify that all 15 specializations exist in MySQL with exact names and descriptions."""
        expected_specializations = [
            ("Dermatologist", "Skin, hair, and nail specialist."),
            ("Cardiologist", "Heart and blood vessel specialist."),
            ("Gynecologist/Obstetrician", "Women's reproductive health and pregnancy specialist."),
            ("Dentist", "Teeth and jaw bone specialist."),
            ("Ophthalmologist", "Eye and vision specialist."),
            ("Orthopedist (Orthopedic Surgeon)", "Bones, joints, muscles, and musculoskeletal system specialist."),
            ("Anesthesiologist", "Pain management and anesthesia specialist during surgery."),
            ("Endocrinologist", "Hormone imbalances, diabetes, and thyroid disease specialist."),
            ("Gastroenterologist", "Digestive system and stomach specialist."),
            ("Hematologist", "Blood and bone marrow specialist."),
            ("Neurologist", "Brain, spine, nerves, and nervous system specialist."),
            ("Pediatrician", "Infants, children, and adolescents' physician."),
            ("Oncologist", "Cancer diagnosis and treatment specialist."),
            ("Nephrologist", "Kidney care and kidney disease specialist."),
            ("Psychiatrist", "Mental health and emotional disorders specialist.")
        ]

        rows = db.query_db("SELECT specialization_id, specialization_name, description FROM specializations")
        self.assertEqual(len(rows), 15, f"Expected 15 specializations, found {len(rows)}")

        db_spec_dict = {r['specialization_name']: r['description'] for r in rows}
        for name, desc in expected_specializations:
            self.assertIn(name, db_spec_dict, f"Missing specialization in DB: {name}")
            self.assertEqual(db_spec_dict[name], desc, f"Description mismatch for {name}: got '{db_spec_dict[name]}' vs expected '{desc}'")
        print("\n[PASS] All 15 specializations and descriptions verified in MySQL database.")

    def test_02_indian_phone_validation_and_normalization(self):
        """2. Test valid and invalid Indian mobile numbers and confirm +91 prefix is never duplicated."""
        # Valid cases
        valid_cases = [
            ("9876543210", "+91 9876543210"),
            ("+91 9876543210", "+91 9876543210"),
            ("+919876543210", "+91 9876543210"),
            ("+91 +91 9876543210", "+91 9876543210"), # Duplicate input cleaned!
            ("09876543210", "+91 9876543210"),
            ("919876543210", "+91 9876543210"),
            ("98765-43210", "+91 9876543210"),
            ("8765432109", "+91 8765432109"),
            ("7890123456", "+91 7890123456"),
            ("6789012345", "+91 6789012345"),
        ]
        for inp, expected in valid_cases:
            valid, norm, err = validate_and_normalize_indian_phone(inp)
            self.assertTrue(valid, f"Failed for valid input: {inp} - {err}")
            self.assertEqual(norm, expected, f"Normalization error for {inp}: got {norm}")
            # Ensure +91 is not duplicated
            self.assertEqual(norm.count("+91"), 1, f"+91 duplicated in: {norm}")

        # Invalid cases
        invalid_cases = [
            ("5551234567", "must start with 6, 7, 8, or 9"),
            ("987654321", "too short"),
            ("98765432101", "too long"),
            ("98765abc10", "letters"),
            ("+1 5550100001", "Only Indian"),
            ("", "required")
        ]
        for inp, err_fragment in invalid_cases:
            valid, norm, err = validate_and_normalize_indian_phone(inp)
            self.assertFalse(valid, f"Should have failed for invalid input: {inp}")
            self.assertIn(err_fragment.lower(), err.lower(), f"Expected '{err_fragment}' in error: {err}")
        print("\n[PASS] Indian phone validation & normalization verified (+91 never duplicated).")

    def test_03_doctors_directory_and_filtering(self):
        """3. Test specialization filtering and descriptions on the doctor listing page."""
        response = self.client.get('/doctors')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        # Check all 15 specializations appear in filter dropdown
        rows = db.query_db("SELECT specialization_id, specialization_name FROM specializations")
        for r in rows:
            self.assertIn(r['specialization_name'], html, f"Specialization {r['specialization_name']} not in filter")

        # Test filtering by Cardiologist (id=1)
        cardiologist_id = [r['specialization_id'] for r in rows if r['specialization_name'] == 'Cardiologist'][0]
        filter_resp = self.client.get(f'/doctors?specialization={cardiologist_id}')
        self.assertEqual(filter_resp.status_code, 200)
        f_html = filter_resp.data.decode('utf-8')
        self.assertIn("Filtered by Cardiologist", f_html)
        self.assertIn("Heart and blood vessel specialist.", f_html)
        self.assertIn("Dr. Sarah Jenkins", f_html)
        # Doctor Michael Chen (Neurologist) should not be in the filtered cards
        self.assertNotIn("Dr. Michael Chen", f_html)

        print("\n[PASS] Doctor directory page and specialization filtering verified.")

    def test_04_doctor_registration_with_all_15_specializations(self):
        """4. Test registering a doctor for each of the 15 specializations and verifying MySQL storage."""
        # Login as admin to use admin doctor registration
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_role'] = 'admin'
            sess['csrf_token'] = 'test_token'

        specs = db.query_db("SELECT specialization_id, specialization_name FROM specializations ORDER BY specialization_id ASC")

        for idx, s in enumerate(specs):
            spec_id = s['specialization_id']
            spec_name = s['specialization_name']
            email = f"test_doctor_{spec_id}@clinic.test"
            raw_phone = f"+91 98765{idx:05d}"
            expected_phone = f"+91 98765{idx:05d}"

            # Clean previous test run if any
            db.query_db("DELETE FROM users WHERE email = %s", (email,), commit=True)

            resp = self.client.post('/admin/doctor/add', data={
                'csrf_token': 'test_token',
                'full_name': f"Dr. Specialist {spec_id}",
                'email': email,
                'phone': raw_phone,
                'specialization_id': spec_id,
                'qualification': 'MBBS, MD Specialist',
                'experience': 8,
                'consultation_fee': 100.00,
                'biography': f"Clinical specialist in {spec_name}",
                'password': 'Doctor@123'
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            # Verify in DB
            user = db.query_db("SELECT * FROM users WHERE email = %s", (email,), one=True)
            self.assertIsNotNone(user, f"User was not created for spec {spec_name}")
            self.assertEqual(user['phone'], expected_phone, f"Phone mismatch for {spec_name}: {user['phone']}")
            self.assertEqual(user['role'], 'doctor')

            doc = db.query_db("SELECT * FROM doctors WHERE user_id = %s", (user['user_id'],), one=True)
            self.assertIsNotNone(doc, f"Doctor profile was not created for spec {spec_name}")
            self.assertEqual(doc['specialization_id'], spec_id)

            # Clean up test doctor
            db.query_db("DELETE FROM users WHERE user_id = %s", (user['user_id'],), commit=True)

        print("\n[PASS] Doctor registration tested successfully for all 15 specializations with normalized +91 phone.")

    def test_05_doctor_registration_phone_rejection(self):
        """5. Test that invalid Indian phone numbers are rejected in doctor registration."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_role'] = 'admin'
            sess['csrf_token'] = 'test_token'

        invalid_phones = [
            "1234567890",   # Starts with 1
            "98765",        # Too short
            "987654321012", # Too long
            "98765ABCD0",   # Letters
        ]

        for bad_phone in invalid_phones:
            email = "bad_phone_test@clinic.test"
            db.query_db("DELETE FROM users WHERE email = %s", (email,), commit=True)

            resp = self.client.post('/admin/doctor/add', data={
                'csrf_token': 'test_token',
                'full_name': "Dr. Invalid Phone",
                'email': email,
                'phone': bad_phone,
                'specialization_id': 1,
                'qualification': 'MD',
                'password': 'Doctor@123'
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            user = db.query_db("SELECT * FROM users WHERE email = %s", (email,), one=True)
            self.assertIsNone(user, f"Registration should have failed for invalid phone: {bad_phone}")

        print("\n[PASS] Invalid Indian mobile numbers correctly rejected by doctor registration.")

    def test_06_existing_accounts_and_logins_work(self):
        """6. Verify that existing patients, doctors, appointments, and logins continue to work."""
        # 1. Admin login
        self.client.get('/logout')
        admin_resp = self.client.post('/login', data={
            'csrf_token': 'test_token',
            'email': 'admin@carepoint.com',
            'password': 'Admin@123'
        }, follow_redirects=True)
        self.assertEqual(admin_resp.status_code, 200)
        self.assertIn("System Administrator", admin_resp.data.decode('utf-8'))

        # 2. Doctor login
        self.client.get('/logout')
        doc_resp = self.client.post('/login', data={
            'csrf_token': 'test_token',
            'email': 'sarah.jenkins@carepoint.com',
            'password': 'Doctor@123'
        }, follow_redirects=True)
        self.assertEqual(doc_resp.status_code, 200)
        doc_html = doc_resp.data.decode('utf-8')
        self.assertIn("Physician Portal", doc_html)
        self.assertIn("Cardiologist", doc_html)

        # 3. Patient login
        self.client.get('/logout')
        pat_resp = self.client.post('/login', data={
            'csrf_token': 'test_token',
            'email': 'patient@carepoint.com',
            'password': 'Patient@123'
        }, follow_redirects=True)
        self.assertEqual(pat_resp.status_code, 200)
        self.assertIn("Patient Dashboard", pat_resp.data.decode('utf-8'))

        # 4. Patient booking page
        booking_resp = self.client.get('/book-appointment')
        self.assertEqual(booking_resp.status_code, 200)
        b_html = booking_resp.data.decode('utf-8')
        self.assertIn("Dr. Sarah Jenkins", b_html)
        self.assertIn("Cardiologist", b_html)

        print("\n[PASS] Existing patients, doctors, appointments, and logins function properly.")

    def test_07_public_doctor_registration_and_profile_update(self):
        """7. Test public doctor registration and doctor profile updating specialization & phone."""
        email = "dr_public@clinic.test"
        db.query_db("DELETE FROM users WHERE email = %s", (email,), commit=True)

        self.client.get('/logout')
        resp = self.client.post('/register', data={
            'csrf_token': 'test_token',
            'role': 'doctor',
            'full_name': 'Dr. Public Test',
            'email': email,
            'phone': '9812345678',
            'specialization_id': 7, # Dentist
            'qualification': 'BDS, MDS Oral Surgery',
            'experience': 7,
            'consultation_fee': 60.00,
            'biography': 'Specialist in cosmetic and restorative dentistry.',
            'password': 'Password@123',
            'confirm_password': 'Password@123'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        u = db.query_db("SELECT * FROM users WHERE email = %s", (email,), one=True)
        self.assertIsNotNone(u)
        self.assertEqual(u['phone'], '+91 9812345678')

        doc = db.query_db("SELECT * FROM doctors WHERE user_id = %s", (u['user_id'],), one=True)
        self.assertIsNotNone(doc)
        self.assertEqual(doc['specialization_id'], 7)

        # Update profile: change to Ophthalmologist (id 8) and update phone
        with self.client.session_transaction() as sess:
            sess['user_id'] = u['user_id']
            sess['user_role'] = 'doctor'
            sess['doctor_id'] = doc['doctor_id']
            sess['csrf_token'] = 'test_token'

        p_resp = self.client.post('/profile', data={
            'csrf_token': 'test_token',
            'full_name': 'Dr. Public Test Updated',
            'phone': '+91 9822334455',
            'specialization_id': 8, # Ophthalmologist
            'qualification': 'MBBS, MS Ophthalmology',
            'experience': 9,
            'consultation_fee': 85.00,
            'biography': 'Comprehensive eye care specialist.',
            'new_password': '',
            'confirm_password': ''
        }, follow_redirects=True)
        self.assertEqual(p_resp.status_code, 200)

        u2 = db.query_db("SELECT * FROM users WHERE user_id = %s", (u['user_id'],), one=True)
        self.assertEqual(u2['phone'], '+91 9822334455')
        doc2 = db.query_db("SELECT * FROM doctors WHERE user_id = %s", (u['user_id'],), one=True)
        self.assertEqual(doc2['specialization_id'], 8)

        # Check Doctor Dashboard displays updated specialization and description
        d_resp = self.client.get('/doctor/dashboard')
        self.assertEqual(d_resp.status_code, 200)
        html = d_resp.data.decode('utf-8')
        self.assertIn("Ophthalmologist", html)
        self.assertIn("Eye and vision specialist.", html)

        # Clean up
        db.query_db("DELETE FROM users WHERE user_id = %s", (u['user_id'],), commit=True)
        print("\n[PASS] Public doctor registration, profile update, and dashboard display verified.")

    def test_08_patient_registration_with_indian_phone_and_specialization_options(self):
        """8. Test patient registration with Indian phone format, invalid phone rejection, and doctor specialization options."""
        # Check registration page renders specialization options
        reg_page = self.client.get('/register')
        self.assertEqual(reg_page.status_code, 200)
        html = reg_page.data.decode('utf-8')
        self.assertIn('+91', html)
        self.assertIn('Cardiologist', html)
        self.assertIn('Dermatologist', html)
        self.assertIn('Dentist', html)
        self.assertIn('Gynecologist', html)
        self.assertIn('Orthopedist', html)
        self.assertIn('Neurologist', html)
        self.assertIn('Pediatrician', html)
        self.assertIn('Endocrinologist', html)
        self.assertIn('Hematologist', html)

        # Test valid patient registration with Indian phone
        email = "test_patient_indian_phone@clinic.test"
        db.query_db("DELETE FROM users WHERE email = %s", (email,), commit=True)

        self.client.get('/logout')
        resp = self.client.post('/register', data={
            'csrf_token': 'test_token',
            'role': 'patient',
            'full_name': 'Test Indian Patient',
            'email': email,
            'phone': '9876500112',
            'date_of_birth': '1995-05-15',
            'gender': 'Female',
            'password': 'Patient@123',
            'confirm_password': 'Patient@123'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        u = db.query_db("SELECT * FROM users WHERE email = %s", (email,), one=True)
        self.assertIsNotNone(u, "Patient account was not created")
        self.assertEqual(u['phone'], '+91 9876500112', f"Patient phone not normalized: {u['phone']}")
        self.assertEqual(u['role'], 'patient')

        # Test patient profile update with Indian phone
        with self.client.session_transaction() as sess:
            sess['user_id'] = u['user_id']
            sess['user_role'] = 'patient'
            sess['csrf_token'] = 'test_token'

        p_resp = self.client.post('/profile', data={
            'csrf_token': 'test_token',
            'full_name': 'Test Indian Patient Updated',
            'phone': '+91 9888877777',
            'date_of_birth': '1995-05-15',
            'gender': 'Female',
            'new_password': '',
            'confirm_password': ''
        }, follow_redirects=True)
        self.assertEqual(p_resp.status_code, 200)

        u_updated = db.query_db("SELECT * FROM users WHERE user_id = %s", (u['user_id'],), one=True)
        self.assertEqual(u_updated['phone'], '+91 9888877777')

        # Clean up
        db.query_db("DELETE FROM users WHERE user_id = %s", (u['user_id'],), commit=True)
        print("\n[PASS] Patient registration with Indian phone format and specialization options verified.")

if __name__ == '__main__':
    unittest.main()
