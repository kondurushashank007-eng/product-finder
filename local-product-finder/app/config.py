import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production-12345")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", str(INSTANCE_DIR / "local_product_finder.db"))
    APP_NAME = os.environ.get("APP_NAME", "Local Product Finder")
    APP_CURRENCY_SYMBOL = os.environ.get("APP_CURRENCY_SYMBOL", "$")
    APP_CURRENCY_CODE = os.environ.get("APP_CURRENCY_CODE", "USD")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    DEFAULT_USER_LAT = float(os.environ.get("DEFAULT_USER_LAT", 37.7749))
    DEFAULT_USER_LNG = float(os.environ.get("DEFAULT_USER_LNG", -122.4194))
    DEFAULT_USER_CITY = os.environ.get("DEFAULT_USER_CITY", "San Francisco, CA")
    ITEMS_PER_PAGE = int(os.environ.get("ITEMS_PER_PAGE", 12))
    TESTING = False

class TestingConfig(Config):
    TESTING = True
    DATABASE_PATH = str(INSTANCE_DIR / "test_product_finder.db")
    SECRET_KEY = "test-secret-key"
