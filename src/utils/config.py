"""
Configuration Module

Handles all configuration settings and environment variables for the application.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config(BaseSettings):
    """Configuration settings for the Inventory Replenishment Copilot."""
    
    # Application settings
    app_name: str = Field(default="Inventory Replenishment Copilot", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug_mode: bool = Field(default=False, env="DEBUG_MODE")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Composio configuration
    composio_api_key: str = Field(..., env="COMPOSIO_API_KEY")
    composio_base_url: str = Field(default="https://backend.composio.dev", env="COMPOSIO_BASE_URL")
    
    # LLM configuration
    llm_provider: str = Field(default="groq", env="LLM_PROVIDER")
    llm_model: str = Field(default="llama-3.3-70b-versatile", env="LLM_MODEL")
    groq_api_key: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Google Sheets configuration
    google_sheets_credentials_json: str = Field(..., env="GOOGLE_SHEETS_CREDENTIALS_JSON")
    google_sheets_spreadsheet_id: str = Field(..., env="GOOGLE_SHEETS_SPREADSHEET_ID")
    google_sheets_worksheet_name: str = Field(default="Inventory", env="GOOGLE_SHEETS_WORKSHEET_NAME")
    
    # Notion configuration
    notion_api_key: str = Field(..., env="NOTION_TOKEN")
    notion_database_id: str = Field(..., env="NOTION_DB_ID")
    
    # Email configuration
    email_provider: str = Field(default="gmail", env="EMAIL_PROVIDER")
    sender_email: str = Field(..., env="GMAIL_EMAIL")
    sender_password: str = Field(..., env="GMAIL_APP_PASSWORD")
    
    # SMTP configuration (alternative to Gmail)
    smtp_server: Optional[str] = Field(default=None, env="SMTP_SERVER")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")
    
    # Supplier API configuration (optional)
    supplier_api_base_url: Optional[str] = Field(default=None, env="SUPPLIER_API_BASE_URL")
    supplier_api_key: Optional[str] = Field(default=None, env="SUPPLIER_API_KEY")
    supplier_api_version: str = Field(default="v1", env="SUPPLIER_API_VERSION")
    
    # Agent configuration
    check_interval: int = Field(default=3600, env="AGENT_CHECK_INTERVAL")  # seconds
    inventory_threshold_percentage: float = Field(default=20.0, env="INVENTORY_THRESHOLD_PERCENTAGE")
    max_retry_attempts: int = Field(default=3, env="MAX_RETRY_ATTEMPTS")
    
    # Database configuration
    database_url: str = Field(default="sqlite:///inventory.db", env="DATABASE_URL")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    encryption_key: Optional[str] = Field(default=None, env="ENCRYPTION_KEY")
    
    # Business logic parameters
    safety_stock_multiplier: float = Field(default=1.2, env="SAFETY_STOCK_MULTIPLIER")
    default_lead_time_days: int = Field(default=7, env="DEFAULT_LEAD_TIME_DAYS")
    holding_cost_rate: float = Field(default=0.25, env="HOLDING_COST_RATE")
    order_cost: float = Field(default=50.0, env="ORDER_COST")
    service_level: float = Field(default=0.95, env="SERVICE_LEVEL")
    
    # Company information
    company_name: str = Field(default="Your Company", env="COMPANY_NAME")
    company_email: Optional[str] = Field(default=None, env="COMPANY_EMAIL")
    company_phone: Optional[str] = Field(default=None, env="COMPANY_PHONE")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        """Initialize configuration with validation."""
        super().__init__(**kwargs)
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration settings."""
        # Validate file paths
        if not os.path.exists(self.google_credentials_file):
            raise ValueError(f"Google credentials file not found: {self.google_credentials_file}")
        
        # Validate email provider
        if self.email_provider not in ['gmail', 'smtp']:
            raise ValueError(f"Invalid email provider: {self.email_provider}")
        
        # Validate SMTP configuration if using SMTP
        if self.email_provider == 'smtp' and not self.smtp_server:
            raise ValueError("SMTP server must be specified when using SMTP email provider")
        
        # Validate percentage values
        if not 0 <= self.inventory_threshold_percentage <= 100:
            raise ValueError("Inventory threshold percentage must be between 0 and 100")
        
        if not 0 <= self.service_level <= 1:
            raise ValueError("Service level must be between 0 and 1")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.debug_mode
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug_mode
    
    def get_smtp_config(self) -> dict:
        """Get SMTP configuration as dictionary."""
        if self.email_provider == 'gmail':
            return {
                'server': 'smtp.gmail.com',
                'port': 587,
                'use_tls': True,
                'username': self.sender_email,
                'password': self.sender_password
            }
        else:
            return {
                'server': self.smtp_server,
                'port': self.smtp_port,
                'use_tls': self.smtp_use_tls,
                'username': self.sender_email,
                'password': self.sender_password
            }
    
    def get_database_config(self) -> dict:
        """Get database configuration as dictionary."""
        return {
            'url': self.database_url,
            'echo': self.debug_mode
        }
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary (excluding sensitive data)."""
        config_dict = self.dict()
        
        # Remove sensitive information
        sensitive_keys = [
            'composio_api_key',
            'notion_api_key', 
            'sender_password',
            'supplier_api_key',
            'secret_key',
            'encryption_key',
            'groq_api_key',
            'openai_api_key'
        ]
        
        for key in sensitive_keys:
            if key in config_dict:
                config_dict[key] = "***HIDDEN***"
        
        return config_dict