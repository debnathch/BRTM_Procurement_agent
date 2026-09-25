from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models.entities import InventoryBatch, OpenPurchaseOrder

class InventoryService:
    def __init__(self,db:Session): self.db=db
    def position(self,product_code:str,daily_demand:float,expiry_horizon_days:int=90)->dict:
        today=date.today()
        batches=self.db.scalars(select(InventoryBatch).where(InventoryBatch.product_code==product_code)).all()
        active=[b for b in batches if b.expiry_date is None or b.expiry_date>=today]
        expired=sum(max(0.0,b.quantity_on_hand) for b in batches if b.expiry_date is not None and b.expiry_date<today)
        on_hand=sum(max(0.0,b.quantity_on_hand) for b in active)
        near_expiry=sum(max(0.0,b.quantity_on_hand) for b in active if b.expiry_date is not None and (b.expiry_date-today).days<=expiry_horizon_days)
        remaining=daily_demand*expiry_horizon_days; usable=0.0; excess=0.0
        for b in sorted(active,key=lambda x:x.expiry_date or date.max):
            if b.expiry_date is None:
                sellable=min(max(0.0,b.quantity_on_hand),remaining); usable+=sellable; remaining=max(0.0,remaining-sellable); continue
            days=max(0,(b.expiry_date-today).days); capacity=daily_demand*days
            sellable=min(max(0.0,b.quantity_on_hand),max(0.0,min(remaining,capacity)))
            usable+=sellable; remaining=max(0.0,remaining-sellable); excess+=max(0.0,b.quantity_on_hand-sellable)
        open_pos=self.db.scalars(select(OpenPurchaseOrder).where(OpenPurchaseOrder.product_code==product_code,OpenPurchaseOrder.status.in_(['OPEN','PARTIAL']))).all()
        on_order=sum(max(0.0,x.ordered_qty-x.received_qty) for x in open_pos)
        return {'on_hand':on_hand,'expired':expired,'near_expiry':near_expiry,'on_order':on_order,'usable_before_expiry':min(on_hand,usable),'expiry_excess':excess,'expiry_risk':min(1.0,excess/max(on_hand,1.0)),'batches':active}
