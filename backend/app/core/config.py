"""
Central configuration loaded from environment variables.
Using a Settings class (not scattered os.getenv calls) means:
- One place to see every config value the app needs
- Easy to validate required vars at startup
- Autocomplete in IDEs
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
    API_V1_PREFIX: str = "/api/v1"


settings = Settings()