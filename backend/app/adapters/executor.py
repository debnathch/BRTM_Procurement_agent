import csv
from pathlib import Path
from backend.app.adapters.base import ExecutionResult
from backend.app.core.config import settings

class DryRunExecutor:
    def create_purchase_order(self, *, supplier_id, company_code, items, remark, idempotency_key):
        return ExecutionResult(True,f'DRYRUN-{idempotency_key[:12]}','DRY_RUN: no external purchase order was created.')

class CsvExecutor:
    def create_purchase_order(self, *, supplier_id, company_code, items, remark, idempotency_key):
        out=Path('outbox'); out.mkdir(exist_ok=True)
        path=out/f'purchase_order_{idempotency_key}.csv'
        with path.open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f); w.writerow(['company_code','supplier_id','product_code','quantity','unit_cost','remark','idempotency_key'])
            for item in items:w.writerow([company_code,supplier_id,item['product_code'],item['quantity'],item['unit_cost'],remark,idempotency_key])
        return ExecutionResult(True,path.name,f'CSV handoff written to {path}')

class MargExecutor:
    def create_purchase_order(self, **kwargs):
        if not settings.marg_enabled or not settings.marg_purchase_order_endpoint:
            return ExecutionResult(False,'','MARG execution is not configured. Use dry_run until the exact connector contract is validated.')
        return ExecutionResult(False,'','UNKNOWN: live MARG connector contract must be implemented and validated before execution.')

def build_executor():
    mode=settings.execution_mode.lower()
    if mode=='csv': return CsvExecutor()
    if mode=='marg': return MargExecutor()
    return DryRunExecutor()
