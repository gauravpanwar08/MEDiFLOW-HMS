"""
Run: python seed.py
Creates demo hospital, admin, 5 doctors, 3 patients with availability slots.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from datetime import date

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.models import (
    Hospital, User, Doctor, Patient, DoctorAvailability,
    UserRole, DoctorSpecialty, Gender,
)


async def seed():
    print("\n🌱 Seeding MediCore HMS...\n")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        # Hospital
        h = (await db.execute(select(Hospital).where(Hospital.slug == "default"))).scalar_one_or_none()
        if not h:
            h = Hospital(name="City General Hospital", slug="default",
                         address="123 Medical Centre Rd, Mumbai",
                         phone="+91 22 1234 5678", email="info@citygeneral.com",
                         is_active=True, subscription_plan="enterprise")
            db.add(h); await db.flush()
            print(f"  ✅ Hospital: {h.name}")

        async def make_user(email, password, first, last, role):
            ex = (await db.execute(select(User).where(User.email == email, User.hospital_id == h.id))).scalar_one_or_none()
            if ex:
                return ex
            u = User(email=email, hashed_password=get_password_hash(password),
                     first_name=first, last_name=last, role=role,
                     hospital_id=h.id, is_active=True, is_verified=True)
            db.add(u); await db.flush()
            return u

        # Admin
        admin = await make_user("admin@hospital.com", "admin123", "Hospital", "Admin", UserRole.admin)
        print(f"  ✅ Admin:   admin@hospital.com / admin123")

        # Doctors
        doctors_data = [
            ("doctor1@hospital.com", "Sarah", "Chen", DoctorSpecialty.cardiologist, "DL-001", 12, 800.0),
            ("doctor2@hospital.com", "Raj", "Patel", DoctorSpecialty.neurologist, "DL-002", 8, 600.0),
            ("doctor3@hospital.com", "Priya", "Singh", DoctorSpecialty.dermatologist, "DL-003", 5, 400.0),
            ("doctor4@hospital.com", "Ahmed", "Khan", DoctorSpecialty.general_physician, "DL-004", 15, 300.0),
            ("doctor5@hospital.com", "Meera", "Nair", DoctorSpecialty.pediatrician, "DL-005", 10, 500.0),
        ]
        for i, (email, fn, ln, spec, lic, exp, fee) in enumerate(doctors_data):
            u = await make_user(email, "doctor123", fn, ln, UserRole.doctor)
            ex_doc = (await db.execute(select(Doctor).where(Doctor.user_id == u.id))).scalar_one_or_none()
            if not ex_doc:
                doc = Doctor(hospital_id=h.id, user_id=u.id, specialty=spec,
                             license_number=lic, qualification="MD, MBBS",
                             experience_years=exp, consultation_fee=fee,
                             is_available=True, rating=4.0 + i * 0.2, total_reviews=20 + i * 5,
                             bio=f"Experienced {spec.value} with {exp} years of practice.")
                db.add(doc); await db.flush()
                for day in range(5):
                    db.add(DoctorAvailability(doctor_id=doc.id, day_of_week=day,
                                              start_time="09:00", end_time="17:00",
                                              slot_duration_minutes=30, is_active=True))
            print(f"  ✅ Doctor:  {email} / doctor123  ({spec.value})")

        # Patients
        patients_data = [
            ("patient1@email.com", "Amir", "Shaikh", "1990-05-15", Gender.male, "O+"),
            ("patient2@email.com", "Sunita", "Verma", "1985-11-22", Gender.female, "A+"),
            ("patient3@email.com", "Rahul", "Gupta", "2000-03-10", Gender.male, "B+"),
        ]
        for email, fn, ln, dob, gender, bg in patients_data:
            u = await make_user(email, "patient123", fn, ln, UserRole.patient)
            ex_pat = (await db.execute(select(Patient).where(Patient.user_id == u.id))).scalar_one_or_none()
            if not ex_pat:
                pat = Patient(hospital_id=h.id, user_id=u.id,
                              date_of_birth=date.fromisoformat(dob),
                              gender=gender, blood_group=bg,
                              address="Mumbai, India",
                              emergency_contact_name="Family Member",
                              emergency_contact_phone="+91 98765 12345")
                db.add(pat)
            print(f"  ✅ Patient: {email} / patient123")

        await db.commit()

    print("\n🎉 Seed complete! Login at http://localhost:3000")
    print("   Hospital slug: default")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
