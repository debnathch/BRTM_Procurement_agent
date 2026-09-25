from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models.entities import SalesDaily, DemandForecast

class DemandService:
    def __init__(self, db: Session, lookback_days: int = 60):
        self.db=db; self.lookback_days=lookback_days
    def forecast_daily(self, product_code: str) -> tuple[float,str]:
        today=date.today()
        row=self.db.scalar(select(DemandForecast).where(DemandForecast.product_code==product_code,DemandForecast.forecast_date>=today).order_by(DemandForecast.forecast_date.asc()))
        if row: return max(0.0,float(row.forecast_qty)),f'forecast:{row.forecast_method}'
        start=today-timedelta(days=self.lookback_days)
        rows=self.db.scalars(select(SalesDaily).where(SalesDaily.product_code==product_code,SalesDaily.sales_date>=start,SalesDaily.sales_date<=today)).all()
        if not rows: return 0.0,'no_data'
        period_rows=[r for r in rows if r.aggregation_level=='period_summary']
        if period_rows:
            vals=[]
            for r in period_rows:
                gross=float(r.quantity_sold)+float(r.free_quantity or 0)-float(r.sales_return_qty or 0)
                vals.append(gross/max(1,int(r.aggregation_days or 1)))
            if vals: return max(0.0,sum(vals)/len(vals)),'marg_sales_period_average'
        valid=[r for r in rows if not r.stockout_flag] or rows
        daily={}
        for r in valid:
            gross=r.quantity_sold+(r.free_quantity or 0)-r.sales_return_qty
            daily[r.sales_date]=daily.get(r.sales_date,0)+gross
        if not daily: return 0.0,'sales_history'
        weighted_sum=weight_total=0.0
        for d,qty in daily.items():
            age=max(1,(today-d).days); weight=2.0 if age<=30 else 1.0
            weighted_sum+=qty*weight; weight_total+=weight
        return max(0.0,weighted_sum/max(weight_total,1.0)),'sales_weighted_average'
