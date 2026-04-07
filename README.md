# open-smartfarm-doctor

> 메타 설명: 다작물 스마트팜을 위한 공개 설계 문서와 Codex 핸드오프를 모은 저장소입니다.
>
> 라벨: smartfarm, multicrop, greenhouse, agritech, automation, ai

왜 이 저장소가 있냐면, 많은 스마트팜 프로젝트가 처음에는 잘 돌아가다가도 특정 작물, 특정 장비, 특정 현장에 너무 강하게 묶이기 때문입니다.  
`open-smartfarm-doctor`는 그런 병목을 줄이기 위해 만들었습니다. 딸기 중심으로 검증된 BerryDoctor의 흐름을 바탕으로, 작물에 덜 종속되고 더 확장 가능한 스마트팜 설계 문서와 실행 지시서를 공개하는 저장소입니다.

비개발자 기준으로 30초만에 설명하면 이렇습니다.  
이 저장소는 “센서 데이터, 외부 농업 정보, 위성 참고 정보, 자동화 규칙, 현장 운영 문서”를 한데 묶어 다작물 스마트팜으로 확장하기 위한 공개 청사진입니다. 코드를 바로 실행하는 제품 저장소라기보다, 제품과 플랫폼을 더 넓게 만들기 위한 설계의 출발점에 가깝습니다.

## 🌱 이 저장소에 들어 있는 것

- [BerryDoctor_MultiCrop_Codex_Order.md](./docs/BerryDoctor_MultiCrop_Codex_Order.md)
  딸기 전용 구조를 다작물 구조로 바꾸기 위한 리팩터링 지시서입니다.
- [BerryDoctor_v3_TripleIntelligence_Codex_Spec.md](./docs/BerryDoctor_v3_TripleIntelligence_Codex_Spec.md)
  센서, 외부 시그널, 위성 참고 정보를 함께 쓰는 3중 지능 확장 문서입니다.

## 🧭 이 저장소가 다루는 질문

- 어떻게 하면 딸기 전용 스마트팜을 토마토, 고추, 오이 같은 다작물 구조로 확장할 수 있을까
- 센서만 보는 시스템을 넘어서, 외부 맥락과 장기 추세를 함께 판단하는 구조를 어떻게 만들까
- 농부가 복잡한 기술 용어를 몰라도 바로 이해할 수 있는 운영 언어를 어떻게 만들까
- 인터넷이 끊겨도 핵심 생존 기능은 유지되는 구조를 어떻게 지킬까

## 🧩 누가 보면 좋은가

- 다작물 스마트팜 플랫폼을 설계하려는 개발자
- 농업 AI, 자동화, 대시보드, MQTT, 현장 운영 문서를 함께 다루는 팀
- BerryDoctor 계열 프로젝트를 더 범용적인 구조로 확장하려는 메이커
- “제품 코드”보다 먼저 “판단 구조”를 이해하고 싶은 기획자와 운영자

## 📚 추천 읽기 순서

1. 먼저 [BerryDoctor_MultiCrop_Codex_Order.md](./docs/BerryDoctor_MultiCrop_Codex_Order.md)를 읽어 다작물 구조 전환의 뼈대를 잡습니다.
2. 그다음 [BerryDoctor_v3_TripleIntelligence_Codex_Spec.md](./docs/BerryDoctor_v3_TripleIntelligence_Codex_Spec.md)를 읽어 센서 밖의 세계를 어떻게 붙일지 봅니다.
3. 마지막으로 자신의 현장에 맞게 작물 프로필, 알림 정책, 자동화 경계를 다시 정의하면 됩니다.

## 🔧 로컬에서 바로 보는 방법

문서 저장소라서 특별한 빌드 과정은 없습니다. 먼저 내려받고, `docs` 폴더의 문서를 바로 열면 됩니다.

```bash
git clone https://github.com/sinmb79/open-smartfarm-doctor.git
cd open-smartfarm-doctor
```

## 🤝 공개 원칙

- 과대 약속보다 현장 제약을 먼저 적습니다.
- 자동화보다 사람이 이해할 수 있는 판단을 우선합니다.
- 특정 작물에 최적화된 성공을 범용 플랫폼으로 착각하지 않습니다.
- “더 똑똑한 시스템”보다 “덜 속이는 시스템”을 지향합니다.

## 🧠 만든 사람

22B Labs · The 4th Path  
GitHub: [sinmb79](https://github.com/sinmb79)

좋은 스마트팜은 센서를 더 붙이는 시스템이 아니라, 현장을 더 정직하게 해석하는 시스템입니다.
