"""
visualize.py - Matplotlib-based visual analysis for CFS Simulator.

Generates 4 publication-quality visualization figures saved into `output/`:
1. Gantt Chart (`output/gantt_chart.png`): Timeline of task execution per CPU core.
2. Vruntime Convergence Graph (`output/vruntime_convergence.png`): Process vruntime progression over time.
3. CPU Load Balancing Heatmap (`output/cpu_load_heatmap.png`): Per-CPU load intensity over simulation time.
4. Fairness Index Trend (`output/fairness_trend.png`): Evolution of Jain's Fairness Index over time.
"""

import os
from datetime import datetime
from typing import List, Dict, Tuple
import matplotlib
matplotlib.use('Agg')  # Non-interactive background renderer
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

from cfs_simulator.scheduler import CFSScheduler

# Output directory path (resolved relative to project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")


def ensure_output_dir():
    """Ensures output directory exists."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)


def merge_gantt_log(gantt_log: List[Tuple[float, float, int, str]], max_merge_duration: float = 10.0) -> List[Tuple[float, float, int, str]]:
    """
    Merges contiguous time slices for the same process on a CPU core up to max_merge_duration.
    Preserves time-slice preemption boundaries on the Gantt chart.
    """
    if not gantt_log:
        return []
    merged = []
    curr_start, curr_end, curr_pid, curr_name = gantt_log[0]
    for start_t, end_t, pid, name in gantt_log[1:]:
        if pid == curr_pid and abs(start_t - curr_end) < 1e-4 and (end_t - curr_start) <= max_merge_duration:
            curr_end = end_t
        else:
            merged.append((curr_start, curr_end, curr_pid, curr_name))
            curr_start, curr_end, curr_pid, curr_name = start_t, end_t, pid, name
    merged.append((curr_start, curr_end, curr_pid, curr_name))
    return merged


def plot_gantt_chart(scheduler: CFSScheduler, output_filename: str = "gantt_chart.png") -> str:
    """
    Generates a multi-CPU Gantt Chart illustrating task execution timelines across CPU cores.
    """
    ensure_output_dir()
    filepath = os.path.join(OUTPUT_DIR, output_filename)

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(14, 6), dpi=150)

    all_pids = list(set(p.pid for p in scheduler.all_processes))
    colors = cm.plasma(np.linspace(0.1, 0.9, max(1, len(all_pids))))
    pid_to_color = {pid: colors[i] for i, pid in enumerate(all_pids)}

    y_ticks = []
    y_labels = []
    total_bars_plotted = 0

    print(f"\n[DEBUG visualize {datetime.now().isoformat()}] Generating Gantt Chart...")
    for cpu in scheduler.cpus:
        y_pos = cpu.cpu_id * 10
        y_ticks.append(y_pos)
        y_labels.append(f"CPU {cpu.cpu_id}")

        merged_log = merge_gantt_log(cpu.gantt_log)
        total_bars_plotted += len(merged_log)

        for start_t, end_t, pid, name in merged_log:
            duration = end_t - start_t
            ax.broken_barh(
                [(start_t, duration)],
                (y_pos - 3.5, 7.0),
                facecolors=pid_to_color.get(pid, 'tab:blue'),
                edgecolor='#111111',
                linewidth=0.5,
                alpha=0.9
            )

    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, fontsize=12, fontweight='bold')
    ax.set_xlabel('Simulation Time (ms)', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_title('CFS Multi-CPU Task Execution Gantt Chart', fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, linestyle='--', alpha=0.3)

    plt.tight_layout()
    print(f"  [SAVING gantt_chart.png at {datetime.now().isoformat()}] Total bars plotted={total_bars_plotted}")
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filepath


def plot_vruntime_convergence(scheduler: CFSScheduler, output_filename: str = "vruntime_convergence.png") -> str:
    """
    Generates Vruntime Convergence Plot (vruntime vs time per process).
    """
    ensure_output_dir()
    filepath = os.path.join(OUTPUT_DIR, output_filename)

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6), dpi=150)

    sample_pids = list(scheduler.vruntime_history.keys())[:20]
    print(f"\n[DEBUG visualize {datetime.now().isoformat()}] Generating Vruntime Convergence Graph...")

    lines_plotted = 0
    for pid in sample_pids:
        history = scheduler.vruntime_history[pid]
        if not history:
            continue
        times, vruntimes = zip(*history)
        proc = next((p for p in scheduler.all_processes if p.pid == pid), None)
        nice = proc.nice if proc else 0
        ax.plot(times, vruntimes, label=f"P{pid} (nice={nice})", alpha=0.8, linewidth=1.8)
        lines_plotted += 1

    ax.set_xlabel('Simulation Time (ms)', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_ylabel('Virtual Runtime - vruntime (ms)', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_title('CFS Vruntime Convergence (Proving Fair Scheduling)', fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1), fontsize=8, ncol=2)

    plt.tight_layout()
    print(f"  [SAVING vruntime_convergence.png at {datetime.now().isoformat()}] Lines plotted={lines_plotted}")
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filepath


def plot_cpu_load_heatmap(scheduler: CFSScheduler, output_filename: str = "cpu_load_heatmap.png") -> str:
    """
    Generates Per-CPU Load Balancing Heatmap over simulation time.
    """
    ensure_output_dir()
    filepath = os.path.join(OUTPUT_DIR, output_filename)

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 5), dpi=150)

    num_cpus = scheduler.num_cpus
    min_len = min(len(cpu.load_history) for cpu in scheduler.cpus)

    print(f"\n[DEBUG visualize {datetime.now().isoformat()}] Generating CPU Load Heatmap...")

    if min_len == 0:
        for cpu in scheduler.cpus:
            cpu.load_history.append((scheduler.current_time, cpu.get_load()))
        min_len = 1

    time_steps = [scheduler.cpus[0].load_history[i][0] for i in range(min_len)]
    load_matrix = np.zeros((num_cpus, min_len))

    for cpu_idx, cpu in enumerate(scheduler.cpus):
        for t_idx in range(min_len):
            load_matrix[cpu_idx, t_idx] = cpu.load_history[t_idx][1]

    im = ax.imshow(
        load_matrix,
        aspect='auto',
        cmap='magma',
        extent=[time_steps[0], time_steps[-1], num_cpus - 0.5, -0.5],
        interpolation='nearest'
    )

    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label('CPU Load Weight', fontsize=10, fontweight='bold')

    ax.set_yticks(range(num_cpus))
    ax.set_yticklabels([f"CPU {i}" for i in range(num_cpus)], fontsize=11, fontweight='bold')
    ax.set_xlabel('Simulation Time (ms)', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_title('Per-CPU Load Balancing Heatmap Over Time', fontsize=14, fontweight='bold', pad=15)

    plt.tight_layout()
    print(f"  [SAVING cpu_load_heatmap.png at {datetime.now().isoformat()}] Matrix shape={load_matrix.shape}")
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filepath


def plot_fairness_trend(scheduler: CFSScheduler, output_filename: str = "fairness_trend.png") -> str:
    """
    Generates Fairness Index Trend Graph.
    """
    ensure_output_dir()
    filepath = os.path.join(OUTPUT_DIR, output_filename)

    print(f"\n[DEBUG visualize {datetime.now().isoformat()}] Generating Fairness Index Trend Graph...")

    if not scheduler.fairness_history:
        times = [0.0, scheduler.current_time]
        fairness_values = [1.0, 1.0]
    else:
        times, fairness_values = zip(*scheduler.fairness_history)

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)

    ax.plot(times, fairness_values, color='#00E676', linewidth=2.5, label="Jain's Fairness Index")
    ax.axhline(y=0.90, color='#FF1744', linestyle='--', linewidth=1.5, label="Target Fairness Threshold (0.90)")

    ax.set_ylim(0.0, 1.05)
    ax.set_xlabel('Simulation Time (ms)', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_ylabel("Jain's Fairness Index", fontsize=12, fontweight='bold', labelpad=10)
    ax.set_title("CFS Fairness Index Trend Over Time", fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend(loc='lower right', fontsize=10)

    plt.tight_layout()
    # EXACT PRINT BEFORE SAVING:
    print(
        f"  [SAVING fairness_trend.png at {datetime.now().isoformat()}] "
        f"fairness_values length={len(fairness_values)}, "
        f"min={min(fairness_values):.4f}, max={max(fairness_values):.4f}, "
        f"last={fairness_values[-1]:.4f}, ending_t={times[-1]:.1f}ms"
    )
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filepath


def generate_all_visualizations(scheduler: CFSScheduler) -> Dict[str, str]:
    """
    Utility to render and save all 4 required charts.
    """
    gantt_path = plot_gantt_chart(scheduler)
    vruntime_path = plot_vruntime_convergence(scheduler)
    heatmap_path = plot_cpu_load_heatmap(scheduler)
    fairness_path = plot_fairness_trend(scheduler)

    return {
        "Gantt Chart": gantt_path,
        "Vruntime Convergence": vruntime_path,
        "CPU Load Heatmap": heatmap_path,
        "Fairness Trend": fairness_path
    }
