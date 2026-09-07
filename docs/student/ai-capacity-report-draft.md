# Coldline 10x Capacity Review (AI-Generated Draft)

**Status:** Intentionally flawed audit exercise. C01-C10 are claims to assess, not trusted findings. Use the supplied evidence pack and policy.

**C01.** The historical 0.29 seconds is pure worker service time.

**C02.** Historical XLEN values 44 and 45 prove unfinished-job backlog.

**C03.** 1.53 API requests/second is completed-worker throughput and maximum capacity.

**C04.** At the supplied 10x sensor rate, 500 bytes x 1000 readings/second gives 1800000000 MB/hour.

**C05.** At 1000 readings/second and an exception fraction of 0.012, arrival is 120 jobs/second.

**C06.** Seven days of raw readings require 43.2 GB total storage.

**C07.** Required workers = ceil(ceil(arrival x service) x 1.3 x 1.3).

**C08.** API p95 + worker p95 always equals end-to-end p95.

**C09.** These local runs justify immediate multi-region Kubernetes, a service mesh and a managed multi-region stream.

**C10.** The 10x arrival rate is an authored planning assumption, not a measured 10x run.
