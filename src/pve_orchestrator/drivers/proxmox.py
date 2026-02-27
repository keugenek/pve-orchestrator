"""Proxmox VE API driver — cluster state from PVE."""

from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PVENodeStatus(BaseModel):
    node: str
    status: str  # online, offline
    cpu: Optional[float] = None  # 0.0-1.0
    maxcpu: Optional[int] = None
    mem: Optional[int] = None  # bytes used
    maxmem: Optional[int] = None  # bytes total
    uptime: Optional[int] = None


class PVEDriver:
    """Interface to Proxmox VE API via proxmoxer."""

    def __init__(self, host: str, user: str, token_name: str, token_value: str):
        self.host = host
        self.user = user
        self.token_name = token_name
        self.token_value = token_value
        self._api = None

    def connect(self):
        """Establish connection to Proxmox API."""
        try:
            from proxmoxer import ProxmoxAPI

            self._api = ProxmoxAPI(
                self.host,
                user=self.user,
                token_name=self.token_name,
                token_value=self.token_value,
                verify_ssl=False,
            )
            logger.info(f"Connected to Proxmox at {self.host}")
        except ImportError:
            logger.error("proxmoxer not installed: pip install proxmoxer requests")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Proxmox: {e}")
            raise

    @property
    def api(self):
        if self._api is None:
            self.connect()
        return self._api

    def get_nodes(self) -> list[PVENodeStatus]:
        """Get status of all Proxmox nodes."""
        raw = self.api.nodes.get()
        return [PVENodeStatus(**n) for n in raw]

    def get_vms(self, node: str) -> list[dict[str, Any]]:
        """Get all VMs on a node."""
        return self.api.nodes(node).qemu.get()

    def get_containers(self, node: str) -> list[dict[str, Any]]:
        """Get all LXC containers on a node."""
        return self.api.nodes(node).lxc.get()

    def start_vm(self, node: str, vmid: int) -> str:
        """Start a VM."""
        return self.api.nodes(node).qemu(vmid).status.start.post()

    def stop_vm(self, node: str, vmid: int) -> str:
        """Stop a VM."""
        return self.api.nodes(node).qemu(vmid).status.stop.post()

    def start_container(self, node: str, vmid: int) -> str:
        """Start an LXC container."""
        return self.api.nodes(node).lxc(vmid).status.start.post()

    def stop_container(self, node: str, vmid: int) -> str:
        """Stop an LXC container."""
        return self.api.nodes(node).lxc(vmid).status.stop.post()

    def get_node_rrddata(self, node: str, timeframe: str = "hour") -> list[dict]:
        """Get RRD monitoring data for a node."""
        return self.api.nodes(node).rrddata.get(timeframe=timeframe)

    def get_cluster_resources(self, type: Optional[str] = None) -> list[dict]:
        """Get all cluster resources (VMs, CTs, storage, nodes)."""
        params = {}
        if type:
            params["type"] = type
        return self.api.cluster.resources.get(**params)
