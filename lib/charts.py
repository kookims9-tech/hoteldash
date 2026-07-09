import altair as alt
import pandas as pd

from lib.metrics import format_number
from lib.theme import (
    BAD,
    CAT_FB,
    CAT_ROOM,
    CAT_SPA,
    CHART_GRID,
    CHART_GRID_STRONG,
    GOLD,
    GOLD_TINT,
    GOOD,
    NAVY,
    NAVY_MUTED,
    PRIOR,
    rgba,
)

_FONT = "Noto Sans KR, sans-serif"

_CATEGORY_RANGE = [CAT_ROOM, CAT_SPA, CAT_FB]
_CATEGORY_DOMAIN = ["객실", "온천", "F&B"]


def _axis(format_str: str | None = None) -> alt.Axis:
    params = {
        "labelColor": NAVY_MUTED,
        "titleColor": NAVY_MUTED,
        "titleFont": _FONT,
        "labelFont": _FONT,
        "titleFontSize": 11,
        "labelFontSize": 11,
        "gridColor": CHART_GRID,
        "domainColor": CHART_GRID_STRONG,
        "tickColor": CHART_GRID_STRONG,
        "titlePadding": 12,
        "labelPadding": 8,
    }
    if format_str:
        params["format"] = format_str
    return alt.Axis(**params)


def _apply_config(chart: alt.Chart) -> alt.Chart:
    return chart.configure(
        background="transparent",
        view={"strokeWidth": 0},
        padding={"left": 8, "right": 12, "top": 8, "bottom": 8},
        axis={"labelFont": _FONT, "titleFont": _FONT},
        legend={"labelFont": _FONT, "titleFont": _FONT, "labelColor": NAVY_MUTED},
    )


def revenue_line_chart(df: pd.DataFrame, y_col: str) -> alt.Chart:
    chart = (
        alt.Chart(df)
        .mark_area(
            line={"color": NAVY, "strokeWidth": 2.8},
            point=alt.OverlayMarkDef(
                filled=True,
                fill=GOLD_TINT,
                stroke=GOLD,
                strokeWidth=1.5,
                size=55,
            ),
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color=rgba(NAVY, 0.42), offset=0),
                    alt.GradientStop(color=rgba(NAVY, 0.06), offset=1),
                ],
                x1=1,
                x2=1,
                y1=1,
                y2=0,
            ),
            interpolate="monotone",
        )
        .encode(
            x=alt.X("month:N", title=None, axis=_axis()),
            y=alt.Y(f"{y_col}:Q", title="천원", axis=_axis(",.0f")),
            tooltip=[
                alt.Tooltip("month:N", title="월"),
                alt.Tooltip(f"{y_col}:Q", title="매출(천원)", format=",.0f"),
            ],
        )
        .properties(height=260)
    )
    return _apply_config(chart)


def daily_revenue_chart(df: pd.DataFrame, y_col: str) -> alt.Chart:
    chart = (
        alt.Chart(df)
        .mark_line(
            color=NAVY,
            strokeWidth=2.5,
            point=alt.OverlayMarkDef(
                filled=True,
                fill=GOLD_TINT,
                stroke=GOLD,
                strokeWidth=1.2,
                size=45,
            ),
            interpolate="monotone",
        )
        .encode(
            x=alt.X("일:N", title=None, axis=_axis()),
            y=alt.Y(f"{y_col}:Q", title="천원", axis=_axis(",.0f")),
            tooltip=[
                alt.Tooltip("일:N", title="일"),
                alt.Tooltip(f"{y_col}:Q", title="매출(천원)", format=",.0f"),
            ],
        )
        .properties(height=220)
    )
    return _apply_config(chart)


def revenue_bar_chart(df: pd.DataFrame, y_col: str) -> alt.Chart:
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
        .encode(
            x=alt.X("구분:N", title=None, axis=_axis()),
            y=alt.Y(f"{y_col}:Q", title="천원", axis=_axis(",.0f")),
            color=alt.Color(
                "구분:N",
                scale=alt.Scale(domain=_CATEGORY_DOMAIN, range=_CATEGORY_RANGE),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("구분:N", title="구분"),
                alt.Tooltip(f"{y_col}:Q", title="매출(천원)", format=",.0f"),
            ],
        )
        .properties(height=260)
    )
    return _apply_config(chart)


def grouped_bar_chart(df: pd.DataFrame) -> alt.Chart:
    melted = df.reset_index().melt(id_vars="cleaner", var_name="구분", value_name="건수")
    chart = (
        alt.Chart(melted)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("cleaner:N", title=None, axis=_axis()),
            y=alt.Y("건수:Q", title="건수", axis=_axis(",.0f")),
            color=alt.Color(
                "구분:N",
                scale=alt.Scale(
                    domain=["총 건수", "불량 건수"],
                    range=[NAVY, BAD],
                ),
                legend=alt.Legend(
                    title=None,
                    orient="top",
                    direction="horizontal",
                    labelColor=NAVY_MUTED,
                ),
            ),
            xOffset="구분:N",
            tooltip=[
                alt.Tooltip("cleaner:N", title="담당자"),
                alt.Tooltip("구분:N", title="구분"),
                alt.Tooltip("건수:Q", title="건수", format=",.0f"),
            ],
        )
        .properties(height=250)
    )
    return _apply_config(chart)


def yoy_grouped_bar_chart(df: pd.DataFrame, y_col: str = "매출(천원)") -> alt.Chart:
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("구분:N", title=None, axis=_axis()),
            y=alt.Y(f"{y_col}:Q", title="천원", axis=_axis(",.0f")),
            color=alt.Color(
                "기간:N",
                scale=alt.Scale(range=[GOLD, PRIOR]),
                legend=alt.Legend(
                    title=None,
                    orient="top",
                    direction="horizontal",
                    labelColor=NAVY_MUTED,
                ),
            ),
            xOffset="기간:N",
            tooltip=[
                alt.Tooltip("구분:N", title="구분"),
                alt.Tooltip("기간:N", title="기간"),
                alt.Tooltip(f"{y_col}:Q", title="매출(천원)", format=",.0f"),
            ],
        )
        .properties(height=220)
    )
    return _apply_config(chart)


def daily_composition_stacked_chart(df: pd.DataFrame) -> alt.Chart:
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("일:N", title=None, axis=_axis(), sort=None),
            y=alt.Y("매출(천원):Q", title="천원", axis=_axis(",.0f"), stack="zero"),
            color=alt.Color(
                "구분:N",
                scale=alt.Scale(domain=_CATEGORY_DOMAIN, range=_CATEGORY_RANGE),
                legend=alt.Legend(
                    title=None,
                    orient="top",
                    direction="horizontal",
                    labelColor=NAVY_MUTED,
                ),
            ),
            tooltip=[
                alt.Tooltip("일:N", title="일자"),
                alt.Tooltip("구분:N", title="구분"),
                alt.Tooltip("매출(천원):Q", title="매출(천원)", format=",.0f"),
            ],
        )
        .properties(height=240)
    )
    return _apply_config(chart)


def weekly_revenue_chart(df: pd.DataFrame, y_col: str) -> alt.Chart:
    chart = (
        alt.Chart(df)
        .mark_line(
            color=NAVY,
            strokeWidth=2.5,
            point=alt.OverlayMarkDef(
                filled=True,
                fill=GOLD_TINT,
                stroke=GOLD,
                strokeWidth=1.2,
                size=45,
            ),
            interpolate="monotone",
        )
        .encode(
            x=alt.X("주:N", title=None, axis=_axis(), sort=None),
            y=alt.Y(f"{y_col}:Q", title="천원", axis=_axis(",.0f")),
            tooltip=[
                alt.Tooltip("주:N", title="주간"),
                alt.Tooltip(f"{y_col}:Q", title="매출(천원)", format=",.0f"),
            ],
        )
        .properties(height=220)
    )
    return _apply_config(chart)


def daily_composition_donut(df: pd.DataFrame, total: float) -> alt.Chart:
    if df.empty or total <= 0:
        empty = pd.DataFrame({"구분": ["데이터 없음"], "매출(천원)": [1.0], "share_pct": [100.0], "pct_label": [""]})
        return _apply_config(
            alt.Chart(empty)
            .mark_arc(innerRadius=55, outerRadius=100)
            .encode(theta=alt.Theta("매출(천원):Q", stack=True))
            .properties(width=300, height=300)
        )

    base = alt.Chart(df).encode(
        theta=alt.Theta("매출(천원):Q", stack=True, sort=None),
        color=alt.Color(
            "구분:N",
            scale=alt.Scale(domain=_CATEGORY_DOMAIN, range=_CATEGORY_RANGE),
            legend=alt.Legend(
                title=None,
                orient="bottom",
                direction="horizontal",
                labelColor=NAVY_MUTED,
            ),
        ),
        order=alt.Order("구분:N", sort="ascending"),
        tooltip=[
            alt.Tooltip("구분:N", title="구분"),
            alt.Tooltip("매출(천원):Q", title="매출(천원)", format=",.0f"),
            alt.Tooltip("share_pct:Q", title="비중(%)", format=".1f"),
        ],
    )
    donut = base.mark_arc(innerRadius=62, outerRadius=108, stroke="#FFFFFF", strokeWidth=2)
    labels = base.mark_text(radius=84, size=12, fontWeight=600, color="#FFFFFF").encode(
        text="pct_label:N",
    )
    center_label = format_number(total)
    center = (
        alt.Chart(pd.DataFrame({"lines": [f"{center_label}\n총매출"]}))
        .mark_text(
            align="center",
            baseline="middle",
            fontSize=14,
            fontWeight=700,
            color=NAVY,
            lineBreak="\n",
        )
        .encode(
            text=alt.Text("lines:N"),
            theta=alt.ThetaDatum(0),
            radius=alt.RadiusDatum(0),
        )
    )
    chart = (
        alt.layer(donut, labels, center)
        .properties(width="container", height=260)
        .configure_view(strokeWidth=0)
    )
    return _apply_config(chart)


_SEASON_SORT = ["봄(3~5월)", "여름(6~8월)", "가을(9~11월)", "겨울(12~2월)"]


def seasonal_segment_chart(df: pd.DataFrame) -> alt.Chart:
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("계절:N", title=None, axis=_axis(), sort=_SEASON_SORT),
            y=alt.Y("매출(천원):Q", title="천원", axis=_axis(",.0f"), stack="zero"),
            color=alt.Color(
                "구분:N",
                scale=alt.Scale(domain=_CATEGORY_DOMAIN, range=_CATEGORY_RANGE),
                legend=alt.Legend(
                    title=None,
                    orient="top",
                    direction="horizontal",
                    labelColor=NAVY_MUTED,
                ),
            ),
            order=alt.Order("구분:N", sort="ascending"),
            tooltip=[
                alt.Tooltip("계절:N", title="계절"),
                alt.Tooltip("구분:N", title="사업부문"),
                alt.Tooltip("매출(천원):Q", title="매출(천원)", format=",.0f"),
            ],
        )
        .properties(height=260)
    )
    return _apply_config(chart)


def quarterly_revenue_chart(df: pd.DataFrame) -> alt.Chart:
    chart = (
        alt.Chart(df)
        .mark_line(
            color=NAVY,
            strokeWidth=2.8,
            point=alt.OverlayMarkDef(
                filled=True,
                fill=GOLD_TINT,
                stroke=GOLD,
                strokeWidth=1.2,
                size=55,
            ),
            interpolate="monotone",
        )
        .encode(
            x=alt.X("분기:N", title=None, axis=_axis(), sort=["Q1", "Q2", "Q3", "Q4"]),
            y=alt.Y("매출(천원):Q", title="천원", axis=_axis(",.0f")),
            tooltip=[
                alt.Tooltip("분기:N", title="분기"),
                alt.Tooltip("매출(천원):Q", title="매출(천원)", format=",.0f"),
            ],
        )
        .properties(height=220)
    )
    return _apply_config(chart)


def segment_share_chart(df: pd.DataFrame) -> alt.Chart:
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
        .encode(
            x=alt.X("사업부문:N", title=None, axis=_axis(), sort=_CATEGORY_DOMAIN),
            y=alt.Y("연매출(천원):Q", title="천원", axis=_axis(",.0f")),
            color=alt.Color(
                "사업부문:N",
                scale=alt.Scale(domain=_CATEGORY_DOMAIN, range=_CATEGORY_RANGE),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("사업부문:N", title="사업부문"),
                alt.Tooltip("연매출(천원):Q", title="연매출(천원)", format=",.0f"),
                alt.Tooltip("비중(%):Q", title="비중(%)", format=".1f"),
            ],
        )
        .properties(height=240)
    )
    return _apply_config(chart)


def review_rating_chart(df: pd.DataFrame) -> alt.Chart:
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color=NAVY)
        .encode(
            x=alt.X("평점:N", title=None, axis=_axis(), sort=None),
            y=alt.Y("건수:Q", title="건수", axis=_axis(",.0f")),
            tooltip=[
                alt.Tooltip("평점:N", title="평점"),
                alt.Tooltip("건수:Q", title="건수", format=",.0f"),
            ],
        )
        .properties(height=220)
    )
    return _apply_config(chart)


def keyword_bar_chart(df: pd.DataFrame) -> alt.Chart:
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8, color=GOLD)
        .encode(
            y=alt.Y("키워드:N", title=None, axis=_axis(), sort="-x"),
            x=alt.X("언급 건수:Q", title="건수", axis=_axis(",.0f")),
            tooltip=[
                alt.Tooltip("키워드:N", title="키워드"),
                alt.Tooltip("언급 건수:Q", title="건수", format=",.0f"),
            ],
        )
        .properties(height=240)
    )
    return _apply_config(chart)


def voc_bar_chart(df: pd.DataFrame) -> alt.Chart:
    chart = (
        alt.Chart(df.reset_index())
        .mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8, color=GOLD)
        .encode(
            y=alt.Y("category:N", title=None, axis=_axis(), sort="-x"),
            x=alt.X("불만 건수:Q", title="건수", axis=_axis(",.0f")),
            tooltip=[
                alt.Tooltip("category:N", title="카테고리"),
                alt.Tooltip("불만 건수:Q", title="건수", format=",.0f"),
            ],
        )
        .properties(height=250)
    )
    return _apply_config(chart)
