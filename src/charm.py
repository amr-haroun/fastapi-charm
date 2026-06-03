#!/usr/bin/env python3

"""Kubernetes charm for a demo app."""

import ops
import logging

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)


class FastAPIDemoCharm(ops.CharmBase):
    """Charm the service."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        framework.observe(self.on["demo-server"].pebble_ready, self._on_demo_server_pebble_ready)
        self.pebble_service_name = "fastapi-service"

    def _on_demo_server_pebble_ready(self, event: ops.PebbleReadyEvent) -> None:
        """Define and start a workload using the Pebble API."""
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Add initial Pebble config layer using the Pebble API
        container.add_layer("fastapi_demo", self._get_pebble_layer(), combine=True)
        # Make Pebble reevaluate its plan, ensuring any services are started if enabled.
        container.replan()
        # Learn more about statuses at
        # https://documentation.ubuntu.com/juju/3.6/reference/status/
        self.unit.status = ops.ActiveStatus()
        # Update the k8s clusterIP server
        self.unit.open_port(protocol="tcp", port=8000)

    def _get_pebble_layer(self) -> ops.pebble.Layer:
        """Pebble layer for the FastAPI demo services."""
        command = " ".join(
            [
                "uvicorn",
                "api_demo_server.app:app",
                "--host=0.0.0.0",
                "--port=8000",
            ]
        )
        pebble_layer: ops.pebble.LayerDict = {
            "summary": "FastAPI demo service",
            "description": "pebble config layer for FastAPI demo server",
            "services": {
                self.pebble_service_name: {
                    "override": "replace",
                    "summary": "fastapi demo",
                    "command": command,
                    "startup": "enabled",
                }
            },
        }
        return ops.pebble.Layer(pebble_layer)


if __name__ == "__main__":  # pragma: nocover
    ops.main(FastAPIDemoCharm)