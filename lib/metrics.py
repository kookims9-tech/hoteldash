from calendar import monthrange
from datetime import datetime

import pandas as pd

from config import DEFECT_RESULTS, DEFAULT_ROOM_COUNT
from data.voc import VOC_DATA


def _reference_period(dates: pd.Series) -> tuple[int, int]:
    now = datetime.now()
    current_mask = (dates.dt.year == now.year) & (dates.dt.month == now.month)
    if current_mask.any():
        return now.year, now.month

    latest = dates.max()
    return int(latest.year), int(latest.month)


def _month_mask(dates: pd.Series, year: int, month: int) -> pd.Series:
    return (dates.dt.year == year) & (dates.dt.month == month)


def _previous_period(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _current_month_mask(dates: pd.Series) -> pd.Series:
    year, month = _reference_period(dates)
    return _month_mask(dates, year, month)


def _previous_month_mask(dates: pd.Series) -> pd.Series:
    year, month = _reference_period(dates)
    prev_year, prev_month = _previous_period(year, month)
    return _month_mask(dates, prev_year, prev_month)


def _pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100


def format_currency(value: float) -> str:
    if value >= 100_000_000:
        return f"{value / 100_000_000:.2f}억원"
    if value >= 10_000:
        return f"{value / 10_000:,.0f}만원"
    return f"{value:,.0f}원"


def compute_kpis(revenue: pd.DataFrame, rooms: pd.DataFrame) -> dict:
    current = revenue[_current_month_mask(revenue["date"])]
    previous = revenue[_previous_month_mask(revenue["date"])]

    month_revenue = float(current["total_revenue"].sum())
    prev_revenue = float(previous["total_revenue"].sum())
    occupancy = float(current["occupancy_room"].mean()) if not current.empty else 0.0
    prev_occupancy = (
        float(previous["occupancy_room"].mean()) if not previous.empty else 0.0
    )

    room_count = rooms["room_no"].nunique() if not rooms.empty else DEFAULT_ROOM_COUNT
    if room_count == 0:
        room_count = DEFAULT_ROOM_COUNT

    ref_year, ref_month = _reference_period(revenue["date"])
    days_in_month = monthrange(ref_year, ref_month)[1]
    room_revenue_sum = float(current["room_revenue"].sum())
    revpar = room_revenue_sum / (room_count * days_in_month) if days_in_month else 0.0

    prev_revpar = 0.0
    if not previous.empty:
        prev_year = int(previous["date"].dt.year.iloc[0])
        prev_month = int(previous["date"].dt.month.iloc[0])
        prev_days = monthrange(prev_year, prev_month)[1]
        prev_room_revenue = float(previous["room_revenue"].sum())
        prev_revpar = prev_room_revenue / (room_count * prev_days) if prev_days else 0.0

    return {
        "month_revenue": month_revenue,
        "month_revenue_change": _pct_change(month_revenue, prev_revenue),
        "occupancy": occupancy,
        "occupancy_change": _pct_change(occupancy, prev_occupancy),
        "revpar": revpar,
        "revpar_change": _pct_change(revpar, prev_revpar),
    }


def monthly_revenue_trend(revenue: pd.DataFrame) -> pd.DataFrame:
    trend = (
        revenue.assign(month=revenue["date"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)["total_revenue"]
        .sum()
        .rename(columns={"total_revenue": "매출"})
    )
    return trend


def revenue_breakdown(revenue: pd.DataFrame) -> pd.DataFrame:
    current = revenue[_current_month_mask(revenue["date"])]
    breakdown = pd.DataFrame(
        {
            "구분": ["객실", "온천", "F&B"],
            "매출": [
                float(current["room_revenue"].sum()),
                float(current["spa_revenue"].sum()),
                float(current["fb_revenue"].sum()),
            ],
        }
    )
    return breakdown


def room_cleaning_stats(rooms: pd.DataFrame) -> dict:
    if rooms.empty:
        return {
            "defect_rate": 0.0,
            "not_cleaned": 0,
            "by_cleaner": pd.DataFrame(columns=["cleaner", "total", "defects"]),
        }

    results = rooms["result"].str.lower()
    defect_mask = rooms["result"].isin(DEFECT_RESULTS) | results.isin(
        {value.lower() for value in DEFECT_RESULTS}
    )
    defect_rate = (defect_mask.sum() / len(rooms)) * 100

    not_cleaned = int((rooms["status"] != "실시").sum()) if "status" in rooms else 0

    by_cleaner = (
        rooms.assign(defect=defect_mask.astype(int))
        .groupby("cleaner", as_index=False)
        .agg(total=("room_no", "count"), defects=("defect", "sum"))
        .sort_values("total", ascending=False)
    )

    return {
        "defect_rate": float(defect_rate),
        "not_cleaned": not_cleaned,
        "by_cleaner": by_cleaner,
    }


def voc_summary() -> dict:
    return VOC_DATA
