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
#  apply — 기존 프로젝트에 하네스 템플릿 적용
# =========================================================================

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
    apply_parser.add_argument("--stack", default=None, help="기술 스택 (예: Next.js, TypeScript, PostgreSQL)")

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
        _apply_template(target, project_name=args.project_name, tech_stack=args.stack)
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
