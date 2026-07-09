"""Executive management analysis for the latest trailing 12-month window."""

from __future__ import annotations

import pandas as pd

from lib.metrics import (
    CATEGORY_COLUMNS,
    category_mom_changes,
    compute_kpis,
    format_number,
    kpi_category_alerts,
    room_cleaning_stats,
    voc_summary,
)

_SEASON_ORDER = ["봄(3~5월)", "여름(6~8월)", "가을(9~11월)", "겨울(12~2월)"]
_QUARTER_ORDER = ["1Q", "2Q", "3Q", "4Q"]
_SEGMENT_ORDER = ["객실", "온천", "F&B"]


def _analysis_end_month(revenue: pd.DataFrame) -> pd.Timestamp:
    if revenue.empty:
        return pd.Timestamp("today").normalize() + pd.offsets.MonthEnd(-1)
    latest = pd.Timestamp(revenue["date"].max()).normalize()
    return latest.replace(day=1) + pd.offsets.MonthEnd(0)


def _analysis_period(revenue: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    end_month = _analysis_end_month(revenue)
    start_month = (end_month.replace(day=1) - pd.DateOffset(months=11)).normalize()
    return start_month, end_month


def _period_subset(revenue: pd.DataFrame) -> pd.DataFrame:
    if revenue.empty:
        return revenue.copy()
    start_month, end_month = _analysis_period(revenue)
    mask = (revenue["date"] >= start_month) & (revenue["date"] <= end_month)
    return revenue.loc[mask].copy()


def _prior_period_subset(revenue: pd.DataFrame) -> pd.DataFrame:
    if revenue.empty:
        return revenue.copy()
    start_month, end_month = _analysis_period(revenue)
    prior_start = start_month - pd.DateOffset(years=1)
    prior_end = end_month - pd.DateOffset(years=1)
    mask = (revenue["date"] >= prior_start) & (revenue["date"] <= prior_end)
    return revenue.loc[mask].copy()


def _season_label(month: int) -> str:
    if month in (3, 4, 5):
        return "봄(3~5월)"
    if month in (6, 7, 8):
        return "여름(6~8월)"
    if month in (9, 10, 11):
        return "가을(9~11월)"
    return "겨울(12~2월)"


def _quarter_label(month: int) -> str:
    return f"{(month - 1) // 3 + 1}Q"


def _pct_share(value: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return value / total * 100.0


def _pct_change(cur: float, prev: float) -> float | None:
    if prev == 0:
        return None if cur == 0 else 100.0
    return (cur - prev) / prev * 100.0


def annual_revenue_summary(revenue: pd.DataFrame) -> dict:
    start_month, end_month = _analysis_period(revenue)
    current = _period_subset(revenue)
    previous = _prior_period_subset(revenue)

    cur_total = float(current["total_revenue"].sum()) if not current.empty else 0.0
    prv_total = float(previous["total_revenue"].sum()) if not previous.empty else 0.0
    segments = {}
    for label, col in CATEGORY_COLUMNS.items():
        segments[label] = float(current[col].sum()) if not current.empty else 0.0

    top_segment = max(segments, key=segments.get) if segments else "—"
    return {
        "year": int(end_month.year),
        "period_label": f"{start_month.strftime('%Y.%m')}~{end_month.strftime('%Y.%m')}",
        "period_desc": f"{start_month.strftime('%Y.%m')}~{end_month.strftime('%Y.%m')} 최근 1년",
        "total": cur_total,
        "yoy_change": _pct_change(cur_total, prv_total),
        "has_prior_year": prv_total > 0,
        "segments": segments,
        "top_segment": top_segment,
        "top_segment_share": _pct_share(segments.get(top_segment, 0.0), cur_total),
        "days_covered": int(current["date"].dt.normalize().nunique()) if not current.empty else 0,
    }


def seasonal_revenue_report(revenue: pd.DataFrame) -> pd.DataFrame:
    subset = _period_subset(revenue)
    if subset.empty:
        return pd.DataFrame(columns=["계절", "객실", "온천", "F&B", "합계", "비중(%)"])

    work = subset.assign(
        계절=subset["date"].dt.month.map(_season_label),
    )
    grouped = (
        work.groupby("계절", as_index=False)
        .agg(
            **{
                "객실": ("room_revenue", "sum"),
                "온천": ("spa_revenue", "sum"),
                "F&B": ("fb_revenue", "sum"),
                "합계": ("total_revenue", "sum"),
            }
        )
    )
    total = float(grouped["합계"].sum())
    grouped["비중(%)"] = grouped["합계"].map(lambda v: _pct_share(float(v), total))
    grouped["계절"] = pd.Categorical(grouped["계절"], categories=_SEASON_ORDER, ordered=True)
    grouped = grouped.sort_values("계절").reset_index(drop=True)
    return grouped


def seasonal_revenue_chart_data(revenue: pd.DataFrame) -> pd.DataFrame:
    report = seasonal_revenue_report(revenue)
    if report.empty:
        return pd.DataFrame(columns=["계절", "구분", "매출(천원)"])

    rows: list[dict] = []
    for _, row in report.iterrows():
        for segment in _SEGMENT_ORDER:
            rows.append(
                {
                    "계절": row["계절"],
                    "구분": segment,
                    "매출(천원)": float(row[segment]),
                }
            )
    return pd.DataFrame(rows)


def seasonal_revenue_table(revenue: pd.DataFrame) -> pd.DataFrame:
    report = seasonal_revenue_report(revenue)
    if report.empty:
        return report

    table = report.copy()
    for col in ["객실", "온천", "F&B", "합계"]:
        table[col] = table[col].map(format_number)
    table["비중(%)"] = report["비중(%)"].map(lambda v: f"{v:.1f}%")
    return table[["계절", "객실", "온천", "F&B", "합계", "비중(%)"]]


def segment_annual_report(revenue: pd.DataFrame) -> pd.DataFrame:
    current = _period_subset(revenue)
    previous = _prior_period_subset(revenue)
    if current.empty:
        return pd.DataFrame(columns=["사업부문", "연매출(천원)", "비중(%)", "전년비(%)"])

    cur_total = float(current["total_revenue"].sum())
    rows: list[dict] = []
    for label, col in CATEGORY_COLUMNS.items():
        cur_val = float(current[col].sum())
        prv_val = float(previous[col].sum()) if not previous.empty else 0.0
        rows.append(
            {
                "사업부문": label,
                "연매출(천원)": cur_val,
                "비중(%)": _pct_share(cur_val, cur_total),
                "전년비(%)": _pct_change(cur_val, prv_val),
            }
        )
    return pd.DataFrame(rows)


def segment_annual_table(revenue: pd.DataFrame) -> pd.DataFrame:
    report = segment_annual_report(revenue)
    if report.empty:
        return report

    table = report.copy()
    table["연매출(천원)"] = report["연매출(천원)"].map(format_number)
    table["비중(%)"] = report["비중(%)"].map(lambda v: f"{v:.1f}%")
    table["전년비(%)"] = report["전년비(%)"].map(
        lambda v: "—" if v is None else f"{v:+.1f}%"
    )
    return table


def quarterly_revenue_trend(revenue: pd.DataFrame) -> pd.DataFrame:
    subset = _period_subset(revenue)
    if subset.empty:
        return pd.DataFrame(columns=["분기", "매출(천원)", "객실", "온천", "F&B"])

    work = subset.assign(
        분기=subset["date"].dt.month.map(_quarter_label),
        quarter_num=((subset["date"].dt.month - 1) // 3 + 1),
    )
    grouped = (
        work.groupby(["quarter_num", "분기"], as_index=False)
        .agg(
            **{
                "매출": ("total_revenue", "sum"),
                "객실": ("room_revenue", "sum"),
                "온천": ("spa_revenue", "sum"),
                "F&B": ("fb_revenue", "sum"),
            }
        )
        .rename(columns={"매출": "매출(천원)"})
    )
    grouped["분기"] = pd.Categorical(grouped["분기"], categories=_QUARTER_ORDER, ordered=True)
    return grouped.sort_values(["quarter_num", "분기"]).drop(columns=["quarter_num"]).reset_index(drop=True)


def quarterly_revenue_table(revenue: pd.DataFrame) -> pd.DataFrame:
    trend = quarterly_revenue_trend(revenue)
    if trend.empty:
        return trend

    table = trend.copy()
    for col in ["매출(천원)", "객실", "온천", "F&B"]:
        table[col] = trend[col].map(format_number)
    return table


def executive_briefing(revenue: pd.DataFrame, rooms: pd.DataFrame, kpis: dict) -> dict:
    annual = annual_revenue_summary(revenue)
    seasonal = seasonal_revenue_report(revenue)
    voc = voc_summary()
    room_stats = room_cleaning_stats(rooms)

    peak_season = "—"
    if not seasonal.empty:
        peak = seasonal.loc[seasonal["합계"].idxmax()]
        peak_season = str(peak["계절"])

    yoy_text = "전년 비교 데이터 없음"
    if annual["has_prior_year"] and annual["yoy_change"] is not None:
        yoy_text = f"전년 대비 {annual['yoy_change']:+.1f}%"

    headline = (
        f"{annual['period_label']} 누적 매출 {format_number(annual['total'])}천원, {yoy_text}. "
        f"최대 수익 사업부문은 {annual['top_segment']}({annual['top_segment_share']:.1f}%)이며, "
        f"성수기는 {peak_season}로 분석됩니다."
    )

    bullets: list[str] = []
    if kpis.get("occupancy_change") is not None:
        bullets.append(f"당월 점유율 전월 대비 {kpis['occupancy_change']:+.1f}%p")
    if kpis.get("month_revenue_change") is not None:
        bullets.append(f"당월 매출 전월 대비 {kpis['month_revenue_change']:+.1f}%")
    bullets.append(f"평균 고객 평점 {voc.get('average_rating', 0):.1f}점")
    bullets.append(
        f"객실 불량률 {format_number(room_stats.get('defect_rate', 0), 1)}% · "
        f"청소 미실시 {format_number(room_stats.get('not_cleaned', 0))}건"
    )

    return {
        "headline": headline,
        "bullets": bullets,
        "annual": annual,
        "peak_season": peak_season,
    }


def _strategy_item(
    *,
    id: str,
    priority: str,
    title: str,
    body: str,
    actions: list[str],
) -> dict:
    return {
        "id": id,
        "priority": priority,
        "title": title,
        "body": body,
        "actions": actions,
    }


def generate_marketing_strategy(
    revenue: pd.DataFrame, kpis: dict, voc: dict | None = None
) -> list[dict]:
    voc_data = voc or voc_summary()
    annual = annual_revenue_summary(revenue)
    seasonal = seasonal_revenue_report(revenue)
    segment = segment_annual_report(revenue)
    strategies: list[dict] = []

    if not segment.empty:
        spa_row = segment.loc[segment["사업부문"] == "온천"]
        if not spa_row.empty and float(spa_row.iloc[0]["비중(%)"]) >= 28:
            strategies.append(
                _strategy_item(
                    id="mkt_spa_brand",
                    priority="high",
                    title="온천·웰니스 브랜드 중심 프로모션",
                    body=(
                        "온천 사업부문 비중이 높습니다. 지역 관광 연계 패키지와 "
                        "비수기 주중 웰니스 프로그램으로 객실 전환율을 높이세요."
                    ),
                    actions=[
                        "온천+숙박 번들 상품을 OTA·자사몰에 시즌별로 재배치",
                        "비수기 주중 '온천 먼저 방문' 리타겟 광고 집행",
                        "리뷰 키워드 '온천'을 메인 비주얼·랜딩 카피에 반영",
                    ],
                )
            )

        fb_row = segment.loc[segment["사업부문"] == "F&B"]
        if not fb_row.empty:
            fb_change = fb_row.iloc[0]["전년비(%)"]
            if fb_change is not None and fb_change <= -5:
                strategies.append(
                    _strategy_item(
                        id="mkt_fb_revive",
                        priority="high",
                        title="F&B 체험형 마케팅 강화",
                        body=(
                            "F&B 매출이 전년 대비 둔화되었습니다. 지역 식재료 스토리와 "
                            "투숙객 전용 다이닝 오퍼로 객단가를 회복하세요."
                        ),
                        actions=[
                            "조식·디너 세트 메뉴를 객실 패키지에 기본 포함 옵션화",
                            "비투숙객 대상 온천+식사 쿠폰으로 요일별 유입 확대",
                            "식음 VOC 키워드를 메뉴·서빙 개선 백로그와 연동",
                        ],
                    )
                )

    if not seasonal.empty:
        winter = seasonal.loc[seasonal["계절"] == "겨울(12~2월)", "합계"]
        summer = seasonal.loc[seasonal["계절"] == "여름(6~8월)", "합계"]
        if not winter.empty and not summer.empty and float(winter.iloc[0]) > float(summer.iloc[0]):
            strategies.append(
                _strategy_item(
                    id="mkt_winter_peak",
                    priority="medium",
                    title="겨울 성수기 수요 선점 캠페인",
                    body=(
                        "겨울철 매출 비중이 여름보다 큽니다. 온천 수요 피크 시점에 "
                        "예약 전환을 앞당기는 조기 예약 프로모션을 설계하세요."
                    ),
                    actions=[
                        "11월까지 '겨울 온천 패키지' 조기 예약 할인 운영",
                        "기업 연말 워크숍·가족 모임 타깃 B2B 제안서 배포",
                        "성수기 객실 가동률 시뮬레이션 기반 가격 밴드 조정",
                    ],
                )
            )

    occ_change = kpis.get("occupancy_change")
    if occ_change is not None and occ_change < 0:
        strategies.append(
            _strategy_item(
                id="mkt_occupancy_channel",
                priority="high",
                title="점유율 회복 — 채널·요일 믹스 최적화",
                body=(
                    "점유율이 전월 대비 하락했습니다. 고마진 직판 비중을 유지하면서 "
                    "저점유 요일의 프로모션 믹스를 재편하세요."
                ),
                actions=[
                    "일~목 저점유 요일 전용 '온천+조식' 플래시 딜 운영",
                    "리피터·멤버십 대상 직판 전환 캠페인",
                    "채널별 ADR·취소율 대시보드 주간 리뷰",
                ],
            )
        )

    avg_rating = float(voc_data.get("average_rating", 0))
    if avg_rating >= 4.0:
        strategies.append(
            _strategy_item(
                id="mkt_reputation",
                priority="medium",
                title="평판 자산 기반 UGC 마케팅",
                body=(
                    f"평균 평점 {avg_rating:.1f}점으로 평판이 양호합니다. "
                    "고평점 리뷰를 시즌 캠페인 소재로 전환하세요."
                ),
                actions=[
                    "SNS 숏폼 — 온천·조식 하이라이트 주 2회 게시",
                    "투숙 후 리뷰 작성 시 사우나 이용권 리워드",
                    "키워드 상위 항목을 랜딩 페이지 FAQ에 반영",
                ],
            )
        )

    if not strategies:
        strategies.append(
            _strategy_item(
                id="mkt_baseline",
                priority="info",
                title="기본 수요 유지 — 브랜드·패키지 균형",
                body="현재 이상 신호가 제한적입니다. 객실·온천·F&B 패키지 균형을 유지하며 시즌별 메시지를 점검하세요.",
                actions=[
                    "분기별 패키지 구성·가격표 정기 리뷰",
                    "주요 OTA 노출 순위·전환율 모니터링",
                ],
            )
        )

    priority_order = {"high": 0, "medium": 1, "info": 2}
    strategies.sort(key=lambda row: priority_order.get(row["priority"], 9))
    return strategies


def generate_operations_strategy(
    revenue: pd.DataFrame, rooms: pd.DataFrame, kpis: dict
) -> list[dict]:
    room_stats = room_cleaning_stats(rooms)
    seasonal = seasonal_revenue_report(revenue)
    mom = category_mom_changes(revenue)
    alerts = kpi_category_alerts(revenue)
    strategies: list[dict] = []

    defect_rate = float(room_stats.get("defect_rate", 0))
    not_cleaned = int(room_stats.get("not_cleaned", 0))
    if defect_rate >= 5 or not_cleaned > 0:
        strategies.append(
            _strategy_item(
                id="ops_cleaning",
                priority="high",
                title="객실 품질·청소 프로세스 강화",
                body=(
                    f"불량률 {format_number(defect_rate, 1)}%, 미실시 {format_number(not_cleaned)}건입니다. "
                    "성수기 전 검수 체크리스트와 담당자 배치를 재조정하세요."
                ),
                actions=[
                    "불량 다발 객실 유형·담당자 매핑 후 집중 재교육",
                    "체크아웃~체크인 사이 청소 SLA 모니터링",
                    "시설 보수 티켓과 청소 검수 결과 주간 공유",
                ],
            )
        )

    if not seasonal.empty:
        peak = seasonal.loc[seasonal["합계"].idxmax()]
        strategies.append(
            _strategy_item(
                id="ops_peak_staffing",
                priority="medium",
                title=f"{peak['계절']} 성수기 운영 캐파 계획",
                body=(
                    f"{peak['계절']} 매출 비중이 {peak['비중(%)']:.1f}%로 가장 높습니다. "
                    "프론트·하우스키핑·F&B 인력을 성수기 전에 선제 배치하세요."
                ),
                actions=[
                    "성수기 주간 인력표·교대표 사전 확정",
                    "온천·식음 피크 타임 혼잡도 모니터링",
                    "예비 객실·대기 정책을 프론트 SOP에 반영",
                ],
            )
        )

    room_mom = next((m for m in mom if m["category"] == "객실"), None)
    if room_mom and room_mom.get("change_pct") is not None and room_mom["change_pct"] < -5:
        strategies.append(
            _strategy_item(
                id="ops_room_yield",
                priority="high",
                title="객실 수익 관리(Yield) 점검",
                body=(
                    f"객실 매출이 전월 대비 {room_mom['change_pct']:.1f}% 하락했습니다. "
                    "객단가·판매 채널·재고 배분을 함께 점검하세요."
                ),
                actions=[
                    "요일·객실타입별 ADR·점유율 매트릭스 리뷰",
                    "장기 공실 객실 유지보수·판매 전환 우선순위 조정",
                    "체크인 시 온천·F&B 업셀링 스크립트 표준화",
                ],
            )
        )

    if alerts.get("month_revenue"):
        strategies.append(
            _strategy_item(
                id="ops_alert_response",
                priority="high",
                title="매출 이상징후 대응 회의",
                body="카테고리별 급락 신호가 감지되었습니다. 부문장 합동으로 원인·대응안을 48시간 내 정리하세요.",
                actions=[
                    "급락 부문 원인(가격·수요·운영) 체크리스트 작성",
                    "단기 프로모션·운영 조치안 A/B 검토",
                    "다음 주 KPI 모니터링 주기를 일간으로 상향",
                ],
            )
        )

    adr_change = kpis.get("adr_change")
    occ_change = kpis.get("occupancy_change")
    if (
        adr_change is not None
        and occ_change is not None
        and adr_change > 0
        and occ_change < 0
    ):
        strategies.append(
            _strategy_item(
                id="ops_adr_occ_tradeoff",
                priority="medium",
                title="ADR 상승 · 점유율 하락 트레이드오프 관리",
                body=(
                    "객단가는 올랐으나 점유율이 하락했습니다. 가격 정책이 수요를 "
                    "과도하게 억제하지 않는지 검토하세요."
                ),
                actions=[
                    "가격 탄력도가 큰 요일·채널 식별 후 선택적 할인",
                    "고마진 부가상품(온천·식음) 번들로 총수익 보완",
                ],
            )
        )

    if not strategies:
        strategies.append(
            _strategy_item(
                id="ops_baseline",
                priority="info",
                title="표준 운영 유지 · 선제 점검",
                body="운영 리스크 신호가 제한적입니다. 성수기 대비 표준 SOP를 유지하고 분기별 시뮬레이션을 진행하세요.",
                actions=[
                    "분기별 비상 인력·재고 플랜 리허설",
                    "크로스 부문(객실·온천·F&B) 일일 브리핑 유지",
                ],
            )
        )

    priority_order = {"high": 0, "medium": 1, "info": 2}
    strategies.sort(key=lambda row: priority_order.get(row["priority"], 9))
    return strategies
