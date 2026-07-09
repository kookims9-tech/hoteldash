import os

REVENUE_SHEET_ID = os.getenv(
    "REVENUE_SHEET_ID", "13SeEWtUh82azC8DYBtvY669KOoiVoYvCCWn9G_tSZDQ"
)
ROOMS_SHEET_ID = os.getenv(
    "ROOMS_SHEET_ID", "1LQt7W4GARpJkGCVHrwhLtfrsBJUsxn8IuMNj4WjPwOA"
)
HOTEL_NAME = os.getenv("HOTEL_NAME", "○○온천관광호텔")
REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "60"))

DEFECT_RESULTS = {"불량", "fail", "defect", "ng", "NG"}
DEFAULT_ROOM_COUNT = 150
RECENT_DAYS = 7
WEEKLY_LOOKBACK = 12

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
