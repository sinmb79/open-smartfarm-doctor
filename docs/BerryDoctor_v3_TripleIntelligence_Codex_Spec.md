# BerryDoctor v3.0 — 3중 지능 확장 개발구현서

> **기존 BerryDoctor (Phase 0~5) 배포 완료 상태에서 추가 구현**
> Target: OpenClaw (Codex) Implementation
> Date: 2026-04-07

---

## 0. 전제 조건

- BerryDoctor Phase 0~5 이미 구현·배포 완료
- berry-engine, SQLite, Mosquitto, YOLO, 카카오톡 봇 모두 작동 중
- 이 문서는 **기존 코드를 수정하지 않고** 3개 모듈을 추가하는 확장 스펙

## 1. 확장 목표

기존 BerryDoctor는 **센서(땅)**만 본다. v3.0은 여기에 **위성(하늘)**과 **시그널(세계)**을 추가하고, **fusion(두뇌)**이 3개를 하나로 합쳐서 판단한다.

```
         ┌──────────────┐
         │  fusion/     │ ← 3개를 합쳐서 하나의 판단
         │ intelligence │
         └──┬───┬───┬───┘
            │   │   │
    ┌───────┘   │   └───────┐
    ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐
│satellite│ │ sensor │ │ signal │
│ (하늘)  │ │ (땅)   │ │ (세계) │
│        │ │ 기존    │ │        │
│ 신규    │ │ 유지    │ │ 신규    │
└────────┘ └────────┘ └────────┘
```

**농부가 받는 건 여전히 카카오톡 메시지 하나.** 내부에서 3개가 합쳐졌다는 걸 모름.

---

## 2. 추가 디렉토리 구조

```
berry-doctor/                        # 기존 루트
├── engine/
│   ├── rules/                       # 기존 유지
│   ├── ai/                          # 기존 유지
│   ├── kakao/                       # 기존 유지
│   ├── scheduler/                   # 기존 유지 + 신규 job 추가
│   │   ├── ... (기존)
│   │   ├── signal_job.py            # 🆕 시그널 수집 스케줄
│   │   └── satellite_job.py         # 🆕 위성 수집 스케줄
│   │
│   ├── signal/                      # 🆕 전체 신규
│   │   ├── __init__.py
│   │   ├── collector.py             # 소스별 수집기
│   │   ├── sources/
│   │   │   ├── rda_pest.py          # 농진청 병해충 예찰
│   │   │   ├── nongsaro.py          # 농사로 긴급공지
│   │   │   ├── kma_special.py       # 기상청 이상기후 특보
│   │   │   ├── fao_giews.py         # FAO GIEWS RSS
│   │   │   ├── japan_naro.py        # 일본 농연기구
│   │   │   ├── market_alert.py      # 도매시장 가격 급변
│   │   │   ├── x_agri.py            # X(트위터) 농업 키워드
│   │   │   ├── arxiv_agri.py        # 농학 논문 프리프린트
│   │   │   └── community.py         # BerryDoctor 사용자 병해 감지 풀
│   │   ├── analyzer.py              # 관련성 판단 + 긴급도 분류
│   │   ├── translator.py            # 외국어 → 한국어 요약
│   │   └── db.py                    # signal_log 테이블 CRUD
│   │
│   ├── satellite/                   # 🆕 전체 신규
│   │   ├── __init__.py
│   │   ├── copernicus.py            # Sentinel-2 API 클라이언트
│   │   ├── agri_satellite.py        # 한국 농림위성 API (2026~ 연동)
│   │   ├── field_manager.py         # 필지 경계 관리 (주소→GPS→영역)
│   │   ├── indices.py               # NDVI, NDWI, GNDVI 계산
│   │   ├── change_detector.py       # 시계열 변화 감지
│   │   ├── interpreter.py           # 지수 → 한국어 해석
│   │   └── db.py                    # satellite_log 테이블 CRUD
│   │
│   └── fusion/                      # 🆕 핵심 — 3중 통합 판단
│       ├── __init__.py
│       ├── intelligence.py          # 메인: 3개 소스 통합 판단
│       ├── context_builder.py       # 맥락 조합 (위성+센서+시그널)
│       ├── risk_scorer.py           # 복합 위험도 점수 산출
│       ├── message_composer.py      # 통합 카카오톡 메시지 생성
│       └── templates.py             # 통합 메시지 템플릿
│
├── data/
│   ├── ... (기존)
│   ├── signal_sources.json          # 🆕 수집 소스 정의
│   └── satellite_config.json        # 🆕 위성 설정 (타일, 밴드)
│
└── tests/
    ├── ... (기존)
    ├── test_signal.py               # 🆕
    ├── test_satellite.py            # 🆕
    └── test_fusion.py               # 🆕
```

---

## 3. engine/signal/ — 글로벌 농업 시그널

### 3.1 collector.py

```python
"""
시그널 수집기 — 모든 소스를 순회하며 새 시그널을 수집

실행 주기: scheduler/signal_job.py에서 호출
  - 국내 소스: 매 6시간
  - 해외 소스: 매일 06:00
  - 가격 급변: 매 시간
  - 사용자 풀: 실시간 (병해 감지 시 즉시)

수집 흐름:
  1. 각 source 모듈의 fetch() 호출
  2. 새 항목만 필터 (중복 제거: URL 또는 해시)
  3. analyzer.py로 관련성·긴급도 판단
  4. 관련 있으면 DB 저장 + fusion에 전달
  5. 관련 없으면 버림
"""

class SignalCollector:
    def __init__(self, config, db):
        self.sources = [
            RDAPestSource(),       # 농진청 병해충 예찰
            NongsaroSource(),      # 농사로 긴급공지  
            KMASpecialSource(),    # 기상청 특보
            FAOGIEWSSource(),      # FAO 세계식량조기경보
            JapanNAROSource(),     # 일본 농연기구
            MarketAlertSource(),   # 도매시장 가격 급변
            XAgriSource(),         # X 트위터 농업 키워드
            ArxivAgriSource(),     # 농학 논문
            CommunitySource(),     # BerryDoctor 사용자 풀
        ]
    
    async def collect_all(self):
        """모든 소스에서 수집 → 분석 → 저장"""
        for source in self.sources:
            raw_items = await source.fetch()
            for item in raw_items:
                if self.db.is_duplicate(item.hash):
                    continue
                relevance = self.analyzer.evaluate(item, self.farm_profile)
                if relevance.score > 0.3:  # 30% 이상 관련
                    item.relevance = relevance
                    self.db.save_signal(item)
                    self.fusion.on_new_signal(item)  # fusion에 알림
```

### 3.2 sources/ — 개별 수집 모듈 인터페이스

```python
"""
모든 소스는 이 인터페이스를 구현:

class SignalSource:
    name: str               # "농진청 병해충 예찰"
    url: str                # RSS/API 엔드포인트
    language: str           # "ko", "ja", "en"
    check_interval_hours: int
    
    async def fetch(self) -> List[RawSignal]
    
RawSignal:
    source: str             # 소스 이름
    title: str              # 원문 제목
    summary: str            # 원문 요약 (200자)
    url: str                # 원본 링크
    published_at: datetime
    language: str
    hash: str               # 중복 감지용
    tags: List[str]         # ["딸기", "잿빛곰팡이", "충남"]
"""
```

### 3.3 sources/rda_pest.py — 농진청 병해충 예찰 (예시)

```python
"""
농촌진흥청 병해충 예찰 정보 수집
URL: https://ncpms.rda.go.kr (국가 병해충 관리 시스템)

수집 대상:
  - 딸기 관련 병해충 발생 속보
  - 지역별 병해충 발생 동향
  - 약제 저항성 정보

주기: 매 6시간
"""

class RDAPestSource(SignalSource):
    name = "농진청 병해충 예찰"
    language = "ko"
    check_interval_hours = 6
    
    async def fetch(self) -> List[RawSignal]:
        # 1. ncpms.rda.go.kr 크롤링 (RSS 없으면 HTML 파싱)
        # 2. "딸기" 포함 항목 필터
        # 3. RawSignal 리스트 반환
        pass
```

### 3.4 sources/community.py — 사용자 풀 (핵심 차별점)

```python
"""
BerryDoctor 사용자들의 병해 감지를 익명 풀링

작동 방식:
  1. 어떤 농가에서 YOLO가 병해 감지 (확신도 70%+)
  2. 해당 정보를 익명화: 지역(시군구)만 남기고 개인정보 제거
  3. 같은 지역(반경 30km) BerryDoctor 사용자에게 시그널 전송
  
예: "서산시에서 잿빛곰팡이 감지 (오늘)"
  → 부석면 다른 농가에 "우리 동네 잿빛곰팡이 발생, 주의하세요"

※ 반드시 농부 동의 후에만 공유 (초기 설정에서 선택)
※ 개인 식별 정보 절대 포함 안 함
"""

class CommunitySource(SignalSource):
    name = "BerryDoctor 커뮤니티"
    language = "ko"
    
    def on_local_detection(self, detection, farm_config):
        """로컬 YOLO 감지 시 호출됨 (기존 ai/disease_detector.py에서)"""
        if not farm_config.get("share_to_community", False):
            return  # 공유 미동의
        
        signal = RawSignal(
            source="community",
            title=f"{farm_config['region_name']}에서 {detection.disease_ko} 감지",
            summary=f"확신도 {detection.confidence}%, 환경: {detection.temp}°C/{detection.humidity}%",
            tags=[detection.disease_id, farm_config['region_code']],
            # GPS 좌표 없음, 시군구 수준만
        )
        self.broadcast_to_nearby(signal, farm_config['region_code'], radius_km=30)
```

### 3.5 analyzer.py — 관련성 판단

```python
"""
수집된 시그널이 이 농장에 관련 있는지 판단

판단 기준:
  1. 작물 관련성: "딸기" 포함 → 높음 / "사과" → 낮음 / "과일" → 중간
  2. 지역 근접성: 같은 도 → 높음 / 인접 도 → 중간 / 해외 → 맥락에 따라
  3. 시기 관련성: 현재 생육 단계와 매칭되는지
  4. 환경 유사성: 현재 센서 데이터와 시그널 조건이 비슷한지
  5. 긴급도: 발생 속보 > 예방 정보 > 일반 노하우

출력:
  RelevanceScore:
    score: float (0~1)
    urgency: "critical" | "warning" | "info" | "tip"
    reason: str  # "충남 지역 딸기 잿빛곰팡이 발생, 현재 습도 82%와 조건 유사"
"""

class SignalAnalyzer:
    def evaluate(self, signal: RawSignal, farm: FarmProfile) -> RelevanceScore:
        score = 0.0
        reasons = []
        
        # 작물 매칭
        if "딸기" in signal.tags or "strawberry" in signal.tags:
            score += 0.3
            reasons.append("딸기 관련")
        
        # 지역 근접성
        distance = self.calc_region_distance(signal, farm)
        if distance == "same_province":
            score += 0.3
            reasons.append(f"같은 도({farm.province})")
        elif distance == "adjacent":
            score += 0.15
        elif distance == "overseas_similar":
            score += 0.1
            reasons.append("해외지만 유사 조건")
        
        # 환경 유사성 (현재 센서 vs 시그널 발생 조건)
        if self.environment_matches(signal, farm.latest_sensor):
            score += 0.2
            reasons.append("현재 환경 조건 유사")
        
        # 생육 단계 매칭
        if signal.growth_stage_relevant(farm.current_stage):
            score += 0.1
        
        # 외국어 시그널은 번역 필요 플래그
        if signal.language != "ko":
            signal.needs_translation = True
        
        urgency = self.classify_urgency(signal, score)
        return RelevanceScore(score, urgency, " + ".join(reasons))
```

### 3.6 translator.py — 외국어 요약

```python
"""
외국어 시그널 → 한국어 농부 눈높이 요약

방식:
  1. 로컬 LLM 있으면 → 로컬 번역+요약
  2. 없으면 → 룰 기반 핵심 키워드 추출 + 템플릿 요약

출력 형식:
  "일본 시즈오카현에서 딸기 탄저병 새 변종이 발견됐어요.
   기존 약제가 안 들을 수 있어서, 묘를 들일 때 주의가 필요해요."

※ 전문 용어 최소화, 해요체
"""

class SignalTranslator:
    def translate_and_summarize(self, signal: RawSignal) -> str:
        if self.llm_available:
            prompt = f"""
            다음 농업 뉴스를 한국 딸기 농부가 이해할 수 있게 
            3줄로 요약해줘. 전문 용어 쓰지 마. 해요체로.
            왜 중요한지, 지금 뭘 해야 하는지 포함해줘.
            
            원문: {signal.title}\n{signal.summary}
            """
            return self.llm.generate(prompt)
        else:
            return self.template_summary(signal)
```

---

## 4. engine/satellite/ — 위성 데이터 분석

### 4.1 copernicus.py

```python
"""
Copernicus Open Access Hub API 클라이언트
Sentinel-2 Level-2A (대기 보정 완료) 데이터 자동 다운로드

API: https://dataspace.copernicus.eu/
인증: 무료 계정 (22B Labs가 발급, 농부 발급 불필요)

다운로드 밴드:
  - B04 (Red, 10m) → NDVI
  - B08 (NIR, 10m) → NDVI, NDWI
  - B03 (Green, 10m) → GNDVI
  - B11 (SWIR, 20m) → NDWI
  - SCL (Scene Classification, 20m) → 구름 마스킹
"""

class CopernicusClient:
    BASE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1"
    
    async def get_latest_image(self, lat, lng, max_cloud_pct=40):
        """
        주어진 좌표의 최신 구름 없는 Sentinel-2 이미지 조회
        Returns: 타일 ID + 다운로드 URL
        """
        pass
    
    async def download_bands(self, tile_id, bands=["B04","B08","B03","B11","SCL"]):
        """
        필요한 밴드만 다운로드 (전체 타일 X, 필지 영역만)
        → 용량 절감: 전체 타일 ~800MB → 필지 크롭 ~1MB
        """
        pass
```

### 4.2 field_manager.py

```python
"""
농장 주소 → GPS → 필지 경계 관리

초기 설정 시:
  "서산시 부석면 XXX리" 
  → 카카오맵 API로 GPS 변환: (36.xxx, 126.xxx)
  → 200평(660㎡) 기준 사각형 추정: ~25m × 26m
  → Sentinel-2 10m 해상도이므로 약 2.5 × 2.6 픽셀
     (작지만 NDVI 변화 추적은 가능)

※ 한국 농림위성(5m) 서비스 시작 시 → 5 × 5 픽셀로 정밀도 향상
"""

class FieldManager:
    def address_to_gps(self, address: str) -> tuple:
        """카카오맵 API 또는 국가주소API로 좌표 변환"""
        pass
    
    def create_field_boundary(self, center_gps, area_pyeong=200) -> dict:
        """200평 기준 사각형 경계 생성"""
        side_m = (area_pyeong * 3.3058) ** 0.5  # ~25.7m
        # GeoJSON Polygon 반환
        pass
    
    def crop_raster_to_field(self, raster_path, boundary) -> np.ndarray:
        """위성 이미지에서 필지 영역만 추출"""
        pass
```

### 4.3 indices.py

```python
"""
식생 지수 계산 — 밴드 연산

모든 지수는 -1 ~ +1 범위
농부에게는 숫자가 아닌 등급으로 전달:
  0.7+ → "좋음 🟢"
  0.5~0.7 → "보통 🟡"  
  0.3~0.5 → "주의 🟠"
  <0.3 → "위험 🔴"
"""

import numpy as np

def calc_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """식생 건강도: 높을수록 광합성 활발"""
    return (nir - red) / (nir + red + 1e-10)

def calc_ndwi(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
    """수분 스트레스: 낮으면 수분 부족"""
    return (nir - swir) / (nir + swir + 1e-10)

def calc_gndvi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """엽록소 함량: 영양 상태 반영"""
    return (nir - green) / (nir + green + 1e-10)

def index_to_grade(value: float, crop="strawberry") -> dict:
    """숫자 → 농부용 등급"""
    if value >= 0.7:
        return {"grade": "좋음", "emoji": "🟢", "action": None}
    elif value >= 0.5:
        return {"grade": "보통", "emoji": "🟡", "action": None}
    elif value >= 0.3:
        return {"grade": "주의", "emoji": "🟠", "action": "확인 필요"}
    else:
        return {"grade": "위험", "emoji": "🔴", "action": "즉시 점검"}
```

### 4.4 change_detector.py

```python
"""
시계열 변화 감지

비교 대상:
  1. vs 지난 촬영 (5일 전) → 급격한 변화 감지
  2. vs 작년 동기 → 연간 비교
  3. vs 주변 평균 → 상대적 위치 파악

알림 기준:
  - NDVI 5일 변화량 > -0.1 → "활력 급감, 점검 필요"
  - 작년 대비 > -0.15 → "작년보다 상태 안 좋음"
  - 주변 대비 > -0.1 → "주변보다 상태 안 좋음"
"""

class ChangeDetector:
    def compare_temporal(self, current, previous):
        """이전 촬영 대비 변화"""
        delta = current.ndvi_mean - previous.ndvi_mean
        return {"delta": delta, "direction": "up" if delta > 0 else "down"}
    
    def compare_yearly(self, current, year_ago):
        """작년 동기 대비"""
        pass
    
    def compare_regional(self, field_ndvi, region_avg_ndvi):
        """주변 농경지 평균 대비"""
        pass
    
    def detect_anomaly(self, current, history_list):
        """이상치 감지: 정상 범위 벗어나면 플래그"""
        pass
```

### 4.5 interpreter.py

```python
"""
위성 지수 → 한국어 해석

원칙:
  - "NDVI"라는 단어 절대 안 씀
  - "0.58"이라는 숫자 절대 안 씀
  - "2동 딸기가 지난주보다 기운이 없어 보여요" 식으로

해석 로직:
  1. 지수 등급 변환 (indices.py)
  2. 변화 방향 확인 (change_detector.py)
  3. 가능한 원인 추정 (센서 데이터 교차)
  4. 조치 추천
  5. 한국어 메시지 조립
"""

class SatelliteInterpreter:
    def interpret(self, sat_data, sensor_data, farm_config) -> str:
        """
        Returns: 농부가 읽을 수 있는 한국어 해석
        
        ※ 비닐하우스는 위성이 내부를 못 봄 → "참고 수준"으로만 전달
        ※ "2동 가운데가 약하다" 같은 세부 위치 표현 금지 (해상도 부족)
        ※ 반드시 "위성은 바깥에서 본 참고 정보예요" 포함
        
        예:
        "위성으로 봤을 때 2동 주변이 최근 좀 약해진 것 같아요.
         비닐하우스 안은 직접 못 봐서 정확하지 않을 수 있어요.
         센서를 확인해보니 토양이 좀 건조하네요 (45%).
         관수를 한 번 해주시면 좋겠어요."
        """
        pass
```

---

## 5. engine/fusion/ — 3중 통합 판단 (핵심)

### 5.1 intelligence.py — 메인 두뇌

```python
"""
BerryDoctor 3중 지능의 핵심

역할: 위성 + 센서 + 시그널 데이터를 받아서
      하나의 맥락화된 판단을 내리고
      하나의 카카오톡 메시지로 전달

작동 방식:
  1. 이벤트 수신 (3개 소스 중 하나에서 트리거)
  2. 다른 2개 소스의 최신 데이터 조회
  3. context_builder로 맥락 조합
  4. risk_scorer로 복합 위험도 산출
  5. message_composer로 통합 메시지 생성
  6. 카카오톡 발송

트리거 시점:
  - 센서 이상 감지 시 → 위성+시그널 맥락 추가
  - 새 위성 이미지 도착 시 → 센서+시그널 맥락 추가
  - 관련 시그널 수신 시 → 위성+센서 맥락 추가
  - 매일 21:00 일일 리포트 → 3개 전부 합산
"""

class FusionIntelligence:
    def __init__(self, sensor_db, satellite_db, signal_db, kakao):
        self.sensor = sensor_db
        self.satellite = satellite_db
        self.signal = signal_db
        self.kakao = kakao
        self.context = ContextBuilder()
        self.scorer = RiskScorer()
        self.composer = MessageComposer()
    
    def on_sensor_alert(self, alert):
        """센서 이상 → 위성+시그널로 보강"""
        sat = self.satellite.get_latest(alert.house_id)
        signals = self.signal.get_recent_relevant(hours=48)
        
        context = self.context.build(
            trigger="sensor",
            sensor_data=alert,
            satellite_data=sat,
            signals=signals
        )
        risk = self.scorer.calculate(context)
        message = self.composer.compose(context, risk)
        self.kakao.send(message)
    
    def on_satellite_update(self, sat_data):
        """새 위성 이미지 → 센서+시그널로 보강"""
        sensors = self.sensor.get_latest_all_houses()
        signals = self.signal.get_recent_relevant(hours=72)
        
        context = self.context.build(
            trigger="satellite",
            sensor_data=sensors,
            satellite_data=sat_data,
            signals=signals
        )
        risk = self.scorer.calculate(context)
        message = self.composer.compose(context, risk)
        self.kakao.send(message)
    
    def on_new_signal(self, signal):
        """새 시그널 → 위성+센서로 보강"""
        if signal.relevance.urgency in ("critical", "warning"):
            sensors = self.sensor.get_latest_all_houses()
            sat = self.satellite.get_latest_all()
            
            context = self.context.build(
                trigger="signal",
                sensor_data=sensors,
                satellite_data=sat,
                signals=[signal]
            )
            risk = self.scorer.calculate(context)
            message = self.composer.compose(context, risk)
            self.kakao.send(message)
    
    def daily_report(self):
        """매일 21:00 — 3개 소스 전부 합산 리포트"""
        sensors = self.sensor.get_today_summary()
        sat = self.satellite.get_latest_all()
        signals = self.signal.get_today_relevant()
        
        context = self.context.build(
            trigger="daily",
            sensor_data=sensors,
            satellite_data=sat,
            signals=signals
        )
        risk = self.scorer.calculate(context)
        message = self.composer.compose_daily(context, risk)
        self.kakao.send(message)
```

### 5.2 context_builder.py

```python
"""
3개 소스를 하나의 맥락(Context)으로 조합

예시 Context 출력:
{
    "trigger": "sensor",
    "trigger_detail": "2동 습도 88% 감지",
    "sensor": {
        "house_2": {"humidity": 88, "temp": 22, "soil_moisture": 65}
    },
    "satellite": {
        "house_2": {"ndvi_grade": "보통", "ndvi_trend": "하락중", "days_since": 3}
    },
    "signals": [
        {"title": "논산 잿빛곰팡이 발생", "urgency": "warning", "distance": "60km"}
    ],
    "farm": {
        "region": "서산 부석면",
        "variety": "설향",
        "growth_stage": "과실비대기",
        "regional_note": "해풍 지역이라 습도 기준 80%"
    },
    "cross_validation": {
        "sensor_says": "고습 → 곰팡이 위험",
        "satellite_says": "최근 활력 하락 추세",
        "signal_says": "인근 지역 실제 발생",
        "agreement": "3개 소스 모두 곰팡이 위험 시사"
    }
}
"""
```

### 5.3 risk_scorer.py

```python
"""
복합 위험도 점수 (0~100)

개별 소스 점수:
  sensor_risk: 0~100 (기존 disease_risk.py 결과)
  satellite_risk: 0~100 (NDVI 하락 + 변화 속도)
  signal_risk: 0~100 (인근 발생 + 조건 유사도)

복합 점수 산출:
  - 3개 소스가 동의(agreement) → 가중치 증가
  - 2개 동의 → 중간
  - 1개만 → 해당 소스 점수만 반영

  if all_agree: composite = max(individual) * 1.3
  if two_agree: composite = avg(agreeing_two) * 1.1  
  if one_only: composite = that_one * 0.8

레벨 분류:
  80+ → critical (즉시 알림 + 자동 조치)
  60~80 → warning (알림 + 조치 추천)
  40~60 → caution (다음 리포트에 포함)
  <40 → info (일일 리포트에만)
"""

class RiskScorer:
    def calculate(self, context) -> RiskResult:
        sensor_risk = self.eval_sensor(context.sensor)
        satellite_risk = self.eval_satellite(context.satellite)
        signal_risk = self.eval_signal(context.signals)
        
        agreement = self.check_agreement(sensor_risk, satellite_risk, signal_risk)
        composite = self.composite_score(sensor_risk, satellite_risk, signal_risk, agreement)
        
        return RiskResult(
            composite=composite,
            level=self.classify_level(composite),
            breakdown={"sensor": sensor_risk, "satellite": satellite_risk, "signal": signal_risk},
            agreement=agreement
        )
```

### 5.4 message_composer.py — 통합 메시지 생성

```python
"""
3중 맥락을 하나의 카카오톡 메시지로 조합

핵심 원칙:
  1. 어려운 말 없음 (NDVI, 시그널, 퓨전 같은 단어 절대 안 씀)
  2. "왜?" → "뭘 해야 하지?" → "고수는?" 순서
  3. 3개 소스를 자연스럽게 하나의 이야기로 연결
  4. 길어도 카톡 1개 메시지 안에 (500자 이내)
"""

class MessageComposer:
    def compose(self, context, risk) -> str:
        """
        이벤트 트리거 시 — 핵심만 짧게
        
        예시 출력:
        ━━━━━━━━━━━━━━
        ⚠️ 2동 주의가 필요해요
        
        지금 습도가 88%로 높아요.
        위성으로 봤을 때도 2동이 최근
        며칠간 기운이 떨어지고 있었어요.
        
        마침 논산 쪽에서 비슷한 조건에서
        잿빛곰팡이가 났다는 소식이 있어요.
        
        지금 환기를 시켜주시면 좋겠어요.
        "환풍기 켜"라고 답해주세요.
        
        💡 고수 팁: 시든 꽃잎을 매일 
        제거하면 전염을 크게 줄일 수 있어요.
        ━━━━━━━━━━━━━━
        """
        pass
    
    def compose_daily(self, context, risk) -> str:
        """
        매일 21:00 — 하루 종합
        
        예시 출력:
        ━━━━━━━━━━━━━━
        📋 4/7 하루 정리
        
        🌱 하우스 상태
          1동 좋음 🟢 / 2동 주의 🟡 / 3동 좋음 🟢
        
        🛰 하늘에서 본 상태 (4/5 촬영)
          전체적으로 양호, 2동만 살짝 약해짐
        
        📡 오늘의 농업 소식
          • 충남 서부 잿빛곰팡이 주의보 발령
          • 네덜란드 연구: 이랑 간격 넓히면 
            곰팡이 18% 감소
        
        📅 내일 할 일
          1. 2동 관수 + 환기
          2. 꽃잎 정리 (곰팡이 예방)
          3. 보온커튼 22시 닫기 (내일 최저 2°C)
        
        💰 설향 시세: 8,200원/kg (+300)
        ━━━━━━━━━━━━━━
        """
        pass
```

---

## 6. 기존 코드 연결점 (수정 최소화)

기존 berry-engine에서 수정할 부분은 **4곳**뿐:

### 6.1 main.py — 초기화에 3개 모듈 추가

```python
# 기존 초기화 코드 하단에 추가:
from engine.signal.collector import SignalCollector
from engine.satellite.copernicus import CopernicusClient
from engine.fusion.intelligence import FusionIntelligence

signal_collector = SignalCollector(config, db)
satellite_client = CopernicusClient(config)
fusion = FusionIntelligence(sensor_db, satellite_db, signal_db, kakao)
```

### 6.2 scheduler/jobs.py — 스케줄 등록

```python
# 기존 스케줄러에 추가:
scheduler.add_job(signal_collector.collect_domestic, 'interval', hours=6)
scheduler.add_job(signal_collector.collect_global, 'cron', hour=6)
scheduler.add_job(satellite_client.check_new_image, 'cron', hour=6, minute=30)
scheduler.add_job(fusion.daily_report, 'cron', hour=21)  # 기존 daily_report 대체
```

### 6.3 rules/engine.py — 센서 알림 시 fusion 호출

```python
# 기존 룰 엔진의 alert 발생 부분에 1줄 추가:
def trigger_alert(self, alert):
    self.kakao.send(alert.message)      # 기존 (즉시 알림은 유지)
    self.fusion.on_sensor_alert(alert)   # 🆕 fusion에도 전달
```

### 6.4 ai/disease_detector.py — 병해 감지 시 커뮤니티 공유

```python
# 기존 YOLO 감지 결과 처리 부분에 추가:
def on_detection(self, result):
    # 기존 처리 ...
    if result.confidence > 0.7:
        self.community_source.on_local_detection(result, self.config)  # 🆕
```

---

## 7. 추가 SQLite 테이블

```sql
-- schema.sql에 추가:

-- 시그널 로그
CREATE TABLE signal_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT,            -- "rda_pest", "fao_giews", "community" 등
    title TEXT,
    summary TEXT,
    url TEXT,
    language TEXT,
    relevance_score REAL,
    urgency TEXT,           -- "critical", "warning", "info", "tip"
    delivered BOOLEAN DEFAULT 0,
    hash TEXT UNIQUE
);

-- 위성 데이터 로그
CREATE TABLE satellite_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    house_id INTEGER,
    capture_date DATE,
    satellite TEXT,          -- "sentinel2", "agri_satellite_kr"
    cloud_pct REAL,
    ndvi_mean REAL,
    ndvi_min REAL,
    ndvi_max REAL,
    ndwi_mean REAL,
    gndvi_mean REAL,
    change_vs_prev REAL,     -- 이전 촬영 대비 변화
    change_vs_year REAL,     -- 작년 동기 대비
    change_vs_region REAL,   -- 지역 평균 대비
    raw_data_path TEXT       -- 원본 밴드 파일 경로 (선택)
);

-- 퓨전 판단 로그 (디버깅 및 학습용)
CREATE TABLE fusion_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    trigger_source TEXT,     -- "sensor", "satellite", "signal", "daily"
    trigger_detail TEXT,
    sensor_risk REAL,
    satellite_risk REAL,
    signal_risk REAL,
    composite_risk REAL,
    agreement TEXT,          -- "all_agree", "two_agree", "one_only"
    message_sent TEXT,
    farmer_response TEXT     -- 농부가 조치했는지 추적 (선택)
);
```

---

## 8. 추가 의존성

```
# requirements.txt에 추가:
sentinelsat>=1.2       # Copernicus API
rasterio>=1.3          # 위성 영상 처리
numpy>=1.24            # 밴드 연산
shapely>=2.0           # 필지 geometry
pyproj>=3.6            # 좌표 변환
feedparser>=6.0        # RSS 수집
beautifulsoup4>=4.12   # HTML 크롤링
```

---

## 9. data/ 추가 파일

### signal_sources.json

```json
{
  "domestic": [
    {
      "id": "rda_pest",
      "name": "농진청 병해충 예찰",
      "type": "html_scrape",
      "url": "https://ncpms.rda.go.kr",
      "interval_hours": 6,
      "keywords": ["딸기", "잿빛곰팡이", "흰가루병", "탄저병"]
    },
    {
      "id": "nongsaro",
      "name": "농사로 긴급공지",
      "type": "rss",
      "url": "https://www.nongsaro.go.kr/rss",
      "interval_hours": 6
    },
    {
      "id": "kma_special",
      "name": "기상청 특보",
      "type": "api",
      "url": "https://apihub.kma.go.kr",
      "interval_hours": 1
    },
    {
      "id": "market",
      "name": "도매시장 가격 급변",
      "type": "api",
      "url": "https://at.agromarket.kr",
      "interval_hours": 1,
      "threshold_change_pct": 10
    }
  ],
  "global": [
    {
      "id": "fao_giews",
      "name": "FAO GIEWS",
      "type": "rss",
      "url": "https://www.fao.org/giews/rss",
      "interval_hours": 24,
      "language": "en"
    },
    {
      "id": "japan_naro",
      "name": "일본 농연기구",
      "type": "rss",
      "url": "https://www.naro.go.jp/rss",
      "interval_hours": 24,
      "language": "ja"
    },
    {
      "id": "arxiv_agri",
      "name": "농학 논문",
      "type": "api",
      "url": "https://export.arxiv.org/api/query",
      "interval_hours": 24,
      "language": "en",
      "query": "strawberry disease OR strawberry cultivation"
    }
  ],
  "community": [
    {
      "id": "x_agri",
      "name": "X 농업 키워드",
      "type": "x_search",
      "keywords": ["딸기 병해", "딸기 곰팡이", "strawberry disease"],
      "interval_hours": 12
    }
  ]
}
```

### satellite_config.json

```json
{
  "sentinel2": {
    "api_url": "https://catalogue.dataspace.copernicus.eu/odata/v1",
    "max_cloud_pct": 40,
    "bands": ["B04", "B08", "B03", "B11", "SCL"],
    "resolution_m": 10,
    "revisit_days": 5
  },
  "agri_satellite_kr": {
    "api_url": "TBD (2026년 서비스 시작 시 업데이트)",
    "resolution_m": 5,
    "revisit_days": 3,
    "bands": ["B1_Blue", "B2_Green", "B3_Red", "B4_RedEdge", "B5_NIR"],
    "status": "pending_launch"
  },
  "field_defaults": {
    "buffer_m": 5,
    "min_clear_pixels": 4,
    "history_months": 12,
    "regional_comparison_radius_km": 10
  }
}
```

---

## 10. Codex 구현 순서

```
Phase A: 시그널 (초기 3개 소스만)
  1. DB 스키마 추가 (signal_log)
  2. engine/signal/sources/rda_pest.py — 농진청 병해충
  3. engine/signal/sources/kma_special.py — 기상청 특보
  4. engine/signal/sources/market_alert.py — 도매시장 가격
  5. engine/signal/analyzer.py — 관련성 판단
  6. engine/signal/collector.py — 수집 통합 (하루 최대 2건 제한)
  7. scheduler/signal_job.py 등록

Phase B: 위성 (참고 수준, 과대 약속 금지)
  8. DB 스키마 추가 (satellite_log)
  9. engine/satellite/copernicus.py — Sentinel-2 API (필지 크롭만)
  10. engine/satellite/field_manager.py — 주소→GPS→영역
  11. engine/satellite/indices.py — NDVI/NDWI 계산
  12. engine/satellite/change_detector.py — 시계열 변화
  13. engine/satellite/interpreter.py — 한국어 해석 (한계 고지 포함)
  14. engine/satellite/timeline.py — 농장 타임라인 기록
  15. scheduler/satellite_job.py 등록

Phase C: 보안
  16. DB 스키마 추가 (security_log)
  17. firmware/src/security.h/.cpp — PIR+IR LED+부저
  18. engine/security/monitor.py — MQTT 수신→카카오톡
  19. 기존 firmware main.cpp에 야간 모드 전환 추가

Phase D: 퓨전 (3개 연결)
  20. engine/fusion/context_builder.py — 맥락 조합
  21. engine/fusion/risk_scorer.py — 복합 위험도 (제약 반영)
  22. engine/fusion/message_composer.py — 통합 메시지 (제약 반영)
  23. engine/fusion/intelligence.py — 메인 두뇌
  24. 기존 코드 연결 4곳 (main, scheduler, rules, detector)
  25. 메시지 병합 로직 (같은 시간대 이벤트 합치기)

Phase E: 검증
  26. 테스트 (test_signal, test_satellite, test_security, test_fusion)
  27. 제약 사항 체크리스트 전수 확인
  28. PyInstaller 재빌드
```

---

## 11. 제약 사항 (Constraints) — Codex 필독

### 11.1 위성 한계 — 과대 약속 금지

| 제약 | 내용 | 코드 반영 |
|------|------|----------|
| 해상도 한계 | 200평 하우스 = Sentinel-2에서 약 2.5×2.6 픽셀. 동 내부 세부 위치 판별 불가 | interpreter.py에서 "가운데가 약하다" 같은 표현 금지. "전체적으로" 만 사용 |
| 비닐하우스 관통 불가 | 광학 위성은 비닐 지붕 위만 봄. 딸기 직접 관측 아님 | 모든 위성 메시지에 "위성은 바깥에서 본 참고 정보예요" 문구 포함 |
| 구름 문제 | 한국 겨울 흐린 날 많음 → 2~3주간 쓸 이미지 없을 수 있음 | 이미지 없으면 "구름 때문에 촬영이 안 됐어요" 솔직히 알림. 센서만으로 리포트 |
| 촬영 주기 | 5일(Sentinel-2) / 3일(농림위성). 실시간 아님 | "실시간 감시"라는 표현 절대 사용 금지 |
| 야간 촬영 불가 | 광학 위성은 주간만. 새벽 도난 감지 불가 | 보안은 ESP32-CAM+PIR로 해결 (아래 12장 참조) |

**위성의 역할 정의: "전체 추세 참고" + "농장 타임라인 기록"**
**판단의 주체: 센서(정확) > 위성(참고) > 시그널(맥락)**

### 11.2 시그널 한계 — 알림 피로 방지

| 규칙 | 내용 |
|------|------|
| 초기 소스 제한 | 농진청 병해충 예찰, 기상청 특보, 도매시장 가격 3개만. 검증 후 확장 |
| 하루 최대 알림 | 즉시 발송은 critical 등급만 (하루 최대 2건). 나머지는 21:00 일일 리포트에 합산 |
| 커뮤니티 비활성 | 지역당 사용자 5명 이상 될 때까지 community.py 비활성. 그 전엔 농진청 예찰이 대체 |
| 외국어 소스 후순위 | FAO, 일본 NARO 등은 Phase 2 이후 활성. 초기에는 국내 소스만 |
| 메시지 병합 | 같은 시간대(1시간 이내) 여러 이벤트는 하나로 합침 |

### 11.3 퓨전 한계 — 과대 해석 금지

| 규칙 | 내용 |
|------|------|
| "확인해보세요" 필수 | 모든 위험 알림 끝에 "직접 확인해보시는 게 좋겠어요" 포함. "자동 조치했습니다" 금지 |
| 자동 조치는 센서만 | 릴레이 자동 제어(환풍, 보온)는 센서 룰 엔진만. 위성·시그널로 릴레이 자동 작동 절대 금지 |
| 확신도 표시 | "3개 소스가 같은 얘기를 해요" vs "위성은 잘 모르겠고 센서만 감지했어요" 솔직히 구분 |
| 인터넷 없어도 핵심 동작 | 위성·시그널은 보너스. ESP32 로컬 룰 5개가 생명선. 인터넷 끊겨도 보온·환기·침수 대응 |

### 11.4 PC 부하 관리

| 규칙 | 내용 |
|------|------|
| 위성 다운로드 | 전체 타일(~800MB) 금지. 필지 영역만 크롭 다운로드 (~1MB) |
| 최소 사양 | RAM 4GB, 저장공간 2GB, Windows 10+ |
| 백그라운드 처리 | 위성·시그널 처리는 저우선 스레드. 센서 실시간 처리 우선 |

---

## 12. engine/security/ — 야간 보안 모듈

### 12.1 개요

기존 ESP32-CAM(병해 촬영용)에 PIR 모션센서를 추가하여 야간 보안 겸용.
새벽 농작물 도난 대응. **1동당 추가 4,000원.**

### 12.2 추가 부품 (1동당)

| 부품 | 모델 | 단가 | 용도 |
|------|------|------|------|
| PIR 모션센서 | HC-SR501 | 1,500원 | 사람/동물 움직임 감지 |
| IR LED | 850nm 3W 적외선 | 2,000원 | 야간 촬영 보조광 |
| 부저 (선택) | 능동 부저 5V | 500원 | 현장 경고음 |

### 12.3 ESP32 펌웨어 추가 (firmware/src/security.h)

```cpp
// GPIO 추가
#define PIN_PIR_SENSOR    2     // PIR 모션 감지 (입력)
#define PIN_IR_LED        16    // 적외선 LED (출력)
#define PIN_BUZZER        17    // 부저 (출력, 선택)

// 모드 전환: BH1750 조도센서 활용 (이미 설치됨)
// 조도 < 10 lux → 야간 모드 자동 진입
// 조도 > 50 lux → 주간 모드 복귀

enum SecurityMode { DAY_MODE, NIGHT_MODE };

void nightSecurityLoop() {
    if (digitalRead(PIN_PIR_SENSOR) == HIGH) {
        // 1. IR LED 켜기
        digitalWrite(PIN_IR_LED, HIGH);
        delay(200);
        
        // 2. 사진 5장 연속 촬영 (1초 간격)
        for (int i = 0; i < 5; i++) {
            captureAndSave(i);  // SD카드 저장
            delay(1000);
        }
        
        // 3. MQTT로 알림 발송 (PC 켜져있으면 카카오톡)
        mqtt.publish("security/motion", createAlertJSON());
        
        // 4. PC 꺼져있어도 → 부저 경고음 (선택)
        if (BUZZER_ENABLED) {
            tone(PIN_BUZZER, 2000, 3000); // 3초 경고음
        }
        
        // 5. IR LED 끄기
        digitalWrite(PIN_IR_LED, LOW);
        
        // 6. 쿨다운 30초 (연속 트리거 방지)
        delay(30000);
    }
}
```

### 12.4 berry-engine 추가 (engine/security/monitor.py)

```python
"""
야간 보안 모니터

MQTT 수신: security/motion → 카카오톡 즉시 알림 + 사진 전송
사진 저장: SQLite security_log + 파일시스템

※ 야생동물과 사람 구분은 하지 않음 (단순 움직임 감지)
※ 메시지에 "야생동물일 수도 있지만 확인해보세요" 포함
"""

class SecurityMonitor:
    def on_motion_detected(self, payload):
        photos = payload.get("photos", [])
        timestamp = payload.get("timestamp")
        house_id = payload.get("house_id")
        
        self.db.save_security_event(house_id, timestamp, photos)
        
        message = (
            f"🚨 {house_id}동에서 움직임 감지\n"
            f"시간: {timestamp}\n"
            f"📸 사진 {len(photos)}장 촬영됨\n\n"
            f"야생동물일 수도 있지만\n"
            f"확인해보시는 게 좋겠어요.\n\n"
            f"기록은 자동 저장됐어요."
        )
        self.kakao.send_with_photos(message, photos)
```

### 12.5 SQLite 추가 테이블

```sql
CREATE TABLE security_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    house_id INTEGER,
    photo_paths TEXT,    -- JSON 배열 ["path1.jpg", ...]
    acknowledged BOOLEAN DEFAULT 0,
    note TEXT             -- 농부 메모 ("고양이였음" 등)
);
```

---

## 13. 위성 농장 타임라인 기록

### 13.1 목적

도둑 잡기가 아니라 **농장 변화의 객관적 기록**.
GAP 인증, 보험 청구, 연도별 비교에 활용.

### 13.2 기록 구조

```python
# satellite/timeline.py

class FarmTimeline:
    """
    위성 촬영 시마다 자동 기록
    → 월별/연도별 농장 상태 변화 타임라인 생성
    
    저장: satellite_log 테이블 (이미 정의됨)
    
    활용:
    1. 카카오톡 "기록" 명령 → 이번 시즌 타임라인 이미지 전송
    2. 연말 리포트 → "올해 우리 농장은 이랬어요" 요약
    3. GAP 인증 → "위성 기반 재배 이력 증빙" PDF 생성
    """
    
    def generate_season_summary(self, house_id, season) -> dict:
        """
        시즌 요약 — 카카오톡 "기록" 명령 시 반환
        
        출력 예:
        📅 2025~2026 시즌 기록
        9월  ██░░░░░░░░ 정식
        10월 ████░░░░░░ 생장 시작
        11월 ██████░░░░ 순조로움
        12월 ████████░░ 최고 (수확 시작)
        1월  ███████░░░ 수확 중
        2월  ██████░░░░ 후반
        3월  ████░░░░░░ 마무리
        
        최고 시점: 12월 둘째 주
        작년 대비: +8% 좋았어요
        """
        pass
```

### 13.3 카카오톡 명령 추가

| 명령 | 응답 |
|------|------|
| `기록` | 이번 시즌 위성 타임라인 + 요약 |
| `작년 비교` | 작년 동기간 vs 올해 비교 |
| `보안 기록` | 최근 7일 야간 움직임 감지 이력 |

---

## 14. 최종 디렉토리 추가분 요약

```
engine/
├── signal/          # 시그널 (11장 제약 반영)
│   └── sources/     # 초기 3개만: rda_pest, kma_special, market_alert
│
├── satellite/       # 위성 (11장 제약 반영)
│   ├── ...기존...
│   └── timeline.py  # 🆕 농장 타임라인 기록
│
├── fusion/          # 퓨전 (11장 제약 반영)
│   └── ...기존...
│
└── security/        # 🆕 야간 보안
    ├── __init__.py
    ├── monitor.py   # MQTT 수신 → 카카오톡 알림
    └── db.py        # security_log CRUD

firmware/src/
└── security.h/.cpp  # 🆕 PIR + IR LED + 부저
```

---

## 15. 성공 기준

### 시그널 (초기 3개 소스)
- [ ] 농진청 병해충 예찰 새 글 → 6시간 내 카카오톡 수신
- [ ] 기상청 특보 → 1시간 내 카카오톡 수신
- [ ] 도매시장 설향 가격 10% 이상 변동 → 즉시 알림
- [ ] 하루 즉시 알림 최대 2건 이하 (나머지는 일일 리포트)

### 위성
- [ ] Sentinel-2 새 이미지(구름 <40%) → 하우스별 건강 등급 수신
- [ ] 구름 때문에 이미지 없으면 → "구름 때문에 안 됐어요" 알림
- [ ] 모든 위성 메시지에 "바깥에서 본 참고 정보" 문구 포함
- [ ] 카카오톡 "기록" → 시즌 타임라인 수신
- [ ] 비닐하우스 내부 세부 판별 시도하지 않음

### 퓨전
- [ ] 센서 이상 시 → 시그널 맥락이 있으면 함께 전달
- [ ] 모든 위험 알림 끝에 "확인해보세요" 포함
- [ ] 위성·시그널로 릴레이 자동 작동 없음 (센서만)
- [ ] 일일 리포트(21:00): 3개 소스 합산 하루 정리

### 보안
- [ ] 야간 PIR 감지 → 5장 촬영 → 카카오톡 즉시 알림
- [ ] "야생동물일 수도 있어요" 문구 포함
- [ ] PC 꺼져있어도 ESP32 독립 촬영 + SD 저장 + 부저
- [ ] 카카오톡 "보안 기록" → 최근 7일 이력

### 전체
- [ ] 인터넷 끊겨도 센서+로컬룰+보안 정상 작동
- [ ] 전문 용어(NDVI, 시그널, 퓨전) 사용하지 않음
- [ ] 위성 처리 시 PC 메모리 추가 사용 100MB 이하

---

*기존 BerryDoctor Phase 0~5와 완전 호환*
*기존 코드 수정 4곳(각 1~2줄) + 신규 모듈 4개 추가*
*위성은 참고, 센서가 판단, 시그널은 맥락, 보안은 ESP32-CAM*
*Generated by Claude for 22B Labs Codex Handoff*
