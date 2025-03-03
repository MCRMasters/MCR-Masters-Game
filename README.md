# MCR-Masters-Game
Game server for MCR-Masters

## 개발 환경 준비

### 사전 준비사항
[프로젝트 설치 가이드](https://github.com/MCRMasters/MCR-Masters-Hub)

필수 항목:
- Python 3.12.9
- Poetry

## 프로젝트 설정

### 1. python 3.12.9 설치
```bash
pyenv install 3.12.9
```

### 2. 저장소 클론
```bash
git clone https://github.com/MCRMasters/MCR-Masters-Game.git
cd MCR-Masters-Game
```

### 3. 의존성 설치
```bash
poetry install
```

### 4. pre-commit 훅 설치
```bash
poetry run pre-commit install
```

### 5. 테스트 실행
```bash
poetry run pytest
```

### 6. 애플리케이션 실행
```bash
# 개발 모드 실행 (자동 리로드)
poetry run start

# 프로덕션 모드 실행
poetry run start-prod
```
