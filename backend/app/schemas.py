from typing import Literal
from pydantic import BaseModel, Field

class ProcurementRunRequest(BaseModel):
    product_codes: list[str] | None = None

class DecisionRequest(BaseModel):
    action: Literal['approve', 'reject', 'hold', 'create_draft_po']
    approved_qty: float | None = Field(default=None, ge=0)
    supplier_id: str | None = None
    reason: str | None = Field(default=None, max_length=2000)
    actor: str = Field(default='human-ui', max_length=128)

class HealthResponse(BaseModel):
    status: str
    execution_mode: str

class DraftPOReviewRequest(BaseModel):
    quantity: float | None = Field(default=None, ge=0)
    supplier_id: str | None = None
    reason: str | None = Field(default=None, max_length=2000)
    actor: str = Field(default='human-ui', max_length=128)

class DraftPOActionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)
    actor: str = Field(default='human-ui', max_length=128)
