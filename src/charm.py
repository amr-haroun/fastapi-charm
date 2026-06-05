#!/usr/bin/env python3

"""Kubernetes charm for a demo app."""

import ops
import logging
import dataclasses

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)


class FastAPIDemoCharm(ops.CharmBase):
    """Charm the service."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)
        framework.observe(self.on["demo-server"].pebble_ready, self._on_demo_server_pebble_ready)
        self.pebble_service_name = "fastapi-service"
        framework.observe(self.on.config_changed, self._on_config_changed)
        # See 'containers' in charmcraft.yaml.
        self.container = self.unit.get_container("demo-server")
    
    def _on_config_changed(self, _: ops.ConfigChangedEvent) -> None:
        self._replan_workload()

    def _replan_workload(self) -> None:
        """Define and start a workload using the Pebble API.

        You'll need to specify the right entrypoint and environment
        configuration for your specific workload. Tip: you can see the
        standard entrypoint of an existing container using docker inspect
        Learn more about interacting with Pebble at
            https://documentation.ubuntu.com/ops/latest/reference/pebble/
        Learn more about Pebble layers at
            https://documentation.ubuntu.com/pebble/how-to/use-layers/
        """
        # Learn more about statuses at
        # https://documentation.ubuntu.com/juju/3.6/reference/status/
        self.unit.status = ops.MaintenanceStatus("Assembling Pebble layers")
        try:
            config = self.load_config(FastAPIConfig)
        except ValueError as e:
            logger.error("Configuration error: %s", e)
            self.unit.status = ops.BlockedStatus(str(e))
            return
        try:
            self.container.add_layer(
                "fastapi_demo", self._get_pebble_layer(config.server_port), combine=True
            )
            logger.info("Added updated layer 'fastapi_demo' to Pebble plan")

            # Tell Pebble to incorporate the changes, including restarting the
            # service if required.
            self.container.replan()
            logger.info(f"Replanned with '{self.pebble_service_name}' service")

            self.unit.status = ops.ActiveStatus()
        except (ops.pebble.APIError, ops.pebble.ConnectionError) as e:
            logger.info("Unable to connect to Pebble: %s", e)
            self.unit.status = ops.MaintenanceStatus("Waiting for Pebble in workload container")

    def _on_demo_server_pebble_ready(self, _: ops.PebbleReadyEvent) -> None:
        self._replan_workload()

    def _get_pebble_layer(self) -> ops.pebble.Layer:
        """Pebble layer for the FastAPI demo services."""
        command = " ".join(
            [
                "uvicorn",
                "api_demo_server.app:app",
                "--host=0.0.0.0",
                f"--port={port}",
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

@dataclasses.dataclass(frozen=True, kw_only=True)
class FastAPIConfig:
    """Configuration for the FastAPI demo charm."""

    server_port: int = 8000
    """Default port on which FastAPI is available."""

    def __post_init__(self):
        """Validate the configuration."""
        if self.server_port == 22:
            raise ValueError("Invalid port number, 22 is reserved for SSH")
        
if __name__ == "__main__":  # pragma: nocover
    ops.main(FastAPIDemoCharm)