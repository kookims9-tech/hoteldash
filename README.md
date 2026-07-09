# 온천관광호텔 경영 대시보드

Google Sheets 실적·객실 데이터를 연동하는 **Streamlit 경영 대시보드** (과제 제출용 프로토타입).

## 라이브 데모

> Streamlit Cloud 배포 후 아래 URL을 업데이트하세요.

```
https://YOUR-APP-NAME.streamlit.app
```

## 로컬 실행

```bash
cd hoteldash
python3 -m venv VENV
source VENV/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 선택
streamlit run app.py
```

## 문서

| 구분 | 경로 |
|------|------|
| 발표 자료 | [docs/presentation/](docs/presentation/) |
| PRD·ERD·화면정의 | [docs/plan/](docs/plan/) |
| 배포 가이드 | [docs/plan/04_배포_보안_가이드.md](docs/plan/04_배포_보안_가이드.md) |

## 탭 구성

요약 · 실적 · 객실운영 · VOC · AX·인사이트

## 데이터

- **매출·객실:** Google Sheets (CSV Export, 실데이터 only)
- **VOC:** `data/voc.py` 샘플

## Streamlit Cloud 배포 (요약)

1. GitHub에 이 저장소 push
2. https://share.streamlit.io → New app → `app.py`
3. Secrets에 [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example) 내용 입력
4. Deploy

상세: [docs/plan/04_배포_보안_가이드.md](docs/plan/04_배포_보안_가이드.md)
