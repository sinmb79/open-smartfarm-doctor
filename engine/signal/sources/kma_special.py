from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from engine.signal.models import RawSignal
from engine.signal.sources import SignalSource


@dataclass(slots=True)
class KMASpecialSource(SignalSource):
    config: Any = None
    repository: Any = None
    crop_profile: Any | None = None

    def __init__(self, config: Any, repository: Any, crop_profile: Any | None = None) -> None:
        SignalSource.__init__(self, source_id="kma_special", name="기상청 특보", language="ko", check_interval_hours=1)
        self.config = config
        self.repository = repository
        self.crop_profile = crop_profile

    def _crop_name(self) -> str:
        return str(getattr(self.crop_profile, "crop_name_ko", "작물"))

    async def fetch(self) -> list[RawSignal]:
        weather = self.repository.get_config("weather_cache", {})
        rainfall = float(weather.get("max_hourly_rainfall") or 0.0)
        tomorrow_min = float(weather.get("tomorrow_min_temp") or 99.0)
        now = datetime.now()
        farm_location = str(getattr(self.config, "farm_location", "") or "")
        province = farm_location.split()[0] if farm_location else "지역"
        crop_name = self._crop_name()
        items: list[RawSignal] = []
        if rainfall >= 20:
            items.append(
                RawSignal(
                    source_id=self.source_id,
                    source=self.name,
                    title=f"{province} 강한 비 특보",
                    summary="배수로와 비가림 시설을 다시 점검해 두는 편이 좋아요.",
                    url=f"https://apihub.kma.go.kr/mock/rain/{now:%Y%m%d%H}",
                    published_at=now,
                    tags=[crop_name, province, "강우", "특보"],
                    payload={"environment": {"humidity_min": 75, "temp_min": 5, "temp_max": 30}},
                )
            )
        if tomorrow_min <= 0:
            items.append(
                RawSignal(
                    source_id=self.source_id,
                    source=self.name,
                    title=f"{province} 저온 특보",
                    summary="내일 아침 기온이 많이 떨어질 수 있어 보온 준비를 먼저 해 두는 편이 좋아요.",
                    url=f"https://apihub.kma.go.kr/mock/frost/{now:%Y%m%d%H}",
                    published_at=now,
                    tags=[crop_name, province, "저온", "특보"],
                    payload={"environment": {"humidity_min": 50, "temp_min": -10, "temp_max": 6}},
                )
            )
        return items
