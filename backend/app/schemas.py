from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ItemType = Literal["Risk", "Issue"]
Category = Literal[
    "Schedule", "Budget", "Scope", "Resource",
    "Technical", "Vendor", "Compliance", "Security",
]
Status = Literal["Open", "In Progress", "Pending Review", "Closed"]


class ItemCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5)
    item_type: ItemType
    category: Category
    probability: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    owner: str = Field(min_length=1)
    due_date: date
    mitigation: str = ""


class ItemUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = Field(default=None, min_length=5)
    category: Optional[Category] = None
    probability: Optional[int] = Field(default=None, ge=1, le=5)
    impact: Optional[int] = Field(default=None, ge=1, le=5)
    owner: Optional[str] = None
    due_date: Optional[date] = None
    mitigation: Optional[str] = None


class StatusChange(BaseModel):
    status: Status
    note: str = ""


class SuggestRequest(BaseModel):
    title: str = ""
    description: str = Field(min_length=5)
    category: Optional[str] = None

class ExtractRequest(BaseModel):
    text: str = Field(min_length=20, max_length=8000)
    
class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    item_type: str
    category: str
    probability: int
    impact: int
    score: int
    priority: str
    owner: str
    status: str
    due_date: date
    mitigation: Optional[str] = ""
    review_notes: Optional[str] = ""
    created_at: datetime
    updated_at: datetime
    overdue: bool = False