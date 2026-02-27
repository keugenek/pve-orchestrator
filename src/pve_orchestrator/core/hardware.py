"""Hardware capability registry — describes what each node can do."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class AcceleratorType(str, Enum):
    NVIDIA = "nvidia"
    TENSTORRENT = "tenstorrent"
    AMD = "amd"
    INTEL = "intel"
    CPU = "cpu"


class Accelerator(BaseModel):
    type: AcceleratorType
    model: str
    count: int = 1
    vram_gb: Optional[float] = None
    # Runtime state
    utilization_pct: Optional[float] = None
    memory_used_gb: Optional[float] = None
    temperature_c: Optional[float] = None


class Capability(str, Enum):
    LLM_INFERENCE = "llm-inference"
    IMAGE_GENERATION = "image-generation"
    VIDEO_GENERATION = "video-generation"
    SPEECH_TO_TEXT = "speech-to-text"
    EMBEDDINGS = "embeddings"
    TRAINING = "training"
    PREPROCESSING = "preprocessing"
    STORAGE = "storage"


class ServiceEndpoint(BaseModel):
    """A running service on a node (e.g., vLLM, Triton, Whisper)."""

    name: str
    port: int
    protocol: str = "http"
    models: list[str] = []
    healthy: bool = False


class NodeSpec(BaseModel):
    """Hardware specification of a cluster node."""

    name: str
    host: str
    proxmox_node: Optional[str] = None  # PVE node name if managed by Proxmox
    vmid: Optional[int] = None  # VM/CT ID if running inside Proxmox

    accelerators: list[Accelerator] = []
    capabilities: list[Capability] = []
    services: list[ServiceEndpoint] = []

    cpu_cores: Optional[int] = None
    ram_gb: Optional[float] = None
    storage_tb: Optional[float] = None

    # Network
    tailscale_ip: Optional[str] = None
    lan_ip: Optional[str] = None

    # State
    online: bool = False
    power_state: str = "unknown"  # on, off, sleeping, unknown
    wol_mac: Optional[str] = None  # For Wake-on-LAN


class ClusterSpec(BaseModel):
    """Full cluster topology."""

    name: str
    proxmox_host: str
    proxmox_user: str = "root@pam"
    nodes: list[NodeSpec] = []

    def get_node(self, name: str) -> Optional[NodeSpec]:
        return next((n for n in self.nodes if n.name == name), None)

    def nodes_with_capability(self, cap: Capability) -> list[NodeSpec]:
        return [n for n in self.nodes if cap in n.capabilities and n.online]
