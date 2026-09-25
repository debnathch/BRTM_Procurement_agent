from pathlib import Path
import tempfile
from fastapi import APIRouter,File,UploadFile,HTTPException
from backend.app.ingestion.marg_excel import read_marg
from backend.app.ingestion.validation import validate_import

router=APIRouter(prefix='/api/ingestion',tags=['ingestion'])

@router.post('/validate')
async def validate(file:UploadFile=File(...)):
    suffix=Path(file.filename or '').suffix.lower()
    if suffix not in ('.xls','.xlsx','.csv'): raise HTTPException(400,'Only .xls, .xlsx and .csv are supported.')
    data=await file.read()
    with tempfile.NamedTemporaryFile(suffix=suffix,delete=False) as tmp:
        tmp.write(data); path=tmp.name
    try:
        result=read_marg(path)
        return {'filename':file.filename,'dataset':result.dataset,**validate_import(result).as_dict(),'preview':result.records[:25]}
    finally: Path(path).unlink(missing_ok=True)
