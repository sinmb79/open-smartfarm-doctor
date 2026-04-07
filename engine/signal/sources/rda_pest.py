from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from engine.signal.models import RawSignal
from engine.signal.sources import SignalSource


@dataclass(slots=True)
class RDAPestSource(SignalSource):
    config: Any = None
    repository: Any = None
    crop_profile: Any | None = None

    def __init__(self, config: Any, repository: Any, crop_profile: Any | None = None) -> None:
        SignalSource.__init__(self, source_id="rda_pest", name="농진청 병해충 예찰", language="ko", check_interval_hours=6)
        self.config = config
        self.repository = repository
        self.crop_profile = crop_profile

    def _crop_name(self) -> str:
        return str(getattr(self.crop_profile, "crop_name_ko", "작물"))

    async def fetch(self) -> list[RawSignal]:
        weather = self.repository.get_config("weather_cache", {})
        humidity = float(weather.get("current_humidity") or 0.0)
        if humidity < 80:
            return []
        now = datetime.now()
        farm_location = str(getattr(self.config, "farm_location", "") or "")
        province = farm_location.split()[0] if farm_location else "지역"
        crop_name = self._crop_name()
        return [
            RawSignal(
                source_id=self.source_id,
                source=self.name,
                title=f"{province} {crop_name} 병해충 주의",
                summary="습도가 높은 날이 이어져 곰팡이성 병해를 먼저 점검해 두는 편이 좋아요.",
                url=f"https://ncpms.rda.go.kr/mock/{now:%Y%m%d}",
                published_at=now,
                tags=[crop_name, "병해충", province],
                payload={"environment": {"humidity_min": 80, "temp_min": 12, "temp_max": 25}},
            )
        ]
