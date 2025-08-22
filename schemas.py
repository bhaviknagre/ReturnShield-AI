from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ReturnCreate(BaseModel):
    order_id: str
    customer_email: str
    customer_name: Optional[str] = None
    sku: str
    reason: str
    size: Optional[str] = None
    color: Optional[str] = None

class ReturnOut(BaseModel):
    id: int
    created_at: datetime
    order_id: str
    sku: str
    similarity_score: float
    brightness: float
    blur: float
    metadata_score: float
    text_consistency: float
    customer_history: float
    risk_score: float
    decision: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True
