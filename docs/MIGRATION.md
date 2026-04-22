# Harness Template 적용 방법

## 가장 쉬운 방법 (한 줄)

```bash
python3 /tmp/harness-template/scripts/execute.py apply {내프로젝트경로} \
  --project-name {프로젝트명} --stack "{기술스택}"
```

자동으로:
1. 템플릿 파일 복사 (`CLAUDE.md`, `claude/`, `phases/`, `scripts/`, `docs/`)
2. `{프로젝트명}`, `{기술 스택}` placeholder 자동 치환
3. git 커밋

실행 후 남은 placeholder는 `CLAUDE.md`에서 직접 채운다.

## 수동 적용 (단계를 하나씩 확인하며)

```bash
git clone <template-repo-url> /tmp/harness-template
cd {프로젝트루트}
cp /tmp/harness-template/CLAUDE.md ./
cp -r /tmp/harness-template/claude ./
cp -r /tmp/harness-template/phases ./
cp -r /tmp/harness-template/scripts ./
cp -r /tmp/harness-template/docs ./
```

## 기존 프로젝트에 적용 시

### 기존 `docs/` 폴더가 있다면

`apply` 커맨드는 기존 `docs/`가 있으면 새 파일만 추가하고 기존 파일은 건드리지 않는다.

```bash
# docs/가 이미 있으면 apply가 자동으로 병합
python3 /tmp/harness-template/scripts/execute.py apply {내프로젝트경로}
```

### 적용 순서 (기존 프로젝트)

1. **maintenance/step0** — 치명적 버그 수정부터
2. **maintenance/step1** — 복잡한 모듈 리팩토링
3. **maintenance/step2** — 의존성 업데이트 (보안 패치 우선)
4. **maintenance/step3** — 테스트 커버리지 80% 목표

```bash
python3 scripts/execute.py maintenance
```

### karpathy-guidelines 준수

기존 코드 수정 시:
- 옆 코드를 "개선"하지 마라 (주석, 포맷팅 포함)
- 고장 나지 않은 것을 리팩토링하지 마라
- 기존 스타일을 맞춰라
- 관련 없는 dead code는 알리기만 하고 지우지 마라

## 커스터마이징 체크리스트

`apply` 실행 후 다음을 확인한다:

- [ ] `CLAUDE.md` — `{프로젝트명}`, `{기술 스택}`, `{개발 명령어}` 치환 완료
- [ ] `docs/PRD.md` — 프로젝트 정보로 전체 채움
- [ ] `docs/ARCHITECTURE.md` — 아키텍처 구체화
- [ ] `docs/ADR.md` — 기존 기술 결정 기록
- [ ] `phases/*/index.json` — `project` 필드 실제 프로젝트명
