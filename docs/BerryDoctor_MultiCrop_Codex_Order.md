# BerryDoctor Multi-Crop Refactoring — Codex Development Order

## Context

You are refactoring **BerryDoctor (딸기박사)** to support multiple crops (tomato, pepper, cucumber, grape, etc.) beyond the current strawberry-only implementation. The current codebase has ~257 strawberry-hardcoded references across 35+ files.

**Key constraint**: Backward compatibility. Existing strawberry users must see zero difference.

Three reference documents describe the existing architecture:
1. **BerryDoctor_Codex_Handoff_v2.0.md** — Master spec
2. **docs/ARCHITECTURE.md** — 21-section architecture doc
3. This order document — what to build now

Current state: `main` branch, latest commit `f4b7f74`. Tests: 29/29 passing.

---

## Architecture: Crop Profile System

One JSON file per crop under `data/crops/`. A new `engine/crop_profile.py` module loads the active profile. Every module that hardcodes strawberry values receives a `CropProfile` instance instead.

**Total: 3 new files, ~14 modified files, 0 database schema changes.**

---

## Step 1: Create `data/crops/strawberry.json`

Extract ALL hardcoded strawberry values into this single file:

```json
{
  "crop_type": "strawberry",
  "crop_name_ko": "딸기",
  "crop_name_en": "strawberry",
  "varieties": ["설향", "금실", "매향", "기타"],
  "default_variety": "설향",
  "model_file": "berry-disease-v1.onnx",
  "class_labels_file": "class_labels_ko.json",
  "baseline_price_per_kg": 8200,
  "market_item_name": "설향 특품",
  "signal_keywords": ["딸기", "strawberry", "설향"],
  "ndvi_thresholds": {
    "good": 0.7,
    "normal": 0.5,
    "caution": 0.3
  },
  "diseases": {
    "botrytis": {
      "center_temp": 22, "spread": 18,
      "weight_temp": 0.4, "weight_humidity": 0.35, "weight_other": 0.25,
      "humidity_factor": 5, "other_factor_key": "wet_hours", "other_multiplier": 12,
      "action_ko": "오전 환기와 시든 꽃잎 제거가 필요해요."
    },
    "powdery_mildew": {
      "center_temp": 20, "spread": 25,
      "weight_temp": 0.45, "weight_humidity": 0.35, "weight_other": 0.20,
      "humidity_center": 60, "humidity_spread": 300,
      "other_factor_key": "dry_hours", "other_base": 40, "other_multiplier": 5,
      "action_ko": "잎 표면을 자주 확인하고 초기 병반을 빨리 끊는 게 좋아요."
    },
    "anthracnose": {
      "center_temp": 28, "spread": 20,
      "weight_temp": 0.45, "weight_humidity": 0.35, "weight_other": 0.20,
      "humidity_threshold": 75, "humidity_factor": 4,
      "other_factor_key": "wet_hours", "other_multiplier": 10,
      "action_ko": "젖은 식물체 접촉을 줄이고 의심 주를 먼저 분리해 주세요."
    },
    "fusarium_wilt": {
      "center_temp": 27, "spread": 20,
      "weight_temp": 0.65, "weight_humidity": 0.35,
      "use_soil_temp": true,
      "humidity_threshold": 20, "humidity_factor": 4,
      "action_ko": "토양 과습과 연작 피해 징후를 같이 보셔야 해요."
    },
    "leaf_blight": {
      "center_temp": 26, "spread": 24,
      "weight_temp": 0.45, "weight_humidity": 0.35, "weight_other": 0.20,
      "humidity_threshold": 78, "humidity_factor": 4,
      "other_factor_key": "wet_hours", "other_multiplier": 10,
      "action_ko": "고온다습 조건을 짧게 끊어주는 게 중요해요."
    }
  },
  "disease_names_ko": {
    "botrytis": "잿빛곰팡이",
    "powdery_mildew": "흰가루병",
    "anthracnose": "탄저병",
    "fusarium_wilt": "시들음병",
    "leaf_blight": "잎마름병",
    "humidity": "고습 경보"
  },
  "disease_symptoms_ko": {
    "gray_mold": "꽃이나 과실에 회색 곰팡이성 병반이 보일 수 있어요.",
    "powdery_mildew_leaf": "잎 표면에 하얀 가루처럼 보이는 병반이 생길 수 있어요.",
    "powdery_mildew_fruit": "과실 표면에 흰가루처럼 덮이는 증상이 나타날 수 있어요.",
    "anthracnose": "검거나 움푹 꺼지는 병반이 생기고 번지는 속도가 빠를 수 있어요.",
    "angular_leaf_spot": "잎맥 사이로 각진 수침상 병반이 보일 수 있어요.",
    "blossom_blight": "꽃이 갈변하거나 마르며 떨어질 수 있어요.",
    "leaf_spot": "작은 반점이 퍼지며 잎이 마르는 양상이 나타날 수 있어요.",
    "healthy": "뚜렷한 병징은 상대적으로 적어 보여요."
  },
  "data_paths": {
    "knowledge_graph": "knowledge_graph.json",
    "calendar": "seolhyang_calendar.json",
    "farmer_tips": "farmer_tips.json",
    "pesticide_db": "pesticide_db.json"
  }
}
```

---

## Step 2: Create `engine/crop_profile.py`

```python
@dataclass(slots=True)
class CropProfile:
    crop_type: str
    crop_name_ko: str
    crop_name_en: str
    varieties: list[str]
    default_variety: str
    model_file: str
    class_labels_file: str
    baseline_price_per_kg: int
    market_item_name: str
    signal_keywords: list[str]
    ndvi_thresholds: dict[str, float]
    diseases: dict[str, dict[str, Any]]
    disease_names_ko: dict[str, str]
    disease_symptoms_ko: dict[str, str]
    data_paths: dict[str, str]

def load_crop_profile(crop_type: str = "strawberry") -> CropProfile:
    # Load from data/crops/{crop_type}.json
    # Fallback to data/crops/strawberry.json if not found
    # Return CropProfile instance

def resolve_data_path(profile: CropProfile, key: str) -> str:
    # Return full path: data_path(profile.data_paths.get(key, f"{key}.json"))
```

---

## Step 3: Add `crop_type` to Config

**`engine/config.py`**:
- Add `crop_type: str = "strawberry"` to `AppConfig` (after `variety` field)
- In `ConfigManager.load()`: `crop_type=str(data.get("crop_type", "strawberry"))`
- Add `"crop_type"` to `allowed_setting_keys()` return
- In `ensure_runtime_defaults()`: set default `"strawberry"` if missing

**`engine/setup_wizard.py`**:
- Add crop type combobox: `["딸기", "토마토", "고추", "오이", "포도", "기타"]`
- Map display name → crop_type: `{"딸기": "strawberry", "토마토": "tomato", ...}`
- Variety combobox updates based on crop selection (read from crop profile JSON)
- Add `crop_type: str = "strawberry"` to `SetupResult` dataclass
- In headless mode: default to `"strawberry"`

---

## Step 4: Parameterize `disease_risk.py`

**`engine/rules/disease_risk.py`**:

Change `calculate_disease_risk()` signature:
```python
def calculate_disease_risk(
    temp, humidity, wet_hours, soil_temp, profile,
    disease_params: dict[str, dict[str, Any]] | None = None,  # NEW
) -> dict[str, dict[str, Any]]:
```

When `disease_params is None`: use existing hardcoded values (backward compatibility).
When provided: iterate `disease_params.items()` and compute each disease's risk using the parameterized centers/spreads/weights from the dict.

The action strings also come from `disease_params[disease_key]["action_ko"]`.

---

## Step 5: Rename Coach + Wire CropProfile

**`engine/ai/coach.py`**:
- Rename `class StrawberryCoach` → `class CropCoach`
- Add at module level: `StrawberryCoach = CropCoach`  (backward compat alias)
- Add `crop_profile: Any = None` field
- `__post_init__`: if `crop_profile` is not None:
  - Pass crop_profile to `DiseaseDetector(crop_profile=self.crop_profile)`
  - Pass data paths to `KnowledgeGraph`
  - Pass crop_name to `LocalAgronomyAssistant`
  - Use `crop_profile.baseline_price_per_kg` for price forecast
- `_disease_name()`: read from `self.crop_profile.disease_names_ko` if available, else existing hardcoded dict
- `build_market_message()`: replace `"설향 시세"` with `self.crop_profile.market_item_name + " 시세"` if profile exists

---

## Step 6: Disease Detector + Knowledge Graph + LLM + Price

**`engine/ai/disease_detector.py`**:
- Add optional `crop_profile` param to `__init__`
- If provided: `self.model_path = Path(model_path(crop_profile.model_file))`
- If provided: load class_map from `crop_profile.class_labels_file`
- `_symptoms()`: read from `crop_profile.disease_symptoms_ko` if available

**`engine/ai/knowledge_graph.py`**:
- Add optional `knowledge_graph_path` and `calendar_path` params to `__init__`
- If provided, use those instead of hardcoded `data_path("knowledge_graph.json")`

**`engine/ai/llm.py`**:
- Add optional `crop_name_ko` param to `__init__` or accept it in constructor
- `_build_prompt()`: replace `"딸기 재배"` with `f"{self.crop_name_ko} 재배"`

**`engine/ai/price_forecast.py`**:
- Change `baseline_price: int = 8200` to accept constructor param
- When caller passes crop_profile.baseline_price_per_kg, use that

---

## Step 7: Signal/Satellite/Fusion

**`engine/signal/analyzer.py`**:
- Accept `signal_keywords` (set or list) in constructor or via crop_profile
- `evaluate()` line 70: replace `{"딸기", "strawberry"}` with `self.signal_keywords`
- Reason text: use crop_name_ko instead of hardcoded "딸기 관련"

**`engine/satellite/indices.py`**:
- `index_to_grade()`: add optional `thresholds: dict | None = None` param
- When provided: use `thresholds["good"]`, `thresholds["normal"]`, `thresholds["caution"]`
- When None: use existing 0.7/0.5/0.3

**`engine/fusion/message_composer.py`**:
- `compose_daily()` line 81: replace `"설향 시세"` with `context.get("extras", {}).get("crop_item", "설향") + " 시세"`

---

## Step 8: Wire in main.py + market.py

**`main.py`**:
- After `self.config = self.config_manager.load()` add:
  ```python
  from engine.crop_profile import load_crop_profile
  self.crop_profile = load_crop_profile(self.config.crop_type)
  ```
- Pass `crop_profile=self.crop_profile` to `CropCoach()` constructor
- In `reload_runtime_config()`: if crop_type changed, reload profile

**`engine/scheduler/market.py`**:
- Accept `market_item_name` and `baseline_price` via constructor or config
- Replace hardcoded `"설향 특품"` with the passed value

---

## Step 9: i18n

**`i18n/ko.json`**:
- Any template referencing "설향" → use `{crop_item}` placeholder
- Callers pass `crop_item=crop_profile.market_item_name`

---

## Step 10: Create `data/crops/tomato.json`

Minimal tomato profile as proof of multi-crop:

```json
{
  "crop_type": "tomato",
  "crop_name_ko": "토마토",
  "crop_name_en": "tomato",
  "varieties": ["완숙토마토", "방울토마토", "대추토마토", "기타"],
  "default_variety": "완숙토마토",
  "model_file": "tomato-disease-v1.onnx",
  "class_labels_file": "tomato_class_labels_ko.json",
  "baseline_price_per_kg": 3500,
  "market_item_name": "완숙토마토 특품",
  "signal_keywords": ["토마토", "tomato"],
  "ndvi_thresholds": { "good": 0.65, "normal": 0.45, "caution": 0.25 },
  "diseases": {
    "late_blight": {
      "center_temp": 18, "spread": 15,
      "weight_temp": 0.45, "weight_humidity": 0.35, "weight_other": 0.20,
      "humidity_threshold": 80, "humidity_factor": 5,
      "other_factor_key": "wet_hours", "other_multiplier": 15,
      "action_ko": "잎이 젖은 시간을 줄이고 감염 잎을 빨리 제거해 주세요."
    },
    "bacterial_wilt": {
      "center_temp": 30, "spread": 18,
      "weight_temp": 0.60, "weight_humidity": 0.40,
      "use_soil_temp": true,
      "humidity_threshold": 25, "humidity_factor": 3,
      "action_ko": "토양 과습을 피하고 저항성 대목 접목을 고려해 주세요."
    },
    "powdery_mildew": {
      "center_temp": 22, "spread": 20,
      "weight_temp": 0.45, "weight_humidity": 0.35, "weight_other": 0.20,
      "humidity_center": 55, "humidity_spread": 250,
      "other_factor_key": "dry_hours", "other_base": 35, "other_multiplier": 5,
      "action_ko": "환기로 습도를 낮추고 초기 병반을 제거해 주세요."
    },
    "gray_mold": {
      "center_temp": 20, "spread": 20,
      "weight_temp": 0.40, "weight_humidity": 0.35, "weight_other": 0.25,
      "humidity_factor": 5, "other_factor_key": "wet_hours", "other_multiplier": 12,
      "action_ko": "환기를 강화하고 시든 꽃과 과실을 제거해 주세요."
    }
  },
  "disease_names_ko": {
    "late_blight": "역병",
    "bacterial_wilt": "풋마름병",
    "powdery_mildew": "흰가루병",
    "gray_mold": "잿빛곰팡이병",
    "humidity": "고습 경보"
  },
  "disease_symptoms_ko": {
    "late_blight": "잎이 갈색으로 변하며 빠르게 번지는 양상이에요.",
    "bacterial_wilt": "한낮에 시들다가 저녁에 회복하는 패턴이 반복돼요.",
    "powdery_mildew": "잎 표면에 하얀 가루 같은 병반이 생겨요.",
    "gray_mold": "과실이나 줄기에 회색 곰팡이가 보여요.",
    "healthy": "뚜렷한 병징은 적어 보여요."
  },
  "data_paths": {
    "knowledge_graph": "crops/tomato_knowledge.json",
    "calendar": "crops/tomato_calendar.json",
    "farmer_tips": "crops/tomato_tips.json",
    "pesticide_db": "crops/tomato_pesticide.json"
  }
}
```

Also create minimal stub files:
- `data/crops/tomato_knowledge.json` — basic growth stages
- `data/crops/tomato_calendar.json` — month-to-stage mapping
- `data/crops/tomato_tips.json` — a few tips
- `data/crops/tomato_pesticide.json` — basic disease-pesticide mapping

---

## Step 11: Tests

1. Update existing test imports: `from engine.ai.coach import StrawberryCoach` still works (alias)
2. Add `tests/test_crop_profile.py`:
   - `test_load_strawberry_profile_has_all_fields`
   - `test_load_tomato_profile_has_different_diseases`
   - `test_unknown_crop_falls_back_to_strawberry`
   - `test_disease_risk_uses_profile_params_when_provided`
   - `test_signal_analyzer_uses_crop_keywords`
   - `test_ndvi_grade_uses_crop_thresholds`
3. Run all existing 29 tests — MUST still pass (backward compatibility)

---

## Backward Compatibility Checklist

| Scenario | Guarantee |
|----------|-----------|
| No `crop_type` in DB | `AppConfig` defaults to `"strawberry"` |
| `StrawberryCoach` import | Alias `StrawberryCoach = CropCoach` |
| `disease_risk()` direct call | `disease_params=None` → existing hardcoded behavior |
| Existing data files | Untouched; crop profile `data_paths` points to them |
| DB schema | No changes; `crop_type` stored in config KV table |
| All existing tests | Must pass without modification |
| KakaoTalk commands | Parser is crop-agnostic |

---

## Verification

```bash
# All existing tests pass
python -m unittest discover -s tests -v
# Expected: 29+ tests OK

# Smoke test (strawberry default)
python main.py
# Expected: health=200, status=200

# New multi-crop tests pass
python -m unittest tests.test_crop_profile -v
```

---

## Files to Create (3)

1. `data/crops/strawberry.json`
2. `engine/crop_profile.py`
3. `data/crops/tomato.json` (+ 4 tomato data stubs)

## Files to Modify (14)

1. `engine/config.py` — add crop_type field
2. `engine/setup_wizard.py` — add crop selection
3. `engine/rules/disease_risk.py` — parameterize
4. `engine/ai/coach.py` — rename + wire profile
5. `engine/ai/disease_detector.py` — profile-based model loading
6. `engine/ai/knowledge_graph.py` — injectable paths
7. `engine/ai/llm.py` — dynamic crop name in prompt
8. `engine/ai/price_forecast.py` — configurable baseline
9. `engine/signal/analyzer.py` — crop keywords from profile
10. `engine/satellite/indices.py` — crop thresholds
11. `engine/fusion/message_composer.py` — dynamic crop name
12. `main.py` — load and wire crop profile
13. `engine/scheduler/market.py` — configurable item name
14. `i18n/ko.json` — crop placeholder
15. `tests/test_crop_profile.py` — new test file

## Files NOT to Modify

- `engine/db/schema.sql` — no schema changes
- `engine/kakao/commands.py` — crop-agnostic
- `data/regional_profiles.json` — location-specific, not crop
- App branding "딸기박사" — keep as-is
