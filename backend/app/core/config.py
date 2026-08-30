import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "AgentStore"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    SECRET_KEY: str = "supersecretkey-agentstore-buildathon-2026-sha256-production"
    API_V1_PREFIX: str = "/api/v1"

    # Database (SQLite default for standalone zero-config; PostgreSQL in Docker)
    DATABASE_URL: str = "sqlite:///./agentstore.db"
    DATABASE_SYNC_URL: str = "sqlite:///./agentstore.db"

    # Redis (Session & Idempotency store)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Razorpay (Test Mode & Webhooks)
    RAZORPAY_KEY_ID: str = "rzp_test_buildathon2026mock"
    RAZORPAY_KEY_SECRET: str = "buildathon_secret_key_mock_9918273645"
    RAZORPAY_WEBHOOK_SECRET: str = "rzp_webhook_secret_buildathon_mock"
    RAZORPAY_MOCK_MODE: bool = True

    # AI Agent Provider ("mock", "gemini", "claude", "openai")
    AGENT_PROVIDER: str = "mock"
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Server-Side Policy Guardrail Defaults
    POLICY_MAX_ORDER_VALUE: float = 50000.00
    POLICY_MAX_DISCOUNT_PERCENTAGE: float = 25.0
    POLICY_HITL_THRESHOLD: float = 10000.00
    POLICY_DAILY_TRANSACTION_LIMIT: float = 100000.00

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "*"
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
