from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from config import HOTEL_NAME, REFRESH_SECONDS
from lib.metrics import (
    compute_kpis,
    format_currency,
    monthly_revenue_trend,
    revenue_breakdown,
    room_cleaning_stats,
    voc_summary,
)
from lib.sheets import load_revenue, load_rooms

st.set_page_config(
    page_title="온천관광호텔 경영 대시보드",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
    .stApp {
        background-color: #0F1923;
        color: #FFFFFF;
    }
    [data-testid="stHeader"] {
        background: rgba(15, 25, 35, 0.95);
    }
    .dashboard-title {
        font-size: 2rem;
        font-weight: 700;
        color: #C8A96E;
        margin-bottom: 0.2rem;
    }
    .dashboard-subtitle {
        color: #9FB0C3;
        font-size: 0.95rem;
    }
    div[data-testid="stMetric"] {
        background: #1B2A3B;
        border: 1px solid #C8A96E55;
        border-radius: 12px;
        padding: 1rem 1.2rem;
    }
    div[data-testid="stMetric"] label {
        color: #C8A96E !important;
        font-size: 1rem !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 1rem !important;
    }
    .panel {
        background: #1B2A3B;
        border: 1px solid #C8A96E55;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        min-height: 320px;
    }
    .panel h3 {
        color: #C8A96E;
        margin-top: 0;
        font-size: 1.2rem;
    }
    .error-box {
        background: #4A1F1F;
        border: 1px solid #E57373;
        color: #FFCDD2;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_dashboard_data():
    revenue = load_revenue()
    rooms = load_rooms()
    return revenue, rooms


def _delta_text(change: float | None) -> str | None:
    if change is None:
        return None
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.1f}% 전월 대비"


def render_header(last_updated: datetime):
    left, right = st.columns([2, 1])
    with left:
        st.markdown(f'<div class="dashboard-title">{HOTEL_NAME}</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="dashboard-subtitle">경영 대시보드 (발표용 프로토타입)</div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f'<div class="dashboard-subtitle" style="text-align:right;">'
            f"현재 시각<br><span style='font-size:1.4rem;color:#FFFFFF;'>"
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span><br>"
            f"마지막 데이터 갱신: {last_updated.strftime('%H:%M:%S')}"
            f"</div>",
            unsafe_allow_html=True,
        )


def render_kpis(kpis: dict):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(
            "월매출",
            format_currency(kpis["month_revenue"]),
            _delta_text(kpis["month_revenue_change"]),
        )
    with c2:
        st.metric(
            "점유율",
            f"{kpis['occupancy']:.1f}%",
            _delta_text(kpis["occupancy_change"]),
        )
    with c3:
        st.metric(
            "RevPAR",
            f"{kpis['revpar']:,.0f}원",
            _delta_text(kpis["revpar_change"]),
        )


def render_revenue_panels(revenue: pd.DataFrame):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="panel"><h3>월별 매출 추이</h3>', unsafe_allow_html=True)
        trend = monthly_revenue_trend(revenue)
        st.line_chart(trend, x="month", y="매출")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="panel"><h3>매출 구성비 (당월)</h3>', unsafe_allow_html=True)
        breakdown = revenue_breakdown(revenue)
        st.bar_chart(breakdown, x="구분", y="매출")
        st.markdown("</div>", unsafe_allow_html=True)


def render_room_panel(rooms: pd.DataFrame):
    stats = room_cleaning_stats(rooms)
    st.markdown('<div class="panel"><h3>객실 청소 현황</h3>', unsafe_allow_html=True)

    m1, m2 = st.columns(2)
    m1.metric("불량률", f"{stats['defect_rate']:.1f}%")
    m2.metric("청소 미실시", f"{stats['not_cleaned']}건")

    by_cleaner = stats["by_cleaner"]
    if not by_cleaner.empty:
        chart_df = by_cleaner.set_index("cleaner")[["total", "defects"]]
        chart_df.columns = ["총 건수", "불량 건수"]
        st.bar_chart(chart_df)
    st.markdown("</div>", unsafe_allow_html=True)


def render_voc_panel():
    voc = voc_summary()
    st.markdown('<div class="panel"><h3>고객의소리 (VOC)</h3>', unsafe_allow_html=True)

    v1, v2 = st.columns(2)
    v1.metric("평균 평점", f"{voc['average_rating']:.1f} / 5.0")
    v2.metric("리뷰 수", f"{voc['total_reviews']}건")

    complaints = pd.DataFrame(voc["complaints_by_category"])
    complaints = complaints.set_index("category")
    complaints.columns = ["불만 건수"]
    st.bar_chart(complaints)
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    error_message = None
    revenue = pd.DataFrame()
    rooms = pd.DataFrame()

    try:
        revenue, rooms = fetch_dashboard_data()
        last_updated = datetime.now()
    except Exception as exc:
        error_message = str(exc)
        last_updated = datetime.now()

    render_header(last_updated)

    if error_message:
        st.markdown(
            f'<div class="error-box">데이터를 불러오지 못했습니다: {error_message}</div>',
            unsafe_allow_html=True,
        )
        st.info("구글 시트가 '링크가 있는 모든 사용자'에게 보기 권한인지 확인해 주세요.")
        return

    kpis = compute_kpis(revenue, rooms)
    render_kpis(kpis)
    st.markdown("<br>", unsafe_allow_html=True)
    render_revenue_panels(revenue)

    bottom1, bottom2 = st.columns(2)
    with bottom1:
        render_room_panel(rooms)
    with bottom2:
        render_voc_panel()

    st.caption(f"데이터는 {REFRESH_SECONDS}초마다 자동 갱신됩니다.")


main()


@st.fragment(run_every=timedelta(seconds=REFRESH_SECONDS))
def auto_refresh():
    fetch_dashboard_data.clear()
    st.rerun()


auto_refresh()
