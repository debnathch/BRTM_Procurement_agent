from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = 'local'
    database_url: str = 'sqlite:///./data/marg_procurement.db'
    execution_mode: str = 'dry_run'
    marg_enabled: bool = False
    marg_base_url: str = ''
    marg_api_key: str = ''
    marg_purchase_order_endpoint: str = ''
    marg_company_code: str = 'DEMO'
    marg_source_enabled: bool = False
    marg_data_endpoints_json: str = ''
    marg_api_timeout_seconds: int = 30
    default_lookback_days: int = 60
    default_lead_time_days: int = 45
    default_review_days: int = 7
    default_safety_days: int = 3
    expiry_risk_horizon_days: int = 90
    min_reorder_point_units: float = 0
    max_proposal_qty_units: float = 10000
    max_proposal_value: float = 200000
    require_human_approval: bool = True
    allow_supplier_change: bool = True
    upload_replacement_scope: str = 'dataset'
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

settings = Settings()
