"""CLI interface for PVE Orchestrator."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="pve-orch",
    help="AI-native cluster orchestration for Proxmox VE",
)
console = Console()


@app.command()
def status():
    """Show cluster status."""
    console.print("[bold]PVE Orchestrator[/bold] v0.1.0\n")
    console.print("[yellow]⚠ Not connected to a cluster yet.[/yellow]")
    console.print("Run [bold]pve-orch init[/bold] to configure your Proxmox connection.")


@app.command()
def init(
    proxmox_host: str = typer.Option(..., prompt="Proxmox host"),
    user: str = typer.Option("root@pam", prompt="API user"),
):
    """Initialize cluster configuration."""
    console.print(f"Connecting to Proxmox at [bold]{proxmox_host}[/bold]...")
    # TODO: validate connection, discover nodes, write config
    console.print("[green]✓[/green] Configuration saved to cluster.yaml")


@app.command()
def discover():
    """Discover hardware across cluster nodes."""
    console.print("[bold]Discovering hardware...[/bold]\n")
    # TODO: SSH into each node, run nvidia-smi / tt-smi / lscpu
    console.print("[yellow]⚠ Not implemented yet.[/yellow]")


@app.command()
def nodes():
    """List cluster nodes and their status."""
    table = Table(title="Cluster Nodes")
    table.add_column("Node", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("GPUs")
    table.add_column("Utilization")
    table.add_column("Capabilities")

    # TODO: populate from cluster state
    table.add_row("brian", "🟢 online", "3× RTX 3090", "12%", "llm, img-gen, training")
    table.add_row("pve3", "🟢 online", "—", "—", "storage, preprocess")
    table.add_row("edge-tt", "🔴 offline", "1× Wormhole", "—", "stt, embeddings")

    console.print(table)


@app.command()
def run(
    task_type: str = typer.Argument(..., help="Task type (e.g., llm-inference)"),
    input_text: str = typer.Argument("", help="Input text"),
    model: str = typer.Option(None, "--model", "-m", help="Model name"),
    node: str = typer.Option(None, "--node", "-n", help="Force specific node"),
):
    """Submit a task to the orchestrator."""
    console.print(f"Submitting [bold]{task_type}[/bold] task...")
    if model:
        console.print(f"  Model: {model}")
    if node:
        console.print(f"  Target: {node}")
    # TODO: create Task, submit to scheduler
    console.print("[yellow]⚠ Not implemented yet.[/yellow]")


if __name__ == "__main__":
    app()
