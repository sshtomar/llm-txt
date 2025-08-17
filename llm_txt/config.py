"""Configuration management for the LLM-TXT generator."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Anthropic Configuration
    anthropic_api_key: Optional[str] = None
    
    # Crawler Configuration
    max_pages: int = 100
    max_depth: int = 3
    max_kb: int = 500
    request_delay: float = 1.0
    user_agent: str = "llm-txt-generator/0.1.0 (+https://github.com/your-org/llm-txt)"
    
    # Worker Configuration
    worker_concurrency: int = 5
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()