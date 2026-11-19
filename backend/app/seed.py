import csv
from datetime import date
from pathlib import Path

from app import models
from app.scoring import calculate_score, get_priority

CSV_PATH = Path(__file__).resolve().parents[2] / "data" / "sample_register.csv"


def seed_if_empty(db):
    if db.query(models.Item).count() > 0:
        return

    items = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            probability = int(row["probability"])
            impact = int(row["impact"])
            score = calculate_score(probability, impact)
            item = models.Item(
                title=row["title"],
                description=row["description"],
                item_type=row["item_type"],
                category=row["category"],
                probability=probability,
                impact=impact,
                score=score,
                priority=get_priority(score),
                owner=row["owner"],
                status=row["status"],
                due_date=date.fromisoformat(row["due_date"]),
                mitigation=row["mitigation"],
                review_notes=row["review_notes"],
            )
            db.add(item)
            items.append(item)

    db.flush()
    for item in items:
        db.add(models.AuditLog(
            item_id=item.id,
            action="created",
            changed_by="System",
            details="Loaded from sample register",
        ))
    db.commit()