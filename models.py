# backend/app/models.py
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, Enum, Text
from sqlalchemy.orm import Session
import enum
import datetime
from .db import Base

class ComplaintStatusEnum(str, enum.Enum):
    new = "new"
    in_progress = "in_progress"
    resolved = "resolved"
    escalated = "escalated"

class ComplaintModel(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, index=True)
    citizen_name = Column(String(128), default="Anonymous")
    text = Column(Text)
    department = Column(String(64))
    urgency = Column(String(16))
    routed_to = Column(String(64))
    reason = Column(Text, default="")
    status = Column(Enum(ComplaintStatusEnum), default=ComplaintStatusEnum.new)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Pydantic schemas
class ComplaintCreate(BaseModel):
    citizen_name: Optional[str]
    text: str
    department: str
    urgency: str
    routed_to: str
    reason: Optional[str] = ""

class ComplaintRead(BaseModel):
    id: int
    citizen_name: Optional[str]
    text: str
    department: str
    urgency: str
    routed_to: str
    reason: Optional[str]
    status: ComplaintStatusEnum
    created_at: datetime.datetime

    class Config:
        orm_mode = True

# Convenience DB methods
class Complaint:
    @staticmethod
    def create(db: Session, complaint: ComplaintCreate) -> ComplaintRead:
        m = ComplaintModel(
            citizen_name=complaint.citizen_name,
            text=complaint.text,
            department=complaint.department,
            urgency=complaint.urgency,
            routed_to=complaint.routed_to,
            reason=complaint.reason,
            status=ComplaintStatusEnum.in_progress
        )
        db.add(m)
        db.commit()
        db.refresh(m)
        return ComplaintRead.from_orm(m)

    @staticmethod
    def list_all(db: Session):
        rows = db.query(ComplaintModel).order_by(ComplaintModel.id.desc()).all()
        return [ComplaintRead.from_orm(r) for r in rows]

    @staticmethod
    def get(db: Session, cid: int):
        r = db.query(ComplaintModel).filter(ComplaintModel.id == cid).first()
        return ComplaintRead.from_orm(r) if r else None

    @staticmethod
    def update_status(db: Session, cid: int, status: ComplaintStatusEnum):
        r = db.query(ComplaintModel).filter(ComplaintModel.id == cid).first()
        if not r:
            return None
        r.status = status
        db.commit()
        db.refresh(r)
        return ComplaintRead.from_orm(r)

    @staticmethod
    def list_open(db: Session):
        rows = db.query(ComplaintModel).filter(ComplaintModel.status != ComplaintStatusEnum.resolved).all()
        return rows
