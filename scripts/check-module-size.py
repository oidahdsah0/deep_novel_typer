#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Rule:
  key: str
  label: str
  limit: int


RULES = {
  "react_page": Rule("react_page", "React 页面入口", 400),
  "react_component": Rule("react_component", "React 组件", 250),
  "hook": Rule("hook", "Hook", 250),
  "css": Rule("css", "领域 CSS", 500),
  "backend_service": Rule("backend_service", "后端 Service", 450),
  "repository": Rule("repository", "Repository", 350),
  "schema": Rule("schema", "Schema", 300),
  "test": Rule("test", "测试文件", 500),
  "backend_support": Rule("backend_support", "后端支撑模块", 450),
  "frontend_support": Rule("frontend_support", "前端支撑模块", 250),
}


# Current refactor baseline. Items here are known debt and may pass only while
# they do not grow beyond the recorded line count. Remove entries as files are
# split and fall back under their rule limit.
BASELINE_DEBT = {
  "frontend/features/workspace/hooks/useChapterTreeActions.ts": 280,
}


SKIP_DIRS = {
  ".git",
  ".next",
  ".test-build",
  "__pycache__",
  "node_modules",
  ".pytest_cache",
}


def main() -> int:
  parser = argparse.ArgumentParser(
    description="Check module line-count discipline with current refactor debt baseline."
  )
  parser.add_argument(
    "--show-all",
    action="store_true",
    help="Print every checked file, not only violations and baseline debt.",
  )
  parser.add_argument(
    "--baseline",
    action="store_true",
    help="Print the current baseline debt list and exit.",
  )
  args = parser.parse_args()

  if args.baseline:
    print_baseline()
    return 0

  checked: list[tuple[str, Rule, int]] = []
  violations: list[str] = []
  grown_baseline: list[str] = []
  baseline_debt: list[str] = []
  retired_baseline: list[str] = []

  for path in iter_files():
    rel = path.relative_to(ROOT).as_posix()
    rule = classify(rel)
    if rule is None:
      continue
    lines = count_lines(path)
    checked.append((rel, rule, lines))
    baseline_limit = BASELINE_DEBT.get(rel)

    if lines <= rule.limit:
      if baseline_limit is not None:
        retired_baseline.append(
          f"{rel} ({lines}/{rule.limit}) 已回到纪律线内，可从 BASELINE_DEBT 移除。"
        )
      elif args.show_all:
        print(f"ok       {lines:4d}/{rule.limit:<4d} {rule.label} {rel}")
      continue

    if baseline_limit is None:
      violations.append(
        f"{rel} 为 {lines} 行，超过 {rule.label} 上限 {rule.limit} 行，且不在基线内。"
      )
      continue

    if lines > baseline_limit:
      grown_baseline.append(
        f"{rel} 为 {lines} 行，超过基线 {baseline_limit} 行；历史债务不能继续增长。"
      )
      continue

    baseline_debt.append(
      f"{rel} 为 {lines} 行，超过 {rule.label} 上限 {rule.limit} 行；基线允许上限 {baseline_limit} 行。"
    )

  print(f"Checked {len(checked)} files.")
  if baseline_debt:
    print("\nBaseline debt:")
    for item in baseline_debt:
      print(f"  - {item}")
  if retired_baseline:
    print("\nBaseline entries ready to retire:")
    for item in retired_baseline:
      print(f"  - {item}")
  if violations or grown_baseline:
    print("\nModule size check failed:")
    for item in [*violations, *grown_baseline]:
      print(f"  - {item}")
    return 1

  print("\nModule size check passed.")
  return 0


def print_baseline() -> None:
  print("Current baseline debt:")
  for rel, limit in sorted(BASELINE_DEBT.items()):
    print(f"  - {rel}: {limit}")


def iter_files():
  roots = [ROOT / "frontend", ROOT / "backend"]
  for root in roots:
    if not root.exists():
      continue
    for path in root.rglob("*"):
      if not path.is_file():
        continue
      if any(part in SKIP_DIRS for part in path.parts):
        continue
      if path.suffix not in {".css", ".py", ".ts", ".tsx"}:
        continue
      yield path


def classify(rel: str) -> Rule | None:
  path = Path(rel)
  name = path.name
  parts = path.parts

  if rel.startswith("frontend/"):
    if name.endswith(".css"):
      return RULES["css"]
    if rel.startswith("frontend/app/") and name in {"page.tsx", "layout.tsx"}:
      return RULES["react_page"]
    if name.endswith("Client.tsx"):
      return RULES["react_page"]
    if "/hooks/" in rel and name.endswith(".ts"):
      return RULES["hook"]
    if name.endswith(".tsx"):
      return RULES["react_component"]
    if rel.startswith("frontend/lib/api/") and name.endswith(".ts"):
      return RULES["frontend_support"]
    if rel.startswith("frontend/features/") and name.endswith(".ts"):
      return RULES["frontend_support"]
    return None

  if rel.startswith("backend/tests/") and name.endswith(".py"):
    return RULES["test"]

  if rel.startswith("backend/app/Schemas/") and name.endswith(".py"):
    return RULES["schema"]

  if name == "repository.py" and name.endswith(".py"):
    return RULES["repository"]

  if rel.startswith("backend/app/Services/") and name.endswith(".py"):
    if name.endswith("_service.py") or name == "service.py":
      return RULES["backend_service"]
    return RULES["backend_support"]

  if rel.startswith("backend/app/Utils/") and name.endswith(".py"):
    return RULES["backend_support"]

  return None


def count_lines(path: Path) -> int:
  with path.open("r", encoding="utf-8", errors="replace") as file:
    return sum(1 for _ in file)


if __name__ == "__main__":
  raise SystemExit(main())
