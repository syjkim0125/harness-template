# Phase 예시 — 기존 프로젝트 유지보수

`phases/` 디렉토리에 복사해서 사용한다.

## 버그 수정 (`0-bugfix`)

```json
// phases/0-bugfix/index.json
{
  "project": "{프로젝트명}",
  "phase": "bugfix",
  "rules": ["coding-style", "security"],
  "steps": [
    {
      "step": 0,
      "name": "fix-login",
      "status": "pending"
    }
  ]
}
```

**step0.md**: 로그인 실패 원인을 분석하고 수정한다. 기존 테스트를 깨뜨리지 않는다.

## 신규 기능 (`1-feature`)

```json
// phases/1-feature/index.json
{
  "project": "{프로젝트명}",
  "phase": "feature",
  "rules": ["coding-style", "security", "api-conventions"],
  "steps": [
    {
      "step": 0,
      "name": "user-profile",
      "status": "pending"
    },
    {
      "step": 1,
      "name": "profile-api",
      "status": "pending"
    }
  ]
}
```

**step0.md**: 사용자 프로필 페이지 UI를 구현한다.  
**step1.md**: 프로필 CRUD API를 구현한다.

## 리팩토링 (`2-refactor`)

```json
// phases/2-refactor/index.json
{
  "project": "{프로젝트명}",
  "phase": "refactor",
  "rules": ["coding-style", "karpathy-guidelines", "testing"],
  "steps": [
    {
      "step": 0,
      "name": "extract-service",
      "status": "pending"
    }
  ]
}
```

**step0.md**: controller에서 비즈니스 로직을 service 레이어로 분리한다. 기존 테스트 통과 확인.

## 의존성 업데이트 (`3-deps`)

```json
// phases/3-deps/index.json
{
  "project": "{프로젝트명}",
  "phase": "deps",
  "rules": ["coding-style", "security"],
  "steps": [
    {
      "step": 0,
      "name": "upgrade-deps",
      "status": "pending"
    }
  ]
}
```

**step0.md**: 주요 의존성을 최신 메이저 버전으로 업그레이드. breaking change 확인 및 수정.

## rules 선택 가이드

| phase | 추천 rules | 이유 |
|-------|-----------|------|
| bugfix | coding-style, security | 기존 코드 수정 + 보안 검증 |
| feature | coding-style, security, api-conventions | 신규 개발 + API 표준 |
| refactor | coding-style, karpathy-guidelines, testing | 코드 품질 + 테스트 보장 |
| deps | coding-style, security | 호환성 + 취약점 점검 |
