"""NVIDIA GPU monitoring via nvidia-smi or nvidia-ml-py."""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class GPUStatus:
    index: int
    name: str
    utilization_pct: float
    memory_used_mb: float
    memory_total_mb: float
    temperature_c: float
    power_draw_w: float
    processes: list[dict]

    @property
    def memory_free_mb(self) -> float:
        return self.memory_total_mb - self.memory_used_mb

    @property
    def memory_utilization_pct(self) -> float:
        return (self.memory_used_mb / self.memory_total_mb) * 100 if self.memory_total_mb else 0


def query_gpus_ssh(host: str, user: str = "Admin") -> list[GPUStatus]:
    """Query GPU status on a remote host via SSH + nvidia-smi."""
    cmd = [
        "ssh",
        f"{user}@{host}",
        "nvidia-smi",
        "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            logger.error(f"nvidia-smi failed on {host}: {result.stderr}")
            return []

        gpus = []
        for line in result.stdout.strip().split("\n"):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 7:
                gpus.append(
                    GPUStatus(
                        index=int(parts[0]),
                        name=parts[1],
                        utilization_pct=float(parts[2]),
                        memory_used_mb=float(parts[3]),
                        memory_total_mb=float(parts[4]),
                        temperature_c=float(parts[5]),
                        power_draw_w=float(parts[6]),
                        processes=[],
                    )
                )
        return gpus
    except Exception as e:
        logger.error(f"Failed to query GPUs on {host}: {e}")
        return []


def query_gpus_local() -> list[GPUStatus]:
    """Query GPU status on local machine."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return []

        gpus = []
        for line in result.stdout.strip().split("\n"):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 7:
                gpus.append(
                    GPUStatus(
                        index=int(parts[0]),
                        name=parts[1],
                        utilization_pct=float(parts[2]),
                        memory_used_mb=float(parts[3]),
                        memory_total_mb=float(parts[4]),
                        temperature_c=float(parts[5]),
                        power_draw_w=float(parts[6]),
                        processes=[],
                    )
                )
        return gpus
    except FileNotFoundError:
        logger.debug("nvidia-smi not found locally")
        return []
