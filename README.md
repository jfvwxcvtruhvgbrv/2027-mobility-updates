# 2027 Mobility Updates

자동차·모빌리티 디자이너·기획자를 위한 글로벌 관찰 리포트. 매일 새벽 자동 수집 → 한국어 단신 → GitHub Pages 아카이브.
알림은 Claude 앱의 예약 작업이 아침 6시에 리포트를 읽고 보낸다.

## 원칙
- **넓게 본다.** 사용자의 선택(심층 대기)은 수집 범위·점수에 영향을 주지 않는다. 선정은 권역·분야 최소 할당, '처음 보는 것' 가점, 무작위 '탐색 표본'으로 한다.
- **싸게 거르고, 비싼 작업은 고른 것에만.** 발견·중복 제거·본문 추출은 프로그램(토큰 0), 분류·단신은 Claude Haiku, 하루 1회 흐름 요약만 Sonnet.
- **본 범위와 못 본 범위를 함께 보고한다.** 리포트 끝 '공백·범위'에 권역×분야 표, 접근 실패 출처, 상한 때문에 빠진 사건, 실측 비용.
- 원문은 재구성 요약 + 링크. 각 단신에 근거 수준(본문 / 헤드라인·요약 / 초록) 표시.

## 구조
```
config.py          모델·가격·예산, 권역/국가/현지어 검색어, 직접 RSS, 연구 API 쿼리
fetch.py           Google News RSS(국가·언어별), 전문 매체 RSS, arXiv, OpenAlex → 후보 (토큰 0)
process.py         분류(Haiku, 50건 묶음) → 커버리지 선정 → 본문 추출(trafilatura) → 단신(Haiku, 8건 묶음) → 오늘의 흐름(Sonnet 1회)
llm.py             Claude 호출, 실측 사용량 data/usage.jsonl 기록, 실행 예산 상한
render.py          docs/ 정적 사이트: index(오늘), reports/날짜.html, archive.html(전체 검색), pending.html, latest.json
run_pipeline.py    전체 실행. 키 없음/후보 0건/단신 0건이면 종료코드 1
scripts/mock_run.py  키·네트워크 없이 목업으로 화면 확인
.github/workflows/daily.yml  매일 KST 04:37 실행 + 이슈 변경 시 심층 목록 갱신 + Pages 배포
data/              reports/*.json(원본 데이터), seen.json(처리 이력), entities.json(새로움 판정), usage.jsonl, hold/(예산 초과 보류)
```

## 설정 (한 번만)
1. GitHub에서 새 저장소 생성(현재: jfvwxcvtruhvgbrv/2027-mobility-updates)(Public — 무료 계정의 Pages는 공개 저장소 필요), 이 폴더 전체를 업로드.
2. Settings → Secrets and variables → Actions → `ANTHROPIC_API_KEY` 등록 (이 프로젝트 전용 키 권장, 콘솔에서 월 사용 한도 설정 권장).
3. Settings → Pages → Source: **GitHub Actions**.
4. Issues → Labels → `deep-dive` 라벨 생성.
5. Actions → daily-report → **Run workflow**로 첫 실행. 로그의 `[WARN]` 줄로 막힌 출처를 확인.
6. 리포트 주소: https://jfvwxcvtruhvgbrv.github.io/2027-mobility-updates/

## 심층 대기 목록
리포트 카드의 "＋ 심층 대기에 추가" → GitHub 새 이슈 화면(라벨·내용 자동 입력) → 제출. 이슈가 생기면 워크플로가 pending.html을 다시 그린다.
심층 조사는 원할 때 Claude 대화에서 "심층 대기 목록 n건 조사해줘"로 진행하고, 끝나면 이슈를 닫는다.

## 비용 (추정, 첫 실행 후 실측으로 교체)
가격(2026-11-10 확인): Haiku 5.5 입력 $0.10 / 출력 $0.50, Sonnet 5.5 $2 / $10 (100만 토큰당).
하루 후보 약 1,500건 가정 시 분류 ≈ $0.04, 단신 140건 ≈ $0.02, 흐름 ≈ $0.03 → **하루 약 $0.1, 월 약 $3**.
실제 값은 리포트 하단 '운영'과 `data/usage.jsonl`에 기록된다. `RUN_BUDGET_USD`(기본 $0.50)를 넘으면 남은 후보는 `data/hold/`에 보류.

## 알려진 한계
- Google News 링크는 원문 주소로 풀리지 않는 경우가 많아 그 단신은 '헤드라인·요약 기반'으로 표시된다. 현지 매체 직접 RSS를 늘릴수록 '본문 기반' 비율이 오른다.
- 직접 RSS 주소, 국가별 Google News 판, OpenAlex/arXiv 응답은 작업 환경에서 접속이 막혀 실제 검증하지 못했다. 첫 실행 로그로 확인.
- 썸네일은 v1에서 넣지 않았다(인물 사진·권리 확인 비용). 심층 기사에서 공식 이미지로 다룬다.
- '처음 보는 것'은 첫 실행 이후부터 동작한다(기준 기록이 쌓여야 함).
