from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PRIMARY_DATA_FILE = RAW_DATA_DIR / "coffee_sales.csv"
FALLBACK_DATA_FILE = RAW_DATA_DIR / "coffee_sales_sample.csv"

APP_TITLE = "Kahve Dukkani Karar Destek Sistemi"
APP_CAPTION = "Satis tahmini ve kampanya planlama prototipi"

DEFAULT_FORECAST_DAYS = 7
DEFAULT_MOVING_AVERAGE_WINDOW = 7

PROMOTION_DEFAULTS = {
    "discount_rate": 10,
    "uplift_rate": 12,
    "days": 7,
}
