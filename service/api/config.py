"""
Configuration for ClawBackup API
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Database
    database_url: str = "postgresql://clawbackup:clawbackup@localhost:5432/clawbackup"
    
    # S3/MinIO Storage
    s3_endpoint: str = "http://localhost:9000"
    s3_bucket: str = "clawbackup"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_region: str = "us-east-1"
    
    # Service Limits
    free_tier_quota_gb: float = 1.0  # 1GB free
    backup_retention_days: int = 30
    max_backup_size_mb: int = 500
    
    # Security
    api_key_header: str = "Authorization"
    
    class Config:
        env_prefix = "CLAWBACKUP_"
        env_file = ".env"
