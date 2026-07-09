from datetime import datetime
import html as html_lib
import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from config import HOTEL_NAME, RECENT_DAYS, REFRESH_SECONDS
from lib.ax_insights import generate_ax_insights
from lib.executive_analysis import (
    annual_revenue_summary,
    executive_briefing,
    generate_marketing_strategy,
    generate_operations_strategy,
    quarterly_revenue_table,
    quarterly_revenue_trend,
    seasonal_revenue_chart_data,
    seasonal_revenue_table,
    segment_annual_report,
    segment_annual_table,
)
from lib.ai_reviews import build_review_analysis
from lib.charts import (
    daily_composition_donut,
    daily_composition_stacked_chart,
    daily_revenue_chart,
    grouped_bar_chart,
    keyword_bar_chart,
    quarterly_revenue_chart,
    revenue_bar_chart,
    revenue_line_chart,
    review_rating_chart,
    seasonal_segment_chart,
    segment_share_chart,
    voc_bar_chart,
    yoy_grouped_bar_chart,
)
# Keep in sync with lib/metrics.py `__all__` and the export comment block there.
from lib.metrics import (
    available_months,
    CATEGORY_SLUGS,
    compute_kpis,
    daily_performance,
    daily_revenue_table,
    daily_revenue_trend,
    default_month,
    format_number,
    kpi_category_alerts,
    monthly_revenue_table,
    monthly_revenue_trend,
    mom_comparison,
    mom_comparison_chart_data,
    mom_comparison_table,
    recent_days_composition,
    recent_days_period_label,
    recent_days_revenue_table,
    recent_days_revenue_trend,
    revenue_breakdown,
    room_cleaners,
    room_cleaning_stats,
    room_detail_table,
    room_inspection_results,
    voc_summary,
)
from lib.sheets import load_revenue, load_rooms
from lib.theme import CSS_ROOT

st.set_page_config(
    page_title="온천관광호텔 경영 대시보드",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');

    {CSS_ROOT}

    html, body, [class*="css"] {{
        font-family: 'Noto Sans KR', sans-serif;
    }}

    .stApp {{
        background: var(--paper);
        color: var(--navy);
    }}

    [data-testid="stHeader"], [data-testid="stToolbar"] {{
        background: var(--white);
    }}

    .block-container {{
        padding-top: 1.25rem;
        padding-bottom: 1.75rem;
        max-width: 1360px;
    }}

    [data-testid="column"] {{
        padding-left: 0.45rem !important;
        padding-right: 0.45rem !important;
    }}

    .section-gap {{
        height: 1.1rem;
    }}

    .hero {{
        background: var(--white);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 1.35rem 1.75rem;
        margin-bottom: 1.35rem;
        box-shadow: 0 4px 18px var(--shadow);
    }}

    .hero-inner {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1.5rem;
    }}

    .hero-title {{
        font-size: 1.85rem;
        font-weight: 700;
        color: var(--navy);
        letter-spacing: -0.03em;
        margin: 0;
        line-height: 1.25;
    }}

    .hero-subtitle {{
        color: var(--navy-muted);
        font-size: 0.9rem;
        margin-top: 0.4rem;
    }}

    .hero-time {{
        text-align: right;
        color: var(--navy-muted);
        font-size: 0.82rem;
        line-height: 1.55;
        min-width: 200px;
    }}

    .hero-time strong {{
        display: block;
        color: var(--navy);
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0.25rem 0 0.15rem;
        font-variant-numeric: tabular-nums;
    }}

    .kpi-card {{
        position: relative;
        background: var(--white);
        border: 1px solid var(--gold-border);
        border-radius: 14px;
        padding: 1.15rem 1.35rem 1.1rem 1.5rem;
        box-shadow: 0 2px 12px var(--shadow);
        min-height: 148px;
        overflow: hidden;
    }}

    .kpi-alerts {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        margin-bottom: 0.65rem;
    }}

    .kpi-alert-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.2rem;
        padding: 0.22rem 0.55rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        text-decoration: none !important;
        color: var(--bad) !important;
        background: var(--bad-tint);
        border: 1px solid var(--bad);
        transition: background 0.15s ease, transform 0.1s ease;
        white-space: nowrap;
    }}

    .kpi-alert-badge:hover {{
        background: color-mix(in srgb, var(--bad) 18%, var(--white));
        transform: translateY(-1px);
    }}

    .category-anchor {{
        scroll-margin-top: 6.5rem;
        height: 0;
        overflow: hidden;
    }}

    .insight-list {{
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }}

    .insight-card {{
        background: var(--white);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 1rem 1.15rem;
        border-left-width: 4px;
        box-shadow: 0 2px 10px var(--shadow);
    }}

    .insight-card.critical {{ border-left-color: var(--bad); }}
    .insight-card.warning {{ border-left-color: var(--gold); }}
    .insight-card.info {{ border-left-color: var(--navy); }}

    .insight-title {{
        color: var(--navy);
        font-size: 0.95rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }}

    .insight-body {{
        color: var(--navy);
        font-size: 0.86rem;
        line-height: 1.55;
        margin-bottom: 0.45rem;
    }}

    .insight-evidence {{
        color: var(--navy-muted);
        font-size: 0.76rem;
        margin-bottom: 0.55rem;
    }}

    .insight-action {{
        display: inline-block;
        padding: 0.3rem 0.75rem;
        border-radius: 8px;
        font-size: 0.78rem;
        font-weight: 600;
        text-decoration: none !important;
        color: var(--navy) !important;
        background: var(--gold-tint);
        border: 1px solid var(--gold-border);
    }}

    .insight-action:hover {{
        background: color-mix(in srgb, var(--gold) 12%, var(--white));
    }}

    .insight-empty {{
        color: var(--navy-muted);
        font-size: 0.88rem;
        padding: 1rem 1.15rem;
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 12px;
    }}

    .reco-list {{
        margin: 0.5rem 0 0 1.1rem;
        color: var(--navy);
        font-size: 0.86rem;
        line-height: 1.6;
    }}

    .exec-brief-card {{
        background: linear-gradient(135deg, var(--white) 0%, var(--paper) 100%);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 1.2rem 1.3rem;
        margin-bottom: 0.25rem;
        box-shadow: 0 2px 14px var(--shadow);
        border-top: 3px solid var(--gold);
    }}

    .exec-brief-kicker {{
        color: var(--gold);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }}

    .exec-brief-headline {{
        color: var(--navy);
        font-size: 1.02rem;
        font-weight: 700;
        line-height: 1.55;
        margin-bottom: 0.75rem;
        letter-spacing: -0.02em;
    }}

    .exec-brief-bullets {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
    }}

    .exec-brief-pill {{
        display: inline-flex;
        align-items: center;
        padding: 0.28rem 0.65rem;
        border-radius: 999px;
        background: var(--white);
        border: 1px solid var(--line);
        color: var(--navy-muted);
        font-size: 0.74rem;
        font-weight: 600;
    }}

    .report-note {{
        color: var(--navy-muted);
        font-size: 0.78rem;
        margin: 0.15rem 0 0.65rem 0;
        line-height: 1.45;
    }}

    .strategy-list {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.75rem;
    }}

    @media (max-width: 900px) {{
        .strategy-list {{
            grid-template-columns: 1fr;
        }}
    }}

    .strategy-card {{
        background: var(--white);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 1rem 1.1rem;
        box-shadow: 0 2px 10px var(--shadow);
        height: 100%;
    }}

    .strategy-card.high {{ border-top: 3px solid var(--bad); }}
    .strategy-card.medium {{ border-top: 3px solid var(--gold); }}
    .strategy-card.info {{ border-top: 3px solid var(--navy); }}

    .strategy-priority {{
        color: var(--navy-muted);
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        margin-bottom: 0.35rem;
    }}

    .strategy-title {{
        color: var(--navy);
        font-size: 0.94rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
        line-height: 1.35;
    }}

    .strategy-body {{
        color: var(--navy);
        font-size: 0.84rem;
        line-height: 1.55;
        margin-bottom: 0.55rem;
    }}

    .strategy-actions {{
        margin: 0;
        padding-left: 1.05rem;
        color: var(--navy-muted);
        font-size: 0.78rem;
        line-height: 1.55;
    }}

    .strategy-actions li {{
        margin-bottom: 0.2rem;
    }}

    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.9rem;
        margin-bottom: 0.25rem;
    }}

    @media (max-width: 1100px) {{
        .kpi-grid {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }}
    }}

    @media (max-width: 640px) {{
        .kpi-grid {{
            grid-template-columns: 1fr;
        }}
    }}

    .kpi-card::before {{
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background: linear-gradient(180deg, var(--gold-tint) 0%, var(--gold) 100%);
    }}

    .kpi-label {{
        color: var(--gold);
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.65rem;
    }}

    .kpi-value-row {{
        display: flex;
        align-items: baseline;
        gap: 0.35rem;
        flex-wrap: wrap;
    }}

    .kpi-value {{
        color: var(--navy);
        font-size: 2.15rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        line-height: 1.1;
        font-variant-numeric: tabular-nums;
    }}

    .kpi-unit {{
        color: var(--navy-muted);
        font-size: 0.92rem;
        font-weight: 500;
    }}

    .kpi-subtitle {{
        color: var(--navy-muted);
        font-size: 0.72rem;
        margin-top: 0.35rem;
    }}

    .unit-muted {{
        font-size: 0.85rem;
        color: var(--navy-muted);
    }}

    .kpi-delta {{
        display: inline-flex;
        align-items: center;
        margin-top: 0.7rem;
        padding: 0.28rem 0.65rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        font-variant-numeric: tabular-nums;
    }}

    .kpi-delta.up {{ color: var(--good); background: var(--good-tint); }}
    .kpi-delta.down {{ color: var(--bad); background: var(--bad-tint); }}
    .kpi-delta.neutral {{ color: var(--navy-muted); background: var(--neutral-tint); }}

    .panel-card {{
        background: var(--white);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 1.15rem 1.25rem 0.85rem;
        box-shadow: 0 2px 14px var(--shadow);
        height: 100%;
        margin-bottom: 0.85rem;
    }}

    .panel-title {{
        color: var(--navy);
        font-size: 1rem;
        font-weight: 600;
        margin: 0 0 0.85rem 0;
        padding-bottom: 0.65rem;
        border-bottom: 1px solid var(--line);
    }}

    .panel-subtitle {{
        color: var(--navy-muted);
        font-size: 0.78rem;
        font-weight: 500;
        margin: -0.45rem 0 0.75rem 0;
    }}

    .mini-metric {{
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 0.8rem 1rem;
        text-align: center;
    }}

    .mini-metric .label {{ color: var(--navy-muted); font-size: 0.78rem; font-weight: 500; margin-bottom: 0.25rem; }}
    .mini-metric .value {{
        color: var(--navy);
        font-size: 1.5rem;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
    }}

    .yoy-summary {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.65rem;
        margin-bottom: 0.75rem;
    }}

    .yoy-box {{
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 0.75rem 0.9rem;
    }}

    .yoy-box .label {{ color: var(--navy-muted); font-size: 0.76rem; margin-bottom: 0.2rem; }}
    .yoy-box .value {{
        color: var(--navy);
        font-size: 1.25rem;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
    }}

    .yoy-box.current {{ border-color: var(--gold-border); background: var(--gold-tint); }}
    .yoy-box.prior {{ border-color: var(--line); }}

    .yoy-total-delta {{
        text-align: center;
        font-size: 0.88rem;
        font-weight: 600;
        margin-bottom: 0.7rem;
        padding: 0.45rem 0.6rem;
        border-radius: 8px;
        background: var(--neutral-tint);
        color: var(--navy-muted);
    }}

    .yoy-total-delta.up {{ background: var(--good-tint); color: var(--good); }}
    .yoy-total-delta.down {{ background: var(--bad-tint); color: var(--bad); }}
    .yoy-total-delta.neutral {{ background: var(--neutral-tint); color: var(--navy-muted); }}

    .footer-note {{
        color: var(--navy-muted);
        font-size: 0.78rem;
        text-align: center;
        margin-top: 1.1rem;
    }}

    .error-box {{
        background: var(--bad-tint);
        border: 1px solid var(--bad);
        color: var(--bad);
        padding: 0.9rem 1.1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }}

    div[data-testid="stDataFrame"] {{
        border: 1px solid var(--line);
        border-radius: 10px;
        overflow: hidden;
    }}

    div[data-testid="stDataFrame"] div[data-testid="stTable"] {{
        font-variant-numeric: tabular-nums;
    }}

    .drilldown-box {{
        margin-top: 0.9rem;
        padding-top: 0.85rem;
        border-top: 1px solid var(--line);
    }}

    .drilldown-title {{
        color: var(--gold);
        font-size: 0.88rem;
        font-weight: 600;
        margin-bottom: 0.55rem;
    }}

    .filter-hint {{
        color: var(--navy-muted);
        font-size: 0.76rem;
        margin-bottom: 0.5rem;
    }}

    .section-heading {{
        color: var(--gold);
        font-size: 1.05rem;
        font-weight: 700;
        margin: 0.25rem 0 0.65rem 0;
        letter-spacing: -0.02em;
    }}

    .section-desc {{
        color: var(--navy-muted);
        font-size: 0.78rem;
        margin: -0.35rem 0 0.75rem 0;
    }}

    div[data-testid="stSelectbox"] label {{
        color: var(--gold) !important;
        font-weight: 600 !important;
    }}

    .tab-nav-sticky {{
        position: sticky;
        top: 0;
        z-index: 1000;
        background: color-mix(in srgb, var(--white) 97%, transparent);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid var(--line);
        border-radius: 14px;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 20px var(--shadow);
    }}

    .tab-nav-scroll {{
        display: flex;
        gap: 0.35rem;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        padding: 0.45rem 0.55rem;
    }}

    .tab-nav-scroll::-webkit-scrollbar {{
        display: none;
    }}

    .tab-link {{
        flex: 0 0 auto;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 5.5rem;
        padding: 0.62rem 1.15rem;
        border-radius: 10px;
        font-size: 0.9rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        text-decoration: none !important;
        color: var(--navy-muted) !important;
        background: transparent;
        border: 1px solid transparent;
        transition: color 0.15s ease, background 0.15s ease, border-color 0.15s ease;
        white-space: nowrap;
    }}

    .tab-link:hover {{
        color: var(--gold) !important;
        background: var(--gold-tint);
        border-color: var(--gold-border);
    }}

    .tab-link.active {{
        color: var(--gold) !important;
        background: linear-gradient(180deg, var(--gold-tint) 0%, var(--white) 100%);
        border-color: var(--gold-border);
        box-shadow: inset 0 -3px 0 var(--gold);
    }}

    @media (max-width: 640px) {{
        .tab-nav-scroll {{
            padding: 0.4rem 0.45rem;
        }}

        .tab-link {{
            min-width: 4.75rem;
            padding: 0.55rem 0.95rem;
            font-size: 0.84rem;
        }}
    }}

    .daily-performance-wrap {{
        background: var(--white);
        border: 1px solid var(--line);
        border-radius: 14px 14px 0 0;
        border-bottom: none;
        padding: 1.2rem 1.25rem 0.65rem;
        margin-bottom: 0;
        box-shadow: 0 2px 14px var(--shadow);
    }}

    .daily-performance-title {{
        color: var(--navy);
        font-size: 1.05rem;
        font-weight: 700;
        margin: 0 0 0.2rem 0;
        letter-spacing: -0.02em;
    }}

    .daily-performance-sub {{
        color: var(--gold);
        font-size: 0.95rem;
        font-weight: 600;
        margin: 0 0 1rem 0;
    }}

    .daily-kpi-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.7rem;
    }}

    @media (max-width: 640px) {{
        .daily-kpi-grid {{
            grid-template-columns: 1fr;
        }}
    }}

    .daily-kpi-card {{
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 0.9rem 1rem;
        min-height: 112px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}

    .daily-kpi-label {{
        color: var(--gold);
        font-size: 0.74rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        margin-bottom: 0.45rem;
    }}

    .daily-kpi-value {{
        color: var(--navy);
        font-size: 1.38rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1.15;
        font-variant-numeric: tabular-nums;
    }}

    .daily-kpi-unit {{
        color: var(--navy-muted);
        font-size: 0.82rem;
        font-weight: 500;
        margin-left: 0.2rem;
    }}

    .daily-delta {{
        display: inline-flex;
        align-items: center;
        gap: 0.2rem;
        margin-top: 0.55rem;
        padding: 0.22rem 0.55rem;
        border-radius: 999px;
        font-size: 0.74rem;
        font-weight: 600;
        font-variant-numeric: tabular-nums;
    }}

    .daily-delta.up {{ color: var(--good); background: var(--good-tint); }}
    .daily-delta.down {{ color: var(--bad); background: var(--bad-tint); }}
    .daily-delta.neutral {{ color: var(--navy-muted); background: var(--neutral-tint); }}

    .daily-arrow {{
        font-size: 0.7rem;
        line-height: 1;
    }}

    .daily-perf-marker {{
        display: none;
    }}

    .daily-perf-marker + div[data-testid="stHorizontalBlock"] {{
        align-items: stretch !important;
        gap: 1rem !important;
        background: var(--white);
        border: 1px solid var(--line);
        border-top: none;
        border-radius: 0 0 14px 14px;
        padding: 0 1.15rem 1.1rem;
        margin: 0 0 1rem 0;
        box-shadow: 0 2px 14px var(--shadow);
    }}

    .daily-perf-marker + div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {{
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}

    .daily-perf-marker + div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {{
        background: var(--paper);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 0.35rem 0.25rem 0;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 252px;
    }}

    @media (max-width: 768px) {{
        .daily-perf-marker + div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {{
            min-height: 280px;
            margin-top: 0.25rem;
        }}
    }}
</style>
"""

TABS = {
    "summary": "요약",
    "performance": "실적",
    "rooms": "객실운영",
    "voc": "VOC",
    "insights": "AX·인사이트",
}
DEFAULT_TAB = "summary"
VALID_CATEGORY_SLUGS = set(CATEGORY_SLUGS.values())

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def fetch_dashboard_data():
    errors: list[str] = []
    revenue = pd.DataFrame()
    rooms = pd.DataFrame()

    try:
        revenue = load_revenue()
    except Exception as exc:
        errors.append(str(exc))

    try:
        rooms = load_rooms()
    except Exception as exc:
        errors.append(str(exc))

    if errors:
        raise RuntimeError(" / ".join(errors))

    return revenue, rooms


def _html_esc(value: str) -> str:
    return html_lib.escape(str(value), quote=False)


def _delta_html(change: float | None, label: str = "전월 대비") -> str:
    safe_label = _html_esc(label)
    if change is None:
        return f'<div class="kpi-delta neutral">{safe_label} 없음</div>'
    css = "up" if change >= 0 else "down"
    sign = "+" if change >= 0 else ""
    return f'<div class="kpi-delta {css}">{sign}{change:.1f}% {safe_label}</div>'


def _category_detail_href(category: str) -> str:
    slug = CATEGORY_SLUGS.get(category, category)
    return f"?tab=performance&amp;category={slug}"


def _alert_badges_html(alerts: list[dict]) -> str:
    if not alerts:
        return ""
    badges = []
    for item in alerts:
        change = item["change_pct"]
        category = _html_esc(item["category"])
        badges.append(
            f'<a href="{_category_detail_href(item["category"])}" class="kpi-alert-badge" '
            f'target="_self">⚠ {category} {change:.1f}% 급락</a>'
        )
    return f'<div class="kpi-alerts">{"".join(badges)}</div>'


def _kpi_card(
    label: str,
    value: str,
    unit: str = "",
    delta: float | None = None,
    delta_label: str = "전월 대비",
    subtitle: str = "",
    alerts: list[dict] | None = None,
) -> str:
    unit_html = f'<span class="kpi-unit">{_html_esc(unit)}</span>' if unit else ""
    sub_html = (
        f'<div class="kpi-subtitle">{_html_esc(subtitle)}</div>'
        if subtitle
        else ""
    )
    alerts_html = _alert_badges_html(alerts or [])
    return (
        f'<div class="kpi-card">{alerts_html}'
        f'<div class="kpi-label">{_html_esc(label)}</div>'
        f'<div class="kpi-value-row">'
        f'<span class="kpi-value">{_html_esc(value)}</span>{unit_html}'
        f"</div>{_delta_html(delta, delta_label)}{sub_html}</div>"
    )


def _scroll_to_category_focus(category: str | None):
    if not category or category not in VALID_CATEGORY_SLUGS:
        return
    components.html(
        f"""
        <script>
            (function () {{
                const slug = {json.dumps(category)};
                const doc = window.parent.document;
                const el = doc.getElementById("category-detail-" + slug);
                if (el) {{
                    el.scrollIntoView({{ behavior: "smooth", block: "start" }});
                }}
            }})();
        </script>
        """,
        height=0,
    )


def _scroll_to_top_if_tab_changed(active_tab: str):
    if st.query_params.get("category"):
        return
    components.html(
        f"""
        <script>
            (function () {{
                const tab = {json.dumps(active_tab)};
                const key = "hoteldash_tab";
                const storage = window.parent.sessionStorage;
                const prev = storage.getItem(key);
                if (prev !== tab) {{
                    storage.setItem(key, tab);
                    if (prev !== null) {{
                        window.parent.scrollTo(0, 0);
                    }}
                }}
            }})();
        </script>
        """,
        height=0,
    )


def resolve_active_tab() -> str:
    tab = st.query_params.get("tab", DEFAULT_TAB)
    if tab not in TABS:
        tab = DEFAULT_TAB
    if st.query_params.get("tab") != tab:
        st.query_params["tab"] = tab
    st.session_state.dashboard_tab = tab
    return tab


def render_tab_navigation(active_tab: str):
    links = []
    for key, label in TABS.items():
        active_cls = "active" if key == active_tab else ""
        links.append(
            f'<a href="?tab={key}" class="tab-link {active_cls}" target="_self">{label}</a>'
        )
    st.markdown(
        f'<div class="tab-nav-sticky"><div class="tab-nav-scroll">{"".join(links)}</div></div>',
        unsafe_allow_html=True,
    )
    _scroll_to_top_if_tab_changed(active_tab)


def render_header(last_updated: datetime):
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-inner">
                <div>
                    <div class="hero-title">{HOTEL_NAME}</div>
                    <div class="hero-subtitle">Executive Dashboard · 경영 현황</div>
                </div>
                <div class="hero-time">
                    데이터 기준 시각
                    <strong>{last_updated.strftime('%Y-%m-%d %H:%M:%S')}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _mom_summary_html(mom: dict) -> str:
    cur_total = format_number(mom["current"]["total"])
    prv_total = format_number(mom["prior"]["total"])
    change = mom["total_change_pct"]

    if change is None:
        delta_html = '<div class="yoy-total-delta neutral">전월 비교 데이터 없음</div>'
    else:
        css = "up" if change >= 0 else "down"
        sign = "+" if change >= 0 else ""
        delta_html = (
            f'<div class="yoy-total-delta {css}">'
            f"합계 {sign}{change:.1f}% (전월 대비)</div>"
        )

    return f"""
    <div class="yoy-summary">
        <div class="yoy-box current">
            <div class="label">{mom["current_label"]}</div>
            <div class="value">{cur_total}<span class="unit-muted"> 천원</span></div>
        </div>
        <div class="yoy-box prior">
            <div class="label">{mom["prior_label"]}</div>
            <div class="value">{prv_total}<span class="unit-muted"> 천원</span></div>
        </div>
    </div>
    {delta_html}
    """


def render_mom_panel(revenue: pd.DataFrame, selected_month: str):
    anchor_html = "".join(
        f'<div id="category-detail-{slug}" class="category-anchor"></div>'
        for slug in CATEGORY_SLUGS.values()
    )
    st.markdown(anchor_html, unsafe_allow_html=True)

    mom = mom_comparison(revenue, selected_month)
    st.markdown(
        '<div class="panel-card">'
        '<div class="panel-title">전월 대비 실적</div>'
        f'<div class="panel-subtitle">{selected_month.replace("-", "년 ")}월 vs 전월</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_mom_summary_html(mom), unsafe_allow_html=True)

    if mom["has_prior"]:
        chart_data = mom_comparison_chart_data(revenue, selected_month)
        st.altair_chart(yoy_grouped_bar_chart(chart_data), use_container_width=True)
        st.dataframe(
            mom_comparison_table(revenue, selected_month),
            hide_index=True,
            use_container_width=True,
            column_config={
                "구분": st.column_config.TextColumn("구분", width="small"),
                "당월(천원)": st.column_config.TextColumn("당월(천원)", width="medium"),
                "전월(천원)": st.column_config.TextColumn("전월(천원)", width="medium"),
                "증감": st.column_config.TextColumn("증감", width="small"),
            },
        )
    else:
        st.caption("전월 데이터가 없어 비교할 수 없습니다.")

    st.markdown("</div>", unsafe_allow_html=True)


def _daily_delta_html(change: float | None) -> str:
    if change is None:
        return '<div class="daily-delta neutral">전일 대비 없음</div>'
    if change >= 0:
        return (
            f'<div class="daily-delta up">'
            f'<span class="daily-arrow">▲</span> +{change:.1f}% 전일 대비</div>'
        )
    return (
        f'<div class="daily-delta down">'
        f'<span class="daily-arrow">▼</span> {change:.1f}% 전일 대비</div>'
    )


def _daily_kpi_card(label: str, amount: float, change: float | None) -> str:
    return (
        f'<div class="daily-kpi-card">'
        f'<div class="daily-kpi-label">{_html_esc(label)}</div>'
        f'<div><span class="daily-kpi-value">{format_number(amount)}</span>'
        f'<span class="daily-kpi-unit">천원</span></div>'
        f"{_daily_delta_html(change)}"
        f"</div>"
    )


def render_daily_performance_panel(revenue: pd.DataFrame):
    daily = daily_performance(revenue)
    st.markdown(
        '<div class="daily-performance-wrap">'
        '<div class="daily-performance-title">오늘의 실적 (Daily Performance)</div>',
        unsafe_allow_html=True,
    )
    if not daily["has_data"]:
        st.markdown(
            '<div class="insight-empty">표시할 일별 실적 데이터가 없습니다.</div></div>',
            unsafe_allow_html=True,
        )
        return

    cards = "".join(
        _daily_kpi_card(m["label"], m["amount"], m["change_pct"]) for m in daily["metrics"]
    )

    st.markdown(
        '<div class="daily-performance-wrap">'
        '<div class="daily-performance-title">오늘의 실적 (Daily Performance)</div>'
        f'<div class="daily-performance-sub">{_html_esc(daily["date_label"])}</div>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="daily-perf-marker"></div>', unsafe_allow_html=True)
    col_left, col_right = st.columns([1, 1], gap="medium", vertical_alignment="center")
    with col_left:
        st.html(f'<div class="daily-kpi-grid">{cards}</div>')
    with col_right:
        st.altair_chart(
            daily_composition_donut(daily["composition"], daily["total"]),
            use_container_width=True,
        )


def render_kpis(kpis: dict, alerts: dict[str, list[dict]]):
    cards = [
        _kpi_card(
            "월매출",
            format_number(kpis["month_revenue"]),
            "천원",
            kpis["month_revenue_change"],
            alerts=alerts["month_revenue"],
        ),
        _kpi_card(
            "점유율",
            format_number(kpis["occupancy"], 1),
            "%",
            kpis["occupancy_change"],
            alerts=alerts["occupancy"],
        ),
        _kpi_card(
            "ADR",
            format_number(kpis["adr"], 1),
            "천원",
            kpis["adr_change"],
            subtitle="객실매출÷판매객실",
            alerts=alerts["adr"],
        ),
        _kpi_card(
            "주간매출",
            format_number(kpis["week_revenue"]),
            "천원",
            kpis["week_revenue_change"],
            delta_label="전주 대비",
            subtitle=kpis["week_label"],
            alerts=alerts["week_revenue"],
        ),
    ]
    st.html(f'<div class="kpi-grid">{"".join(cards)}</div>')


def _styled_daily_table(df: pd.DataFrame, height: int = 260):
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        height=min(36 * len(df) + 38, height),
        column_config={
            "일자": st.column_config.TextColumn("일자", width="small"),
            "객실": st.column_config.TextColumn("객실(천원)", width="small"),
            "온천": st.column_config.TextColumn("온천(천원)", width="small"),
            "F&B": st.column_config.TextColumn("F&B(천원)", width="small"),
            "합계(천원)": st.column_config.TextColumn("합계(천원)", width="medium"),
        },
    )


def _styled_monthly_daily_table(df: pd.DataFrame, height: int = 420):
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        height=min(36 * len(df) + 38, height),
        column_config={
            "일자": st.column_config.TextColumn("일자", width="small"),
            "객실": st.column_config.TextColumn("객실", width="small"),
            "온천": st.column_config.TextColumn("온천", width="small"),
            "F&B": st.column_config.TextColumn("F&B", width="small"),
            "합계": st.column_config.TextColumn("합계", width="medium"),
        },
    )


def render_operations_panel(revenue: pd.DataFrame):
    period = recent_days_period_label(revenue, RECENT_DAYS)
    st.markdown('<div class="section-heading">실적관리</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-desc">일별 원천 데이터 · 최근 {RECENT_DAYS}일 운영 실적 ({period})</div>',
        unsafe_allow_html=True,
    )

    y_col = "매출(천원)"
    trend = recent_days_revenue_trend(revenue, RECENT_DAYS)
    composition = recent_days_composition(revenue, RECENT_DAYS)

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.markdown(
            '<div class="panel-card">'
            '<div class="panel-title">일별 매출 추이</div>'
            f'<div class="panel-subtitle">최근 {RECENT_DAYS}일 · 단위 천원</div>',
            unsafe_allow_html=True,
        )
        if trend.empty:
            st.caption("최근 일별 매출 데이터가 없습니다.")
        else:
            st.altair_chart(daily_revenue_chart(trend, y_col), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            '<div class="panel-card">'
            '<div class="panel-title">일별 매출 구성</div>'
            '<div class="panel-subtitle">객실 · 온천 · F&B · 누적 막대</div>',
            unsafe_allow_html=True,
        )
        if composition.empty:
            st.caption("최근 일별 구성 데이터가 없습니다.")
        else:
            st.altair_chart(daily_composition_stacked_chart(composition), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="panel-card">'
        '<div class="panel-title">최근 7일 일별 상세</div>'
        '<div class="panel-subtitle">단위: 천원</div>',
        unsafe_allow_html=True,
    )
    detail = recent_days_revenue_table(revenue, RECENT_DAYS)
    if detail.empty:
        st.caption("표시할 일별 데이터가 없습니다.")
    else:
        _styled_daily_table(detail, height=300)
    st.markdown("</div>", unsafe_allow_html=True)


def render_monthly_daily_panel(revenue: pd.DataFrame, selected_month: str):
    y_col = "매출(천원)"
    st.markdown(
        '<div class="panel-card">'
        '<div class="panel-title">일자별 매출</div>'
        f'<div class="panel-subtitle">{selected_month.replace("-", "년 ")}월 · 1일~말일 · 단위: 천원</div>',
        unsafe_allow_html=True,
    )
    daily_trend = daily_revenue_trend(revenue, selected_month)
    if daily_trend.empty or daily_trend["매출(천원)"].sum() <= 0:
        st.caption("선택한 월의 일별 매출 데이터가 없습니다.")
    else:
        st.altair_chart(daily_revenue_chart(daily_trend, y_col), use_container_width=True)
    daily_table = daily_revenue_table(revenue, selected_month)
    if daily_table.empty:
        st.caption("표시할 일자별 테이블 데이터가 없습니다.")
    else:
        _styled_monthly_daily_table(daily_table)
    st.markdown("</div>", unsafe_allow_html=True)


def _init_month_state(revenue: pd.DataFrame):
    months = available_months(revenue)
    if not months:
        st.session_state.selected_month = None
        return

    if (
        "selected_month" not in st.session_state
        or st.session_state.selected_month not in months
    ):
        st.session_state.selected_month = default_month(revenue)


def _apply_table_selection(revenue: pd.DataFrame):
    state = st.session_state.get("month_table_select")
    if not state:
        return

    rows = state.get("selection", {}).get("rows", [])
    if not rows:
        return

    trend = monthly_revenue_trend(revenue)
    if rows[0] < len(trend):
        st.session_state.selected_month = trend.iloc[rows[0]]["month"]


def _styled_month_table(df: pd.DataFrame):
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        height=min(36 * len(df) + 38, 220),
        on_select="rerun",
        selection_mode="single-row",
        key="month_table_select",
        column_config={
            "월": st.column_config.TextColumn("월", width="small"),
            "매출(천원)": st.column_config.TextColumn(
                "매출(천원)",
                width="medium",
                help="행을 클릭하면 해당 월이 선택됩니다.",
            ),
        },
    )


def render_monthly_panel(revenue: pd.DataFrame):
    _init_month_state(revenue)
    if not st.session_state.get("selected_month"):
        st.markdown('<div class="section-heading">월별 실적</div>', unsafe_allow_html=True)
        st.warning("표시할 월별 매출 데이터가 없습니다.")
        return

    _apply_table_selection(revenue)

    st.markdown('<div class="section-heading">월별 실적</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">장기 추이 · 경영 보고용 · 월 선택 시 전월 대비·구성비가 갱신됩니다</div>',
        unsafe_allow_html=True,
    )

    filter_col, _ = st.columns([1.2, 2.8])
    with filter_col:
        st.selectbox(
            "조회 월",
            available_months(revenue),
            key="selected_month",
            format_func=lambda value: value.replace("-", "년 ") + "월",
        )

    selected_month = st.session_state.selected_month
    y_col = "매출(천원)"

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.markdown(
            '<div class="panel-card">'
            '<div class="panel-title">월별 매출 추이</div>'
            '<div class="panel-subtitle">단위: 천원 · 콤마(,) 구분</div>',
            unsafe_allow_html=True,
        )
        trend = monthly_revenue_trend(revenue)
        st.altair_chart(revenue_line_chart(trend, y_col), use_container_width=True)
        _styled_month_table(monthly_revenue_table(revenue))
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        render_monthly_daily_panel(revenue, selected_month)

    col3, col4 = st.columns(2, gap="medium")

    with col3:
        render_mom_panel(revenue, selected_month)

    with col4:
        st.markdown(
            '<div class="panel-card">'
            '<div class="panel-title">월별 매출 구성비</div>'
            f'<div class="panel-subtitle">{selected_month.replace("-", "년 ")}월 · 객실 / 온천 / F&B</div>',
            unsafe_allow_html=True,
        )
        breakdown = revenue_breakdown(revenue, month=selected_month)
        st.altair_chart(revenue_bar_chart(breakdown, y_col), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


def _render_room_detail_list(rooms: pd.DataFrame):
    cleaners = ["전체", *room_cleaners(rooms)]
    results = ["전체", *room_inspection_results(rooms)]
    status_options = ["전체", "완료", "미실시", "불량"]

    f1, f2, f3 = st.columns(3, gap="small")
    with f1:
        st.selectbox("담당자", cleaners, key="room_cleaner_filter")
    with f2:
        st.selectbox("청소상태", status_options, key="room_status_filter")
    with f3:
        st.selectbox("검수결과", results, key="room_result_filter")

    detail = room_detail_table(
        rooms,
        cleaner=st.session_state.get("room_cleaner_filter", "전체"),
        status_filter=st.session_state.get("room_status_filter", "전체"),
        result_filter=st.session_state.get("room_result_filter", "전체"),
    )
    if detail.empty:
        st.caption("선택한 조건에 맞는 객실이 없습니다.")
    else:
        st.caption(f"총 {format_number(len(detail))}건")
        st.dataframe(
            detail,
            hide_index=True,
            use_container_width=True,
            height=min(36 * len(detail) + 38, 420),
            column_config={
                "객실번호": st.column_config.TextColumn("객실번호", width="small"),
                "담당자": st.column_config.TextColumn("담당자", width="small"),
                "상태": st.column_config.TextColumn(
                    "청소상태",
                    width="small",
                    help="완료 / 미실시 / 불량",
                ),
                "검수자": st.column_config.TextColumn("검수자", width="small"),
                "검수일": st.column_config.TextColumn("검수일", width="small"),
                "검수결과": st.column_config.TextColumn("검수결과", width="small"),
                "비고": st.column_config.TextColumn("비고", width="medium"),
            },
        )


def render_room_panel(rooms: pd.DataFrame, *, show_room_list: bool = False):
    stats = room_cleaning_stats(rooms)
    st.markdown(
        '<div class="panel-card"><div class="panel-title">객실 청소 현황</div>',
        unsafe_allow_html=True,
    )

    m1, m2 = st.columns(2, gap="small")
    with m1:
        st.markdown(
            f'<div class="mini-metric"><div class="label">불량률</div>'
            f'<div class="value">{format_number(stats["defect_rate"], 1)}%</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="mini-metric"><div class="label">청소 미실시</div>'
            f'<div class="value">{format_number(stats["not_cleaned"])}건</div></div>',
            unsafe_allow_html=True,
        )

    by_cleaner = stats["by_cleaner"]
    if not by_cleaner.empty:
        chart_df = by_cleaner.set_index("cleaner")[["total", "defects"]]
        chart_df.columns = ["총 건수", "불량 건수"]
        st.altair_chart(grouped_bar_chart(chart_df), use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if show_room_list:
        st.markdown(
            '<div class="panel-card"><div class="panel-title">객실 리스트</div>'
            '<div class="panel-subtitle">담당자 · 청소상태 · 검수결과 필터</div>',
            unsafe_allow_html=True,
        )
        _render_room_detail_list(rooms)
        st.markdown("</div>", unsafe_allow_html=True)


def render_voc_panel():
    voc = voc_summary()
    st.markdown(
        '<div class="panel-card"><div class="panel-title">고객의소리 (VOC)</div>',
        unsafe_allow_html=True,
    )

    v1, v2 = st.columns(2, gap="small")
    with v1:
        st.markdown(
            f'<div class="mini-metric"><div class="label">평균 평점</div>'
            f'<div class="value">{format_number(voc["average_rating"], 1)}</div>'
            f'<div class="label">/ 5.0</div></div>',
            unsafe_allow_html=True,
        )
    with v2:
        st.markdown(
            f'<div class="mini-metric"><div class="label">리뷰 수</div>'
            f'<div class="value">{format_number(voc["total_reviews"])}</div>'
            f'<div class="label">건</div></div>',
            unsafe_allow_html=True,
        )

    complaints = pd.DataFrame(voc["complaints_by_category"])
    complaints = complaints.set_index("category")
    complaints.columns = ["불만 건수"]
    st.altair_chart(voc_bar_chart(complaints), use_container_width=True)
    st.caption('상세 분석은 [AX·인사이트 탭](?tab=insights)에서 확인하세요.')
    st.markdown("</div>", unsafe_allow_html=True)


def _insight_cards_html(insights: list[dict]) -> str:
    if not insights:
        return '<div class="insight-empty">현재 주의가 필요한 이상 신호가 없습니다.</div>'
    cards = []
    for item in insights:
        title = _html_esc(item["title"])
        body = _html_esc(item["body"])
        evidence = _html_esc(item["evidence"])
        label = _html_esc(item["action_label"])
        href = item["action_href"]
        sev = _html_esc(item["severity"])
        cards.append(
            f'<div class="insight-card {sev}">'
            f'<div class="insight-title">{title}</div>'
            f'<div class="insight-body">{body}</div>'
            f'<div class="insight-evidence">{evidence}</div>'
            f'<a href="{href}" class="insight-action" target="_self">{label}</a>'
            f"</div>"
        )
    return f'<div class="insight-list">{"".join(cards)}</div>'


def _strategy_cards_html(strategies: list[dict]) -> str:
    if not strategies:
        return '<div class="insight-empty">권고 전략이 없습니다.</div>'
    priority_label = {"high": "우선", "medium": "중요", "info": "참고"}
    cards = []
    for item in strategies:
        pri = _html_esc(priority_label.get(item["priority"], item["priority"]))
        title = _html_esc(item["title"])
        body = _html_esc(item["body"])
        actions = "".join(f"<li>{_html_esc(a)}</li>" for a in item.get("actions", []))
        sev = _html_esc(item["priority"])
        cards.append(
            f'<div class="strategy-card {sev}">'
            f'<div class="strategy-priority">{pri}</div>'
            f'<div class="strategy-title">{title}</div>'
            f'<div class="strategy-body">{body}</div>'
            f'<ul class="strategy-actions">{actions}</ul>'
            f"</div>"
        )
    return f'<div class="strategy-list">{"".join(cards)}</div>'


def _exec_brief_html(brief: dict) -> str:
    bullets = "".join(
        f'<span class="exec-brief-pill">{_html_esc(item)}</span>' for item in brief.get("bullets", [])
    )
    return (
        '<div class="exec-brief-card">'
        '<div class="exec-brief-kicker">Executive Briefing</div>'
        f'<div class="exec-brief-headline">{_html_esc(brief["headline"])}</div>'
        f'<div class="exec-brief-bullets">{bullets}</div>'
        "</div>"
    )


def render_executive_briefing_section(revenue: pd.DataFrame, rooms: pd.DataFrame, kpis: dict):
    st.markdown(
        '<div class="section-heading">경영분석 Executive Dashboard</div>'
        '<div class="section-desc">연중 매출·사업부문·전략 권고를 경영진 보고 형식으로 제공합니다</div>',
        unsafe_allow_html=True,
    )
    brief = executive_briefing(revenue, rooms, kpis)
    st.html(_exec_brief_html(brief))


def render_annual_revenue_report(revenue: pd.DataFrame):
    annual = annual_revenue_summary(revenue)
    period_label = annual.get("period_label", "최근 1년")
    period_desc = annual.get("period_desc", f"{period_label} 분석")
    st.markdown(
        '<div id="annual-report" class="category-anchor"></div>'
        '<div class="section-heading">연중 매출 분석 보고</div>'
        f'<div class="section-desc">{period_desc} · 계절별·사업부문별 실적 (단위: 천원)</div>',
        unsafe_allow_html=True,
    )

    seasonal_chart = seasonal_revenue_chart_data(revenue)
    seasonal_table = seasonal_revenue_table(revenue)
    segment_report = segment_annual_report(revenue)
    segment_table = segment_annual_table(revenue)

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.markdown(
            '<div class="panel-card">'
            '<div class="panel-title">계절별 매출 구성</div>'
            '<div class="panel-subtitle">봄·여름·가을·겨울 · 사업부문별 누적</div>',
            unsafe_allow_html=True,
        )
        if seasonal_chart.empty:
            st.caption("계절별 매출 데이터가 없습니다.")
        else:
            st.altair_chart(seasonal_segment_chart(seasonal_chart), use_container_width=True)
            st.markdown(
                '<div class="report-note">계절별 객실·온천·F&B 매출과 비중을 비교합니다.</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(seasonal_table, hide_index=True, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            '<div class="panel-card">'
            '<div class="panel-title">사업부문별 연간 실적</div>'
            f'<div class="panel-subtitle">{period_label} · 객실 / 온천 / F&B</div>',
            unsafe_allow_html=True,
        )
        if segment_report.empty:
            st.caption("사업부문별 연간 데이터가 없습니다.")
        else:
            st.altair_chart(segment_share_chart(segment_report), use_container_width=True)
            st.markdown(
                '<div class="report-note">사업부문별 연매출·비중·전년 대비 증감을 확인합니다.</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(
                segment_table,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "사업부문": st.column_config.TextColumn("사업부문", width="small"),
                    "연매출(천원)": st.column_config.TextColumn("연매출(천원)", width="medium"),
                    "비중(%)": st.column_config.TextColumn("비중(%)", width="small"),
                    "전년비(%)": st.column_config.TextColumn("전년비(%)", width="small"),
                },
            )
        st.markdown("</div>", unsafe_allow_html=True)

    quarterly = quarterly_revenue_trend(revenue)
    st.markdown(
        '<div class="panel-card">'
        '<div class="panel-title">분기별 매출 추이</div>'
        f'<div class="panel-subtitle">{period_label} · 최근 1년 분기 리뷰</div>',
        unsafe_allow_html=True,
    )
    if quarterly.empty:
        st.caption("분기별 매출 데이터가 없습니다.")
    else:
        st.altair_chart(quarterly_revenue_chart(quarterly), use_container_width=True)
        st.dataframe(
            quarterly_revenue_table(revenue),
            hide_index=True,
            use_container_width=True,
            column_config={
                "분기": st.column_config.TextColumn("분기", width="small"),
                "매출(천원)": st.column_config.TextColumn("매출(천원)", width="medium"),
                "객실": st.column_config.TextColumn("객실", width="small"),
                "온천": st.column_config.TextColumn("온천", width="small"),
                "F&B": st.column_config.TextColumn("F&B", width="small"),
            },
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_marketing_strategy_section(revenue: pd.DataFrame, kpis: dict):
    st.markdown(
        '<div id="marketing-strategy" class="category-anchor"></div>'
        '<div class="section-heading">마케팅 전략 권고</div>'
        '<div class="section-desc">매출·계절·평판 데이터 기반 수요 창출·채널·패키지 전략</div>',
        unsafe_allow_html=True,
    )
    strategies = generate_marketing_strategy(revenue, kpis)
    st.html(_strategy_cards_html(strategies))


def render_operations_strategy_section(revenue: pd.DataFrame, rooms: pd.DataFrame, kpis: dict):
    st.markdown(
        '<div id="operations-strategy" class="category-anchor"></div>'
        '<div class="section-heading">운영 전략 권고</div>'
        '<div class="section-desc">객실·인력·성수기·수익관리 관점의 실행 과제</div>',
        unsafe_allow_html=True,
    )
    strategies = generate_operations_strategy(revenue, rooms, kpis)
    st.html(_strategy_cards_html(strategies))


def render_ax_insights_section(revenue: pd.DataFrame, rooms: pd.DataFrame):
    st.markdown(
        '<div id="ax-insights" class="category-anchor"></div>'
        '<div class="section-heading">AX 인사이트 및 이상징후</div>'
        '<div class="section-desc">실적·객실·VOC 교차 분석 — 즉시 점검이 필요한 신호</div>',
        unsafe_allow_html=True,
    )
    insights = generate_ax_insights(revenue, rooms)
    st.html(_insight_cards_html(insights))


def render_review_analysis_section(kpis: dict):
    st.markdown(
        '<div id="review-analysis" class="category-anchor"></div>'
        '<div class="section-heading">고객 리뷰 분석</div>'
        '<div class="section-desc">리뷰 키워드·평점 분포·개선 권고 (규칙 기반, API 키 설정 시 AI 요약)</div>',
        unsafe_allow_html=True,
    )
    analysis = build_review_analysis(kpis)
    voc = analysis["voc"]
    narrative = analysis["narrative"]

    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        st.markdown(
            f'<div class="mini-metric"><div class="label">평균 평점</div>'
            f'<div class="value">{format_number(voc["average_rating"], 1)}</div>'
            f'<div class="label">/ 5.0</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="mini-metric"><div class="label">분석 리뷰</div>'
            f'<div class="value">{format_number(len(analysis["reviews"]))}</div>'
            f'<div class="label">건 (샘플)</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        top_kw = "—"
        if not analysis["keywords"].empty:
            top_kw = str(analysis["keywords"].iloc[0]["키워드"])
        st.markdown(
            f'<div class="mini-metric"><div class="label">Top 키워드</div>'
            f'<div class="value" style="font-size:1.15rem;">{_html_esc(top_kw)}</div></div>',
            unsafe_allow_html=True,
        )

    col_l, col_r = st.columns(2, gap="medium")
    with col_l:
        st.markdown(
            '<div class="panel-card"><div class="panel-title">평점 분포</div>',
            unsafe_allow_html=True,
        )
        ratings = analysis["ratings"]
        if ratings.empty:
            st.caption("표시할 리뷰가 없습니다.")
        else:
            st.altair_chart(review_rating_chart(ratings), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r:
        st.markdown(
            '<div class="panel-card"><div class="panel-title">키워드 언급</div>',
            unsafe_allow_html=True,
        )
        keywords = analysis["keywords"]
        if keywords.empty:
            st.caption("키워드 데이터가 없습니다.")
        else:
            st.altair_chart(keyword_bar_chart(keywords), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="panel-card"><div class="panel-title">분석 요약 및 권고</div>',
        unsafe_allow_html=True,
    )
    source_note = {
        "ai": "AI 요약",
        "rule": "규칙 기반 요약",
        "rule_fallback": "규칙 기반 요약 (AI 호출 실패)",
    }.get(narrative.get("source", "rule"), "규칙 기반 요약")
    st.caption(source_note)
    st.markdown(f'<p style="color:var(--navy);font-size:0.9rem;line-height:1.6;">{_html_esc(narrative["summary"])}</p>', unsafe_allow_html=True)
    if narrative.get("recommendations"):
        items = "".join(f"<li>{_html_esc(r)}</li>" for r in narrative["recommendations"])
        st.markdown(f'<ul class="reco-list">{items}</ul>', unsafe_allow_html=True)

    reviews = analysis["reviews"]
    if reviews:
        table = pd.DataFrame(reviews).rename(
            columns={"date": "일자", "rating": "평점", "channel": "채널", "text": "리뷰"}
        )
        st.dataframe(
            table[["일자", "채널", "평점", "리뷰"]],
            hide_index=True,
            use_container_width=True,
            height=min(36 * len(table) + 38, 360),
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_insights_panel(revenue: pd.DataFrame, rooms: pd.DataFrame, kpis: dict):
    render_executive_briefing_section(revenue, rooms, kpis)
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    render_annual_revenue_report(revenue)
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    render_marketing_strategy_section(revenue, kpis)
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    render_operations_strategy_section(revenue, rooms, kpis)
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    render_ax_insights_section(revenue, rooms)
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    render_review_analysis_section(kpis)


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
    active_tab = resolve_active_tab()
    render_tab_navigation(active_tab)

    if error_message:
        st.markdown(
            f'<div class="error-box">데이터를 불러오지 못했습니다: {error_message}</div>',
            unsafe_allow_html=True,
        )
        st.info(
            "Google Sheets 실데이터를 불러오지 못해 화면 계산을 중단했습니다. "
            "시트 공개 범위, 시트 ID, 탭 이름(`revenue`, `Rooms`), 필수 컬럼 구성을 확인해 주세요."
        )
        return

    if active_tab == "summary":
        render_kpis(compute_kpis(revenue, rooms), kpi_category_alerts(revenue))
        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
        render_daily_performance_panel(revenue)
    elif active_tab == "performance":
        render_operations_panel(revenue)
        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
        render_monthly_panel(revenue)
        _scroll_to_category_focus(st.query_params.get("category"))
    elif active_tab == "rooms":
        render_room_panel(rooms, show_room_list=True)
    elif active_tab == "voc":
        render_voc_panel()
    elif active_tab == "insights":
        kpis = compute_kpis(revenue, rooms)
        render_insights_panel(revenue, rooms, kpis)

    st.markdown(
        '<div class="footer-note">매출 단위: 천원 · 브라우저 새로고침 시 최신 데이터 반영</div>',
        unsafe_allow_html=True,
    )


main()
