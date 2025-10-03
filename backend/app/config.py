from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "postgresql://davey:aptossend123@localhost:5432/aptossend"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "aptossend"
    database_user: str = "davey"
    database_password: str = "aptossend123"
    
    # Aptos Configuration
    aptos_node_url: str = "https://fullnode.testnet.aptoslabs.com/v1"
    aptos_faucet_url: str = "https://faucet.testnet.aptoslabs.com"
    aptos_private_key: Optional[str] = None
    aptos_contract_address: str = "0xa3bbeb9cc35bab4c3c0af22c9b1398e4d849d4b33ed59b59a6dc4b1ca5298a2d"
    admin_private_key: Optional[str] = None
    
    # Nodit RPC Configuration
    nodit_api_key: Optional[str] = None
    nodit_rpc_url: str = "https://aptos-testnet.nodit.io"
    
    # JWT Configuration
    jwt_secret_key: str = "super_secret_jwt_key_for_aptossend_production_change_this_in_production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = "Preklo"
    debug: bool = True
    
    # Circle USDC Configuration
    circle_usdc_contract_address: str = "0x498d8926f16eb9ca90cab1b3a26aa6f97a080b3fcbe6e83ae150b7243a00fb68::usdc::USDC"
    circle_api_key: Optional[str] = None
    circle_wallet_set_id: Optional[str] = None
    circle_entity_secret: Optional[str] = None
    
    # Redis Configuration (for rate limiting and caching)
    redis_url: str = "redis://localhost:6379"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Unlimit Card Issuing Configuration
    unlimit_api_key: Optional[str] = None
    unlimit_secret_key: Optional[str] = None
    unlimit_base_url: str = "https://sandbox-cardapi.unlimit.com"  # Sandbox URL
    unlimit_webhook_secret: Optional[str] = None
    unlimit_environment: str = "sandbox"  # sandbox or production
    
    # Fee Collection Configuration
    revenue_wallet_address: str = "0x51951264992eb8b2b4ce4cfb0d388423561dcbd8b1165ce443886ab0e8ae8d47"  # Your revenue collection wallet
    revenue_wallet_private_key: Optional[str] = None  # Private key for fee collection
    fee_collection_contract_address: str = "0xa59f81b8d890df161743b64101f62bba9bd5f35071476849f168651e3788f583"  # Fee collector contract address
    
    # Transaction Fee Configuration (in basis points, e.g., 25 = 0.25%)
    fee_p2p_domestic: int = 25  # 0.25%
    fee_p2p_cross_border: int = 50  # 0.5%
    fee_card_present: int = 180  # 1.8%
    fee_card_not_present: int = 250  # 2.5%
    fee_merchant: int = 150  # 1.5%
    
    # Fee Collection Settings
    enable_fee_collection: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
