from dataclasses import dataclass
from pathlib import Path
import hashlib,re
import pandas as pd

@dataclass
class ImportResult:
    dataset:str
    rows:int
    warnings:list[str]
    errors:list[str]
    records:list[dict]

PROFILES={
 'sales':['item description','quantity','free','av.rate','amount'],
 'purchase':['item description','quantity','free','av.rate','amount'],
 'stock':['item description','batch','expiry','quantity','cost','mrp','amount'],
}

def _norm(x): return re.sub(r'[^a-z0-9]+',' ',str(x).strip().lower()).strip()
def detect_profile(df):
    cols={_norm(c) for c in df.columns}
    if 'batch' in cols and 'expiry' in cols:return 'stock'
    if 'av rate' in cols or 'amount' in cols:
        return 'sales'
    return None

def read_marg(path,profile=None):
    p=Path(path)
    engine='xlrd' if p.suffix.lower()=='.xls' else None
    df=pd.read_excel(p,engine=engine)
    df=df.dropna(how='all').copy()
    profile=profile or detect_profile(df)
    if not profile: return ImportResult('unknown',len(df),[],['Unable to identify a supported MARG report profile.'],[])
    cols={_norm(c):c for c in df.columns}
    def col(name):return cols.get(_norm(name))
    if not col('item description'):return ImportResult(profile,len(df),[],['Required Item Description column is missing.'],[])
    records=[]
    warnings=[]
    for _,r in df.iterrows():
        name=str(r[col('item description')]).strip()
        if not name or name.lower()=='nan':continue
        code='MARGDESC-'+hashlib.sha1(_norm(name).encode()).hexdigest()[:12].upper()
        rec={'product_code':code,'product_name':name}
        for target,source in [('quantity','quantity'),('free','free'),('unit_cost','cost'),('unit_cost','av.rate'),('mrp','mrp'),('batch_no','batch'),('expiry_raw','expiry')]:
            c=col(source)
            if c is not None and target not in rec:rec[target]=r[c]
        records.append(rec)
    return ImportResult(profile,len(records),warnings,[],records)
