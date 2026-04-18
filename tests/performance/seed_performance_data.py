from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.alert import Alert
from app.models.incident import Incident, IncidentCategory
from app.models.report import Report
from app.models.user import User


def ensure_user(email: str, full_name: str) -> User:
    with SessionLocal() as db:
        existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if existing:
            return existing

        user = User(
            email=email,
            password_hash=hash_password("PerfSeed#12345"),
            full_name=full_name,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def ensure_categories() -> list[int]:
    defaults = [
        ("CLOSURE", "Road Closure"),
        ("DELAY", "Delay"),
        ("ACCIDENT", "Accident"),
        ("WEATHER_HAZARD", "Weather Hazard"),
    ]
    with SessionLocal() as db:
        existing = {
            row.key: row
            for row in db.execute(select(IncidentCategory)).scalars().all()
        }
        for key, label in defaults:
            if key not in existing:
                row = IncidentCategory(key=key, label=label)
                db.add(row)
                db.flush()
                existing[key] = row
        db.commit()
        return [row.id for row in existing.values()]


def seed_incidents(total: int, category_ids: list[int], user_id) -> list[int]:
    now = datetime.now(timezone.utc)
    rows: list[Incident] = []
    for idx in range(total):
        category_id = category_ids[idx % len(category_ids)]
        rows.append(
            Incident(
                category_id=category_id,
                checkpoint_id=None,
                title=f"Seeded incident #{idx + 1}",
                description="Performance-seeded incident record",
                severity=(idx % 5) + 1,
                status="VERIFIED" if idx % 3 == 0 else "OPEN",
                source_type="SYSTEM",
                latitude=31.90 + (idx % 50) * 0.001,
                longitude=35.20 + (idx % 50) * 0.001,
                occurred_at=now - timedelta(minutes=idx),
                reported_at=now - timedelta(minutes=idx),
                created_by_user_id=user_id,
                verified_at=now - timedelta(minutes=idx) if idx % 3 == 0 else None,
                verified_by_user_id=user_id if idx % 3 == 0 else None,
                confidence_score=70.0,
            )
        )

    with SessionLocal() as db:
        db.add_all(rows)
        db.commit()
        incident_ids = [row.id for row in rows]
    return incident_ids


def seed_reports(total: int, category_ids: list[int], user_id, incident_ids: list[int]) -> None:
    now = datetime.now(timezone.utc)
    rows: list[Report] = []
    for idx in range(total):
        category_id = category_ids[idx % len(category_ids)]
        linked_incident_id = incident_ids[idx % len(incident_ids)] if incident_ids else None
        rows.append(
            Report(
                user_id=user_id,
                incident_id=linked_incident_id,
                checkpoint_id=None,
                category_id=category_id,
                latitude=31.80 + (idx % 80) * 0.001,
                longitude=35.10 + (idx % 80) * 0.001,
                description=f"Seeded report #{idx + 1}",
                reported_at=now - timedelta(seconds=idx * 10),
                status="PENDING" if idx % 2 == 0 else "REVIEWED",
                duplicate_hash=f"seed-hash-{idx:05d}",
                source_channel="SEED",
                abuse_score=0.0,
                credibility_score=55.0,
            )
        )

    with SessionLocal() as db:
        db.add_all(rows)
        db.commit()


def seed_alerts(total: int, category_ids: list[int], incident_ids: list[int]) -> None:
    if not incident_ids:
        return

    now = datetime.now(timezone.utc)
    rows: list[Alert] = []
    for idx in range(total):
        category_id = category_ids[idx % len(category_ids)]
        rows.append(
            Alert(
                incident_id=incident_ids[idx % len(incident_ids)],
                category_id=category_id,
                severity=(idx % 5) + 1,
                title=f"Seeded alert #{idx + 1}",
                body="Performance-seeded alert record",
                generated_at=now - timedelta(seconds=idx * 5),
            )
        )

    with SessionLocal() as db:
        db.add_all(rows)
        db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed realistic data volume for k6 performance runs.")
    parser.add_argument("--incidents", type=int, default=1000)
    parser.add_argument("--reports", type=int, default=1000)
    parser.add_argument("--alerts", type=int, default=500)
    args = parser.parse_args()

    category_ids = ensure_categories()
    seed_user = ensure_user("perf-seed@wasel.local", "Performance Seeder")

    incident_ids = seed_incidents(args.incidents, category_ids, seed_user.id)
    seed_reports(args.reports, category_ids, seed_user.id, incident_ids)
    seed_alerts(args.alerts, category_ids, incident_ids)

    print(
        "Seeding complete:",
        f"incidents={args.incidents}",
        f"reports={args.reports}",
        f"alerts={args.alerts}",
    )


if __name__ == "__main__":
    main()
