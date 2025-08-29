"""Configuration settings for the Text-to-SQL chatbot."""

import os
from typing import Optional
#from pydantic import BaseSettings, Field
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    groq_api_key: str = Field(..., env="GROQ_API_KEY")
    model_name: str = Field(default="mixtral-8x7b-32768", env="MODEL_NAME")
    max_tokens: int = Field(default=4000, env="MAX_TOKENS")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///retail_database.db", env="DATABASE_URL")
    
    # Context Management
    context_window_size: int = Field(default=10, env="CONTEXT_WINDOW_SIZE")
    
    # Application Configuration
    app_title: str = "Text-to-SQL Conversational Chatbot"
    app_description: str = "AI-powered chatbot for querying retail database using natural language"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
