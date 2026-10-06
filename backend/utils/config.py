"""
Configuration Settings
Loads configuration from environment variables
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # API Configuration
    api_title: str = "Resume Parser & Job Matcher"
    api_version: str = "1.0.0"
    
    # Claude API
    claude_api_key: str = os.getenv("CLAUDE_API_KEY", "sk-ant-demo-key")
    claude_model: str = "claude-sonnet-4-6"

    # Google Sign-In
    google_client_id: str = os.getenv(
        "GOOGLE_CLIENT_ID",
        "641426987741-rv89d5lardcelvv0mgikfdui05219prk.apps.googleusercontent.com",
    )
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///app.db")
    
    # Vector Store
    vector_db_path: str = os.getenv("VECTOR_DB_PATH", "./chroma_db")
    
    # Job APIs
    jsearch_api_key: str = os.getenv("JSEARCH_API_KEY", "")
    adzuna_api_key: str = os.getenv("ADZUNA_API_KEY", "")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = "app.log"
    
    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    
    # Features
    enable_api_docs: bool = True
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    
    class Config:
        env_file = Path(__file__).resolve().parents[2] / ".env"
        case_sensitive = False
