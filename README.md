# Coldline Task 1.6 — Held-out review and instructor defense

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/tripleten-com/ai-system-engineering-curriculum-sprint-1-task-1-6/tree/main)

## Start the system

Prerequisites are Python 3.12 and Docker with Compose v2. The supplied bootstrap supports macOS
arm64/x86-64, Windows x86-64, and Linux x86-64/aarch64, and installs pinned uv 0.11.8 under
`.tools/bin`. If your computer cannot run the stack locally, use the Codespaces button above.

On macOS and most Linux distributions the interpreter is `python3`; substitute it wherever these
commands say `python`.

```shell
python infra/scripts/bootstrap.py
./.tools/bin/uv sync --frozen
./.tools/bin/uv run --frozen poe preflight
./.tools/bin/uv run --frozen poe start
./.tools/bin/uv run --frozen poe ready
./.tools/bin/uv run --frozen poe scenario
```

PowerShell and POSIX wrappers are available under `infra/scripts/`. After uv is on `PATH`, the
shorter `uv run --frozen poe <task>` form works.

| Service | Local URL | Purpose |
|---|---|---|
| API | `http://localhost:8000` | Submit and inspect exception workflows |
| Grafana | `http://localhost:3000` | Use the focused diagnostics dashboard |
| Prometheus | `http://localhost:9090` | Query bounded metrics |
| Jaeger | `http://localhost:16686` | Inspect local traces |

Each of these ports can be overridden by setting the matching `COLDLINE_API_HOST_PORT`,
`COLDLINE_GRAFANA_HOST_PORT`, `COLDLINE_PROMETHEUS_HOST_PORT`, or `COLDLINE_JAEGER_HOST_PORT` environment
variable in your shell environment or a local `.env` file (copy `.env.example`) if a default
collides with something already running on your machine. Keep the override in place for every
`poe` command.

If you change the API port, also set `COLDLINE_API_HOST_PORT` in the shell that runs
`poe load-test`: this command does not read `.env`. Use the same port for startup and load testing.
For example, to use port 8001, run the command for your shell before starting the system:

| Shell | Set the API host port |
|---|---|
| PowerShell | `$env:COLDLINE_API_HOST_PORT = "8001"` |
| macOS/Linux (POSIX) | `export COLDLINE_API_HOST_PORT=8001` |

PostgreSQL, Redis, worker metrics, and OTLP remain inside the Compose network. Codespaces uses the
same `compose.yaml` and keeps every forwarded port private.

## Command path

For a fresh investigation, run the supplied commands in this order:

```text
poe start
poe ready
poe scenario
poe verify
```

| Command | Use |
|---|---|
| `poe unit` | Run fast isolated behavior tests |
| `poe contract` | Check interfaces, boundaries, submissions, and repository structure |
| `poe smoke` | Check the initialized running platform |
| `poe e2e` | Run the external API-to-worker workflow |
| `poe verify` | Run the public student verification path |
| `poe load-test` | Run this repository's supplied traffic profile |
| `poe reset-baseline` | Clear exception and Redis data, then restart the worker between load runs |
| `poe restart` | Restart the existing API and worker containers **without rebuilding**; run `poe start` instead after editing source |
| `poe stop` | Remove containers and the network, keeping named volumes |
| `poe reset` | Remove containers, the network, and local named volumes |

For Task 1.6, `poe verify` runs readiness, smoke tests, the end-to-end workflow, and
answer/protected-path checks.

The supplied `poe load-test` profile uses 2 users, a spawn rate of 2 users/second, and a 30-second run.
Keep the profile unchanged when comparing measurements.

## Folder map

```text
repository root/
├── docs/                Student guidance, public contracts, and fidelity notes
│   ├── contracts/       Machine-readable public contracts
│   ├── fidelity/        Local-runtime boundary notes
│   └── student/         Task guidance and submission documents
├── infra/               Local setup and runtime configuration
├── loadtest/            Supplied traffic profile and provider-latency harness
├── src/
│   ├── api/             HTTP application code
│   ├── worker/          Background application code
│   ├── domain/          Shared domain code and data contracts
│   ├── ports/           Application interfaces
│   └── adapters/        Technology-specific implementations
└── tests/
    ├── unit/            Isolated behavior checks
    ├── contract/        Interface and repository checks
    ├── smoke/           Running-platform checks
    └── e2e/             Supplied workflow checks
```

## Overview

Use the Task 1.6 lesson to decide what evidence to collect. This README covers local setup and
repository orientation; investigate the supplied system from your own run.

1. `README.md` — local setup, commands, and permitted changes.
2. `compose.yaml` — the supplied local services and startup order.
3. `docs/student/` — the Task's supporting documents; see the permitted files below.
4. `src/domain/contracts.py` and `src/ports/__init__.py` — shared data and application interfaces.
5. `src/api/use_cases.py` and `src/worker/use_cases.py` — synchronous and background application work.
6. `src/adapters/` — technology-specific implementations.
7. `tests/e2e/test_exception_workflow.py` — the external workflow checks.

The application source lives in five flat packages:

| Package | Responsibility |
|---|---|
| `api` | HTTP delivery, API use case, configuration, and composition |
| `worker` | Background processing, retries, configuration, and composition |
| `domain` | Provider-neutral contracts, state rules, identity, and redaction |
| `ports` | Exactly five visible application interfaces |
| `adapters` | PostgreSQL, Redis Streams, deterministic model, logs, and traces |

`src/api/bootstrap.py` and `src/worker/bootstrap.py` compose each process from its settings and
adapters. Process settings live in `src/api/config.py` and `src/worker/config.py`; other modules
receive settings or collaborators through function and constructor arguments.

## The five ports

Find the available interfaces in `src/ports/`. A port describes an application capability; an
adapter provides it using a concrete technology. Determine which ports are active from your own
runtime evidence rather than from this guide.

| Port | General responsibility |
|---|---|
| `ModelProvider` | Call an AI model service |
| `Retriever` | Look up relevant context or documents |
| `ObjectStore` | Store large binary objects or files |
| `JobQueue` | Publish and consume background work |
| `SecretProvider` | Read API keys and credentials |

## Test levels

| Level | Requires Compose | Main question |
|---|---:|---|
| Unit | No | Does one responsibility behave correctly, including failures? |
| Contract | Usually no | Do interfaces, schemas, paths, and dependency rules stay compatible? |
| Smoke | Yes | Did the complete local platform initialize and become observable? |
| E2E | Yes | Can an external client complete the supplied workflow? |

## Task boundary

Complete the supplied review cases, pass the single isolated protected held-out scenario, and prepare the one final instructor defense.

Only these paths are student-editable:

- `submission.yaml`
- `docs/student/decision-evidence-record.md`

Read [the evidence guide](docs/student/evidence-guide.md) and the versioned
[fixed evidence pack](docs/student/evidence-pack.json) before completing `submission.yaml`.
The sheet and its fictional sample show exact objects, values, and units. Graded
analysis comes from this supplied pack; actual local investigations remain required
and provide evidence for the final instructor defense. Keep those sources distinct.

The public verifier checks answer structure, permitted changes, and the Task's
published runtime behavior and public arithmetic checks. Protected automated answer
checks establish semantic correctness against the public fixed pack. These protected
answer checks are distinct from the single Task 1.6 held-out runtime scenario.
Deterministic CI accepts Task
answers; there is no separate instructor Task-answer grade. Green required public and protected CI opens
the next Task. Sprint completion requires all six Task PRs CI-green and one final
instructor defense covering empirical reasoning, uncertainty, alternatives, and judgment.

Task 1.6 also runs the Sprint's single isolated protected held-out telemetry/capacity
scenario through the published interface on the supplied trusted default-branch runtime.
It is a runtime regression check, independent of candidate YAML answers and Markdown;
it does not assess student diagnostic judgment. Its result is separate from public CI; a
missing or skipped check is not a pass. Keep protected workflows and evaluator code
unchanged. The Markdown record prepares the final defense and has no separate
instructor answer grade; automated answer acceptance does not certify its prose.

### Student walkthrough

Analyze the fixed review pack in `submission.yaml`. Prepare `docs/student/decision-evidence-record.md` using your own traces, repairs, repeated baseline experiments, controlled provider-delay run, and capacity reasoning. Label supplied reference data separately. Run the public check, open the PR, confirm the single protected held-out result, and defend the empirical evidence and judgment within 10 minutes.

Run `./.tools/bin/uv run --frozen poe verify` from the repository root before
submitting a feature-branch PR against `main`. See the course Task lesson for the
three-Step walkthrough and exact matching acceptance/self-review criteria.

## Operational limits

This local system has no user authentication, authorization, TLS termination, or production secret
store. The Compose PostgreSQL password is a local-only non-secret credential. Never place real
credentials, personal data, or production records in this repository.

Named volumes preserve local PostgreSQL, Redis, Prometheus, Grafana, and Jaeger state across
`poe stop`. The `poe reset` command deletes that state. This topology makes no backup,
replication, high-availability, disaster-recovery, capacity, latency-SLO, or availability claim.
See [JobQueue fidelity](docs/fidelity/JobQueue.md) and
[ModelProvider fidelity](docs/fidelity/ModelProvider.md) for the active adapter boundaries. The
[local runtime evidence](docs/fidelity/local-runtime.md) records the current measurement and its
qualification limits.
