import os
from pathlib import Path
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent

logger.warning("Config module loading...")

class Settings(BaseSettings):
    # base path for locating files in your repo
    BASE_DIR: Path = BASE_DIR

    FASTGPT_API_KEY: str = ""
    FASTGPT_URL: str = ""
    PROCESS_BOTH_STEPS: bool = True
    USE_CONFIG_MODE: bool = True
    QUESTION_NUMBER: int = 10

    class Config:
        env_file = ".env"

settings = Settings()