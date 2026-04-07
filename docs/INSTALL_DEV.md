# 개발 환경 안내

1. Python 3.11 이상을 준비합니다.
2. `pip install -r requirements.txt`로 기본 의존성을 설치합니다.
3. `python main.py`로 프로그램을 실행합니다.
4. `python -m unittest discover -s tests -v`로 기본 회귀 테스트를 확인합니다.

실 API 키가 없으면 프로그램은 mock 데이터 중심으로 동작합니다. 위성 실연동이 필요할 때만 `requirements-satellite.txt`를 추가로 설치하면 됩니다.
