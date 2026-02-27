"""Task scheduler — routes tasks to optimal hardware."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from .hardware import Capability, ClusterSpec, NodeSpec
from .task import Task, TaskStatus

logger = logging.getLogger(__name__)


class Scheduler:
    """Routes tasks to the best available node based on capabilities, load, and constraints."""

    def __init__(self, cluster: ClusterSpec):
        self.cluster = cluster
        self.queue: asyncio.PriorityQueue[tuple[int, Task]] = asyncio.PriorityQueue()
        self._running_tasks: dict[str, Task] = {}

    async def submit(self, task: Task) -> Task:
        """Submit a task for scheduling."""
        task.status = TaskStatus.ROUTING

        node = self._find_best_node(task)
        if node is None:
            task.status = TaskStatus.FAILED
            task.error = f"No available node with capability: {task.type}"
            logger.warning(f"Task {task.id} failed: {task.error}")
            return task

        task.assigned_node = node.name
        task.status = TaskStatus.QUEUED
        logger.info(f"Task {task.id} ({task.type}) → {node.name}")

        # TODO: actually execute the task via executor
        return task

    def _find_best_node(self, task: Task) -> Optional[NodeSpec]:
        """Find the optimal node for a task."""
        candidates = self.cluster.nodes_with_capability(task.type)

        # Apply constraints
        if task.constraints.preferred_node:
            preferred = self.cluster.get_node(task.constraints.preferred_node)
            if preferred and preferred.online and task.type in preferred.capabilities:
                return preferred

        if task.constraints.excluded_nodes:
            candidates = [n for n in candidates if n.name not in task.constraints.excluded_nodes]

        if task.constraints.min_vram_gb:
            candidates = [
                n
                for n in candidates
                if any(
                    a.vram_gb and a.vram_gb >= task.constraints.min_vram_gb
                    for a in n.accelerators
                )
            ]

        if not candidates:
            return None

        # Warm model routing: prefer nodes that already have the model loaded
        if task.model and task.constraints.require_warm_model:
            warm = [
                n
                for n in candidates
                if any(task.model in s.models for s in n.services)
            ]
            if warm:
                candidates = warm

        # Score candidates (lower utilization = better)
        def score(node: NodeSpec) -> float:
            # Prefer nodes with lower GPU utilization
            gpu_util = 0.0
            gpu_count = 0
            for acc in node.accelerators:
                if acc.utilization_pct is not None:
                    gpu_util += acc.utilization_pct
                    gpu_count += 1
            avg_util = gpu_util / max(gpu_count, 1)

            # Bonus for warm models
            warm_bonus = 0
            if task.model:
                for svc in node.services:
                    if task.model in svc.models and svc.healthy:
                        warm_bonus = -50  # Big bonus for warm models

            return avg_util + warm_bonus

        candidates.sort(key=score)
        return candidates[0]
