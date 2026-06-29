from io import StringIO

import certifi
import pandas as pd
import requests

from config import REVENUE_SHEET_ID, ROOMS_SHEET_ID

REVENUE_COLUMNS = [
    "date",
    "occupancy_room",
    "room_revenue",
    "spa_revenue",
    "fb_revenue",
    "total_revenue",
]
ROOMS_COLUMNS = [
    "room_no",
    "cleaner",
    "status",
    "inspector",
    "inspector_date",
    "result",
    "repair_staff",
    "repair_date",
    "note",
]


def _sheet_csv_url(sheet_id: str, tab_name: str) -> str:
    return (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        f"/gviz/tq?tqx=out:csv&sheet={tab_name}"
    )


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip().lower() for col in df.columns]
    return df


def _clean_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )


def _fetch_csv(url: str) -> str:
    response = requests.get(url, timeout=30, verify=certifi.where())
    response.raise_for_status()
    return response.text


def load_revenue() -> pd.DataFrame:
    url = _sheet_csv_url(REVENUE_SHEET_ID, "revenue")
    df = pd.read_csv(StringIO(_fetch_csv(url)))
    df = _normalize_columns(df)
    df = df[[col for col in REVENUE_COLUMNS if col in df.columns]]

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in REVENUE_COLUMNS[1:]:
        if col in df.columns:
            df[col] = _clean_numeric(df[col])

    return df.dropna(subset=["date"]).reset_index(drop=True)


def load_rooms() -> pd.DataFrame:
    url = _sheet_csv_url(ROOMS_SHEET_ID, "Rooms")
    df = pd.read_csv(StringIO(_fetch_csv(url)))
    df = _normalize_columns(df)
    df = df[[col for col in ROOMS_COLUMNS if col in df.columns]]

    for col in ["room_no", "cleaner", "status", "inspector", "result"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    if "inspector_date" in df.columns:
        df["inspector_date"] = pd.to_datetime(df["inspector_date"], errors="coerce")
    if "repair_date" in df.columns:
        df["repair_date"] = pd.to_datetime(df["repair_date"], errors="coerce")

    return df.reset_index(drop=True)
