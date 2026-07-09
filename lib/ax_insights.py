"""Rule-based AX insights from revenue, rooms, and VOC data."""

from __future__ import annotations

import pandas as pd

from lib.metrics import (
    ALERT_THRESHOLD_PCT,
    CATEGORY_SLUGS,
    category_mom_changes,
    compute_kpis,
    format_number,
    kpi_category_alerts,
    room_cleaning_stats,
    voc_summary,
)

_SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


def _insight(
    *,
    id: str,
    severity: str,
    title: str,
    body: str,
    evidence: str,
    action_label: str,
    action_href: str,
) -> dict:
    return {
        "id": id,
        "severity": severity,
        "title": title,
        "body": body,
        "evidence": evidence,
        "action_label": action_label,
        "action_href": action_href,
    }


def generate_ax_insights(revenue: pd.DataFrame, rooms: pd.DataFrame) -> list[dict]:
    insights: list[dict] = []
    kpis = compute_kpis(revenue, rooms)
    alerts = kpi_category_alerts(revenue)
    voc = voc_summary()
    room_stats = room_cleaning_stats(rooms)
    mom = category_mom_changes(revenue)

    for item in alerts.get("month_revenue", []):
        slug = CATEGORY_SLUGS.get(item["category"], "room")
        insights.append(
            _insight(
                id=f"alert_{slug}",
                severity="critical",
                title=f'{item["category"]} 매출 급락',
                body=(
                    f'전월 대비 {item["category"]} 매출이 {item["change_pct"]:.1f}% 하락했습니다. '
                    "해당 부문 프로모션·운영 점검을 권고합니다."
                ),
                evidence=(
                    f'당월 {format_number(item["current"])}천원 → '
                    f'전월 {format_number(item["previous"])}천원'
                ),
                action_label="실적 상세 보기",
                action_href=f"?tab=performance&amp;category={slug}",
            )
        )

    complaints = voc.get("complaints_by_category", [])
    top_complaint = complaints[0] if complaints else None
    defect_rate = room_stats.get("defect_rate", 0.0)
    not_cleaned = room_stats.get("not_cleaned", 0)

    if top_complaint and top_complaint["category"] == "시설노후" and defect_rate >= 5:
        insights.append(
            _insight(
                id="facility_voc_room",
                severity="warning",
                title="시설 노후 VOC × 객실 품질 연계",
                body=(
                    "고객 불만 1위가 시설노후이며 객실 불량률도 높습니다. "
                    "시설 보수 우선순위와 청소·검수 프로세스를 함께 점검하세요."
                ),
                evidence=(
                    f'시설노후 불만 {format_number(top_complaint["count"])}건 · '
                    f"불량률 {format_number(defect_rate, 1)}%"
                ),
                action_label="객실운영 보기",
                action_href="?tab=rooms",
            )
        )

    cleaning_count = next(
        (c["count"] for c in complaints if c["category"] == "청결"),
        0,
    )
    if cleaning_count >= 20 and not_cleaned > 0:
        insights.append(
            _insight(
                id="cleaning_voc_ops",
                severity="warning",
                title="청결 VOC · 미실시 건수 동시 발생",
                body=(
                    "청결 관련 VOC가 많고 청소 미실시 건수도 있습니다. "
                    "담당자별 배치와 검수 빈도 조정을 검토하세요."
                ),
                evidence=(
                    f"청결 불만 {format_number(cleaning_count)}건 · "
                    f"미실시 {format_number(not_cleaned)}건"
                ),
                action_label="객실 리스트 보기",
                action_href="?tab=rooms",
            )
        )

    room_mom = next((m for m in mom if m["category"] == "객실"), None)
    if (
        room_mom
        and kpis.get("occupancy_change") is not None
        and kpis["occupancy_change"] < 0
        and room_mom.get("change_pct") is not None
        and room_mom["change_pct"] < 0
    ):
        insights.append(
            _insight(
                id="occupancy_room_drop",
                severity="info",
                title="점유율·객실매출 동반 하락",
                body=(
                    "점유율과 객실 매출이 함께 줄었습니다. "
                    "객단가(ADR) 유지 여부와 채널 믹스를 확인하세요."
                ),
                evidence=(
                    f'점유율 {kpis["occupancy_change"]:+.1f}% · '
                    f'객실매출 {room_mom["change_pct"]:+.1f}%'
                ),
                action_label="요약 KPI 보기",
                action_href="?tab=summary",
            )
        )

    if (
        kpis.get("month_revenue_change") is not None
        and kpis["month_revenue_change"] > 0
        and kpis.get("occupancy_change") is not None
        and kpis["occupancy_change"] > 0
        and not alerts.get("month_revenue")
    ):
        insights.append(
            _insight(
                id="positive_trend",
                severity="info",
                title="매출·점유율 동반 개선",
                body="당월 매출과 점유율이 모두 전월 대비 상승했습니다. 현재 운영 전략을 유지·확대하세요.",
                evidence=(
                    f'월매출 {kpis["month_revenue_change"]:+.1f}% · '
                    f'점유율 {kpis["occupancy_change"]:+.1f}%'
                ),
                action_label="실적 추이 보기",
                action_href="?tab=performance",
            )
        )

    fb_alert = next((a for a in alerts.get("month_revenue", []) if a["category"] == "F&B"), None)
    food_voc = next((c["count"] for c in complaints if c["category"] == "식음"), 0)
    if fb_alert and food_voc >= 10:
        insights.append(
            _insight(
                id="fb_voc_cross",
                severity="warning",
                title="F&B 실적·식음 VOC 교차 신호",
                body="F&B 매출 하락과 식음 불만 VOC가 동시에 관측됩니다. 메뉴·가격·서빙 품질을 점검하세요.",
                evidence=(
                    f'F&B {fb_alert["change_pct"]:.1f}% · '
                    f"식음 VOC {format_number(food_voc)}건"
                ),
                action_label="F&B 실적 보기",
                action_href="?tab=performance&amp;category=fb",
            )
        )

    insights.sort(key=lambda row: _SEVERITY_ORDER.get(row["severity"], 9))
    return insights
