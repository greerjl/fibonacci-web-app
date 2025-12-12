# Fibonacci Web Server
Simple HTTP service that returns the first `n` Fibonacci numbers.

## Run locally
```bash
cd python
python -m pip install --upgrade pip
python -m pip install -r requirements.txt  # empty, stdlib only
python main.py
```
Defaults: `PORT=8000`, `HOST=0.0.0.0`, `MAX_N=10000`.

or as Docker:
```bash
    docker build -t fib-ui:local python
    docker run -p 8000:8000 fib-ui:local
```

## API
- `GET /fib?n=<n>` returns JSON: `{"n": 6, "sequence": [0,1,1,2,3,5]}`
- `GET /healthz`, `GET /readyz` return `{"status":"ok"}` for probes
- `GET /ui` serves a minimal browser front-end

## Tests and checks
```bash
cd python
python -m pip install -r requirements-dev.txt
pytest -q
ruff check .
```
Quick verification: `curl "http://localhost:8000/fib?n=6"`.

## Docker
```bash
docker build -t fib-app:local python
docker run -p 8000:8000 fib-app:local
```

### Build and push (example: GHCR)
```bash
IMAGE=ghcr.io/<owner>/<repo>/fib-app:v0.1.0
docker build -t "$IMAGE" python
docker push "$IMAGE"
```
Set `image.repository`/`image.tag` in Helm values to deploy.

## Helm (chart/)
- Templates render with `helm template fib ./chart`; HPA optional via `--set autoscaling.enabled=true`.
- Probes point to `/healthz` and `/readyz`.
- Deploy to Kubernetes: `helm upgrade --install fib ./chart --set image.repository=ghcr.io/<owner>/<repo>/fib-app --set image.tag=v0.1.0`

## CI
GitHub Actions workflow runs ruff, yamllint, hadolint, pytest, Helm template checks, and Docker build + Trivy scan (`.github/workflows/build.yml`).

## Observability
- Health/readiness: `/healthz`, `/readyz`
- Logging: plain stdout logs (see `GetFibs.log_message`); wire to your log collector.
- Metrics/tracing: no-ops by default; easiest drop-in is sidecar/agent (e.g., OpenTelemetry) scraping container logs or instrumenting `fibonacci_first_n` if needed.

## Scalability & ops notes
- Stateless HTTP service; horizontal scale via Kubernetes `replicas` or HPA (`chart/values.yaml`).
- Tune resources: set `resources.requests/limits` in Helm values; defaults are unset.
- Input guardrails: `MAX_N` env caps work per request; adjust for CPU budget.

## Incident response basics
- Detect: hook liveness/readiness to Kubernetes probes; add 5xx alert on ingress and log volume anomaly alerts.
- Recover: roll pods (`kubectl rollout restart deploy/fib`), scale up (`kubectl scale deploy/fib --replicas=N`), or redeploy new image tags via Helm.
- Verify: hit `/healthz` and send a sample `GET /fib?n=6` after changes.
