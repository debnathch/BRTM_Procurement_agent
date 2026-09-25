from dataclasses import dataclass
@dataclass
class ValidationReport:
    ok:bool
    errors:list[str]
    warnings:list[str]
    rows:int
    def as_dict(self):return {'ok':self.ok,'errors':self.errors,'warnings':self.warnings,'rows':self.rows}

def validate_import(result):
    errors=list(result.errors); warnings=list(result.warnings)
    if result.rows==0:errors.append('No usable rows were found.')
    for r in result.records:
        if not r.get('product_code') or not r.get('product_name'):errors.append('A row has no deterministic product identity.')
    return ValidationReport(not errors,errors,warnings,result.rows)
