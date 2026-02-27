# PVE Orchestrator — AI-Native Cluster Orchestration for Proxmox

> Executable architecture meets intelligent infrastructure. Deploy AI workloads across heterogeneous hardware with Proxmox as the foundation — no Kubernetes required.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## The Problem

You have a home lab or small cluster with mixed hardware:
- NVIDIA GPUs (training, LLM inference, image generation)
- Tenstorrent accelerators (efficient inference, speech-to-text)
- CPUs (preprocessing, orchestration, lightweight tasks)
- FPGAs (specialized workloads)

Kubernetes is overkill. You already run Proxmox. You want an **AI agent** that understands your hardware and routes tasks to the optimal device — automatically.

## What is PVE Orchestrator?

PVE Orchestrator is an **agent-driven workload orchestrator** built on top of Proxmox VE's API. It treats your Proxmox cluster as an **executable architecture** where:

1. **Hardware is described, not configured** — declare what each node has (GPUs, accelerators, memory, storage)
2. **Tasks are intent-based** — "run Whisper on this audio" not "SSH into node X, activate venv, run script"
3. **An AI agent routes tasks** to the optimal hardware based on real-time utilization, task type, and cost
4. **Proxmox manages the VMs/CTs** — we don't replace it, we orchestrate on top of it

```
┌─────────────────────────────────────────────────┐
│              PVE Orchestrator Agent              │
│  Intent → Plan → Route → Execute → Monitor      │
├─────────────────────────────────────────────────┤
│              Proxmox VE API Layer                │
│  Nodes │ VMs │ CTs │ Storage │ Network │ GPU    │
├────────┼──────┼─────┼─────────┼─────────┼───────┤
│ Node 1 │Node 2│Node3│  NAS    │Tailscale│  ...  │
│ 3×3090 │ TT   │ CPU │  14TB   │ Overlay │       │
└────────┴──────┴─────┴─────────┴─────────┴───────┘
```

## Architecture

### Core Components

```
pve-orchestrator/
├── core/
│   ├── agent.py            # AI agent: task routing & optimization
│   ├── cluster.py          # Proxmox cluster state & topology
│   ├── scheduler.py        # Task queue & scheduling engine
│   └── hardware.py         # Hardware capability registry
├── drivers/
│   ├── proxmox.py          # Proxmox VE API driver (via proxmoxer)
│   ├── nvidia.py           # NVIDIA GPU monitoring (nvidia-smi)
│   ├── tenstorrent.py      # Tenstorrent device driver (tt-smi)
│   └── generic.py          # CPU/memory/disk monitoring
├── executors/
│   ├── container.py        # LXC container task execution
│   ├── vm.py               # VM-based task execution
│   ├── ssh.py              # Direct SSH execution (for existing VMs)
│   └── api.py              # HTTP API call execution (vLLM, Triton)
├── api/
│   ├── server.py           # REST API + WebSocket
│   └── openai_compat.py    # OpenAI-compatible API proxy
├── config/
│   └── cluster.yaml        # Cluster topology definition
├── web/                    # Dashboard (optional)
└── cli.py                  # CLI interface
```

### Hardware Registry (cluster.yaml)

```yaml
cluster:
  name: homelab
  proxmox:
    host: 192.168.0.2
    user: root@pam
    token_name: orchestrator
    token_value: <secret>

nodes:
  brian:
    host: 192.168.0.183
    type: gpu-worker
    accelerators:
      - type: nvidia
        model: RTX 3090
        count: 3
        vram_gb: 24
    capabilities:
      - llm-inference
      - image-generation
      - video-generation
      - training
    services:
      vllm:
        port: 8000
        models: [llama-3.3-70b, qwen-2.5-32b]

  pve3:
    host: 192.168.0.103
    type: storage-compute
    storage:
      - path: /mnt/nas
        size_tb: 14
        type: hdd
    capabilities:
      - storage
      - preprocessing
      - lightweight-inference

  edge-tt:
    host: 192.168.0.xxx
    type: accelerator
    accelerators:
      - type: tenstorrent
        model: wormhole-n150
        count: 1
    capabilities:
      - speech-to-text
      - small-llm-inference
      - embeddings
```

### Task Routing

```python
# User submits intent
task = Task(
    type="llm-inference",
    model="llama-3.3-70b",
    input="Explain quantum computing",
    constraints={"max_latency_ms": 5000}
)

# Agent evaluates:
# 1. Which nodes CAN run this? (capability match)
# 2. Which node SHOULD run this? (utilization, latency, cost)
# 3. Is the model already loaded? (warm routing)
# 4. Fallback options if primary is busy

result = await orchestrator.submit(task)
```

### Proxmox-Native Features

Unlike K8s-based solutions, we leverage what Proxmox already does well:

| Feature | Proxmox Native | PVE Orchestrator Adds |
|---------|---------------|----------------------|
| VM/CT management | ✅ Create, start, stop, migrate | Task-aware lifecycle |
| Live migration | ✅ Between cluster nodes | Load-triggered auto-migration |
| GPU passthrough | ✅ PCIe passthrough to VMs | Automatic GPU assignment |
| Storage | ✅ ZFS, Ceph, NFS, local | Task-aware data placement |
| Networking | ✅ VLAN, bridges, SDN | Service mesh via Tailscale |
| Monitoring | ✅ Basic metrics | AI-driven anomaly detection |
| Snapshots | ✅ VM/CT snapshots | Pre-task checkpoints |
| HA | ✅ Fencing, failover | Workload-aware failover |

### Existing Proxmox Tools We Build On

- **[proxmoxer](https://github.com/proxmoxer/proxmoxer)** — Python API wrapper (our primary interface)
- **[ProxLB](https://github.com/gyptazy/ProxLB)** — Resource scheduler & load balancer for Proxmox (inspiration for VM placement)
- **Proxmox REST API v2** — Full cluster control: nodes, VMs, CTs, storage, networking

## Key Differentiators

### vs Kubernetes
- No etcd, no kubelet, no CNI plugins, no CRDs
- Proxmox is the control plane — battle-tested, GUI included
- GPU passthrough just works (no device plugin dance)
- Perfect for 2-10 node home labs and small teams

### vs SkyPilot / Ray
- Proxmox-native (not cloud-first adapted to on-prem)
- Agent-driven routing (not just resource matching)
- Understands heterogeneous accelerators natively
- No YAML-per-job — submit intents, get results

### vs Manual SSH Scripts
- Automatic hardware discovery and health monitoring
- Warm model routing (don't reload what's already running)
- Queue management with priority and preemption
- OpenAI-compatible API — drop-in replacement for cloud

## Roadmap

### Phase 1: Foundation ✦ (current)
- [ ] Proxmox API integration (proxmoxer)
- [ ] Hardware discovery (nvidia-smi, tt-smi, lscpu)
- [ ] Cluster state model
- [ ] Basic task submission & routing
- [ ] CLI tool

### Phase 2: Intelligence
- [ ] GPU utilization monitoring (real-time)
- [ ] Warm model tracking (which model is loaded where)
- [ ] Cost-aware routing (power consumption estimation)
- [ ] OpenAI-compatible API proxy
- [ ] Task queue with priorities

### Phase 3: Automation
- [ ] Auto-scaling: spin up/down VMs based on demand
- [ ] Live migration triggers (thermal, utilization)
- [ ] Model preloading based on usage patterns
- [ ] WoL integration (wake nodes on demand, sleep when idle)
- [ ] Tenstorrent integration

### Phase 4: Agent
- [ ] LLM-powered task planning (complex multi-step workflows)
- [ ] Self-optimizing: learn from past routing decisions
- [ ] Anomaly detection and self-healing
- [ ] Multi-cluster federation

## Quick Start

```bash
# Install
pip install pve-orchestrator

# Configure cluster
pve-orch init --proxmox-host 192.168.0.2

# Discover hardware
pve-orch discover

# Submit a task
pve-orch run --type llm-inference --model llama-3.3-70b "Hello, world"

# Check cluster status
pve-orch status
```

## Tech Stack

- **Python 3.11+** — core runtime
- **proxmoxer** — Proxmox API
- **FastAPI** — REST API server
- **asyncio** — concurrent task management
- **pydantic** — config & task schemas
- **nvidia-ml-py** — GPU monitoring
- **rich** — CLI output

## Contributing

This project is in early development. We're looking for:
- Home lab enthusiasts with Proxmox clusters
- People running AI workloads on heterogeneous hardware
- Tenstorrent / AMD / Intel accelerator users

## License

Apache License 2.0

---

*Built by humans and AI agents, for humans and AI agents.*
