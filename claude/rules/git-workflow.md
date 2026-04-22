# Git 워크플로우

## 브랜치 전략

### 브랜치 이름 규칙
- `feature/` — 새 기능 (예: `feature/user-auth`)
- `fix/` — 버그 수정 (예: `fix/login-crash`)
- `refactor/` — 리팩토링 (예: `refactor/api-layer`)
- `docs/` — 문서 변경
- `chore/` — 유지보수, 의존성
- `hotfix/` — 운영 긴급 수정

### 브랜칭 모델 (GitHub Flow)

```
main (항상 배포 가능)
 └── feature/* → PR → main
```

- **main**: 운영 준비 완료. 모든 커밋 배포 가능.
- **feature/fix**: `main`에서 분기, 완료 후 `main`으로 PR.
- **hotfix/**: `main`에서 분기, `main`으로 바로 병합.

> **참고**: 대규모 팀(>10명)이나 고정 릴리스 주기가 있는 프로젝트는 **git-flow**(`main` + `develop` + `release/*`)를 고려하라. 소규모 팀(≤5명)이나 CI/CD 기반 팀에는 GitHub Flow가 권장된다.

## 커밋 메시지

```
<type>(<scope>): <설명>

<옵션 본문>
```

| Type | 용도 |
|------|------|
| `feat` | 새로운 기능 |
| `fix` | 버그 수정 |
| `refactor` | 기능 변경 없이 코드 개선 |
| `docs` | 문서 변경 |
| `test` | 테스트 추가/수정 |
| `chore` | 유지보수, 의존성 |
| `perf` | 성능 개선 |
| `ci` | CI/CD 설정 변경 |

### 규칙
- 제목: 최대 72자, 명령법 ("add" not "added")
- 본문: WHAT과 WHY를 설명 (HOW는 코드가 보여줌)
- 푸터: 티켓 번호 (`Closes #123`)

## PR 워크플로우

### PR 전
1. 대상 브랜치에 리베이스 (`git rebase origin/main`)
2. 전체 테스트 실행
3. 린트/타입 체커 실행
4. 스스로 diff 리뷰

### PR 작성
- 전체 변경 사항 요약 (`git diff [base]...HEAD`)
- **What**: 변경 내용, **Why**: 배경, **Testing**: 테스트 방법
- UI 변경이면 before/after 스크린샷

### PR 크기 가이드
- **작음** (< 400줄): 권장. 리뷰 쉽고 빠름.
- **중간** (400-800줄): 구조 설명 필요.
- **큼** (> 800줄): 가능하면 분할. 불가피하면 상세 walkthrough 추가.

## 충돌 해결

```
1. git fetch origin
2. git rebase origin/main
3. 수동으로 충돌 해결
4. git add <해결된 파일>
5. git rebase --continue
6. 테스트 실행으로 확인
```

### 금지
- `git rebase --skip` — 건너뛰는 내용 확인 전 금지
- `git checkout --theirs` / `--ours` — 무조건 금지
- 충돌 해결 후 테스트 없이 커밋 금지

## 되돌리기

```
git restore --staged <file>        # 스테이지 취소 (작업 복사본 유지)
git restore <file>                 # 로컬 변경 버림
git reset --soft HEAD~1            # 마지막 커밋 취소 (변경 유지)
git revert <commit-hash>           # 푸시된 커밋 되돌리기 (새 커밋 생성)
git reset --hard <commit>          # 위험! 확인 필요 — 지정 커밋 이후 전부 삭제
```

## [CUSTOMIZE] 프로젝트별 Git 규칙

- 브랜치 보호 규칙
- 필수 리뷰어 수
- CI/CD 요구사항
