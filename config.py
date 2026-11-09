"""2027 Mobility Updates 설정.

수집 범위는 '넓게'가 원칙이다. 사용자 선택(심층 대기 목록)은 이 설정이나 점수에 영향을 주지 않는다.
"""

# ── 모델과 가격 (USD / 1M tokens) ─────────────────────────────────────────
# 가격 확인일: 2026-11-10 (Claude 공식 가격표를 인용한 보도 기준). 바뀌면 여기만 고친다.
CHEAP_MODEL = "claude-haiku-5-5"      # 분류·단신 (프롬프트 10만 토큰 이하 구간)
MID_MODEL = "claude-sonnet-5-5"       # 오늘의 흐름 요약 1회 (선택)
PRICES = {
    "claude-haiku-5-5": {"in": 0.10, "out": 0.50, "cache_read": 0.01},
    "claude-sonnet-5-5": {"in": 2.00, "out": 10.00, "cache_read": 0.10},
}
PRICES_CHECKED = "2026-11-10"

# 실행 1회 예산 상한(USD). 넘으면 남은 후보는 data/hold/ 로 보류하고 계속 렌더링한다.
RUN_BUDGET_USD = 0.50
USE_MID_MODEL_FOR_OVERVIEW = True

# ── 수집 범위 ──────────────────────────────────────────────────────────────
LOOKBACK_HOURS = 30          # 매일 실행, 겹침 6시간(중복은 seen.json이 제거)
MAX_PER_QUERY = 30           # Google News 쿼리당 최대 항목
TRIAGE_BATCH = 50            # 저비용 분류 1회 호출당 제목 수
MAX_BRIEFS = 140             # 하루 단신 상한
BRIEF_BATCH = 8              # 단신 1회 호출당 기사 수
BODY_CHARS = 1500            # 단신 작성 시 기사당 본문 상한(글자)
EXPLORATION_SLOTS = 6        # 낮은 점수 중 무작위로 싣는 '탐색 표본'
MIN_PER_REGION = 3           # 권역별 최소 게재(후보가 있을 때)
MIN_PER_AREA = 4             # 분야별 최소 게재(후보가 있을 때)

AREAS = {
    "car": "글로벌 자동차",
    "mobility": "글로벌 모빌리티",
    "research": "글로벌 리서치",
    "event": "글로벌 이벤트",
}

# 관찰 태그 (분류 모델이 이 목록 안에서 고른다. 새 주제는 'new_topic'으로 자유 기입)
TAGS = [
    "신차·현지출시", "외장디자인", "실내·HMI", "CMF·소재", "패키징", "PQ(감성품질)", "전동화",
    "배터리", "충전", "상용차", "레트로·클래식", "콘셉트카", "이륜차", "마이크로모빌리티",
    "카고바이크", "로보틱스", "자율주행", "배송·물류", "농어촌·다목적", "교통약자·접근성",
    "드론·항공이동", "스마트시티", "대중교통", "IT·SW·AI", "디자인프로세스·도구", "인간공학",
    "제조·3D프린팅", "지속가능성", "비즈니스모델", "정책·규제", "모터쇼·전시", "학술대회",
]

# 권역 → 국가. 각 국가는 Google News 판(hl, gl, ceid)과 현지어 검색어를 가진다.
# 판이나 검색어가 맞지 않으면 0건이 나오고, 그 사실이 리포트의 '공백' 표에 그대로 드러난다.
REGIONS = {
    "북미": [
        ("미국", "en-US", "US", "US:en", ["car design", "new car launch", "electric vehicle", "micromobility", "robotaxi"]),
        ("캐나다", "en-CA", "CA", "CA:en", ["new car Canada", "electric vehicle Canada"]),
        ("멕시코", "es-419", "MX", "MX:es-419", ["auto nuevo México", "auto eléctrico", "movilidad urbana"]),
    ],
    "유럽": [
        ("독일", "de", "DE", "DE:de", ["Autodesign", "Elektroauto neu", "Mobilität Zukunft", "autonomes Fahren"]),
        ("프랑스", "fr", "FR", "FR:fr", ["design automobile", "voiture électrique nouvelle", "mobilité urbaine"]),
        ("영국", "en-GB", "GB", "GB:en", ["car design", "new car UK", "e-bike cargo"]),
        ("이탈리아", "it", "IT", "IT:it", ["design auto", "auto elettrica nuova", "mobilità sostenibile"]),
    ],
    "동아시아": [
        ("중국", "zh-CN", "CN", "CN:zh-Hans", ["新能源汽车 新车", "汽车设计", "智能驾驶", "智能座舱"]),
        ("한국", "ko", "KR", "KR:ko", ["신차 출시", "전기차", "자동차 디자인", "모빌리티", "자율주행"]),
        ("일본", "ja", "JP", "JP:ja", ["新型車 発表", "電気自動車", "カーデザイン", "モビリティ"]),
    ],
    "남아시아": [
        ("인도", "en-IN", "IN", "IN:en", ["car launch India", "electric scooter India", "EV India"]),
        ("인도(힌디)", "hi", "IN", "IN:hi", ["इलेक्ट्रिक कार", "नई कार लॉन्च"]),
        ("파키스탄", "en-PK", "PK", "PK:en", ["car launch Pakistan", "electric vehicle Pakistan"]),
    ],
    "동남아시아": [
        ("인도네시아", "id", "ID", "ID:id", ["mobil baru", "mobil listrik", "motor listrik", "desain mobil"]),
        ("태국", "th", "TH", "TH:th", ["รถยนต์ไฟฟ้า", "รถใหม่ เปิดตัว"]),
        ("베트남", "vi", "VN", "VN:vi", ["xe điện", "ô tô mới ra mắt"]),
        ("말레이시아", "en-MY", "MY", "MY:en", ["kereta elektrik", "new car Malaysia"]),
        ("필리핀", "en-PH", "PH", "PH:en", ["car launch Philippines", "electric jeepney"]),
    ],
    "서남아시아": [
        ("튀르키예", "tr", "TR", "TR:tr", ["elektrikli otomobil", "yeni otomobil"]),
        ("UAE", "ar", "AE", "AE:ar", ["سيارة كهربائية", "سيارة جديدة"]),
        ("사우디아라비아", "ar", "SA", "SA:ar", ["سيارة كهربائية السعودية"]),
    ],
    "아프리카": [
        ("이집트", "ar", "EG", "EG:ar", ["سيارة كهربائية مصر"]),
        ("모로코", "fr", "MA", "MA:fr", ["voiture Maroc", "mobilité électrique Maroc"]),
        ("나이지리아", "en-NG", "NG", "NG:en", ["electric vehicle Nigeria", "car Nigeria"]),
        ("케냐", "en-KE", "KE", "KE:en", ["electric motorcycle Kenya", "boda boda electric"]),
        ("남아공", "en-ZA", "ZA", "ZA:en", ["new car South Africa", "electric vehicle South Africa"]),
    ],
}

# 직접 RSS (전문 매체). 피드 주소는 배포 후 Actions 로그로 확인해야 한다(미검증).
DIRECT_FEEDS = [
    ("Electrek", "https://electrek.co/feed/", "북미", "미국"),
    ("InsideEVs", "https://insideevs.com/rss/articles/all/", "북미", "미국"),
    ("Car and Driver", "https://www.caranddriver.com/rss/all.xml/", "북미", "미국"),
    ("electrive", "https://www.electrive.com/feed/", "유럽", "독일"),
    ("CnEVPost", "https://cnevpost.com/feed/", "동아시아", "중국"),
    ("Yanko Design", "https://www.yankodesign.com/feed/", "글로벌", "글로벌"),
    ("designboom transportation", "https://www.designboom.com/transportation/feed/", "글로벌", "글로벌"),
    ("detikOto", "https://rss.detik.com/index.php/oto", "동남아시아", "인도네시아"),
]

# 연구 (무료 공식 API). Google Scholar는 자동 수집 불가라 쓰지 않는다.
ARXIV_QUERY = (
    'abs:"vehicle design" OR abs:"automotive design" OR abs:"car interior" OR abs:"in-vehicle" '
    'OR abs:"micromobility" OR abs:"perceived quality" OR abs:"automotive HMI" OR abs:"e-scooter"'
)
OPENALEX_SEARCHES = ["automotive design", "vehicle interior", "micromobility", "automotive HMI",
                     "perceived quality automotive", "vehicle materials sustainability"]

# GitHub (심층 대기 버튼용). Actions에서는 GITHUB_REPOSITORY 환경변수가 우선한다.
DEFAULT_REPO = "jfvwxcvtruhvgbrv/2027-mobility-updates"
PENDING_LABEL = "deep-dive"
