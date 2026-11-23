import os
from app.middleware import register_middleware
from collections import Counter
from typing import Optional

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import Base, SessionLocal, engine, get_db
from app.models import utcnow
from app.scoring import calculate_score, get_priority, is_overdue
from app.seed import seed_if_empty
from app.services.llm_service import extract_items, suggest_text
from app.services.policy_service import (
    MAX_BYTES, mark_dirty, pdf_to_passages, search_policies,
)
from app.services.vector_service import search_similar

Base.metadata.create_all(bind=engine)
with SessionLocal() as _db:
    seed_if_empty(_db)

app = FastAPI(title="RiskPilot: Project Risk & Issue Triage and Mitigation")
register_middleware(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
    ).split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

ALL_STATUSES = {"Open", "In Progress", "Pending Review", "Closed"}
STATUS_RIGHTS = {
    "Project Manager": ALL_STATUSES,
    "Programme Lead": ALL_STATUSES,
    "Risk Owner": {"In Progress", "Pending Review"},
}
# Which status may follow which. Closed is reached only through review.
TRANSITIONS = {
    "Open": {"In Progress", "Pending Review"},
    "In Progress": {"Pending Review"},
    "Pending Review": {"In Progress", "Closed"},
    "Closed": {"Open"},
}


def check_role(role: str) -> str:
    if role not in STATUS_RIGHTS:
        raise HTTPException(
            status_code=400,
            detail="X-Role must be Project Manager, Risk Owner or Programme Lead",
        )
    return role


def write_log(db: Session, item_id: int, action: str, role: str, details: str):
    db.add(models.AuditLog(
        item_id=item_id, action=action, changed_by=role, details=details
    ))


def get_item_or_404(db: Session, item_id: int) -> models.Item:
    item = db.get(models.Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return item


def to_out(item: models.Item) -> schemas.ItemOut:
    out = schemas.ItemOut.model_validate(item)
    out.overdue = is_overdue(item.due_date, item.status)
    return out


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/items", response_model=schemas.ItemOut, status_code=201)
def create_item(
    data: schemas.ItemCreate,
    db: Session = Depends(get_db),
    x_role: str = Header(..., alias="X-Role"),
):
    role = check_role(x_role)
    if role != "Project Manager":
        raise HTTPException(status_code=403, detail="Only a Project Manager can create records")
    score = calculate_score(data.probability, data.impact)
    item = models.Item(
        **data.model_dump(),
        score=score,
        priority=get_priority(score),
        status="Open",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    write_log(db, item.id, "created", role, f"Created {item.item_type}: {item.title}")
    db.commit()
    return to_out(item)


@app.get("/items", response_model=list[schemas.ItemOut])
def list_items(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    owner: Optional[str] = None,
    category: Optional[str] = None,
    overdue: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Item)
    if status:
        query = query.filter(models.Item.status == status)
    if priority:
        query = query.filter(models.Item.priority == priority)
    if category:
        query = query.filter(models.Item.category == category)
    if owner:
        query = query.filter(models.Item.owner.ilike(f"%{owner}%"))
    items = query.order_by(models.Item.score.desc(), models.Item.due_date).all()
    result = [to_out(i) for i in items]
    if overdue is not None:
        result = [r for r in result if r.overdue == overdue]
    return result


@app.get("/items/{item_id}", response_model=schemas.ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    return to_out(get_item_or_404(db, item_id))


@app.put("/items/{item_id}", response_model=schemas.ItemOut)
def update_item(
    item_id: int,
    data: schemas.ItemUpdate,
    db: Session = Depends(get_db),
    x_role: str = Header(..., alias="X-Role"),
):
    role = check_role(x_role)
    if role not in ("Project Manager", "Risk Owner"):
        raise HTTPException(status_code=403, detail="Your role cannot edit records")
    item = get_item_or_404(db, item_id)
    if item.status == "Closed":
        raise HTTPException(status_code=400, detail="Closed records cannot be edited")

    details = []
    for field, value in data.model_dump(exclude_unset=True).items():
        old = getattr(item, field)
        if value is not None and old != value:
            setattr(item, field, value)
            details.append(f"{field}: {old} -> {value}")

    if not details:
        return to_out(item)
    item.score = calculate_score(item.probability, item.impact)
    item.priority = get_priority(item.score)
    item.updated_at = utcnow()
    write_log(db, item.id, "updated", role, "; ".join(details))
    db.commit()
    db.refresh(item)
    return to_out(item)


@app.patch("/items/{item_id}/status", response_model=schemas.ItemOut)
def change_status(
    item_id: int,
    data: schemas.StatusChange,
    db: Session = Depends(get_db),
    x_role: str = Header(..., alias="X-Role"),
):
    role = check_role(x_role)
    if data.status not in STATUS_RIGHTS[role]:
        raise HTTPException(
            status_code=403,
            detail=f"{role} cannot set the status to {data.status}",
        )
    item = get_item_or_404(db, item_id)
    if data.status not in TRANSITIONS[item.status]:
        raise HTTPException(
            status_code=400,
            detail=f"A record cannot move from {item.status} to {data.status}",
        )
    old_status = item.status
    item.status = data.status
    item.updated_at = utcnow()
    if data.note:
        prefix = (item.review_notes + "\n") if item.review_notes else ""
        item.review_notes = f"{prefix}[{role}] {data.note}"
    write_log(
        db, item.id, "status_change", role,
        f"{old_status} -> {data.status}. Note: {data.note or '-'}",
    )
    db.commit()
    db.refresh(item)
    return to_out(item)


@app.get("/items/{item_id}/audit")
def get_audit(item_id: int, db: Session = Depends(get_db)):
    get_item_or_404(db, item_id)
    logs = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.item_id == item_id)
        .order_by(models.AuditLog.id)
        .all()
    )
    return [
        {
            "action": log.action,
            "changed_by": log.changed_by,
            "details": log.details,
            "timestamp": log.timestamp,
        }
        for log in logs
    ]


@app.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    items = db.query(models.Item).all()
    open_items = [i for i in items if i.status != "Closed"]
    return {
        "total": len(items),
        "open": len(open_items),
        "overdue": sum(1 for i in items if is_overdue(i.due_date, i.status)),
        "high_priority": sum(1 for i in open_items if i.priority in ("High", "Critical")),
        "by_status": dict(Counter(i.status for i in items)),
        "by_priority": dict(Counter(i.priority for i in items)),
    }


@app.post("/suggest")
def suggest(data: schemas.SuggestRequest, db: Session = Depends(get_db)):
    try:
        similar_cases = search_similar(data.description)
    except Exception:
        similar_cases = []
    try:
        policies = search_policies(db, f"{data.title} {data.description}")
    except Exception:
        policies = []
    try:
        result = suggest_text(
            data.title, data.description, data.category, similar_cases, policies
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
    return {
        "suggestion": True,
        "note": "AI-generated suggestion. A human must review it before saving.",
        "result": result,
        "similar": similar_cases,
        "policies": policies,
    }


@app.get("/policies")
def list_policies(db: Session = Depends(get_db)):
    docs = db.query(models.PolicyDocument).order_by(models.PolicyDocument.uploaded_at.desc()).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "pages": d.pages,
            "passages": d.passages,
            "uploaded_by": d.uploaded_by,
            "uploaded_at": d.uploaded_at,
        }
        for d in docs
    ]


@app.post("/policies", status_code=201)
def upload_policy(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    x_role: str = Header(..., alias="X-Role"),
):
    role = check_role(x_role)
    if role != "Project Manager":
        raise HTTPException(status_code=403, detail="Only a Project Manager can upload policies")
    name = (file.filename or "").strip()
    if not name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file")
    if db.query(models.PolicyDocument).filter(models.PolicyDocument.name == name).first():
        raise HTTPException(status_code=400, detail="A policy with this name already exists. Delete it first.")
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="The PDF is larger than 10 MB")
    try:
        pages, passages = pdf_to_passages(data)
    except Exception:
        raise HTTPException(status_code=400, detail="This PDF could not be read")
    if not passages:
        raise HTTPException(
            status_code=400,
            detail="No readable text found. Scanned PDFs (images) are not supported.",
        )
    doc = models.PolicyDocument(
        name=name, pages=pages, passages=len(passages), uploaded_by=role
    )
    db.add(doc)
    db.flush()
    for page, text in passages:
        db.add(models.PolicyChunk(document_id=doc.id, document_name=name, page=page, text=text))
    db.commit()
    mark_dirty()
    return {"id": doc.id, "name": name, "pages": pages, "passages": len(passages)}


@app.delete("/policies/{doc_id}")
def delete_policy(
    doc_id: int,
    db: Session = Depends(get_db),
    x_role: str = Header(..., alias="X-Role"),
):
    role = check_role(x_role)
    if role != "Project Manager":
        raise HTTPException(status_code=403, detail="Only a Project Manager can delete policies")
    doc = db.get(models.PolicyDocument, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.query(models.PolicyChunk).filter(models.PolicyChunk.document_id == doc_id).delete()
    db.delete(doc)
    db.commit()
    mark_dirty()
    return {"deleted": True}


@app.post("/extract")
def extract(data: schemas.ExtractRequest):
    try:
        items = extract_items(data.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
    return {
        "suggestion": True,
        "note": "AI-extracted drafts. A human must review each one before saving.",
        "items": items,
    }


@app.post("/similar")
def similar(data: schemas.SuggestRequest):
    try:
        return search_similar(data.description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")