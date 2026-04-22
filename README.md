# Harness Template

AI 기반 프로젝트 개발 템플릿. Claude Code와 함께 단계별(phase/step)로 프로젝트를 구축한다.

## 빠른 시작

### 신규 프로젝트
```bash
git clone <저장소 URL>
cd <프로젝트명>
python3 scripts/execute.py 0-mvp
```

### 기존 프로젝트에 적용 (한 줄)
```bash
# 템플릿 레포를 별도 디렉토리에 클론
git clone <template-repo-url> /tmp/harness-template

# 내 프로젝트 루트에서 한 번에 적용
python3 /tmp/harness-template/scripts/execute.py apply {내프로젝트경로} \
  --project-name {프로젝트명} --stack "{기술스택}"
```

예시:
```bash
python3 /tmp/harness-template/scripts/execute.py apply ~/projects/my-app \
  --project-name MyApp --stack "Next.js 16, TypeScript, PostgreSQL"
```

자동으로 다음이 수행된다:
1. 템플릿 파일 복사 (CLAUDE.md, claude/, phases/, scripts/, docs/)
2. `{프로젝트명}`, `{기술 스택}` placeholder 자동 치환
3. git 커밋
4. 남은 placeholder 안내

자세한 적용 가이드는 `docs/MIGRATION.md` 참조.

## 구조

```
├── CLAUDE.md              # 메인 프로젝트 가이드
├── docs/
│   ├── PRD.md             # 제품 요구사항
│   ├── ARCHITECTURE.md    # 아키텍처
│   ├── ADR.md             # 기술 결정 기록
│   ├── MIGRATION.md       # 기존 프로젝트 적용 방법
│   └── UI_GUIDE.md        # UI 디자인 가이드
├── claude/
│   ├── rules/             # 개발 규칙 9종
│   └── examples/          # 프레임워크별 예시
├── phases/
│   ├── index.json         # 페이즈 목록
│   ├── 0-mvp/             # 신규 MVP (3 steps)
│   ├── 1-polish/          # 완성도 향상 (5 steps)
│   └── maintenance/       # 기존 프로젝트 유지보수 (4 steps)
└── scripts/
    └── execute.py         # apply + step 실행
```

## 명령어

```bash
# 템플릿을 내 프로젝트에 한 번에 적용
python3 scripts/execute.py apply /path/to/project \
  --project-name MyProject --stack "Next.js, TypeScript, PostgreSQL"

# 신규 프로젝트 MVP phase 실행
python3 scripts/execute.py 0-mvp

# MVP 완성도 향상
python3 scripts/execute.py 1-polish

# 기존 프로젝트 유지보수
python3 scripts/execute.py maintenance

# 완료 후 push 포함
python3 scripts/execute.py 0-mvp --push
```

## Phase 요약

| Phase | 대상 | Step | 내용 |
|-------|------|------|------|
| `0-mvp` | 신규 프로젝트 | 3 | 프로젝트 설정 → 핵심 로직 → API 레이어 |
| `1-polish` | MVP 완성 | 5 | 에러 핸들링 → 보안 → 성능 → 문서 → E2E |
| `maintenance` | 기존 프로젝트 | 4 | 버그 수정 → 리팩토링 → 의존성 → 테스트 |

## 규칙 (rules)

`phases/*/index.json`의 `rules` 배열에서 사용할 규칙만 선택 로드. 미지정 시 전체 로드.

| 파일 | 내용 |
|------|------|
| `coding-style.md` | 코딩 스타일, 가독성, 불변성 |
| `karpathy-guidelines.md` | 생각 후 코딩, 단순함, 수술적 변경 |
| `testing.md` | TDD, 80% 커버리지, 에지 케이스 |
| `security.md` | 시크릿 관리, 입력 검증, 인가 |
| `performance.md` | 알고리즘 효율, 모델 선택 |
| `git-workflow.md` | 커밋 컨벤션, 브랜치 전략 (GitHub Flow) |
| `onboarding.md` | clone → 실행 가이드 |
| `api-conventions.md` | REST API 설계 규칙 |
| `data-model.md` | 스키마, 마이그레이션, 관계 |

## License

MIT
