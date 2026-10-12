import db

def migrate():
    new_specs = [
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

    rename_map = {
        "Cardiology": ("Cardiologist", "Heart and blood vessel specialist."),
        "Neurology": ("Neurologist", "Brain, spine, nerves, and nervous system specialist."),
        "Pediatrics": ("Pediatrician", "Infants, children, and adolescents' physician."),
        "Dermatology": ("Dermatologist", "Skin, hair, and nail specialist."),
        "Orthopedics": ("Orthopedist (Orthopedic Surgeon)", "Bones, joints, muscles, and musculoskeletal system specialist."),
        "General Medicine": ("Gynecologist/Obstetrician", "Women's reproductive health and pregnancy specialist.")
    }

    for old_name, (new_name, new_desc) in rename_map.items():
        db.query_db(
            "UPDATE specializations SET specialization_name = %s, description = %s WHERE specialization_name = %s",
            (new_name, new_desc, old_name),
            commit=True
        )

    existing = {row["specialization_name"]: row["specialization_id"] for row in db.query_db("SELECT * FROM specializations")}

    for name, desc in new_specs:
        if name not in existing:
            db.query_db(
                "INSERT INTO specializations (specialization_name, description) VALUES (%s, %s)",
                (name, desc),
                commit=True
            )
            print(f"Inserted: {name}")
        else:
            db.query_db(
                "UPDATE specializations SET description = %s WHERE specialization_name = %s",
                (desc, name),
                commit=True
            )
            print(f"Updated description: {name}")

    specs = db.query_db("SELECT specialization_id, specialization_name, description FROM specializations ORDER BY specialization_id ASC")
    print(f"\nTotal specializations in MySQL: {len(specs)}")
    for s in specs:
        print(f"  [{s['specialization_id']}] {s['specialization_name']} — {s['description']}")

    # Verify doctors
    doctors = db.query_db("""
        SELECT d.doctor_id, u.full_name, s.specialization_name
        FROM doctors d
        JOIN users u ON d.user_id = u.user_id
        JOIN specializations s ON d.specialization_id = s.specialization_id
    """)
    print("\nVerified doctors with their updated specializations:")
    for d in doctors:
        print(f"  Doctor #{d['doctor_id']} {d['full_name']} -> {d['specialization_name']}")

if __name__ == "__main__":
    migrate()
