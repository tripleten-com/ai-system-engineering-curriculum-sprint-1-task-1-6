"""Coldline — Task 1.1.

===================

File:              tests/contract/authoring.py
Component:         Authoring and export verifier
Purpose:           Checks repository boundaries that student tests must not own.
Interacts With:    Source packages, Compose, Codespaces, schemas, and uv.lock
Sprint/Task:       Sprint 1 — Project 1 / Task 1.1
Concepts:          Dependency direction, identity parity, export hygiene
Tools:             Python 3.12, AST, uv, Docker Compose YAML
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_CONTENT_DIRECTORIES = {"docs", "infra", "src", "tests", "loadtest"}
EXPECTED_SOURCE_PACKAGES = {"adapters", "api", "domain", "ports", "worker"}
EXPECTED_PORTS = {"JobQueue", "ModelProvider", "ObjectStore", "Retriever", "SecretProvider"}
EXPECTED_SERVICES = {
    "api",
    "grafana",
    "initializer",
    "jaeger",
    "postgres",
    "prometheus",
    "redis",
    "worker",
}
IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tools",
    ".venv",
    "__pycache__",
}


def main() -> int:
    """Run every author-owned check and report all failures together.

    Returning every failure in one run keeps review cycles short. The student
    verifier stays smaller and checks only the published Task contract.
    """
    files = _authored_files()
    failures: list[str] = []
    failures.extend(_check_layout())
    failures.extend(_check_placeholders(files))
    failures.extend(_check_publication_tokens(files))
    failures.extend(_check_nested_git())
    failures.extend(_check_ports())
    failures.extend(_check_compose())
    failures.extend(_check_container_policy())
    failures.extend(_check_state_contract())
    failures.extend(_check_service_identities())
    failures.extend(_check_dependency_directions(files))
    failures.extend(_check_configuration_ownership(files))
    failures.extend(_check_submission_schema())
    failures.extend(_check_bootstrap_target())
    failures.extend(_check_markdown_links(files))
    failures.extend(_check_secrets(files))
    failures.extend(_check_lock())
    if failures:
        print("Author verification failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("Author verification passed: structure, boundaries, pins, and export hygiene are valid.")
    return 0


def _authored_files() -> list[Path]:
    """Return source-controlled candidates while ignoring local tool output."""
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not any(part in IGNORED_PARTS for part in path.parts)
        and path.suffix != ".pyc"
    ]


def _check_layout() -> list[str]:
    """Keep the visible repository and Python source trees easy to scan."""
    visible = {
        path.name
        for path in ROOT.iterdir()
        if path.is_dir() and not path.name.startswith(".") and _contains_authored_file(path)
    }
    source_packages = {
        path.name
        for path in (ROOT / "src").iterdir()
        if path.is_dir() and _contains_authored_file(path)
    }
    failures: list[str] = []
    if visible != EXPECTED_CONTENT_DIRECTORIES:
        failures.append(
            f"visible content directories differ: expected {sorted(EXPECTED_CONTENT_DIRECTORIES)}, "
            f"got {sorted(visible)}"
        )
    if source_packages != EXPECTED_SOURCE_PACKAGES:
        failures.append(
            f"source packages differ: expected {sorted(EXPECTED_SOURCE_PACKAGES)}, "
            f"got {sorted(source_packages)}"
        )
    return failures


def _contains_authored_file(directory: Path) -> bool:
    """Ignore empty folders and stale Python caches left by local execution."""
    return any(
        path.is_file()
        and not any(part in IGNORED_PARTS for part in path.parts)
        and path.suffix != ".pyc"
        for path in directory.rglob("*")
    )


def _check_placeholders(files: list[Path]) -> list[str]:
    """Reject temporary placeholders and restricted-looking export paths."""
    failures: list[str] = []
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        lowered = relative.lower()
        if path.name == ".gitkeep":
            failures.append(f"placeholder remains: {relative}")
        if "localstack" in lowered:
            failures.append(f"LocalStack path is forbidden in Task 1.1: {relative}")
        if any(part in lowered for part in ("solution", "held-out", "evaluator", "instructor")):
            failures.append(f"restricted-looking path is forbidden: {relative}")
    return failures


def _check_publication_tokens(files: list[Path]) -> list[str]:
    """Allow only the one CMS-owned URL token that publication must replace."""
    found: set[tuple[str, str]] = set()
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(ROOT).as_posix()
        found.update((relative, token) for token in re.findall(r"(?<!\$)\{\{[^{}]+\}\}", text))
    # Build the marker in parts so this checker does not match its own source.
    export_token = (chr(123) * 2) + "CODESPACES_URL" + (chr(125) * 2)
    expected = {("README.md", export_token)}
    if found != expected:
        return [f"publication token allowlist mismatch: {sorted(found)}"]
    return []


def _check_nested_git() -> list[str]:
    """Reject nested repository metadata inside the future export root."""
    nested = [path for path in ROOT.rglob(".git") if path.parent.resolve() != ROOT.resolve()]
    return [f"nested Git metadata is forbidden: {path.relative_to(ROOT)}" for path in nested]


def _check_ports() -> list[str]:
    """Confirm that src/ports exposes exactly the five accepted interfaces."""
    ports = {
        node.name
        for path in (ROOT / "src/ports").glob("*.py")
        for node in _parse(path).body
        if isinstance(node, ast.ClassDef) and node.name != "Protocol"
    }
    failures: list[str] = []
    if ports != EXPECTED_PORTS:
        failures.append(
            f"five-port contract mismatch: expected {sorted(EXPECTED_PORTS)}, got {sorted(ports)}"
        )
    for path in (ROOT / "src").rglob("*.py"):
        if path.parent == ROOT / "src/ports":
            continue
        duplicates = {
            node.name
            for node in _parse(path).body
            if isinstance(node, ast.ClassDef) and node.name in EXPECTED_PORTS
        }
        if duplicates:
            failures.append(
                f"port interface redefined outside src/ports: "
                f"{path.relative_to(ROOT)} ({sorted(duplicates)})"
            )
    return failures


def _check_service_identities() -> list[str]:
    """Align process names, import roots, Compose services, and telemetry names."""
    failures: list[str] = []
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if project["project"]["name"] != "coldline-task-1-1":
        failures.append("root distribution identity must be coldline-task-1-1")

    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    for service, telemetry_name in {"api": "coldline-api", "worker": "coldline-worker"}.items():
        if service not in compose["services"]:
            failures.append(f"Compose identity is missing for {service}")
        config_text = (ROOT / "src" / service / "config.py").read_text(encoding="utf-8")
        if f'service_name: str = "{telemetry_name}"' not in config_text:
            failures.append(f"telemetry identity mismatch for {service}")
    return failures


def _check_compose() -> list[str]:
    """Confirm the bounded runtime roster, profiles, and public ports."""
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))
    services = set(compose["services"])
    failures: list[str] = []
    if services != EXPECTED_SERVICES:
        failures.append(f"Compose service roster mismatch: {sorted(services)}")

    published: set[int] = set()
    for definition in compose["services"].values():
        for mapping in definition.get("ports", []):
            match = re.search(r":-(\d+)}", str(mapping))
            published.add(
                int(match.group(1)) if match else int(str(mapping).split(":", maxsplit=1)[0])
            )
    if published != {3000, 8000, 9090, 16686}:
        failures.append(f"published port contract mismatch: {sorted(published)}")
    if "localstack" in json.dumps(compose).lower():
        failures.append("Compose must not configure LocalStack in Sprint 1")
    for service in ("jaeger", "prometheus", "grafana"):
        if compose["services"][service].get("profiles") != ["observability"]:
            failures.append(f"{service} must belong to the observability Compose profile")

    devcontainer = json.loads(
        (ROOT / ".devcontainer/devcontainer.json").read_text(encoding="utf-8")
    )
    if set(devcontainer["forwardPorts"]) != published:
        failures.append("Codespaces forwarded ports do not match Compose public ports")
    attributes = devcontainer.get("portsAttributes", {})
    if {int(port) for port in attributes} != published:
        failures.append("Codespaces port attributes do not match forwarded ports")
    for port, attribute in attributes.items():
        if attribute.get("visibility") != "private":
            failures.append(f"Codespaces port {port} must remain private")
    return failures


def _check_container_policy() -> list[str]:
    """Keep the API and worker runtime images explicitly unprivileged."""
    failures: list[str] = []
    for service in ("api", "worker"):
        dockerfile = ROOT / "infra/containers" / f"{service}.Dockerfile"
        text = dockerfile.read_text(encoding="utf-8")
        if "\nUSER coldline\n" not in text:
            failures.append(f"{service} runtime image must declare USER coldline")
    return failures


def _check_state_contract() -> list[str]:
    """Keep the PostgreSQL constraint aligned with the domain state enum."""
    module = _parse(ROOT / "src/domain/contracts.py")
    state_class = next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "ExceptionState"
    )
    contract_states = {
        node.value.value
        for node in state_class.body
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }
    sql = (ROOT / "infra/postgres/001_opening_checkpoint.sql").read_text(encoding="utf-8")
    match = re.search(r"state IN \(([^)]+)\)", sql)
    sql_states = set(re.findall(r"'([^']+)'", match.group(1))) if match else set()
    if sql_states != contract_states:
        return [
            "PostgreSQL state constraint differs from ExceptionState: "
            f"{sorted(sql_states)} != {sorted(contract_states)}"
        ]
    return []


def _check_dependency_directions(files: list[Path]) -> list[str]:
    """Reject imports that cross the inward-pointing source boundaries."""
    failures: list[str] = []
    provider_modules = ("asyncpg", "boto3", "botocore", "fastapi", "redis", "sqlalchemy")
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix != ".py" or not relative.startswith("src/"):
            continue
        package = relative.split("/", maxsplit=2)[1]
        imports = _imports(_parse(path))
        if package == "domain" and any(
            name == boundary or name.startswith(f"{boundary}.")
            for name in imports
            for boundary in ("adapters", "api", "ports", "worker")
        ):
            failures.append(f"domain imports outward: {relative}")
        if package == "ports" and any(
            name == boundary or name.startswith(f"{boundary}.")
            for name in imports
            for boundary in ("adapters", "api", "worker")
        ):
            failures.append(f"ports import outward: {relative}")
        if package in {"domain", "ports"} and any(
            name == provider or name.startswith(f"{provider}.")
            for name in imports
            for provider in provider_modules
        ):
            failures.append(f"{package} imports a provider or framework: {relative}")
        if package == "adapters" and any(
            name == service or name.startswith(f"{service}.")
            for name in imports
            for service in ("api", "worker")
        ):
            failures.append(f"adapters import a service: {relative}")
        if package == "api" and any(
            name == "worker" or name.startswith("worker.") for name in imports
        ):
            failures.append(f"API imports worker code: {relative}")
        if package == "worker" and any(
            name == "api" or name.startswith("api.") for name in imports
        ):
            failures.append(f"worker imports API code: {relative}")

    collaborators = _parse(ROOT / "src/domain/repositories.py")
    collaborator_names = {
        node.name for node in collaborators.body if isinstance(node, ast.ClassDef)
    }
    if collaborator_names != {"ExceptionRepository", "StateConflict"}:
        failures.append(f"internal collaborator allowlist mismatch: {sorted(collaborator_names)}")
    return failures


def _check_configuration_ownership(files: list[Path]) -> list[str]:
    """Keep direct runtime environment reads in each process config module."""
    allowed = {"src/api/config.py", "src/worker/config.py"}
    failures: list[str] = []
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix != ".py" or not relative.startswith("src/"):
            continue
        text = path.read_text(encoding="utf-8")
        if ("os.environ" in text or "os.getenv" in text) and relative not in allowed:
            failures.append(f"runtime environment read outside service config.py: {relative}")
    return failures


def _check_submission_schema() -> list[str]:
    """Confirm the answer schema exposes one direct answers mapping."""
    schema = json.loads(
        (ROOT / "docs/contracts/submission.schema.json").read_text(encoding="utf-8")
    )
    if schema.get("required") != ["answers"] or set(schema.get("properties", {})) != {"answers"}:
        return ["submission schema must expose exactly one top-level answers mapping"]
    return []


def _check_bootstrap_target() -> list[str]:
    """Keep the pinned uv binary at the root path used by every wrapper and workflow."""
    bootstrap = (ROOT / "infra/scripts/bootstrap.py").read_text(encoding="utf-8")
    if 'Path(__file__).resolve().parents[2] / ".tools" / "bin"' not in bootstrap:
        return ["bootstrap must install uv below the Task root .tools/bin directory"]
    return []


def _check_markdown_links(files: list[Path]) -> list[str]:
    """Resolve local Markdown links before a history-free export removes context."""
    failures: list[str] = []
    pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    for path in files:
        if path.suffix.lower() != ".md":
            continue
        for target in pattern.findall(path.read_text(encoding="utf-8")):
            target = target.strip().strip("<>").split("#", maxsplit=1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                failures.append(f"broken Markdown link in {path.relative_to(ROOT)}: {target}")
    return failures


def _check_secrets(files: list[Path]) -> list[str]:
    """Reject common private-key and cloud-token shapes from the student-safe tree."""
    patterns = {
        "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
        "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    }
    failures: list[str] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in patterns.items():
            if pattern.search(text):
                failures.append(f"possible {label} in {path.relative_to(ROOT)}")
    return failures


def _check_lock() -> list[str]:
    """Confirm uv can resolve the committed lock without changing it."""
    executable = ROOT / ".tools" / "bin" / ("uv.exe" if sys.platform == "win32" else "uv")
    try:
        result = subprocess.run(
            [executable, "lock", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return [f"pinned uv is missing at {executable.relative_to(ROOT)}; run bootstrap first"]
    return [] if result.returncode == 0 else [result.stderr.strip() or "uv.lock is stale"]


def _parse(path: Path) -> ast.Module:
    """Parse one Python module for boundary checks."""
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imports(module: ast.Module) -> set[str]:
    """Collect absolute import roots from one syntax tree."""
    names: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


if __name__ == "__main__":
    raise SystemExit(main())
