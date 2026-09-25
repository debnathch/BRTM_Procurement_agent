from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.database import Base

class Product(Base):
    __tablename__ = 'products'
    product_code: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_name: Mapped[str] = mapped_column(String(255))
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pack_size: Mapped[int] = mapped_column(Integer, default=1)
    unit: Mapped[str] = mapped_column(String(32), default='PCS')
    reorder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    min_order_qty: Mapped[int] = mapped_column(Integer, default=1)
    shelf_life_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_supplier_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    unit_cost: Mapped[float] = mapped_column(Float, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Supplier(Base):
    __tablename__ = 'suppliers'
    supplier_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    supplier_name: Mapped[str] = mapped_column(String(255))
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7)
    min_order_value: Mapped[float] = mapped_column(Float, default=0)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=0)
    reliability_score: Mapped[float] = mapped_column(Float, default=0.8)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class InventoryBatch(Base):
    __tablename__ = 'inventory_batches'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_code: Mapped[str] = mapped_column(String(64), index=True)
    batch_no: Mapped[str] = mapped_column(String(128))
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    quantity_on_hand: Mapped[float] = mapped_column(Float, default=0)
    unit_cost: Mapped[float] = mapped_column(Float, default=0)
    mrp: Mapped[float] = mapped_column(Float, default=0)
    received_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    warehouse: Mapped[str | None] = mapped_column(String(64), nullable=True)

class SalesDaily(Base):
    __tablename__ = 'sales_daily'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sales_date: Mapped[date] = mapped_column(Date, index=True)
    product_code: Mapped[str] = mapped_column(String(64), index=True)
    quantity_sold: Mapped[float] = mapped_column(Float, default=0)
    sales_return_qty: Mapped[float] = mapped_column(Float, default=0)
    free_quantity: Mapped[float] = mapped_column(Float, default=0)
    aggregation_level: Mapped[str] = mapped_column(String(32), default='daily')
    aggregation_days: Mapped[int] = mapped_column(Integer, default=1)
    stockout_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    warehouse: Mapped[str | None] = mapped_column(String(64), nullable=True)

class PurchaseHistory(Base):
    __tablename__ = 'purchase_history'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    purchase_date: Mapped[date] = mapped_column(Date, index=True)
    supplier_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    product_code: Mapped[str] = mapped_column(String(64), index=True)
    invoice_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    batch_no: Mapped[str | None] = mapped_column(String(128), nullable=True)
    quantity_purchased: Mapped[float] = mapped_column(Float, default=0)
    unit_cost: Mapped[float] = mapped_column(Float, default=0)
    mrp: Mapped[float] = mapped_column(Float, default=0)
    free_quantity: Mapped[float] = mapped_column(Float, default=0)
    aggregation_level: Mapped[str] = mapped_column(String(32), default='transaction')
    aggregation_days: Mapped[int] = mapped_column(Integer, default=1)
    warehouse: Mapped[str | None] = mapped_column(String(64), nullable=True)

class OpenPurchaseOrder(Base):
    __tablename__ = 'open_purchase_orders'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    po_no: Mapped[str] = mapped_column(String(64), index=True)
    supplier_id: Mapped[str] = mapped_column(String(64))
    product_code: Mapped[str] = mapped_column(String(64), index=True)
    order_date: Mapped[date] = mapped_column(Date)
    expected_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    ordered_qty: Mapped[float] = mapped_column(Float, default=0)
    received_qty: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(32), default='OPEN')

class DemandForecast(Base):
    __tablename__ = 'demand_forecasts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    forecast_date: Mapped[date] = mapped_column(Date, index=True)
    product_code: Mapped[str] = mapped_column(String(64), index=True)
    forecast_qty: Mapped[float] = mapped_column(Float)
    forecast_method: Mapped[str] = mapped_column(String(64), default='moving_average')
    confidence_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_high: Mapped[float | None] = mapped_column(Float, nullable=True)

class ProcurementRun(Base):
    __tablename__ = 'procurement_runs'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default='COMPLETED')
    product_count: Mapped[int] = mapped_column(Integer, default=0)
    proposal_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ProcurementProposal(Base):
    __tablename__ = 'procurement_proposals'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    product_code: Mapped[str] = mapped_column(String(64))
    product_name: Mapped[str] = mapped_column(String(255))
    supplier_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    supplier_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recommended_qty: Mapped[float] = mapped_column(Float)
    approved_qty: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit_cost: Mapped[float] = mapped_column(Float, default=0)
    estimated_value: Mapped[float] = mapped_column(Float, default=0)
    avg_daily_demand: Mapped[float] = mapped_column(Float, default=0)
    demand_source: Mapped[str] = mapped_column(String(64), default='sales_history')
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7)
    stock_on_hand: Mapped[float] = mapped_column(Float, default=0)
    stock_on_order: Mapped[float] = mapped_column(Float, default=0)
    near_expiry_qty: Mapped[float] = mapped_column(Float, default=0)
    expired_qty: Mapped[float] = mapped_column(Float, default=0)
    expiry_risk_score: Mapped[float] = mapped_column(Float, default=0)
    expiry_action: Mapped[str] = mapped_column(String(64), default='NORMAL_FEFO')
    rationale: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default='PENDING')
    human_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    forecast_daily_demand: Mapped[float] = mapped_column(Float, default=0)
    lead_time_demand: Mapped[float] = mapped_column(Float, default=0)
    review_period_days: Mapped[int] = mapped_column(Integer, default=7)
    review_period_demand: Mapped[float] = mapped_column(Float, default=0)
    safety_stock: Mapped[float] = mapped_column(Float, default=0)
    reorder_point: Mapped[float] = mapped_column(Float, default=0)
    target_stock: Mapped[float] = mapped_column(Float, default=0)
    usable_before_expiry: Mapped[float] = mapped_column(Float, default=0)
    inventory_position: Mapped[float] = mapped_column(Float, default=0)
    effective_stock: Mapped[float] = mapped_column(Float, default=0)
    expiry_excess_qty: Mapped[float] = mapped_column(Float, default=0)
    nearest_expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    days_to_nearest_expiry: Mapped[int | None] = mapped_column(Integer, nullable=True)
    purchase_value: Mapped[float] = mapped_column(Float, default=0)
    calculation_snapshot_json: Mapped[str] = mapped_column(Text, default='{}')

class DraftPurchaseOrder(Base):
    __tablename__ = 'draft_purchase_orders'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    po_reference: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    proposal_id: Mapped[int] = mapped_column(Integer, index=True)
    supplier_id: Mapped[str] = mapped_column(String(64))
    supplier_name: Mapped[str] = mapped_column(String(255))
    product_code: Mapped[str] = mapped_column(String(64))
    product_name: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[float] = mapped_column(Float)
    unit_cost: Mapped[float] = mapped_column(Float, default=0)
    estimated_value: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(32), default='DRAFT')
    created_by: Mapped[str] = mapped_column(String(128), default='human-ui')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    execution_status: Mapped[str] = mapped_column(String(32), default='NOT_STARTED')
    execution_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    execution_idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    execution_attempts: Mapped[int] = mapped_column(Integer, default=0)
    execution_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class ExecutionAttempt(Base):
    __tablename__ = 'execution_attempts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draft_po_id: Mapped[int] = mapped_column(Integer, index=True)
    po_reference: Mapped[str] = mapped_column(String(64), index=True)
    attempt_no: Mapped[int] = mapped_column(Integer)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default='IN_PROGRESS')
    actor: Mapped[str] = mapped_column(String(128), default='system')
    request_json: Mapped[str] = mapped_column(Text, default='{}')
    response_json: Mapped[str] = mapped_column(Text, default='{}')
    response_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class FeedbackEvent(Base):
    __tablename__ = 'feedback_events'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proposal_id: Mapped[int] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(32))
    original_qty: Mapped[float] = mapped_column(Float)
    final_qty: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AuditEvent(Base):
    __tablename__ = 'audit_events'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    actor: Mapped[str] = mapped_column(String(128), default='system')
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details_json: Mapped[str] = mapped_column(Text, default='{}')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class SyncRun(Base):
    __tablename__ = 'sync_runs'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(64))
    dataset: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    rows_loaded: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
