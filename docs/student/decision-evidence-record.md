# Decision-Evidence Record (template)

Fill in one row per claim you plan to defend in your presentation. Every claim must cite a specific,
checkable source — a log line, a trace ID, a metric query, a test result.

| Claim | Source | What it proves | Limitation |
|---|---|---|---|
| e.g. "Worker concurrency is the primary bottleneck" | Task 1.4 load test, `coldline_job_queue_stream_length` over the run | Queue backlog grew steadily while completed jobs per window stayed flat | Local Docker Compose only; not validated at real 10x traffic |
