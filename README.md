# FastAPI Demo Charm

A [Juju](https://juju.is) charm that deploys and operates a demo [FastAPI](https://fastapi.tiangolo.com/) web server on Kubernetes using the [Ops](https://ops.readthedocs.io/) framework.

## Overview

This charm demonstrates how to write a Kubernetes sidecar charm with Ops. It manages an OCI container running a small FastAPI application (`ghcr.io/canonical/api_demo_server`) via the [Pebble](https://documentation.ubuntu.com/pebble/) API, starting a `uvicorn` server on port 8000.

## Requirements

- [Juju](https://juju.is/docs/olm/install-juju) >= 3.6
- A Kubernetes cloud (e.g. MicroK8s)
- [Charmcraft](https://documentation.ubuntu.com/charmcraft/stable/) (to build)

## Build and Deploy

```bash
# Build the charm
charmcraft pack

# Deploy to a Kubernetes model
juju deploy ./fastapi-demo_*.charm \
  --resource demo-server-image=ghcr.io/canonical/api_demo_server:1.0.4
```

## Configuration

| Option      | Default | Description |
|-------------|---------|-------------|
| `log-level` | `info`  | Gunicorn log level. Accepted values: `debug`, `info`, `warning`, `error`, `critical` |

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