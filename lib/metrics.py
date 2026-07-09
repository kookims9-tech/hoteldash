from calendar import monthrange
from datetime import datetime

import pandas as pd

from config import DEFECT_RESULTS, DEFAULT_ROOM_COUNT, RECENT_DAYS, WEEKLY_LOOKBACK
from data.voc import VOC_DATA

# ---------------------------------------------------------------------------
# Public exports — keep in sync with app.py `from lib.metrics import (...)`.
# app.py imports:
#   available_months, available_weeks, CATEGORY_SLUGS, compute_kpis,
#   daily_revenue_table_by_week, daily_revenue_trend_by_week, default_month,
#   default_week, format_number, kpi_category_alerts, monthly_revenue_table,
#   monthly_revenue_trend, mom_comparison, mom_comparison_chart_data,
#   mom_comparison_table, recent_days_composition, recent_days_period_label,
#   recent_days_revenue_table, recent_days_revenue_trend, revenue_breakdown,
#   room_cleaners, room_cleaning_stats, room_detail_table,
#   room_inspection_results, voc_summary, week_label_for_key,
#   weekly_revenue_table, weekly_revenue_trend, daily_performance
# ---------------------------------------------------------------------------

# Category constants (④ 이상지표 자동표시)
CATEGORY_COLUMNS = {
    "객실": "room_revenue",
    "온천": "spa_revenue",
    "F&B": "fb_revenue",
}
CATEGORY_SLUGS = {"객실": "room", "온천": "spa", "F&B": "fb"}
ALERT_THRESHOLD_PCT = -10.0

__all__ = [
    "ALERT_THRESHOLD_PCT",
    "CATEGORY_COLUMNS",
    "CATEGORY_SLUGS",
    "available_months",
    "available_weeks",
    "category_mom_changes",
    "category_wow_changes",
    "compute_kpis",
    "daily_performance",
    "daily_revenue_table",
    "daily_revenue_table_by_week",
    "daily_revenue_trend",
    "daily_revenue_trend_by_week",
    "default_month",
    "default_week",
    "format_currency",
    "format_number",
    "format_week_label",
    "kpi_category_alerts",
    "monthly_revenue_table",
    "monthly_revenue_trend",
    "mom_comparison",
    "mom_comparison_chart_data",
    "mom_comparison_table",
    "recent_days_composition",
    "recent_days_period_label",
    "recent_days_revenue_table",
    "recent_days_revenue_trend",
    "revenue_breakdown",
    "room_cleaners",
    "room_cleaning_stats",
    "room_detail_table",
    "room_inspection_results",
    "voc_summary",
    "week_label_for_key",
    "weekly_revenue_table",
    "weekly_revenue_trend",
]


def _reference_period(dates: pd.Series) -> tuple[int, int]:
    if dates.empty:
        now = datetime.now()
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


def format_number(value: float, decimals: int = 0) -> str:
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:,.{decimals}f}"


def format_currency(value: float) -> str:
    return f"{format_number(value)}천원"


def _sold_room_nights(df: pd.DataFrame, room_count: int) -> float:
    if df.empty or room_count <= 0:
        return 0.0
    return float((df["occupancy_room"] / 100.0 * room_count).sum())


def _month_adr(df: pd.DataFrame, room_count: int) -> float:
    if df.empty:
        return 0.0
    sold = _sold_room_nights(df, room_count)
    if sold <= 0:
        return 0.0
    return float(df["room_revenue"].sum()) / sold


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

    adr = _month_adr(current, room_count)
    prev_adr = _month_adr(previous, room_count)

    week_kpi = _week_kpi(revenue)

    return {
        "month_revenue": month_revenue,
        "month_revenue_change": _pct_change(month_revenue, prev_revenue),
        "occupancy": occupancy,
        "occupancy_change": _pct_change(occupancy, prev_occupancy),
        "adr": adr,
        "adr_change": _pct_change(adr, prev_adr),
        "week_revenue": week_kpi["week_revenue"],
        "week_revenue_change": week_kpi["week_revenue_change"],
        "week_label": week_kpi["week_label"],
    }


def _day_revenue_sums(df: pd.DataFrame) -> dict[str, float]:
    if df.empty:
        return {"total": 0.0, "room": 0.0, "spa": 0.0, "fb": 0.0}
    return {
        "total": float(df["total_revenue"].sum()),
        "room": float(df["room_revenue"].sum()),
        "spa": float(df["spa_revenue"].sum()),
        "fb": float(df["fb_revenue"].sum()),
    }


def daily_performance(revenue: pd.DataFrame) -> dict:
    """Latest-day revenue vs prior day for Executive Summary daily panel."""
    empty = {
        "date_label": "일별 실적 없음",
        "has_data": False,
        "metrics": [],
        "composition": pd.DataFrame(columns=["구분", "매출(천원)", "share_pct", "pct_label"]),
        "total": 0.0,
    }
    if revenue.empty:
        return empty

    dates = revenue["date"].dt.normalize()
    ref_date = dates.max()
    prev_date = ref_date - pd.Timedelta(days=1)

    today_df = revenue.loc[dates == ref_date]
    prev_df = revenue.loc[dates == prev_date]

    cur = _day_revenue_sums(today_df)
    prv = _day_revenue_sums(prev_df)

    metric_defs = [
        ("매출합계", "total"),
        ("객실매출", "room"),
        ("온천매출", "spa"),
        ("F&B매출", "fb"),
    ]
    metrics = []
    for label, key in metric_defs:
        metrics.append(
            {
                "label": label,
                "amount": cur[key],
                "change_pct": _pct_change(cur[key], prv[key]),
            }
        )

    total = cur["total"]
    col_to_short = {"room_revenue": "room", "spa_revenue": "spa", "fb_revenue": "fb"}
    comp_rows = []
    for cat, col in CATEGORY_COLUMNS.items():
        amount = cur[col_to_short[col]]
        share = (amount / total * 100.0) if total > 0 else 0.0
        comp_rows.append(
            {
                "구분": cat,
                "매출(천원)": amount,
                "share_pct": share,
                "pct_label": f"{share:.1f}%",
            }
        )
    composition = pd.DataFrame(comp_rows)

    return {
        "date_label": f"{ref_date.year}년 {ref_date.month}월 {ref_date.day}일 실적",
        "has_data": not today_df.empty,
        "metrics": metrics,
        "composition": composition,
        "total": total,
    }


def _category_changes(
    current: pd.DataFrame, previous: pd.DataFrame
) -> list[dict]:
    rows: list[dict] = []
    for category, column in CATEGORY_COLUMNS.items():
        cur_val = float(current[column].sum()) if not current.empty else 0.0
        prv_val = float(previous[column].sum()) if not previous.empty else 0.0
        rows.append(
            {
                "category": category,
                "current": cur_val,
                "previous": prv_val,
                "change_pct": _pct_change(cur_val, prv_val),
            }
        )
    return rows


def category_mom_changes(revenue: pd.DataFrame) -> list[dict]:
    current = revenue[_current_month_mask(revenue["date"])]
    previous = revenue[_previous_month_mask(revenue["date"])]
    return _category_changes(current, previous)


def category_wow_changes(revenue: pd.DataFrame) -> list[dict]:
    if revenue.empty:
        return _category_changes(pd.DataFrame(), pd.DataFrame())

    latest_date = revenue["date"].max().normalize()
    current_week_start = _week_start_ts(latest_date)
    sunday = current_week_start + pd.Timedelta(days=6)
    in_progress = latest_date < sunday
    ref_week_start = (
        current_week_start - pd.Timedelta(days=7) if in_progress else current_week_start
    )
    prev_week_start = ref_week_start - pd.Timedelta(days=7)

    def _week_subset(week_start: pd.Timestamp) -> pd.DataFrame:
        week_end = week_start + pd.Timedelta(days=6)
        mask = (revenue["date"] >= week_start) & (revenue["date"] <= week_end)
        return revenue.loc[mask]

    return _category_changes(_week_subset(ref_week_start), _week_subset(prev_week_start))


def _filter_alerts(
    items: list[dict],
    *,
    categories: set[str] | None = None,
    threshold: float = ALERT_THRESHOLD_PCT,
) -> list[dict]:
    alerts: list[dict] = []
    for item in items:
        if categories is not None and item["category"] not in categories:
            continue
        change = item.get("change_pct")
        if change is not None and change <= threshold:
            alerts.append(item)
    return alerts


def kpi_category_alerts(
    revenue: pd.DataFrame, threshold: float = ALERT_THRESHOLD_PCT
) -> dict[str, list[dict]]:
    mom = category_mom_changes(revenue)
    wow = category_wow_changes(revenue)
    room_only = {"객실"}
    return {
        "month_revenue": _filter_alerts(mom, threshold=threshold),
        "occupancy": _filter_alerts(mom, categories=room_only, threshold=threshold),
        "adr": _filter_alerts(mom, categories=room_only, threshold=threshold),
        "week_revenue": _filter_alerts(wow, threshold=threshold),
    }


def _week_start(series: pd.Series) -> pd.Series:
    return series.dt.normalize() - pd.to_timedelta(series.dt.dayofweek, unit="D")


def _week_start_ts(date: pd.Timestamp) -> pd.Timestamp:
    normalized = pd.Timestamp(date).normalize()
    return normalized - pd.Timedelta(days=int(normalized.dayofweek))


def format_week_label(week_start: pd.Timestamp, latest_date: pd.Timestamp | None = None) -> str:
    sunday = week_start + pd.Timedelta(days=6)
    label = f"{week_start.strftime('%m/%d')}(월)~{sunday.strftime('%m/%d')}(일)"
    if latest_date is not None and latest_date.normalize() < sunday:
        label += " · 진행 중"
    return label


def _week_revenue_sum(revenue: pd.DataFrame, week_start: pd.Timestamp) -> float:
    week_end = week_start + pd.Timedelta(days=6)
    mask = (revenue["date"] >= week_start) & (revenue["date"] <= week_end)
    subset = revenue.loc[mask]
    if subset.empty:
        return 0.0
    return float(subset["total_revenue"].sum())


def _week_kpi(revenue: pd.DataFrame) -> dict:
    if revenue.empty:
        return {"week_revenue": 0.0, "week_revenue_change": None, "week_label": "-"}

    latest_date = revenue["date"].max().normalize()
    current_week_start = _week_start_ts(latest_date)
    sunday = current_week_start + pd.Timedelta(days=6)
    in_progress = latest_date < sunday

    ref_week_start = (
        current_week_start - pd.Timedelta(days=7) if in_progress else current_week_start
    )
    prev_week_start = ref_week_start - pd.Timedelta(days=7)

    week_revenue = _week_revenue_sum(revenue, ref_week_start)
    prev_week_revenue = _week_revenue_sum(revenue, prev_week_start)

    return {
        "week_revenue": week_revenue,
        "week_revenue_change": _pct_change(week_revenue, prev_week_revenue),
        "week_label": format_week_label(
            ref_week_start, latest_date if in_progress else None
        ),
    }


def recent_days_subset(revenue: pd.DataFrame, days: int = RECENT_DAYS) -> pd.DataFrame:
    if revenue.empty:
        return revenue.copy()
    latest = revenue["date"].max().normalize()
    cutoff = latest - pd.Timedelta(days=days - 1)
    return revenue.loc[(revenue["date"] >= cutoff) & (revenue["date"] <= latest)].sort_values(
        "date"
    )


def recent_days_revenue_trend(
    revenue: pd.DataFrame, days: int = RECENT_DAYS
) -> pd.DataFrame:
    subset = recent_days_subset(revenue, days)
    if subset.empty:
        return pd.DataFrame(columns=["일", "매출(천원)"])

    return (
        subset.assign(일=subset["date"].dt.strftime("%m/%d"))
        .rename(columns={"total_revenue": "매출(천원)"})[["일", "매출(천원)"]]
        .reset_index(drop=True)
    )


def recent_days_revenue_table(
    revenue: pd.DataFrame, days: int = RECENT_DAYS
) -> pd.DataFrame:
    subset = recent_days_subset(revenue, days)
    if subset.empty:
        return pd.DataFrame(columns=["일자", "객실", "온천", "F&B", "합계(천원)"])

    table = subset.assign(일자=subset["date"].dt.strftime("%Y-%m-%d"))
    table = table.rename(
        columns={
            "room_revenue": "객실",
            "spa_revenue": "온천",
            "fb_revenue": "F&B",
            "total_revenue": "합계(천원)",
        }
    )
    for col in ["객실", "온천", "F&B", "합계(천원)"]:
        table[col] = table[col].map(format_number)
    return table[["일자", "객실", "온천", "F&B", "합계(천원)"]].reset_index(drop=True)


def recent_days_composition(
    revenue: pd.DataFrame, days: int = RECENT_DAYS
) -> pd.DataFrame:
    subset = recent_days_subset(revenue, days)
    if subset.empty:
        return pd.DataFrame(columns=["일", "구분", "매출(천원)"])

    rows: list[dict] = []
    for _, row in subset.iterrows():
        day = row["date"].strftime("%m/%d")
        for label, col in [
            ("객실", "room_revenue"),
            ("온천", "spa_revenue"),
            ("F&B", "fb_revenue"),
        ]:
            rows.append({"일": day, "구분": label, "매출(천원)": float(row[col])})
    return pd.DataFrame(rows)


def recent_days_period_label(revenue: pd.DataFrame, days: int = RECENT_DAYS) -> str:
    subset = recent_days_subset(revenue, days)
    if subset.empty:
        return f"최근 {days}일"
    start = subset["date"].min().strftime("%Y-%m-%d")
    end = subset["date"].max().strftime("%Y-%m-%d")
    return f"{start} ~ {end}"


def _week_records(revenue: pd.DataFrame) -> pd.DataFrame:
    if revenue.empty:
        return pd.DataFrame(columns=["week_start", "last_date", "total_revenue"])

    latest_date = revenue["date"].max().normalize()
    grouped = (
        revenue.assign(week_start=_week_start(revenue["date"]))
        .groupby("week_start", as_index=False)
        .agg(total_revenue=("total_revenue", "sum"), last_date=("date", "max"))
    )
    grouped["last_date"] = grouped["last_date"].dt.normalize()
    grouped["label"] = grouped.apply(
        lambda row: format_week_label(row["week_start"], latest_date), axis=1
    )
    grouped["week_key"] = grouped["week_start"].dt.strftime("%Y-%m-%d")
    return grouped.sort_values("week_start")


def available_weeks(revenue: pd.DataFrame, limit: int = WEEKLY_LOOKBACK) -> list[str]:
    records = _week_records(revenue)
    if records.empty:
        return []
    return records.tail(limit)["week_key"].tolist()


def default_week(revenue: pd.DataFrame) -> str | None:
    weeks = available_weeks(revenue)
    return weeks[-1] if weeks else None


def week_label_for_key(revenue: pd.DataFrame, week_key: str) -> str:
    records = _week_records(revenue)
    match = records.loc[records["week_key"] == week_key]
    if match.empty:
        return week_key
    return str(match.iloc[0]["label"])


def weekly_revenue_trend(
    revenue: pd.DataFrame, limit: int = WEEKLY_LOOKBACK
) -> pd.DataFrame:
    records = _week_records(revenue).tail(limit)
    if records.empty:
        return pd.DataFrame(columns=["주", "매출(천원)"])

    return records.rename(columns={"label": "주", "total_revenue": "매출(천원)"})[
        ["주", "매출(천원)", "week_key"]
    ].reset_index(drop=True)


def weekly_revenue_table(
    revenue: pd.DataFrame, limit: int = WEEKLY_LOOKBACK
) -> pd.DataFrame:
    trend = weekly_revenue_trend(revenue, limit).copy()
    if trend.empty:
        return pd.DataFrame(columns=["주간", "매출(천원)"])
    trend = trend.rename(columns={"주": "주간"})
    trend["매출(천원)"] = trend["매출(천원)"].map(format_number)
    return trend[["주간", "매출(천원)", "week_key"]]


def _week_filter(dates: pd.Series, week_key: str) -> pd.Series:
    week_start = pd.Timestamp(week_key).normalize()
    week_end = week_start + pd.Timedelta(days=6)
    return (dates >= week_start) & (dates <= week_end)


def daily_revenue_trend_by_week(revenue: pd.DataFrame, week_key: str) -> pd.DataFrame:
    subset = revenue.loc[_week_filter(revenue["date"], week_key)].copy()
    if subset.empty:
        return pd.DataFrame(columns=["일", "매출(천원)"])

    return (
        subset.assign(일=subset["date"].dt.strftime("%m/%d"))
        .sort_values("date")
        .rename(columns={"total_revenue": "매출(천원)"})[["일", "매출(천원)"]]
        .reset_index(drop=True)
    )


def daily_revenue_table_by_week(revenue: pd.DataFrame, week_key: str) -> pd.DataFrame:
    subset = revenue.loc[_week_filter(revenue["date"], week_key)].copy()
    if subset.empty:
        return pd.DataFrame(columns=["일자", "객실", "온천", "F&B", "합계(천원)"])

    table = subset.assign(일자=subset["date"].dt.strftime("%Y-%m-%d")).sort_values("date")
    table = table.rename(
        columns={
            "room_revenue": "객실",
            "spa_revenue": "온천",
            "fb_revenue": "F&B",
            "total_revenue": "합계(천원)",
        }
    )
    for col in ["객실", "온천", "F&B", "합계(천원)"]:
        table[col] = table[col].map(format_number)
    return table[["일자", "객실", "온천", "F&B", "합계(천원)"]].reset_index(drop=True)


def monthly_revenue_trend(revenue: pd.DataFrame) -> pd.DataFrame:
    trend = (
        revenue.assign(month=revenue["date"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)["total_revenue"]
        .sum()
        .rename(columns={"total_revenue": "매출(천원)"})
    )
    return trend


def monthly_revenue_table(revenue: pd.DataFrame) -> pd.DataFrame:
    trend = monthly_revenue_trend(revenue).copy()
    trend = trend.rename(columns={"month": "월"})
    trend["매출(천원)"] = trend["매출(천원)"].map(format_number)
    return trend[["월", "매출(천원)"]]


def _month_filter(dates: pd.Series, month_str: str) -> pd.Series:
    year, month = (int(part) for part in month_str.split("-"))
    return _month_mask(dates, year, month)


def available_months(revenue: pd.DataFrame) -> list[str]:
    if revenue.empty:
        return []
    months = (
        revenue["date"].dt.to_period("M").astype(str).drop_duplicates().sort_values().tolist()
    )
    return months


def default_month(revenue: pd.DataFrame) -> str | None:
    months = available_months(revenue)
    if not months:
        return None

    ref_year, ref_month = _reference_period(revenue["date"])
    ref = f"{ref_year}-{ref_month:02d}"
    return ref if ref in months else months[-1]


def _month_calendar(month_str: str) -> pd.DatetimeIndex:
    year, month = (int(part) for part in month_str.split("-"))
    start = pd.Timestamp(year=year, month=month, day=1)
    end = start + pd.offsets.MonthEnd(0)
    return pd.date_range(start, end, freq="D")


def _daily_month_aggregate(revenue: pd.DataFrame, month_str: str) -> pd.DataFrame:
    subset = revenue.loc[_month_filter(revenue["date"], month_str)].copy()
    if subset.empty:
        return pd.DataFrame(
            columns=["date", "room_revenue", "spa_revenue", "fb_revenue", "total_revenue"]
        )

    normalized = subset.assign(date=subset["date"].dt.normalize())
    return (
        normalized.groupby("date", as_index=False)
        .agg(
            room_revenue=("room_revenue", "sum"),
            spa_revenue=("spa_revenue", "sum"),
            fb_revenue=("fb_revenue", "sum"),
            total_revenue=("total_revenue", "sum"),
        )
        .sort_values("date")
    )


def daily_revenue_trend(revenue: pd.DataFrame, month_str: str) -> pd.DataFrame:
    calendar = _month_calendar(month_str)
    if len(calendar) == 0:
        return pd.DataFrame(columns=["일", "매출(천원)"])

    agg = _daily_month_aggregate(revenue, month_str)
    full = pd.DataFrame({"date": calendar})
    merged = full.merge(agg, on="date", how="left").fillna(
        {"room_revenue": 0.0, "spa_revenue": 0.0, "fb_revenue": 0.0, "total_revenue": 0.0}
    )
    return (
        merged.assign(일=merged["date"].dt.strftime("%m/%d"))
        .rename(columns={"total_revenue": "매출(천원)"})[["일", "매출(천원)"]]
        .reset_index(drop=True)
    )


def daily_revenue_table(revenue: pd.DataFrame, month_str: str) -> pd.DataFrame:
    calendar = _month_calendar(month_str)
    if len(calendar) == 0:
        return pd.DataFrame(columns=["일자", "객실", "온천", "F&B", "합계"])

    agg = _daily_month_aggregate(revenue, month_str)
    full = pd.DataFrame({"date": calendar})
    merged = full.merge(agg, on="date", how="left").fillna(0.0)
    table = merged.assign(일자=merged["date"].dt.strftime("%Y-%m-%d")).sort_values("date")
    table = table.rename(
        columns={
            "room_revenue": "객실",
            "spa_revenue": "온천",
            "fb_revenue": "F&B",
            "total_revenue": "합계",
        }
    )
    for col in ["객실", "온천", "F&B", "합계"]:
        table[col] = table[col].map(format_number)
    return table[["일자", "객실", "온천", "F&B", "합계"]].reset_index(drop=True)


def revenue_breakdown(revenue: pd.DataFrame, month: str | None = None) -> pd.DataFrame:
    if month:
        current = revenue.loc[_month_filter(revenue["date"], month)]
    else:
        current = revenue.loc[_current_month_mask(revenue["date"])]

    breakdown = pd.DataFrame(
        {
            "구분": ["객실", "온천", "F&B"],
            "매출(천원)": [
                float(current["room_revenue"].sum()),
                float(current["spa_revenue"].sum()),
                float(current["fb_revenue"].sum()),
            ],
        }
    )
    return breakdown


def cleaning_status_label(status: str, result: str) -> str:
    if status != "실시":
        return "미실시"
    if result in DEFECT_RESULTS or result.lower() in {v.lower() for v in DEFECT_RESULTS}:
        return "불량"
    return "완료"


def room_inspection_results(rooms: pd.DataFrame) -> list[str]:
    if rooms.empty or "result" not in rooms.columns:
        return []
    return sorted(rooms["result"].dropna().unique().tolist())


def room_detail_table(
    rooms: pd.DataFrame,
    cleaner: str | None = None,
    status_filter: str | None = None,
    result_filter: str | None = None,
) -> pd.DataFrame:
    if rooms.empty:
        return pd.DataFrame(
            columns=["객실번호", "담당자", "상태", "검수자", "검수일", "검수결과", "비고"]
        )

    detail = rooms.copy()
    if cleaner and cleaner != "전체":
        detail = detail[detail["cleaner"] == cleaner]
    if result_filter and result_filter != "전체":
        detail = detail[detail["result"] == result_filter]

    detail["상태"] = detail.apply(
        lambda row: cleaning_status_label(row.get("status", ""), row.get("result", "")),
        axis=1,
    )
    if status_filter and status_filter != "전체":
        detail = detail[detail["상태"] == status_filter]

    detail["검수일"] = pd.to_datetime(detail.get("inspector_date"), errors="coerce").dt.strftime(
        "%Y-%m-%d"
    )
    detail["검수일"] = detail["검수일"].fillna("-")

    return (
        detail.rename(
            columns={
                "room_no": "객실번호",
                "cleaner": "담당자",
                "inspector": "검수자",
                "result": "검수결과",
                "note": "비고",
            }
        )[["객실번호", "담당자", "상태", "검수자", "검수일", "검수결과", "비고"]]
        .sort_values("객실번호")
        .reset_index(drop=True)
    )


def room_cleaners(rooms: pd.DataFrame) -> list[str]:
    if rooms.empty or "cleaner" not in rooms.columns:
        return []
    return sorted(rooms["cleaner"].dropna().unique().tolist())


def _prior_month_str(month_str: str) -> str | None:
    months = month_str.split("-")
    if len(months) != 2:
        return None
    year, month = int(months[0]), int(months[1])
    prev_year, prev_month = _previous_period(year, month)
    return f"{prev_year}-{prev_month:02d}"


def mom_comparison(revenue: pd.DataFrame, month_str: str) -> dict:
    year, month = (int(part) for part in month_str.split("-"))
    current = revenue.loc[_month_mask(revenue["date"], year, month)]
    prev_year, prev_month = _previous_period(year, month)
    prior = revenue.loc[_month_mask(revenue["date"], prev_year, prev_month)]

    def _sums(df: pd.DataFrame) -> dict[str, float]:
        if df.empty:
            return {"total": 0.0, "room": 0.0, "spa": 0.0, "fb": 0.0}
        return {
            "total": float(df["total_revenue"].sum()),
            "room": float(df["room_revenue"].sum()),
            "spa": float(df["spa_revenue"].sum()),
            "fb": float(df["fb_revenue"].sum()),
        }

    cur = _sums(current)
    prv = _sums(prior)

    return {
        "current_label": f"{year}년 {month:02d}월",
        "prior_label": f"{prev_year}년 {prev_month:02d}월",
        "current": cur,
        "prior": prv,
        "total_change_pct": _pct_change(cur["total"], prv["total"]),
        "has_prior": not prior.empty,
    }


def mom_comparison_chart_data(revenue: pd.DataFrame, month_str: str) -> pd.DataFrame:
    mom = mom_comparison(revenue, month_str)
    rows = []
    labels = {
        "total": "합계",
        "room": "객실",
        "spa": "온천",
        "fb": "F&B",
    }
    for key, label in labels.items():
        rows.append(
            {
                "구분": label,
                "기간": mom["current_label"],
                "매출(천원)": mom["current"][key],
            }
        )
        rows.append(
            {
                "구분": label,
                "기간": mom["prior_label"],
                "매출(천원)": mom["prior"][key],
            }
        )
    return pd.DataFrame(rows)


def mom_comparison_table(revenue: pd.DataFrame, month_str: str) -> pd.DataFrame:
    mom = mom_comparison(revenue, month_str)
    rows = []
    labels = {
        "total": "합계",
        "room": "객실",
        "spa": "온천",
        "fb": "F&B",
    }
    for key, label in labels.items():
        cur_val = mom["current"][key]
        prv_val = mom["prior"][key]
        change = _pct_change(cur_val, prv_val)
        change_text = f"{change:+.1f}%" if change is not None else "-"
        rows.append(
            {
                "구분": label,
                "당월(천원)": format_number(cur_val),
                "전월(천원)": format_number(prv_val),
                "증감": change_text,
            }
        )
    return pd.DataFrame(rows)


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
