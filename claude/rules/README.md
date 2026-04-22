# 규칙 템플릿 안내

이 디렉토리는 프로젝트별 규칙 템플릿이다. 복사해서 각 프로젝트에 맞게 수정해라.

## 사용 방법

1. 프로젝트 루트에 `claude/` 디렉토리 복사
2. `claude/rules/` 파일을 프로젝트에 맞게 수정
3. `[CUSTOMIZE]` 마커를 프로젝트별 내용으로 교체
4. `CLAUDE.md`에 프로젝트명, 기술 스택, 명령어 기입
5. `docs/` 템플릿(PRD, ARCHITECTURE, ADR) 채움

## 자동 로드

`claude/rules/*.md` 파일들은 자동으로 컨텍스트에 로드된다.

## 파일 목록

| 파일 | 용도 |
|------|------|
| `coding-style.md` — 네이밍, 불변성, 파일 조직, 에러 핸들링 |
| `karpathy-guidelines.md` — 생각 후 코딩, 단순함, 수술적 변경 |
| `testing.md` — TDD, 커버리지, 모킹, 에지 케이스 |
| `security.md` — 시크릿, 입력 검증, 인가, 취약점 |
| `performance.md` — 알고리즘, 프론트/백엔드 성능, 캐싱 |
| `git-workflow.md` — 브랜치, 커밋, PR, 충돌 해결 |
| `onboarding.md` — clone → 실행까지 단계별 가이드 |
| `api-conventions.md` — REST API 응답/에러/페이지네이션 규칙 |
| `data-model.md` — ORM, 마이그레이션, 네이밍, 관계 설계 |

## 커스터마이징 우선순위

1. **CLAUDE.md** — 프로젝트명, 기술 스택, 개발 명령어
2. **docs/** — PRD 먼저, 그 다음 ARCHITECTURE, 결정 시 ADR 기록
3. **claude/rules/** — `[CUSTOMIZE]` 부분에 프로젝트별 규칙
4. **삭제** — 프로젝트와 무관한 규칙 파일은 삭제

## 새 규칙 추가

`claude/rules/`에 `*.md` 파일을 자유롭게 추가:
- `deployment.md` — 배포 프로세스, 환경
- `database.md` — 스키마 규칙, 마이그레이션
- `webhooks.md` — 웹훅 설계 규칙
