# Onboarding

## 프로젝트 시작 가이드

### 1. 레포지토리 클론
```bash
git clone <레포지토리 URL>
cd <프로젝트명>
```

### 2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일에서 실제 값으로 채운다
```

### 3. 의존성 설치
```bash
# 프로젝트별 의존성 설치 명령어
# 예: npm install, uv sync, cargo build
```

### 4. 개발 서버 실행
```bash
# 예: npm run dev, python main.py, cargo run
```

### 5. 검증
```bash
# 빌드
# 테스트
# 린트
```

## 프로젝트 구조
- `docs/` — 제품 요구사항, 아키텍처, 기술 결정
- `claude/rules/` — 개발 규칙
- `phases/` — Phase/Step 정의 및 상태
- `scripts/` — 실행 스크립트

## 하네스 실행
```bash
python3 scripts/execute.py 0-mvp
```

## 문제 해결
- 빌드 실패: `.env`에 올바른 값이 설정되었는지 확인
- 테스트 실패: 의존성 버전을 확인하고 `install` 재실행
- 기타: `docs/` 문서를 참고하여 아키텍처와 요구사항 재확인
