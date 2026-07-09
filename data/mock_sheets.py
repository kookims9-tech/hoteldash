"""Fallback mock data for revenue and rooms when Google Sheets is unavailable."""

from __future__ import annotations

import math

import pandas as pd

from config import DEFAULT_ROOM_COUNT, DEFECT_RESULTS

_CLEANERS = ["김영희", "이철수", "박미경", "최동훈", "정수진"]
_INSPECTORS = ["검수A", "검수B", "검수C"]
_RESULTS_OK = ["양호", "pass", "OK"]
_NOTE_SAMPLES = ["", "", "환기 점검 필요", "욕실 타일 보수 예정", ""]
_MOCK_END_DATE = pd.Timestamp("2026-05-31")


def mock_revenue(days: int = 365) -> pd.DataFrame:
    """Synthetic daily revenue aligned with REVENUE_COLUMNS schema."""
    end = _MOCK_END_DATE
    dates = pd.date_range(end - pd.Timedelta(days=days - 1), periods=days, freq="D")
    rows: list[dict] = []
    for i, day in enumerate(dates):
        dow = int(day.dayofweek)
        weekend = 1.12 if dow >= 5 else 1.0
        season = 1.0 + 0.12 * math.sin(i / 28.0)
        occupancy = min(88.0, max(12.0, 42 + 14 * math.sin(i / 9.0) + (dow - 2) * 2.5))
        room = round(6200 * weekend * season * (occupancy / 50.0))
        spa = round(1800 * weekend * season * (0.85 + 0.15 * math.cos(i / 17.0)))
        fb = round(900 * weekend * (0.9 + 0.2 * math.sin(i / 11.0)))
        total = room + spa + fb
        rows.append(
            {
                "date": day,
                "occupancy_room": round(occupancy, 1),
                "room_revenue": room,
                "spa_revenue": spa,
                "fb_revenue": fb,
                "total_revenue": total,
            }
        )
    return pd.DataFrame(rows)


def mock_rooms(room_count: int = DEFAULT_ROOM_COUNT) -> pd.DataFrame:
    """Synthetic room inspection rows aligned with ROOMS_COLUMNS schema."""
    rows: list[dict] = []
    for idx in range(1, room_count + 1):
        cleaner = _CLEANERS[idx % len(_CLEANERS)]
        status = "실시" if idx % 17 != 0 else "미실시"
        if status != "실시":
            result = ""
            inspector = ""
            inspector_date = pd.NaT
        elif idx % 23 == 0:
            result = "불량"
            inspector = _INSPECTORS[idx % len(_INSPECTORS)]
            inspector_date = _MOCK_END_DATE - pd.Timedelta(days=idx % 5)
        else:
            result = _RESULTS_OK[idx % len(_RESULTS_OK)]
            inspector = _INSPECTORS[idx % len(_INSPECTORS)]
            inspector_date = _MOCK_END_DATE - pd.Timedelta(days=idx % 7)
        rows.append(
            {
                "room_no": str(100 + idx),
                "cleaner": cleaner,
                "status": status,
                "inspector": inspector,
                "inspector_date": inspector_date,
                "result": result,
                "repair_staff": "" if result not in DEFECT_RESULTS else "시설팀",
                "repair_date": pd.NaT
                if result not in DEFECT_RESULTS
                else _MOCK_END_DATE,
                "note": _NOTE_SAMPLES[idx % len(_NOTE_SAMPLES)],
            }
        )
    return pd.DataFrame(rows)
