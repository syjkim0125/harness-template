#!/usr/bin/env python3
"""
Harness Step Executor — phase 내 step을 순차 실행하고 자가 교정한다.
Harness Template Apply — 기존 프로젝트에 템플릿을 한 번에 적용한다.

Usage:
    python3 scripts/execute.py <phase-dir> [--push]
    python3 scripts/execute.py apply <project-root> [--project-name <name>] [--stack <stack>]
"""

import argparse
import contextlib
import json
import re
import shutil
import subprocess
import sys
import threading
import time
import types
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent
ROOT = TEMPLATE_ROOT  # backward compatibility for tests


@contextlib.contextmanager
def progress_indicator(label: str):
    """터미널 진행 표시기. with 문으로 사용하며 .elapsed 로 경과 시간을 읽는다."""
    frames = "◐◓◑◒"
    stop = threading.Event()
    t0 = time.monotonic()

    def _animate():
        idx = 0
        while not stop.wait(0.12):
            sec = int(time.monotonic() - t0)
            sys.stderr.write(f"\r{frames[idx % len(frames)]} {label} [{sec}s]")
            sys.stderr.flush()
            idx += 1
        sys.stderr.write("\r" + " " * (len(label) + 20) + "\r")
        sys.stderr.flush()

    th = threading.Thread(target=_animate, daemon=True)
    th.start()
    info = types.SimpleNamespace(elapsed=0.0)
    try:
        yield info
    finally:
        stop.set()
        th.join()
        info.elapsed = time.monotonic() - t0


# =========================================================================
#  step 파일 자동 생성 — 감지된 스택에 맞춰 step 내용 생성
# =========================================================================

STEP_TEMPLATES: dict[str, dict] = {
    "Python": {
        "0-mvp": [
            (
                "project-setup",
                "# Step 0: 프로젝트 초기 설정\n"
                "\n## 작업 내용\n"
                "- Python 가상환경 생성 및 활성화 (`python -m venv .venv`)\n"
                "- 패키지 매니저 초기화 (`pyproject.toml` 또는 `requirements.txt`)\n"
                "- 의존성 설치: 프레임워크, ORM, 테스트 도구, 린터(`ruff`)\n"
                "- 프로젝트 스캐폴딩: `src/`, `tests/`, `config/` 디렉토리\n"
                "- 환경변수 설정 (`.env.example` → `.env`)\n"
                "- 린트/포맷터/테스트 프레임워크 설정\n"
                "- Git 저장소 초기화 및 `.gitignore` 적용\n"
                "\n## AC (Acceptance Criteria)\n"
                "- [ ] `pip install -e .` (또는 `uv sync`) 성공\n"
                "- [ ] `uv run src/main.py` 실행 시 서버 시작 (또는 `python -m src.main`)\n"
                "- [ ] `ruff check src/` 에러 없이 통과\n"
                "- [ ] `.env` 파일에서 기본 설정 읽음\n"
                "- [ ] 빈 테스트 스위트 실행 성공 (`pytest`)\n",
            ),
            (
                "core-logic",
                "# Step 1: 핵심 비즈니스 로직\n"
                "\n## 작업 내용\n"
                "- 도메인 모델 정의 (Pydantic `BaseModel` 또는 dataclass)\n"
                "- 핵심 비즈니스 로직 구현 (서비스 레이어, 순수 함수 우선)\n"
                "- 데이터 접근 계층 설정 (SQLAlchemy ORM 또는 peewee 등)\n"
                "- 단위 테스트 작성 (pytest)\n"
                "\n## AC (Acceptance Criteria)\n"
                "- [ ] 핵심 엔티티 CRUD 동작 (메모리 또는 임시 DB)\n"
                "- [ ] 단위 테스트 통과 (`pytest --cov=src`, 커버리지 80%+)\n"
                "- [ ] 비즈니스 로직이 순수 함수로 분리됨 (외부 의존성 없음)\n",
            ),
            (
                "api-layer",
                "# Step 2: API 레이어\n"
                "\n## 작업 내용\n"
                "- REST API 엔드포인트 정의 (FastAPI router 또는 Flask Blueprint)\n"
                "- 컨트롤러/라우터 구현 (요청 → 서비스 → 응답)\n"
                "- 요청 검증 (Pydantic `BaseModel` / marshmallow 스키마)\n"
                "- 인증/인가 미들웨어 적용\n"
                "- 통합 테스트 작성 (httpx TestClient 또는 pytest)\n"
                "\n## AC (Acceptance Criteria)\n"
                "- [ ] 주요 API 엔드포인트 CRUD 동작 (`httpx.TestClient`로 검증)\n"
                "- [ ] 입력 검증 실패 시 400 응답 (자동 Pydantic 검증)\n"
                "- [ ] 인증 없이 보호된 엔드포인트 접근 시 401 응답\n"
                "- [ ] API 응답 포맷이 api-conventions.md 규칙 준수\n",
            ),
        ],
        "1-polish": [
            ("error-handling", "# Step 0: 에러 핸들링 정비"),
            ("security-hardening", "# Step 1: 보안 강화"),
            ("performance-audit", "# Step 2: 성능 감사"),
            ("docs-refinement", "# Step 3: 문서 정비"),
            ("e2e-testing", "# Step 4: E2E 테스트"),
        ],
        "maintenance": [
            ("bugfix-critical", "# Step 0: 치명적 버그 수정"),
            ("refactor-hotspot", "# Step 1: 핫스팟 리팩토링"),
            ("deps-update", "# Step 2: 의존성 업데이트"),
            ("test-coverage", "# Step 3: 테스트 커버리지 개선"),
        ],
    },
    "Go": {
        "0-mvp": [
            (
                "project-setup",
                "# Step 0: 프로젝트 초기 설정\n"
                "\n## 작업 내용\n"
                "- Go 모듈 초기화 (`go mod init`)\n"
                "- 의존성 설치: 웹 프레임워크, ORM, 테스트 도구, 린터(`golangci-lint`)\n"
                "- 프로젝트 스캐폴딩: `cmd/`, `internal/`, `pkg/`, `config/`\n"
                "- 환경변수 설정 (`.env.example` → `.env`)\n"
                "- 빌드/테스트/린트 설정 (`Makefile` 또는 `Taskfile.yml`)\n"
                "- Git 저장소 초기화\n"
                "\n## AC (Acceptance Criteria)\n"
                "- [ ] `go build ./...` 성공\n"
                "- [ ] `go run cmd/server/main.go` 실행 시 서버 시작\n"
                "- [ ] `golangci-lint run` 에러 없이 통과\n"
                "- [ ] 빈 테스트 스위트 실행 성공 (`go test ./...`)\n",
            ),
            (
                "core-logic",
                "# Step 1: 핵심 비즈니스 로직\n"
                "\n## 작업 내용\n"
                "- 도메인 모델 정의 (struct + interface)\n"
                "- 핵심 비즈니스 로직 구현 (internal/service/, 순수 함수 우선)\n"
                "- 데이터 접근 계층 설정 (internal/repository/, GORM 또는 sqlx)\n"
                "- 단위 테스트 작성 (표준 `testing` + testify)\n"
                "\n## AC (Acceptance Criteria)\n"
                "- [ ] 핵심 엔티티 CRUD 동작 (인터페이스 기반 모킹)\n"
                "- [ ] 단위 테스트 통과 (`go test ./... -cover`, 커버리지 80%+)\n"
                "- [ ] 비즈니스 로직이 인터페이스로 분리됨 (의존성 주입)\n",
            ),
            (
                "api-layer",
                "# Step 2: API 레이어\n"
                "\n## 작업 내용\n"
                "- REST API 라우트 정의 (chi, gin, 또는 표준 `net/http`)\n"
                "- HTTP 핸들러 구현 (요청 검증 → 서비스 → JSON 응답)\n"
                "- 요청 검증 (구조체 태그 기반 또는 go-playground/validator)\n"
                "- 인증/인가 미들웨어 적용 (JWT, CORS)\n"
                "- 통합 테스트 작성 (`httptest`)\n"
                "\n## AC (Acceptance Criteria)\n"
                "- [ ] 주요 API 엔드포인트 CRUD 동작 (`httptest.NewRecorder`로 검증)\n"
                "- [ ] 입력 검증 실패 시 400 응답 (자동 구조체 검증)\n"
                "- [ ] 인증 없이 보호된 엔드포인트 접근 시 401 응답\n"
                "- [ ] API 응답 포맷이 api-conventions.md 규칙 준수\n",
            ),
        ],
        "1-polish": [
            ("error-handling", "# Step 0: 에러 핸들링 정비"),
            ("security-hardening", "# Step 1: 보안 강화"),
            ("performance-audit", "# Step 2: 성능 감사"),
            ("docs-refinement", "# Step 3: 문서 정비"),
            ("e2e-testing", "# Step 4: E2E 테스트"),
        ],
        "maintenance": [
            ("bugfix-critical", "# Step 0: 치명적 버그 수정"),
            ("refactor-hotspot", "# Step 1: 핫스팟 리팩토링"),
            ("deps-update", "# Step 2: 의존성 업데이트"),
            ("test-coverage", "# Step 3: 테스트 커버리지 개선"),
        ],
    },
    "Rust": {
        "0-mvp": [
            (
                "project-setup",
                "# Step 0: 프로젝트 초기 설정\n"
                "\n## 작업 내용\n"
                "- Cargo 프로젝트 초기화 (`cargo init`)\n"
                "- 의존성 설정: 웹 프레임워크 (axum/actix), ORM (sea-orm/sqlx), serde, tracing\n"
                "- 프로젝트 구조: `src/bin/`, `src/api/`, `src/domain/`, `src/infra/`\n"
                "- 환경변수 설정 (`.env.example` → `.env`, dotenvy)\n"
                "- 린트/포맷 설정 (`cargo clippy`, `cargo fmt`)\n"
                "\n## AC (Acceptance Criteria)\n"
                "- [ ] `cargo build` 성공\n"
                "- [ ] `cargo run` 실행 시 서버 시작\n"
                "- [ ] `cargo clippy` 에러 없이 통과 (또는 경고만)\n"
                "- [ ] `cargo test` 통과 (빈 테스트 포함)\n",
            ),
            (
                "core-logic",
                "# Step 1: 핵심 비즈니스 로직\n"
                "\n## 작업 내용\n"
                "- 도메인 모델 정의 (struct + trait)\n"
                "- 비즈니스 로직 구현 (src/domain/, 순수 함수)\n"
                "- 데이터 접근 레이어 설정 (src/infra/, sea-orm 또는 sqlx)\n"
                "- 단위 테스트 작성 (표준 `#[test]`)\n"
                "\n## AC (Acceptance Criteria)\n"
                "- [ ] 핵심 엔티티 CRUD 동작 (인메모리 리포지토리로 테스트)\n"
                "- [ ] `cargo test` 전체 통과 (커버리지 목표)\n"
                "- [ ] 비즈니스 로직이 트레이트로 분리됨 (의존성 주입)\n",
            ),
            (
                "api-layer",
                "# Step 2: API 레이어\n"
                "\n## 작업 내용\n"
                "- REST API 라우트 정의 (axum Router 또는 actix-web)\n"
                "- HTTP 핸들러 구현 (요청 추출 → 서비스 → JSON 응답)\n"
                "- 요청 검증 (serde + validator)\n"
                "- 인증/인가 미들웨어 (JWT, tower 레이어)\n"
                "- 통합 테스트 (`axum::Router` 또는 `actix_web::test`)\n"
                "\n## AC (Acceptance Criteria)\n"
                "- [ ] 주요 API 엔드포인트 CRUD 동작\n"
                "- [ ] 입력 검증 실패 시 400 응답 (serde 역직렬화 에러)\n"
                "- [ ] 인증 없이 보호된 엔드포인트 접근 시 401 응답\n"
                "- [ ] API 응답 포맷이 api-conventions.md 규칙 준수\n",
            ),
        ],
        "1-polish": [
            ("error-handling", "# Step 0: 에러 핸들링 정비"),
            ("security-hardening", "# Step 1: 보안 강화"),
            ("performance-audit", "# Step 2: 성능 감사"),
            ("docs-refinement", "# Step 3: 문서 정비"),
            ("e2e-testing", "# Step 4: E2E 테스트"),
        ],
        "maintenance": [
            ("bugfix-critical", "# Step 0: 치명적 버그 수정"),
            ("refactor-hotspot", "# Step 1: 핫스팟 리팩토링"),
            ("deps-update", "# Step 2: 의존성 업데이트"),
            ("test-coverage", "# Step 3: 테스트 커버리지 개선"),
        ],
    },
    "Ruby": {
        "0-mvp": [
            (
                "project-setup",
                "# Step 0: 프로젝트 초기 설정\n"
                "\n## 작업 내용\n"
                "- Gemfile 초기화 (`bundle init`)\n"
                "- 의존성 설정: Rails 또는 Sinatra, RSpec, rubocop\n"
                "- 프로젝트 스캐폴딩 (`rails new` 또는 `sinatra`) \n"
                "- 환경변수 설정 (`.env.example` → `.env`, dotenv)\n"
                "- 린트/테스트 설정 (`.rubocop.yml`, `spec/`)\n"
                "\n## AC (Acceptance Criteria)\n"
                "- [ ] `bundle install` 성공\n"
                "- [ ] `bin/rails server` (또는 `ruby app.rb`) 실행 시 서버 시작\n"
                "- [ ] `rubocop` 에러 없이 통과\n"
                "- [ ] `bundle exec rspec` 통과\n",
            ),
            (
                "core-logic",
                "# Step 1: 핵심 비즈니스 로직",
            ),
            (
                "api-layer",
                "# Step 2: API 레이어",
            ),
        ],
        "1-polish": [
            ("error-handling", "# Step 0: 에러 핸들링 정비"),
            ("security-hardening", "# Step 1: 보안 강화"),
            ("performance-audit", "# Step 2: 성능 감사"),
            ("docs-refinement", "# Step 3: 문서 정비"),
            ("e2e-testing", "# Step 4: E2E 테스트"),
        ],
        "maintenance": [
            ("bugfix-critical", "# Step 0: 치명적 버그 수정"),
            ("refactor-hotspot", "# Step 1: 핫스팟 리팩토링"),
            ("deps-update", "# Step 2: 의존성 업데이트"),
            ("test-coverage", "# Step 3: 테스트 커버리지 개선"),
        ],
    },
    "Java": {
        "0-mvp": [
            (
                "project-setup",
                "# Step 0: 프로젝트 초기 설정\n"
                "\n## 작업 내용\n"
                "- 빌드 도구 초기화 (`mvn archetype:generate` 또는 `gradle init`)\n"
                "- 의존성 설정: Spring Boot, JUnit, checkstyle/spotless\n"
                "- 프로젝트 스캐폴딩 (`src/main/java/`, `src/test/java/`)\n"
                "- 환경변수 설정 (`application.yml`)\n"
                "\n## AC (Acceptance Criteria)\n"
                "- [ ] `./mvnw clean compile` (또는 `./gradlew build`) 성공\n"
                "- [ ] `./mvnw spring-boot:run` 실행 시 서버 시작\n"
                "- [ ] `./mvnw test` 통과\n",
            ),
            (
                "core-logic",
                "# Step 1: 핵심 비즈니스 로직",
            ),
            (
                "api-layer",
                "# Step 2: API 레이어",
            ),
        ],
        "1-polish": [
            ("error-handling", "# Step 0: 에러 핸들링 정비"),
            ("security-hardening", "# Step 1: 보안 강화"),
            ("performance-audit", "# Step 2: 성능 감사"),
            ("docs-refinement", "# Step 3: 문서 정비"),
            ("e2e-testing", "# Step 4: E2E 테스트"),
        ],
        "maintenance": [
            ("bugfix-critical", "# Step 0: 치명적 버그 수정"),
            ("refactor-hotspot", "# Step 1: 핫스팟 리팩토링"),
            ("deps-update", "# Step 2: 의존성 업데이트"),
            ("test-coverage", "# Step 3: 테스트 커버리지 개선"),
        ],
    },
    "Swift": {
        "0-mvp": [
            (
                "project-setup",
                "# Step 0: 프로젝트 초기 설정",
            ),
            (
                "core-logic",
                "# Step 1: 핵심 비즈니스 로직",
            ),
            (
                "api-layer",
                "# Step 2: API 레이어",
            ),
        ],
        "1-polish": [
            ("error-handling", "# Step 0: 에러 핸들링 정비"),
            ("security-hardening", "# Step 1: 보안 강화"),
            ("performance-audit", "# Step 2: 성능 감사"),
            ("docs-refinement", "# Step 3: 문서 정비"),
            ("e2e-testing", "# Step 4: E2E 테스트"),
        ],
        "maintenance": [
            ("bugfix-critical", "# Step 0: 치명적 버그 수정"),
            ("refactor-hotspot", "# Step 1: 핫스팟 리팩토링"),
            ("deps-update", "# Step 2: 의존성 업데이트"),
            ("test-coverage", "# Step 3: 테스트 커버리지 개선"),
        ],
    },
}


def _generate_step_files(
    target: Path,
    stack_list: list[str],
) -> None:
    """감지된 기술 스택에 맞게 step 파일을 생성한다."""
    # 지원 언어 선택: 첫 번째 매칭
    lang = None
    for item in stack_list:
        for supported in STEP_TEMPLATES:
            if item.lower() == supported.lower():
                lang = supported
                break
        if lang:
            break

    if not lang:
        return  # 미지원 언어 → 기존 템플릿 유지

    template = STEP_TEMPLATES[lang]

    for phase_name, steps in template.items():
        phase_dir = target / "phases" / phase_name
        if not phase_dir.is_dir():
            continue

        for step_num, (name, content) in enumerate(steps):
            step_file = phase_dir / f"step{step_num}.md"
            step_file.write_text(content, encoding="utf-8")

        print(f"  ~ phases/{phase_name}/ step files → {lang}용으로 생성 ({len(steps)}개)")


# =========================================================================
#  apply — 기존 프로젝트에 하네스 템플릿 적용
# =========================================================================

def _detect_tech_stack(target: Path) -> str:
    """대상 프로젝트의 기술 스택을 분석하여 반환한다."""
    stack_list = _detect_tech_stack_raw(target)
    if not stack_list:
        return ""
    return ", ".join(stack_list)


def _detect_tech_stack_raw(target: Path) -> list[str]:
    """기술 스택을 리스트로 반환한다."""
    detected = []

    # 언어/프레임워크 감지 맵
    detectors = {
        # Node.js / JS
        ("package.json",): lambda c: _parse_package_json(c),
        # Python
        ("requirements.txt",): lambda c: "Python" if c.strip() else None,
        ("pyproject.toml",): lambda c: "Python" if c.strip() else None,
        ("Pipfile",): lambda c: "Python" if c.strip() else None,
        # Rust
        ("Cargo.toml",): lambda c: "Rust" if c.strip() else None,
        # Go
        ("go.mod",): lambda c: "Go" if c.strip() else None,
        # Java / Kotlin
        ("pom.xml",): lambda c: "Java" if c.strip() else None,
        ("build.gradle",): lambda c: "Java" if c.strip() else None,
        ("build.gradle.kts",): lambda c: "Java/Kotlin" if c.strip() else None,
        # Ruby
        ("Gemfile",): lambda c: "Ruby" if c.strip() else None,
        # Swift
        ("Package.swift",): lambda c: "Swift" if c.strip() else None,
        # Docker
        ("Dockerfile",): lambda c: "Docker" if c.strip() else None,
        ("docker-compose.yml",): lambda c: "Docker Compose" if c.strip() else None,
        ("docker-compose.yaml",): lambda c: "Docker Compose" if c.strip() else None,
        # Infra
        ("terraform.tf",): lambda c: "Terraform" if c.strip() else None,
        # TypeScript config
        ("tsconfig.json",): lambda c: "TypeScript" if c.strip() else None,
    }

    for files, parser in detectors.items():
        for fname in files:
            fpath = target / fname
            if fpath.exists():
                try:
                    content = fpath.read_text(encoding="utf-8")
                    result = parser(content)
                    if result:
                        if isinstance(result, list):
                            detected.extend(result)
                        else:
                            detected.append(result)
                except Exception:
                    pass
                break

    if not detected:
        return ""

    # 중복 제거, 순서 유지
    seen = set()
    unique = []
    for item in detected:
        if item not in seen:
            seen.add(item)
            unique.append(item)

    return ", ".join(unique)


def _parse_package_json(content: str) -> list[str]:
    """package.json을 분석하여 기술 스택을 반환한다."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return ["Node.js"]

    deps = {}
    deps.update(data.get("dependencies", {}))
    deps.update(data.get("devDependencies", {}))

    stack = ["Node.js"]

    # TypeScript 체크
    if "typescript" in deps or "tsconfig.json" in [str(p.name) for p in Path(content[:0] or ".").parent.glob("tsconfig.json")]:
        stack.append("TypeScript")

    # 프레임워크 감지
    frameworks = {
        "next": "Next.js",
        "react": "React",
        "vue": "Vue.js",
        "@angular/core": "Angular",
        "svelte": "Svelte",
        "remix": "Remix",
        "gatsby": "Gatsby",
        "express": "Express",
        "fastify": "Fastify",
        "nestjs": "NestJS",
        "@nestjs/core": "NestJS",
        "hono": "Hono",
        "elysia": "Elysia",
        "tailwindcss": "Tailwind CSS",
        "@tailwindcss/vite": "Tailwind CSS",
    }
    for dep, name in frameworks.items():
        if dep in deps:
            stack.append(name)

    # DB/ORM 감지
    databases = {
        "prisma": "Prisma",
        "@prisma/client": "Prisma",
        "typeorm": "TypeORM",
        "sequelize": "Sequelize",
        "drizzle-orm": "Drizzle",
        "pg": "PostgreSQL",
        "postgres": "PostgreSQL",
        "mysql2": "MySQL",
        "sqlite3": "SQLite",
        "mongodb": "MongoDB",
        "mongoose": "MongoDB",
        "@supabase/supabase-js": "Supabase",
        "firebase": "Firebase",
        "@firebase/app": "Firebase",
        "redis": "Redis",
        "ioredis": "Redis",
    }
    for dep, name in databases.items():
        if dep in deps:
            stack.append(name)

    return stack


def _apply_template(target: Path, *, project_name: Optional[str], tech_stack: Optional[str]) -> None:
    """템플릿 파일들을 대상 프로젝트에 복사하고 placeholder를 치환한다."""

    src = TEMPLATE_ROOT
    print(f"\n{'='*60}")
    print(f"  Harness Template Apply")
    print(f"  Target: {target}")
    print(f"{'='*60}")

    # 프로젝트명 결정
    if not project_name:
        project_name = target.name
    print(f"\n  Project: {project_name}")
    if tech_stack:
        print(f"  Stack:   {tech_stack}")

    # 복사할 파일/디렉토리
    items = [
        ("CLAUDE.md", True),          # (file/dir, always_overwrite)
        ("claude/", False),           # 기존 claude/가 있으면 병합
        ("phases/", True),
        ("scripts/", True),
        ("docs/", False),             # 기존 docs/가 있으면 병합
        (".env.example", False),
        (".gitignore", False),
    ]

    for name, force in items:
        src_path = src / name
        dst_path = target / name

        if not src_path.exists():
            continue

        if dst_path.exists() and not force:
            # 병합: 디렉토리면 새 파일만 복사, 파일이면 건너뛰기
            if src_path.is_dir():
                for item in src_path.rglob("*"):
                    rel = item.relative_to(src_path)
                    dst = dst_path / rel
                    if not dst.exists():
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        if item.is_file():
                            shutil.copy2(item, dst)
                            print(f"  + {rel}")
            else:
                print(f"  ~ {name} (already exists, skipped)")
        else:
            if src_path.is_dir():
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                print(f"  + {name}/")
            else:
                shutil.copy2(src_path, dst_path)
                print(f"  + {name}")

    # 기술 스택에 맞춰 step 파일 재생성
    stack_list = _detect_tech_stack_raw(target)
    if stack_list:
        _generate_step_files(target, stack_list)

    # Placeholder 치환
    replacements = {
        "{프로젝트명}": project_name,
    }
    if tech_stack:
        replacements["{기술 스택}"] = tech_stack

    replace_files = [
        target / "CLAUDE.md",
        target / "docs" / "PRD.md",
        target / "docs" / "ARCHITECTURE.md",
        target / "docs" / "ADR.md",
        target / "phases" / "0-mvp" / "index.json",
        target / "phases" / "1-polish" / "index.json",
        target / "phases" / "maintenance" / "index.json",
    ]

    replaced_count = 0
    for fpath in replace_files:
        if not fpath.exists():
            continue
        content = fpath.read_text(encoding="utf-8")
        original = content
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        if content != original:
            fpath.write_text(content, encoding="utf-8")
            replaced_count += 1
            print(f"  ~ {fpath.relative_to(target)} (placeholder 치환)")

    # README 업데이트
    readme = target / "README.md"
    if readme.exists():
        content = readme.read_text(encoding="utf-8")
        # 기존 README가 비어있거나 "# " 만 있으면 새로 작성
        if not content.strip() or content.strip() == "# ":
            readme.write_text(
                f"# {project_name}\n\nAI 기반 개발 프로젝트.\n\n"
                f"## 빠른 시작\n\n"
                f"```bash\n"
                f"python3 scripts/execute.py 0-mvp\n"
                f"```\n\n"
                f"자세한 작업 방식은 `CLAUDE.md` 참조.\n",
                encoding="utf-8",
            )
            print(f"  + README.md")
        else:
            # 기존 내용이 있으면 하단에 하네스 링크만 추가
            if "CLAUDE.md" not in content and "scripts/execute.py" not in content:
                readme.write_text(
                    content.rstrip() + "\n\n---\n\n자세한 작업 방식은 `CLAUDE.md` 참조.\n",
                    encoding="utf-8",
                )
                print(f"  ~ README.md (harness 링크 추가)")
    else:
        (target / "README.md").write_text(
            f"# {project_name}\n\nAI 기반 개발 프로젝트.\n\n"
            f"## 빠른 시작\n\n"
            f"```bash\n"
            f"python3 scripts/execute.py 0-mvp\n"
            f"```\n\n"
            f"자세한 작업 방식은 `CLAUDE.md` 참조.\n",
            encoding="utf-8",
        )
        print(f"  + README.md")

    # Git 커밋
    print(f"\n  Git commit...")
    r = subprocess.run(
        ["git", "add", "-A"],
        cwd=str(target), capture_output=True, text=True,
    )
    if r.returncode == 0:
        r2 = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=str(target), capture_output=True, text=True,
        )
        if r2.returncode != 0:
            r3 = subprocess.run(
                ["git", "commit", "-m", "chore: harness template 적용"],
                cwd=str(target), capture_output=True, text=True,
            )
            if r3.returncode == 0:
                print(f"  ✓ committed")
            else:
                print(f"  ~ commit skipped: {r3.stderr.strip()[:100]}")
        else:
            print(f"  ~ no changes to commit")
    else:
        print(f"  ~ git repo가 아님")

    # 남은 placeholder 안내
    remaining = _count_remaining_placeholders(target)
    print(f"\n{'='*60}")
    print(f"  Template applied!")
    if remaining > 0:
        print(f"  ⚠ 남은 placeholder: {remaining}개")
        print(f"  CLAUDE.md에서 {{...}} 항목을 직접 채워주세요.")
    print(f"  다음: python3 scripts/execute.py 0-mvp")
    print(f"{'='*60}\n")


def _count_remaining_placeholders(target: Path) -> int:
    """파일에서 치환되지 않은 {placeholder} 개수를 센다."""
    count = 0
    pattern = re.compile(r"\{[^}]+\}")
    for fpath in target.rglob("*.md"):
        if any(p.name in str(fpath) for p in [target / ".git"]):
            continue
        content = fpath.read_text(encoding="utf-8")
        count += len(pattern.findall(content))
    for fpath in target.rglob("*.json"):
        if any(p.name in str(fpath) for p in [target / ".git"]):
            continue
        content = fpath.read_text(encoding="utf-8")
        count += len(pattern.findall(content))
    return count


# =========================================================================
#  StepExecutor — phase step 순차 실행
# =========================================================================

class StepExecutor:
    """Phase 디렉토리 안의 step들을 순차 실행하는 하네스."""

    MAX_RETRIES = 3
    FEAT_MSG = "feat({phase}): step {num} — {name}"
    CHORE_MSG = "chore({phase}): step {num} output"
    TZ = timezone(timedelta(hours=9))

    def __init__(self, phase_dir_name: str, *, auto_push: bool = False):
        self._root = str(TEMPLATE_ROOT)
        self._phases_dir = TEMPLATE_ROOT / "phases"
        self._phase_dir = self._phases_dir / phase_dir_name
        self._phase_dir_name = phase_dir_name
        self._top_index_file = self._phases_dir / "index.json"
        self._auto_push = auto_push

        if not self._phase_dir.is_dir():
            print(f"ERROR: {self._phase_dir} not found")
            sys.exit(1)

        self._index_file = self._phase_dir / "index.json"
        if not self._index_file.exists():
            print(f"ERROR: {self._index_file} not found")
            sys.exit(1)

        idx = self._read_json(self._index_file)
        self._project = idx.get("project", "project")
        self._phase_name = idx.get("phase", phase_dir_name)
        self._total = len(idx["steps"])
        self._rules = idx.get("rules", [])  # 사용할 규칙 파일 목록

    def run(self):
        self._print_header()
        self._check_blockers()
        self._checkout_branch()
        guardrails = self._load_guardrails()
        self._ensure_created_at()
        self._execute_all_steps(guardrails)
        self._finalize()

    # --- timestamps ---

    def _stamp(self) -> str:
        return datetime.now(self.TZ).strftime("%Y-%m-%dT%H:%M:%S%z")

    # --- JSON I/O ---

    @staticmethod
    def _read_json(p: Path) -> dict:
        return json.loads(p.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(p: Path, data: dict):
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- git ---

    def _run_git(self, *args) -> subprocess.CompletedProcess:
        cmd = ["git"] + list(args)
        return subprocess.run(cmd, cwd=self._root, capture_output=True, text=True)

    def _checkout_branch(self):
        branch = f"feat-{self._phase_name}"

        r = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        if r.returncode != 0:
            print(f"  ERROR: git을 사용할 수 없거나 git repo가 아닙니다.")
            print(f"  {r.stderr.strip()}")
            sys.exit(1)

        if r.stdout.strip() == branch:
            return

        r = self._run_git("rev-parse", "--verify", branch)
        r = self._run_git("checkout", branch) if r.returncode == 0 else self._run_git("checkout", "-b", branch)

        if r.returncode != 0:
            print(f"  ERROR: 브랜치 '{branch}' checkout 실패.")
            print(f"  {r.stderr.strip()}")
            print(f"  Hint: 변경사항을 stash하거나 commit한 후 다시 시도하세요.")
            sys.exit(1)

        print(f"  Branch: {branch}")

    def _commit_step(self, step_num: int, step_name: str):
        output_rel = f"phases/{self._phase_dir_name}/step{step_num}-output.json"
        index_rel = f"phases/{self._phase_dir_name}/index.json"

        self._run_git("add", "-A")
        self._run_git("reset", "HEAD", "--", output_rel)
        self._run_git("reset", "HEAD", "--", index_rel)

        if self._run_git("diff", "--cached", "--quiet").returncode != 0:
            msg = self.FEAT_MSG.format(phase=self._phase_name, num=step_num, name=step_name)
            r = self._run_git("commit", "-m", msg)
            if r.returncode == 0:
                print(f"  Commit: {msg}")
            else:
                print(f"  WARN: 코드 커밋 실패: {r.stderr.strip()}")

        self._run_git("add", "-A")
        if self._run_git("diff", "--cached", "--quiet").returncode != 0:
            msg = self.CHORE_MSG.format(phase=self._phase_name, num=step_num)
            r = self._run_git("commit", "-m", msg)
            if r.returncode != 0:
                print(f"  WARN: housekeeping 커밋 실패: {r.stderr.strip()}")

    # --- top-level index ---

    def _update_top_index(self, status: str):
        if not self._top_index_file.exists():
            return
        top = self._read_json(self._top_index_file)
        ts = self._stamp()
        for phase in top.get("phases", []):
            if phase.get("dir") == self._phase_dir_name:
                phase["status"] = status
                ts_key = {"completed": "completed_at", "error": "failed_at", "blocked": "blocked_at"}.get(status)
                if ts_key:
                    phase[ts_key] = ts
                break
        self._write_json(self._top_index_file, top)

    # --- guardrails & context ---

    def _load_guardrails(self) -> str:
        sections = []
        claude_md = TEMPLATE_ROOT / "CLAUDE.md"
        if claude_md.exists():
            sections.append(f"## 프로젝트 규칙 (CLAUDE.md)\n\n{claude_md.read_text()}")
        rules_dir = TEMPLATE_ROOT / "claude" / "rules"
        if rules_dir.is_dir():
            # index.json에 rules가 지정되어 있으면 해당 파일만 로드
            # 지정이 없으면 전체 로드 (하위 호환)
            rule_names = self._rules if self._rules else None
            for rule in sorted(rules_dir.glob("*.md")):
                if rule.name == "README.md":
                    continue
                if rule_names and rule.stem not in rule_names:
                    continue
                sections.append(f"## 규칙: {rule.stem}\n\n{rule.read_text()}")
        docs_dir = TEMPLATE_ROOT / "docs"
        if docs_dir.is_dir():
            for doc in sorted(docs_dir.glob("*.md")):
                sections.append(f"## {doc.stem}\n\n{doc.read_text()}")
        return "\n\n---\n\n".join(sections) if sections else ""

    @staticmethod
    def _build_step_context(index: dict) -> str:
        lines = [
            f"- Step {s['step']} ({s['name']}): {s['summary']}"
            for s in index["steps"]
            if s["status"] == "completed" and s.get("summary")
        ]
        if not lines:
            return ""
        return "## 이전 Step 산출물\n\n" + "\n".join(lines) + "\n\n"

    def _build_preamble(self, guardrails: str, step_context: str,
                        prev_error: Optional[str] = None) -> str:
        commit_example = self.FEAT_MSG.format(
            phase=self._phase_name, num="N", name="<step-name>"
        )
        retry_section = ""
        if prev_error:
            retry_section = (
                f"\n## ⚠ 이전 시도 실패 — 아래 에러를 반드시 참고하여 수정하라\n\n"
                f"{prev_error}\n\n---\n\n"
            )
        return (
            f"당신은 {self._project} 프로젝트의 개발자입니다. 아래 step을 수행하세요.\n\n"
            f"{guardrails}\n\n---\n\n"
            f"{step_context}{retry_section}"
            f"## 작업 규칙\n\n"
            f"1. 이전 step에서 작성된 코드를 확인하고 일관성을 유지하라.\n"
            f"2. 이 step에 명시된 작업만 수행하라. 추가 기능이나 파일을 만들지 마라.\n"
            f"3. 기존 테스트를 깨뜨리지 마라.\n"
            f"4. AC(Acceptance Criteria) 검증을 직접 실행하라.\n"
            f"5. /phases/{self._phase_dir_name}/index.json의 해당 step status를 업데이트하라:\n"
            f"   - AC 통과 → \"completed\" + \"summary\" 필드에 이 step의 산출물을 한 줄로 요약\n"
            f"   - {self.MAX_RETRIES}회 수정 시도 후에도 실패 → \"error\" + \"error_message\" 기록\n"
            f"   - 사용자 개입이 필요한 경우 (API 키, 인증, 수동 설정 등) → \"blocked\" + \"blocked_reason\" 기록 후 즉시 중단\n"
            f"6. 모든 변경사항을 커밋하라:\n"
            f"   {commit_example}\n\n---\n\n"
        )

    # --- Claude 호출 ---

    def _invoke_claude(self, step: dict, preamble: str) -> dict:
        step_num, step_name = step["step"], step["name"]
        step_file = self._phase_dir / f"step{step_num}.md"

        if not step_file.exists():
            print(f"  ERROR: {step_file} not found")
            sys.exit(1)

        prompt = preamble + step_file.read_text()
        result = subprocess.run(
            ["claude", "-p", "--dangerously-skip-permissions", "--output-format", "json", prompt],
            cwd=self._root, capture_output=True, text=True, timeout=1800,
        )

        if result.returncode != 0:
            print(f"\n  WARN: Claude가 비정상 종료됨 (code {result.returncode})")
            if result.stderr:
                print(f"  stderr: {result.stderr[:500]}")

        output = {
            "step": step_num, "name": step_name,
            "exitCode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr,
        }
        out_path = self._phase_dir / f"step{step_num}-output.json"
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return output

    # --- 헤더 & 검증 ---

    def _print_header(self):
        print(f"\n{'='*60}")
        print(f"  Harness Step Executor")
        print(f"  Phase: {self._phase_name} | Steps: {self._total}")
        if self._auto_push:
            print(f"  Auto-push: enabled")
        print(f"{'='*60}")

    def _check_blockers(self):
        index = self._read_json(self._index_file)
        for s in reversed(index["steps"]):
            if s["status"] == "error":
                print(f"\n  ✗ Step {s['step']} ({s['name']}) failed.")
                print(f"  Error: {s.get('error_message', 'unknown')}")
                print(f"  Fix and reset status to 'pending' to retry.")
                sys.exit(1)
            if s["status"] == "blocked":
                print(f"\n  ⏸ Step {s['step']} ({s['name']}) blocked.")
                print(f"  Reason: {s.get('blocked_reason', 'unknown')}")
                print(f"  Resolve and reset status to 'pending' to retry.")
                sys.exit(2)
            if s["status"] != "pending":
                break

    def _ensure_created_at(self):
        index = self._read_json(self._index_file)
        if "created_at" not in index:
            index["created_at"] = self._stamp()
            self._write_json(self._index_file, index)

    # --- 실행 루프 ---

    def _execute_single_step(self, step: dict, guardrails: str) -> bool:
        """단일 step 실행 (재시도 포함). 완료되면 True, 실패/차단이면 False."""
        step_num, step_name = step["step"], step["name"]
        done = sum(1 for s in self._read_json(self._index_file)["steps"] if s["status"] == "completed")
        prev_error = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            index = self._read_json(self._index_file)
            step_context = self._build_step_context(index)
            preamble = self._build_preamble(guardrails, step_context, prev_error)

            tag = f"Step {step_num}/{self._total - 1} ({done} done): {step_name}"
            if attempt > 1:
                tag += f" [retry {attempt}/{self.MAX_RETRIES}]"

            with progress_indicator(tag) as pi:
                self._invoke_claude(step, preamble)
                elapsed = int(pi.elapsed)

            index = self._read_json(self._index_file)
            status = next((s.get("status", "pending") for s in index["steps"] if s["step"] == step_num), "pending")
            ts = self._stamp()

            if status == "completed":
                for s in index["steps"]:
                    if s["step"] == step_num:
                        s["completed_at"] = ts
                self._write_json(self._index_file, index)
                self._commit_step(step_num, step_name)
                print(f"  ✓ Step {step_num}: {step_name} [{elapsed}s]")
                return True

            if status == "blocked":
                for s in index["steps"]:
                    if s["step"] == step_num:
                        s["blocked_at"] = ts
                self._write_json(self._index_file, index)
                reason = next((s.get("blocked_reason", "") for s in index["steps"] if s["step"] == step_num), "")
                print(f"  ⏸ Step {step_num}: {step_name} blocked [{elapsed}s]")
                print(f"    Reason: {reason}")
                self._update_top_index("blocked")
                sys.exit(2)

            err_msg = next(
                (s.get("error_message", "Step did not update status") for s in index["steps"] if s["step"] == step_num),
                "Step did not update status",
            )

            if attempt < self.MAX_RETRIES:
                for s in index["steps"]:
                    if s["step"] == step_num:
                        s["status"] = "pending"
                        s.pop("error_message", None)
                self._write_json(self._index_file, index)
                prev_error = err_msg
                print(f"  ↻ Step {step_num}: retry {attempt}/{self.MAX_RETRIES} — {err_msg}")
            else:
                for s in index["steps"]:
                    if s["step"] == step_num:
                        s["status"] = "error"
                        s["error_message"] = f"[{self.MAX_RETRIES}회 시도 후 실패] {err_msg}"
                        s["failed_at"] = ts
                self._write_json(self._index_file, index)
                self._commit_step(step_num, step_name)
                print(f"  ✗ Step {step_num}: {step_name} failed after {self.MAX_RETRIES} attempts [{elapsed}s]")
                print(f"    Error: {err_msg}")
                self._update_top_index("error")
                sys.exit(1)

        return False  # unreachable

    def _execute_all_steps(self, guardrails: str):
        while True:
            index = self._read_json(self._index_file)
            pending = next((s for s in index["steps"] if s["status"] == "pending"), None)
            if pending is None:
                print("\n  All steps completed!")
                return

            step_num = pending["step"]
            for s in index["steps"]:
                if s["step"] == step_num and "started_at" not in s:
                    s["started_at"] = self._stamp()
                    self._write_json(self._index_file, index)
                    break

            self._execute_single_step(pending, guardrails)

    def _finalize(self):
        index = self._read_json(self._index_file)
        index["completed_at"] = self._stamp()
        self._write_json(self._index_file, index)
        self._update_top_index("completed")

        self._run_git("add", "-A")
        if self._run_git("diff", "--cached", "--quiet").returncode != 0:
            msg = f"chore({self._phase_name}): mark phase completed"
            r = self._run_git("commit", "-m", msg)
            if r.returncode == 0:
                print(f"  ✓ {msg}")

        if self._auto_push:
            branch = f"feat-{self._phase_name}"
            r = self._run_git("push", "-u", "origin", branch)
            if r.returncode != 0:
                print(f"\n  ERROR: git push 실패: {r.stderr.strip()}")
                sys.exit(1)
            print(f"  ✓ Pushed to origin/{branch}")

        print(f"\n{'='*60}")
        print(f"  Phase '{self._phase_name}' completed!")
        print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Harness Step Executor & Template Apply",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 템플릿을 내 프로젝트에 한 번에 적용
  python3 scripts/execute.py apply /path/to/my-project --project-name MyProject --stack "Next.js, TypeScript, PostgreSQL"

  # 신규 프로젝트 MVP phase 실행
  python3 scripts/execute.py 0-mvp

  # 기존 프로젝트 유지보수
  python3 scripts/execute.py maintenance

  # 완료 후 push 포함
  python3 scripts/execute.py 0-mvp --push
        """,
    )
    subparsers = parser.add_subparsers(dest="command")

    # apply 서브커맨드
    apply_parser = subparsers.add_parser("apply", help="기존 프로젝트에 하네스 템플릿 적용")
    apply_parser.add_argument("target", help="적용할 프로젝트 루트 경로")
    apply_parser.add_argument("--project-name", default=None, help="프로젝트명 (기본: 디렉토리명)")
    apply_parser.add_argument("--stack", default=None, help="기술 스택 (미지정 시 자동 감지)")

    # execute 서브커맨드 (기본)
    exec_parser = subparsers.add_parser("execute", help="Phase step 실행")
    exec_parser.add_argument("exec_phase", help="Phase directory name")
    exec_parser.add_argument("--push", action="store_true", help="Push after completion")

    # positional 인자 (하위 호환)
    parser.add_argument("phase_dir", nargs="?", help="Phase directory name (e.g. 0-mvp)")
    parser.add_argument("--push", action="store_true", help="Push branch after completion")

    args = parser.parse_args()

    if args.command == "apply":
        target = Path(args.target).resolve()
        if not target.is_dir():
            print(f"ERROR: {target} is not a directory")
            sys.exit(1)

        stack = args.stack
        if not stack:
            detected = _detect_tech_stack(target)
            if detected:
                print(f"\n  자동 감지된 기술 스택: {detected}")
                print(f"  (직접 지정하려면 --stack 옵션 사용)")
                stack = detected

        _apply_template(target, project_name=args.project_name, tech_stack=stack)
    elif args.command == "execute":
        StepExecutor(args.exec_phase, auto_push=args.push).run()
    elif args.phase_dir:
        # 하위 호환: phase_dir이 positional로 넘어옴
        StepExecutor(args.phase_dir, auto_push=args.push).run()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
