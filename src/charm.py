#!/usr/bin/env python3

"""Kubernetes charm for a demo app."""

import ops
import logging
import dataclasses

# Import the 'data_interfaces' library.
# The import statement omits the top-level 'lib' directory
# because 'charmcraft pack' copies its contents to the project root.
from charms.data_platform_libs.v0.data_interfaces import (
    DatabaseCreatedEvent,
    DatabaseEndpointsChangedEvent,
    DatabaseRequires,
)

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
        # The 'relation_name' comes from the 'charmcraft.yaml file'.
        # The 'database_name' is the name of the database that our application requires.
        self.database = DatabaseRequires(self, relation_name="database", database_name="names_db")
        # See https://charmhub.io/data-platform-libs/libraries/data_interfaces
        framework.observe(self.database.on.database_created, self._on_database_endpoint)
        framework.observe(self.database.on.endpoints_changed, self._on_database_endpoint)
        # Report the unit status after each event.
        framework.observe(self.on.collect_unit_status, self._on_collect_status)
    
    def _on_database_endpoint(
        self, _: DatabaseCreatedEvent | DatabaseEndpointsChangedEvent
    ) -> None:
        """Event is fired when the database is created or its endpoint is changed."""
        self._replan_workload()

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
            return
        env = self.get_app_environment()
        try:
            self.container.add_layer(
                "fastapi_demo",
                self._get_pebble_layer(config.server_port, env),
                combine=True,
            )
            logger.info("Added updated layer 'fastapi_demo' to Pebble plan")

            # Tell Pebble to incorporate the changes, including restarting the
            # service if required.
            self.container.replan()
            logger.info(f"Replanned with '{self.pebble_service_name}' service")
        except (ops.pebble.APIError, ops.pebble.ConnectionError) as e:
            logger.info("Unable to connect to Pebble: %s", e)

    def _on_demo_server_pebble_ready(self, _: ops.PebbleReadyEvent) -> None:
        self._replan_workload()

    def _get_pebble_layer(self, port: int, environment: dict[str, str]) -> ops.pebble.Layer:
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
                    "environment": environment,
                }
            },
        }
        return ops.pebble.Layer(pebble_layer)
    
    def get_app_environment(self) -> dict[str, str]:
        """Return a dictionary of environment variables for the application."""
        db_data = self.fetch_database_relation_data()
        if not db_data:
            return {}
        return {
            "DEMO_SERVER_DB_HOST": db_data["db_host"],
            "DEMO_SERVER_DB_PORT": db_data["db_port"],
            "DEMO_SERVER_DB_USER": db_data["db_username"],
            "DEMO_SERVER_DB_PASSWORD": db_data["db_password"],
        }

    def _on_collect_status(self, event: ops.CollectStatusEvent) -> None:
        try:
            self.load_config(FastAPIConfig)
        except ValueError as e:
            event.add_status(ops.BlockedStatus(str(e)))
        if not self.model.get_relation("database"):
            # We need the user to do 'juju integrate'.
            event.add_status(ops.BlockedStatus("Waiting for database relation"))
        elif not self.database.fetch_relation_data():
            # We need the charms to finish integrating.
            event.add_status(ops.WaitingStatus("Waiting for database relation"))
        try:
            status = self.container.get_service(self.pebble_service_name)
        except (ops.pebble.APIError, ops.pebble.ConnectionError, ops.ModelError):
            event.add_status(ops.MaintenanceStatus("Waiting for Pebble in workload container"))
        else:
            if not status.is_running():
                event.add_status(ops.MaintenanceStatus("Waiting for the service to start up"))
        # If nothing is wrong, then the status is active.
        event.add_status(ops.ActiveStatus())

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