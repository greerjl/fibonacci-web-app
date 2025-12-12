# Fibonacci Web App – Runbook

## Purpose

This runbook provides basic operational guidance for deploying, monitoring, and troubleshooting the Fibonacci web application in Kubernetes. It is intended for engineers responding to incidents or performing routine operational tasks.

---

## Service Overview

* **Service name:** fibonacci
* **Type:** Stateless HTTP service
* **Primary endpoint:** `GET /?n=<int>`
* **Health endpoints:**

  * `/healthz` (liveness)
  * `/readyz` (readiness)

The service computes Fibonacci sequences and returns results synchronously.

---

## Deployment

### Install

```bash
helm install fib oci://ghcr.io/<owner>/<repo>/charts/fibonacci --version <version>
```

### Upgrade

```bash
helm upgrade fib oci://ghcr.io/<owner>/<repo>/charts/fibonacci --version <version>
```

### Rollback

```bash
helm rollback fib
```

---

## Normal Operating Characteristics

* Low memory usage
* CPU usage increases with larger values of `n`
* Horizontal scaling occurs when CPU utilization exceeds the HPA target

Expected steady-state:

* Pods are Ready
* CPU usage below target threshold
* No pod restarts

---

## Health Checks

### Liveness Probe

* Path: `/healthz`
* Failure indicates the process is unhealthy
* Kubernetes will restart the pod

### Readiness Probe

* Path: `/readyz`
* Failure removes pod from Service endpoints
* Used during startup or transient failures

---

## Monitoring

### Key Signals

* Pod readiness status
* Pod restart count
* CPU utilization
* Request latency (if measured externally)

### Common Commands

```bash
kubectl get pods
kubectl describe pod <pod>
kubectl top pods
```

---

## Common Issues and Resolutions

### Pods Not Ready

**Symptoms**

* Pods stuck in `NotReady`
* Service not routing traffic

**Checks**

```bash
kubectl describe pod <pod>
```

**Likely Causes**

* Readiness probe path mismatch
* Application not listening on expected port

**Resolution**

* Verify probe paths match application endpoints
* Confirm `PORT` environment variable

---

### Pods Restarting Frequently

**Symptoms**

* Restart count increasing

**Checks**

```bash
kubectl logs <pod>
kubectl describe pod <pod>
```

**Likely Causes**

* Liveness probe failing
* Application crash due to invalid configuration

**Resolution**

* Verify liveness probe path
* Validate environment variables

---

### High CPU Usage

**Symptoms**

* HPA scaling events
* Increased latency

**Checks**

```bash
kubectl get hpa
kubectl top pods
```

**Likely Causes**

* Large `n` values
* Increased request volume

**Resolution**

* Confirm `MAX_N` is set appropriately
* Allow HPA to scale
* Increase `maxReplicas` if needed

---

### HPA Not Scaling

**Symptoms**

* CPU usage high but replica count unchanged

**Checks**

```bash
kubectl describe hpa fib-fibonacci
```

**Likely Causes**

* Metrics server not installed
* Resource requests missing or incorrect

**Resolution**

* Ensure metrics-server is running
* Verify CPU requests are set in the Deployment

---

## Logs

### View Logs

```bash
kubectl logs <pod>
```

Logs are written to stdout and include request handling output.

---

## Configuration Changes

### Update MAX_N

```bash
helm upgrade fib oci://ghcr.io/<owner>/<repo>/charts/fibonacci \
  --set env.MAX_N=5000
```

### Disable Autoscaling

```bash
helm upgrade fib oci://ghcr.io/<owner>/<repo>/charts/fibonacci \
  --set autoscaling.enabled=false
```

---

## Emergency Actions

### Scale Manually

```bash
kubectl scale deployment fib-fibonacci --replicas=1
```

### Restart Pods

```bash
kubectl rollout restart deployment fib-fibonacci
```

---

## Assumptions and Limitations

* No persistent state
* No authentication
* No rate limiting
* Designed for demonstration and controlled usage

---

## Runbook Philosophy

This runbook is intentionally lightweight. The service is designed to be simple, observable, and self-healing, minimizing the need for manual intervention.
