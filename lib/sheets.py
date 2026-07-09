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

_DATA_SOURCE: dict[str, str] = {"revenue": "unknown", "rooms": "unknown"}


def data_sources() -> dict[str, str]:
    return dict(_DATA_SOURCE)


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
    # Ignore IDE/local proxy env vars for public Google Sheets CSV reads.
    session = requests.Session()
    session.trust_env = False
    response = session.get(url, timeout=30, verify=certifi.where())
    response.raise_for_status()
    return response.text


def _require_columns(df: pd.DataFrame, required_columns: list[str], label: str) -> pd.DataFrame:
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"{label} 시트 필수 컬럼 누락: {', '.join(missing)}")
    return df[required_columns]


def _load_revenue_from_sheet() -> pd.DataFrame:
    url = _sheet_csv_url(REVENUE_SHEET_ID, "revenue")
    df = pd.read_csv(StringIO(_fetch_csv(url)))
    df = _normalize_columns(df)
    df = _require_columns(df, REVENUE_COLUMNS, "revenue")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in REVENUE_COLUMNS[1:]:
        if col in df.columns:
            df[col] = _clean_numeric(df[col])

    df = df.dropna(subset=["date"]).reset_index(drop=True)
    if df.empty:
        raise ValueError("revenue 시트에 유효한 date 행이 없습니다.")
    return df


def _load_rooms_from_sheet() -> pd.DataFrame:
    url = _sheet_csv_url(ROOMS_SHEET_ID, "Rooms")
    df = pd.read_csv(StringIO(_fetch_csv(url)))
    df = _normalize_columns(df)
    df = _require_columns(df, ROOMS_COLUMNS, "Rooms")

    for col in ["room_no", "cleaner", "status", "inspector", "result"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    if "inspector_date" in df.columns:
        df["inspector_date"] = pd.to_datetime(df["inspector_date"], errors="coerce")
    if "repair_date" in df.columns:
        df["repair_date"] = pd.to_datetime(df["repair_date"], errors="coerce")

    df = df.reset_index(drop=True)
    if df.empty:
        raise ValueError("Rooms 시트에 유효한 행이 없습니다.")
    return df


def load_revenue() -> pd.DataFrame:
    try:
        df = _load_revenue_from_sheet()
        _DATA_SOURCE["revenue"] = "sheets"
        return df
    except Exception as exc:
        _DATA_SOURCE["revenue"] = "error"
        raise RuntimeError(f"실적 시트 로딩 실패: {exc}") from exc


def load_rooms() -> pd.DataFrame:
    try:
        df = _load_rooms_from_sheet()
        _DATA_SOURCE["rooms"] = "sheets"
        return df
    except Exception as exc:
        _DATA_SOURCE["rooms"] = "error"
        raise RuntimeError(f"객실 시트 로딩 실패: {exc}") from exc
