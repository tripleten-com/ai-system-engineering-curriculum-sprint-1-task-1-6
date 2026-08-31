# Local runtime qualification evidence

This record captures one authoring run on 2026-08-29. It supports local sizing decisions. It does
not qualify GitHub Codespaces or a student release.

## Measured run

| Measurement | Result |
|---|---:|
| No-cache API, worker, and initializer build | 15.8 s |
| Cold start through dependency-ready health checks | 13.1 s |
| API and worker restart through readiness | 13.6 s |
| History-free frozen-install and complete walkthrough | 132.8 s |
| API image | 186,872,784 bytes |
| Worker image | 181,513,613 bytes |
| Post-readiness memory sample, seven long-running containers | about 404 MiB |

The initializer completed once with exit code `0`. The runtime used seven long-running containers:
API, worker, PostgreSQL, Redis, Jaeger, Prometheus, and Grafana. The published host ports remained
API `8000`, Grafana `3000`, Prometheus `9090`, and Jaeger `16686`; temporary local overrides avoided
ports already used by another project during this authoring run.

## Boundary of this evidence

- Host: Windows Docker Desktop with local base images available.
- The no-cache build rebuilt application layers; it did not prove a cold network pull.
- Memory is one post-readiness sample, not a measured peak.
- Storage and build-cache peaks are not yet recorded.
- The run is not a fresh real Codespace, CMS-generated repository, or independent student pilot.
- The current Codespaces host requirements still need the later real-Codespaces qualification gate.

These limits prevent local speed or resource results from becoming a production, availability, or
student-workload claim.
