from math import ceil

class ProcurementPolicy:
    def __init__(self,review_days:int=7,safety_days:int=3,expiry_horizon_days:int=90):
        self.review_days=review_days; self.safety_days=safety_days; self.expiry_horizon_days=expiry_horizon_days
    def calculate(self,*,avg_daily_demand,lead_time_days,stock_on_hand,stock_on_order,usable_before_expiry,near_expiry_qty,min_order_qty,pack_size,unit_cost,expiry_risk):
        daily=max(0.0,avg_daily_demand); lead_demand=daily*max(0,lead_time_days); review_demand=daily*self.review_days; safety_stock=daily*self.safety_days
        target_stock=lead_demand+review_demand+safety_stock
        effective_stock=min(max(0.0,stock_on_hand),max(0.0,usable_before_expiry))
        gap=max(0.0,target_stock-effective_stock-max(0.0,stock_on_order))
        order_qty=0.0 if gap<=self.safety_days*daily or daily<=0 else max(gap,float(min_order_qty))
        if order_qty>0:
            pack=max(1,int(pack_size)); order_qty=ceil(order_qty/pack)*pack
        if expiry_risk>=0.50: order_qty=0.0
        elif expiry_risk>=0.25:
            order_qty=0.0 if gap<2*daily*max(1,lead_time_days) else order_qty*0.5
            if order_qty>0:
                pack=max(1,int(pack_size)); order_qty=ceil(order_qty/pack)*pack
        action='NORMAL_FEFO'
        if near_expiry_qty>0 and expiry_risk>=0.25: action='SELL_NEAR_EXPIRY_FIRST'
        if expiry_risk>=0.50: action='HOLD_NEW_PURCHASE_FOR_EXPIRY_REVIEW'
        return {'lead_demand':lead_demand,'review_demand':review_demand,'safety_stock':safety_stock,'target_stock':target_stock,'effective_stock':effective_stock,'order_qty':order_qty,'estimated_value':order_qty*max(0.0,unit_cost),'expiry_risk':min(1.0,max(0.0,expiry_risk)),'expiry_action':action}
