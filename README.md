# FastAPI Demo Charm

A [Juju](https://juju.is) charm that deploys and operates a demo [FastAPI](https://fastapi.tiangolo.com/) web server on Kubernetes using the [Ops](https://ops.readthedocs.io/) framework.

## Overview

This charm demonstrates how to write a Kubernetes sidecar charm with Ops. It manages an OCI container running a small FastAPI application (`ghcr.io/canonical/api_demo_server`) via the [Pebble](https://documentation.ubuntu.com/pebble/) API, starting a `uvicorn` server.

The charm requires a `database` relation (`postgresql_client` interface). When integrated, it injects database connection data into the workload environment.

For observability, the charm also supports COS Lite integration: it forwards workload logs over the `logging` relation and provides `metrics-endpoint` and `grafana-dashboard` relations.

## Requirements

- [Juju](https://juju.is/docs/olm/install-juju) >= 3.6
- A Kubernetes cloud (e.g. Canonical K8s or MicroK8s)
- [Charmcraft](https://documentation.ubuntu.com/charmcraft/stable/) (to build)

## Build and Deploy

```bash
# Build the charm
charmcraft pack

# Deploy to a Kubernetes model
juju deploy ./fastapi-demo_*.charm \
  --resource demo-server-image=ghcr.io/canonical/api_demo_server:1.0.4

# Deploy PostgreSQL and integrate
juju deploy postgresql-k8s --channel 14/stable --trust
juju integrate fastapi-demo postgresql-k8s

# Optional: integrate logs with COS Lite Loki (cross-model)
# From the COS model:
#   juju offer loki:logging
# From your app model:
juju integrate fastapi-demo <cos-model>.loki
```

## Configuration

| Option      | Default | Description |
|-------------|---------|-------------|
| `log-level` | `info`  | Workload log level. Accepted values: `debug`, `info`, `warning`, `error`, `critical` |
| `server-port` | `8000` | Default port on which FastAPI is available |

## Actions

Run `get-db-info` to retrieve database connection details from the current relation.

```bash
# Host/port only
juju run fastapi-demo/0 get-db-info

# Include username/password
juju run fastapi-demo/0 get-db-info show-password=true
```

## Development

```bash
# Format and lint
tox -e format
tox -e lint

# Unit tests
tox -e unit

# Integration tests (requires a packed charm)
tox -e integration
```
