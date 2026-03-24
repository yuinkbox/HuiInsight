# -*- coding: utf-8 -*-
"""
Configuration management for multi-environment support.

This module provides centralized configuration management for the backend,
supporting development, production, and test environments.

Author : xvyu
Version: 1.0.0
"""

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Environment type
Environment = Literal["development", "production", "test"]


class DatabaseConfig(BaseModel):
    """Database configuration."""

    url: str = Field(
        ...,
        description="Database connection URL",
        examples=["mysql+pymysql://user:pass@localhost:3306/dbname?charset=utf8mb4"],
    )
    pool_size: int = Field(10, description="Connection pool size")
    max_overflow: int = Field(20, description="Maximum overflow connections")
    pool_recycle: int = Field(1800, description="Connection recycle time in seconds")
    echo: bool = Field(False, description="Enable SQL echo for debugging")


class AuthConfig(BaseModel):
    """Authentication configuration."""

    jwt_secret_key: str = Field(
        ..., description="JWT secret key (minimum 32 characters)", min_length=32
    )
    jwt_algorithm: str = Field("HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        30, description="Access token expiry in minutes"
    )


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str = Field("0.0.0.0", description="Server host address")
    port: int = Field(8000, description="Server port")
    reload: bool = Field(False, description="Enable auto-reload for development")


class AppConfig(BaseModel):
    """Application configuration."""

    # Environment
    environment: Environment = Field("development", description="Current environment")
    debug: bool = Field(False, description="Debug mode")
    app_name: str = Field("徽鉴 HuiInsight", description="Application name")
    app_version: str = Field("1.0.0", description="Application version")

    # Components
    database: DatabaseConfig
    auth: AuthConfig
    server: ServerConfig

    # Features
    enable_cors: bool = Field(True, description="Enable CORS middleware")
    enable_docs: bool = Field(True, description="Enable API documentation")
    enable_redoc: bool = Field(True, description="Enable ReDoc documentation")


def load_environment() -> Environment:
    """Load environment from OS environment variable."""
    env = os.environ.get("ENVIRONMENT", "development").lower()
    if env not in ["development", "production", "test"]:
        print(f"⚠ Warning: Unknown environment '{env}', defaulting to 'development'")
        env = "development"
    return env  # type: ignore


def load_env_file(environment: Environment) -> bool:
    """Load environment variables from appropriate .env file.

    Returns:
        True if environment file was loaded, False otherwise.
    """
    env_files = [
        Path(__file__).parent.parent / f".env.{environment}",
        Path(__file__).parent.parent / ".env",
        Path(__file__).parent.parent / ".env.example",
    ]

    for env_file in env_files:
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=True)
            print(f"📁 Loaded environment file: {env_file.name}")
            return True

    print(f"⚠ Warning: No .env file found for environment '{environment}'")
    return False


def create_config() -> AppConfig:
    """Create application configuration from environment variables."""
    # Determine environment
    environment = load_environment()

    # Load environment file
    load_env_file(environment)

    # Determine debug mode
    debug = (
        environment == "development"
        or os.environ.get("DEBUG", "false").lower() == "true"
    )

    # Database configuration
    database_config = DatabaseConfig(
        url=os.environ.get(
            "DATABASE_URL",
            "mysql+pymysql://ahdunyi_superyu:changeme@127.0.0.1:3306/ahdunyi_pro_db?charset=utf8mb4",
        ),
        echo=debug,
    )

    # Auth configuration
    auth_config = AuthConfig(
        jwt_secret_key=os.environ.get(
            "JWT_SECRET_KEY", "development-jwt-secret-key-change-in-production"
        ),
        jwt_algorithm=os.environ.get("JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(
            os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        ),
    )

    # Server configuration
    server_config = ServerConfig(
        host=os.environ.get("SERVER_HOST", "0.0.0.0"),
        port=int(os.environ.get("SERVER_PORT", "8000")),
        reload=debug,
    )

    # Create app config
    config = AppConfig(
        environment=environment,
        debug=debug,
        app_name=os.environ.get("APP_NAME", "徽鉴 HuiInsight"),
        app_version=os.environ.get("APP_VERSION", "1.0.0"),
        database=database_config,
        auth=auth_config,
        server=server_config,
        enable_cors=True,
        enable_docs=debug,  # Only enable docs in development
        enable_redoc=debug,  # Only enable redoc in development
    )

    # Log configuration (safely)
    _log_config(config)

    return config


def _log_config(config: AppConfig) -> None:
    """Log configuration safely (without sensitive information)."""
    print("=" * 60)
    print(f"🚀 {config.app_name} - {config.environment.upper()} Environment")
    print("=" * 60)
    print(f"📊 Environment: {config.environment}")
    print(f"🔧 Debug Mode: {config.debug}")
    print(f"🌐 Server: {config.server.host}:{config.server.port}")
    print(f"📁 Database: {_safe_db_url(config.database.url)}")
    print(f"🔐 JWT Algorithm: {config.auth.jwt_algorithm}")
    print(f"📚 API Docs: {'Enabled' if config.enable_docs else 'Disabled'}")
    print(f"🔄 Auto-reload: {config.server.reload}")
    print("=" * 60)


def _safe_db_url(db_url: str) -> str:
    """Return a safe version of database URL (without password)."""
    if "@" not in db_url:
        return db_url

    # Split at @ and take everything after it
    parts = db_url.split("@")
    if len(parts) == 2:
        return f"***@{parts[1]}"

    return "***"


# Global configuration instance
config = create_config()
