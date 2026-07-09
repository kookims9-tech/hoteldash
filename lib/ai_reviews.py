"""Customer review analysis — rule-based summary with optional OpenAI."""

from __future__ import annotations

import json
import re
from collections import Counter

import pandas as pd
import streamlit as st

from config import OPENAI_API_KEY, OPENAI_MODEL
from lib.metrics import voc_summary

KEYWORD_LEXICON = {
    "시설": ["시설", "노후", "노후", "에어컨", "욕실", "타일", "환기", "오래"],
    "청결": ["청결", "청소", "냄새", "침구", "먼지"],
    "서비스": ["서비스", "응대", "직원", "체크인", "안내", "대기"],
    "온천": ["온천", "사우나", "스파"],
    "식음": ["조식", "식음", "룸서비스", "메뉴", "식사", "가격"],
    "접근성": ["주차", "접근", "위치", "교통"],
}


def _reviews_list(voc: dict | None = None) -> list[dict]:
    data = voc or voc_summary()
    return list(data.get("reviews", []))


def review_keyword_stats(reviews: list[dict] | None = None) -> pd.DataFrame:
    items = reviews if reviews is not None else _reviews_list()
    counts: Counter[str] = Counter()
    for review in items:
        text = review.get("text", "")
        for label, tokens in KEYWORD_LEXICON.items():
            if any(token in text for token in tokens):
                counts[label] += 1
    if not counts:
        return pd.DataFrame(columns=["키워드", "언급 건수"])
    rows = [{"키워드": k, "언급 건수": v} for k, v in counts.most_common()]
    return pd.DataFrame(rows)


def review_rating_distribution(reviews: list[dict] | None = None) -> pd.DataFrame:
    items = reviews if reviews is not None else _reviews_list()
    if not items:
        return pd.DataFrame(columns=["평점", "건수"])
    ratings = [int(r.get("rating", 0)) for r in items]
    dist = Counter(ratings)
    rows = [{"평점": f"{star}점", "건수": dist.get(star, 0)} for star in range(5, 0, -1)]
    return pd.DataFrame(rows)


def _top_complaint_label(voc: dict) -> str:
    complaints = voc.get("complaints_by_category", [])
    return complaints[0]["category"] if complaints else "—"


def rule_based_review_summary(voc: dict, keywords: pd.DataFrame) -> dict:
    reviews = _reviews_list(voc)
    avg = voc.get("average_rating", 0)
    total = voc.get("total_reviews", len(reviews))
    top_cat = _top_complaint_label(voc)
    neg = sum(1 for r in reviews if int(r.get("rating", 0)) <= 2)
    pos = sum(1 for r in reviews if int(r.get("rating", 0)) >= 4)

    kw_line = "—"
    if not keywords.empty:
        kw_line = ", ".join(f'{row["키워드"]}({row["언급 건수"]})' for _, row in keywords.head(3).iterrows())

    summary = (
        f"분석 대상 리뷰 {len(reviews)}건(전체 {total}건) 기준 평균 평점은 {avg:.1f}점입니다. "
        f"불만 카테고리 1위는 「{top_cat}」이며, 샘플 리뷰에서 자주 언급된 키워드는 {kw_line}입니다."
    )

    recommendations = []
    if top_cat == "시설노후":
        recommendations.append("노후 구역 보수 우선순위를 정하고, 객실 환기·욕실 설비 점검 주기를 단축하세요.")
    if top_cat == "청결" or (not keywords.empty and keywords.iloc[0]["키워드"] == "청결"):
        recommendations.append("청소·검수 체크리스트를 강화하고, 미실시·불량 건수를 주간 모니터링하세요.")
    if neg >= pos:
        recommendations.append("평점 2점 이하 리뷰의 공통 패턴을 주간 회의 안건으로 공유하세요.")
    if not recommendations:
        recommendations.append("긍정 리뷰의 강점(온천·서비스)을 프로모션 메시지에 반영하세요.")

    food_hits = 0
    if not keywords.empty:
        food_rows = keywords[keywords["키워드"] == "식음"]
        if not food_rows.empty:
            food_hits = int(food_rows.iloc[0]["언급 건수"])
    if food_hits >= 2:
        recommendations.append("식음 관련 VOC와 F&B 실적을 함께 보고 메뉴·가격 전략을 조정하세요.")

    return {
        "summary": summary,
        "recommendations": recommendations[:5],
        "source": "rule",
    }


@st.cache_data(ttl=300, show_spinner=False)
def ai_review_summary(voc_blob: str, keywords_blob: str, kpi_blob: str) -> dict:
    if not OPENAI_API_KEY:
        voc = voc_summary()
        keywords = review_keyword_stats()
        if keywords_blob:
            keywords = pd.DataFrame(json.loads(keywords_blob))
        return rule_based_review_summary(voc, keywords)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = (
            "당신은 온천관광호텔 경영 컨설턴트입니다. 아래 VOC·KPI 데이터를 바탕으로 "
            "한국어로 (1) 3문장 이내 요약 (2) 실행 가능한 개선 권고 3~5개 bullet을 JSON으로 답하세요.\n"
            f"VOC/KPI:\n{voc_blob}\n키워드:\n{keywords_blob}\nKPI:\n{kpi_blob}\n"
            '형식: {"summary":"...","recommendations":["...","..."]}'
        )
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content or ""
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            return {
                "summary": parsed.get("summary", ""),
                "recommendations": parsed.get("recommendations", []),
                "source": "ai",
            }
    except Exception:
        pass

    voc = voc_summary()
    keywords = review_keyword_stats()
    if keywords_blob:
        keywords = pd.DataFrame(json.loads(keywords_blob))
    result = rule_based_review_summary(voc, keywords)
    result["source"] = "rule_fallback"
    return result


def build_review_analysis(kpis: dict) -> dict:
    voc = voc_summary()
    reviews = _reviews_list(voc)
    keywords = review_keyword_stats(reviews)
    ratings = review_rating_distribution(reviews)

    voc_blob = str({k: voc[k] for k in ("average_rating", "total_reviews", "complaints_by_category")})
    kw_blob = keywords.to_json(orient="records", force_ascii=False) if not keywords.empty else "[]"
    kpi_blob = str(
        {
            "month_revenue": kpis.get("month_revenue"),
            "occupancy": kpis.get("occupancy"),
            "adr": kpis.get("adr"),
        }
    )
    narrative = ai_review_summary(voc_blob, kw_blob, kpi_blob)

    return {
        "voc": voc,
        "reviews": reviews,
        "keywords": keywords,
        "ratings": ratings,
        "narrative": narrative,
    }
