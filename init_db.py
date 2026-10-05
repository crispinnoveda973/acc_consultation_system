"""
Initializes the SQLite database for the ACC Consultation System and
populates it with sample seed data (users, consultations, messages).

Usage:
    python init_db.py            # creates tables, seeds if empty
    python init_db.py --reset    # drops all tables first, then recreates + seeds
"""
import sys
from datetime import datetime, timedelta

from app import create_app
from extensions import db
from models import User, Consultation, Message, Setting, ROLE_SUPER_ADMIN, ROLE_MEDICAL_EXPERT, ROLE_STUDENT


def seed():
    if User.query.first():
        print("Database already contains data — skipping seed. Use --reset to start fresh.")
        return

    print("Seeding sample data...")

    # --- Users --------------------------------------------------------
    admin = User(
        username="admin",
        email="admin@acc.edu",
        full_name="Alex Rivera",
        role=ROLE_SUPER_ADMIN,
        program="System Administration",
    )
    admin.set_password("admin123")

    expert1 = User(
        username="dr.santos",
        email="santos@acc.edu",
        full_name="Dr. Maria Santos",
        role=ROLE_MEDICAL_EXPERT,
        program="General Medicine",
    )
    expert1.set_password("expert123")

    expert2 = User(
        username="dr.lim",
        email="lim@acc.edu",
        full_name="Dr. Ken Lim",
        role=ROLE_MEDICAL_EXPERT,
        program="Mental Health & Counseling",
    )
    expert2.set_password("expert123")

    student1 = User(
        username="jdoe",
        email="jdoe@student.acc.edu",
        full_name="Jamie Doe",
        role=ROLE_STUDENT,
        program="BS Computer Science",
    )
    student1.set_password("student123")

    student2 = User(
        username="mgarcia",
        email="mgarcia@student.acc.edu",
        full_name="Mika Garcia",
        role=ROLE_STUDENT,
        program="BS Nursing",
    )
    student2.set_password("student123")

    student3 = User(
        username="rcruz",
        email="rcruz@student.acc.edu",
        full_name="Ronan Cruz",
        role=ROLE_STUDENT,
        program="BS Psychology",
    )
    student3.set_password("student123")

    db.session.add_all([admin, expert1, expert2, student1, student2, student3])
    db.session.commit()

    # --- Consultations --------------------------------------------------
    now = datetime.utcnow()

    c1 = Consultation(
        student_id=student1.id,
        expert_id=expert1.id,
        subject="Persistent headaches during exam week",
        description="I've been getting frequent headaches for the past week, especially after "
                     "long study sessions. Should I be concerned?",
        status="in_progress",
        priority="high",
        created_at=now - timedelta(days=3),
        updated_at=now - timedelta(hours=5),
    )

    c2 = Consultation(
        student_id=student2.id,
        expert_id=expert1.id,
        subject="Follow-up on allergy medication",
        description="The antihistamine prescribed last month seems less effective now. "
                     "Is it okay to adjust the dosage?",
        status="resolved",
        priority="normal",
        created_at=now - timedelta(days=10),
        updated_at=now - timedelta(days=8),
    )

    c3 = Consultation(
        student_id=student3.id,
        expert_id=expert2.id,
        subject="Trouble sleeping and anxiety before deadlines",
        description="I have been struggling to sleep before major deadlines and feel anxious "
                     "most evenings. Looking for some guidance.",
        status="in_progress",
        priority="high",
        created_at=now - timedelta(days=1, hours=4),
        updated_at=now - timedelta(hours=2),
    )

    c4 = Consultation(
        student_id=student1.id,
        expert_id=None,
        subject="Question about flu vaccination on campus",
        description="Is the campus clinic offering flu shots this semester, and are there any "
                     "side effects I should watch out for?",
        status="pending",
        priority="low",
        created_at=now - timedelta(hours=6),
        updated_at=now - timedelta(hours=6),
    )

    c5 = Consultation(
        student_id=student2.id,
        expert_id=None,
        subject="Sports injury - twisted ankle",
        description="Twisted my ankle during intramurals yesterday. It's swollen but I can still "
                     "walk. Should I get it checked in person or is rest enough?",
        status="pending",
        priority="urgent",
        created_at=now - timedelta(hours=1),
        updated_at=now - timedelta(hours=1),
    )

    db.session.add_all([c1, c2, c3, c4, c5])
    db.session.commit()

    # --- Messages ---------------------------------------------------------
    messages = [
        Message(consultation_id=c1.id, sender_id=student1.id,
                body="It's mostly a dull pain around my temples, worse in the evenings.",
                created_at=now - timedelta(days=3)),
        Message(consultation_id=c1.id, sender_id=expert1.id,
                body="Thanks for the details. Try to stay hydrated and take short breaks every "
                     "45 minutes. Let's monitor this for a few more days.",
                created_at=now - timedelta(days=2, hours=20)),
        Message(consultation_id=c1.id, sender_id=student1.id,
                body="Will do. It's been a bit better today, thank you!",
                created_at=now - timedelta(hours=5)),

        Message(consultation_id=c2.id, sender_id=student2.id,
                body="Sneezing a lot more again even with the medication.",
                created_at=now - timedelta(days=10)),
        Message(consultation_id=c2.id, sender_id=expert1.id,
                body="Let's switch you to a different antihistamine — I've noted it in your "
                     "record. Should improve within a few days.",
                created_at=now - timedelta(days=9)),
        Message(consultation_id=c2.id, sender_id=student2.id,
                body="Much better now, thank you Dr. Santos!",
                created_at=now - timedelta(days=8)),

        Message(consultation_id=c3.id, sender_id=student3.id,
                body="It's mostly racing thoughts about upcoming submissions.",
                created_at=now - timedelta(days=1, hours=4)),
        Message(consultation_id=c3.id, sender_id=expert2.id,
                body="That's a common experience during crunch periods. Let's try a short "
                     "wind-down routine before bed — I'll share some resources.",
                created_at=now - timedelta(hours=2)),
    ]
    db.session.add_all(messages)
    db.session.commit()

    # --- Settings -----------------------------------------------------
    Setting.set("site_name", "ACC Consultation System")
    Setting.set("support_email", "support@acc.edu")
    Setting.set("maintenance_mode", "off")

    print("Seed complete.")
    print("-" * 60)
    print("Sample login credentials:")
    print("  Super Admin    -> username: admin       password: admin123")
    print("  Medical Expert -> username: dr.santos    password: expert123")
    print("  Medical Expert -> username: dr.lim        password: expert123")
    print("  Student        -> username: jdoe          password: student123")
    print("  Student        -> username: mgarcia       password: student123")
    print("  Student        -> username: rcruz         password: student123")
    print("-" * 60)


def main():
    app = create_app()
    with app.app_context():
        if "--reset" in sys.argv:
            print("Dropping all tables...")
            db.drop_all()
        db.create_all()
        seed()


if __name__ == "__main__":
    main()
