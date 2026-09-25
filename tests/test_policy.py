from backend.app.services.policy import ProcurementPolicy

def test_procurement_quantity_respects_pack():
    p=ProcurementPolicy(7,3,90)
    r=p.calculate(avg_daily_demand=10,lead_time_days=10,stock_on_hand=20,stock_on_order=0,usable_before_expiry=20,near_expiry_qty=0,min_order_qty=5,pack_size=10,unit_cost=100,expiry_risk=0)
    assert r['order_qty']%10==0
    assert r['order_qty']>=0

def test_high_expiry_blocks_purchase():
    p=ProcurementPolicy()
    r=p.calculate(avg_daily_demand=10,lead_time_days=10,stock_on_hand=0,stock_on_order=0,usable_before_expiry=0,near_expiry_qty=100,min_order_qty=1,pack_size=1,unit_cost=10,expiry_risk=.5)
    assert r['order_qty']==0
