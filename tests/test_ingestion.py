from backend.app.ingestion.marg_excel import ImportResult
from backend.app.ingestion.validation import validate_import

def test_validation_blocks_empty():
    r=validate_import(ImportResult('sales',0,[],[],[]))
    assert not r.ok
    assert r.errors

def test_validation_accepts_identity():
    r=validate_import(ImportResult('sales',1,[],[],[{'product_code':'MARGDESC-ABC','product_name':'TEST'}]))
    assert r.ok
