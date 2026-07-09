# 온천관광호텔 경영 대시보드 — 개발 계획 문서 (PRD v0.1)

과제 제출·Build 전 정의 문서 모음입니다. 발표 자료(`docs/presentation/`)와 함께 제출하세요.

| # | 문서 | 내용 |
|---|------|------|
| 0 | [00_웹앱개발프로세스_대조표.md](00_웹앱개발프로세스_대조표.md) | 첨부 프로세스 문서·통합 PDF와 계획 정합성 |
| 1 | [01_PRD.md](01_PRD.md) | 서비스 목적·사용자·시나리오·출력 정의 |
| 2 | [02_데이터정의서.md](02_데이터정의서.md) | 입력 데이터·컬럼·입력 형식·DB 매핑 |
| 3 | [03_화면정의서.md](03_화면정의서.md) | 탭 구성·화면별 I/O·URL 규칙 |
| 4 | [04_배포_보안_가이드.md](04_배포_보안_가이드.md) | 환경변수·Streamlit Cloud·보안 |
| 5 | [05_ERD_Phase2_아키텍처.md](05_ERD_Phase2_아키텍처.md) | Supabase ERD·migration·ETL·Next.js |
| 6 | [06_업무자동화_설계서.md](06_업무자동화_설계서.md) | 2차 업무자동화 탭 설계 (1차 미구현) |

## Phase 요약

| Phase | 목표 | 플랫폼 |
|-------|------|--------|
| **1차 (현재)** | 과제 제출·발표용 프로토타입 | Streamlit + Google Sheets |
| **2차 (과제 후)** | 운영형 웹앱 | Next.js (Vercel) + Supabase |

## 빠른 링크

- 발표 자료: [docs/presentation/README.md](../presentation/README.md)
- Streamlit Cloud 배포: [04_배포_보안_가이드.md](04_배포_보안_가이드.md)
- Secrets 예시: [.streamlit/secrets.toml.example](../../.streamlit/secrets.toml.example)
