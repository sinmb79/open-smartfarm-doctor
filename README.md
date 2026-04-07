# open-smartfarm-doctor

> 메타 설명: 다작물 스마트팜 운영을 위한 공개 프로그램 저장소입니다. 센서, 카카오톡, 자동화, 대시보드를 함께 담았습니다.
>
> 라벨: smartfarm, multicrop, greenhouse, agritech, mqtt, kakao, automation, ai

왜 이 저장소를 따로 만들었냐면, 좋은 현장 도구는 특정 작물 하나에만 갇히는 순간 확장성을 잃기 때문입니다.  
`open-smartfarm-doctor`는 기존 `berry-doctor`를 보존한 채, 다작물과 범용 스마트팜 운영으로 넓혀 가기 위한 별도 공개 프로그램 저장소입니다. 문서만 모아 둔 아카이브가 아니라, 실제로 실행하고 확장할 수 있는 코드베이스를 담고 있습니다.

30초만에 설명하면 이렇습니다.  
이 프로그램은 센서 데이터, 카카오톡 명령, 병해 진단, 자동 제어 제안, 위성 참고 정보, 외부 농업 시그널, 대시보드 운영 화면을 하나의 흐름으로 묶습니다. 농부는 카카오톡 한 채널만 보면 되고, 내부에서는 더 많은 판단이 조용히 작동합니다.

## 🌱 이 저장소의 정체성

- `berry-doctor`를 그대로 보존하면서 별도로 공개하는 프로그램 저장소입니다.
- 딸기에서 시작했지만, 토마토 같은 다른 작물로 확장할 수 있는 구조를 목표로 합니다.
- 인터넷 기반 기능이 있어도, 로컬 센서와 기본 자동화는 가능한 한 독립적으로 유지합니다.
- 과장된 “완전 자동”보다, 현장을 덜 속이는 판단 구조를 우선합니다.

## ✨ 핵심 기능

- 카카오톡으로 상태 확인, 사진 진단, 작업 기록, 제어 명령 처리
- MQTT 기반 센서 수집과 환경 제어 제안
- 병해 진단, 시세 추정, 일일·월간 리포트
- 외부 농업 시그널 수집과 3축 교차 검증
- 위성 참고 정보와 시즌 타임라인 기록
- 대시보드 기반 운영, 백업, 이력 조회
- 멀티크롭 프로필 구조
  현재 기본 작물은 딸기이며, 토마토 시드 프로필까지 포함되어 있습니다.

## 🧭 지금 바로 이해해야 할 점

- 이 저장소는 문서 저장소가 아니라 실제 프로그램 코드 저장소입니다.
- 다만 일부 운영 자산은 현장 환경에 따라 별도로 채워야 합니다.
  예: 실 ONNX 모델, 카카오 채널 토큰, Mosquitto 바이너리
- 저장소 안의 일부 설계 문서와 명칭에는 여전히 `BerryDoctor`가 남아 있습니다.
  이것은 원본 계보를 보존하기 위한 것이고, 공개 배포 레포의 방향은 `open-smartfarm-doctor`입니다.

## 📦 구성

- [main.py](./main.py)
  프로그램 진입점
- [engine](./engine)
  AI, 제어, 스케줄러, DB, 웹, 시그널, 위성, 보안 모듈
- [data](./data)
  작물 프로필, 규칙, 팁, 시그널 설정 데이터
- [firmware](./firmware)
  ESP32 기반 센서·보안 펌웨어
- [tests](./tests)
  회귀 테스트와 기능 검증
- [docs](./docs)
  아키텍처, 설치 가이드, 핸드오프 문서

## 🚀 빠른 시작

먼저 저장소를 내려받고, Python 가상환경을 만든 뒤 의존성을 설치합니다.

```bash
git clone https://github.com/sinmb79/open-smartfarm-doctor.git
cd open-smartfarm-doctor
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

그다음 프로그램을 바로 실행할 수 있습니다.

```bash
python main.py
```

첫 실행 시 설정 마법사에서 농장 위치, 동 수, 작물, 품종, WiFi 정보를 입력하면 됩니다.

## 🛠️ 빌드

Windows 단일 실행 파일을 만들려면 아래처럼 실행합니다.

```bash
python setup.py
```

이 저장소에서는 PyInstaller 출력 이름을 `open-smartfarm-doctor`로 맞췄습니다.  
Mosquitto 바이너리가 없으면 해당 번들은 제외하고 빌드되도록 처리했습니다.

## 📚 함께 읽으면 좋은 문서

- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- [docs/INSTALL_DEV.md](./docs/INSTALL_DEV.md)
- [docs/INSTALL_FARMER.md](./docs/INSTALL_FARMER.md)
- [docs/BerryDoctor_MultiCrop_Codex_Order.md](./docs/BerryDoctor_MultiCrop_Codex_Order.md)
- [docs/BerryDoctor_v3_TripleIntelligence_Codex_Spec.md](./docs/BerryDoctor_v3_TripleIntelligence_Codex_Spec.md)

## 🤝 공개 원칙

- 현장 제약을 숨기지 않습니다.
- 사람이 이해할 수 없는 자동화는 좋은 자동화로 보지 않습니다.
- 작물 하나에서 통하던 감각을 범용 진실처럼 포장하지 않습니다.
- 제품보다 먼저 판단의 경계를 설계합니다.

## 🧠 만든 사람

22B Labs · The 4th Path  
GitHub: [sinmb79](https://github.com/sinmb79)

좋은 스마트팜은 센서를 더 다는 시스템이 아니라, 현장을 덜 오해하는 시스템입니다.
