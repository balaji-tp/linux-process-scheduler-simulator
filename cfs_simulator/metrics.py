"""
metrics.py - Fairness and Performance Metrics calculations for CFS simulation.

Provides mathematical formulations for evaluating OS kernel scheduler performance:
- Jain's Fairness Index across weighted CPU allocations.
- System throughput, turnaround time, waiting time, and CPU utilization.
- Context switch overhead percentages.
- Nice priority proportionality analysis.
"""

from typing import List, Dict, Any, TYPE_CHECKING
from cfs_simulator.process import Process

if TYPE_CHECKING:
    from cfs_simulator.scheduler import CFSScheduler


def calculate_jains_fairness_index(processes: List[Process]) -> float:
    """
    Calculates Jain's Fairness Index across CPU time allocation.

    Mathematical Formula:
        J(x_1, x_2, ..., x_n) = (sum(x_i))^2 / (n * sum(x_i^2))

    Where x_i is the normalized CPU execution time allocated to process i relative to its weight:
        x_i = cpu_time_executed_i / process.weight

    Theoretical Properties:
    - Range: [1/n, 1.0]
    - If all processes receive CPU time strictly proportional to their static weight (nice value),
      x_1 = x_2 = ... = x_n, resulting in J = 1.0 (perfect CFS fairness).
    - If a single process monopolizes all CPU resources while others starve, J approaches 1/n.

    Args:
        processes: List of completed or active Process instances.

    Returns:
        float: Jain's Fairness Index value between 0.0 and 1.0.
    """
    active_procs = [p for p in processes if p.cpu_time_executed > 0.0]
    n = len(active_procs)
    if n == 0:
        return 1.0

    # Normalized CPU time per weight unit
    x = [p.cpu_time_executed / p.weight for p in active_procs]

    sum_x = sum(x)
    sum_sq_x = sum(val * val for val in x)

    if sum_sq_x == 0.0:
        return 1.0

    return (sum_x ** 2) / (n * sum_sq_x)


def calculate_simulation_metrics(scheduler: 'CFSScheduler') -> Dict[str, Any]:
    """
    Computes comprehensive system-wide performance and fairness metrics for a completed simulation.

    Args:
        scheduler: Executed CFSScheduler instance.

    Returns:
        Dict[str, Any]: Dictionary containing computed metrics summary.
    """
    processes = scheduler.completed_processes if scheduler.completed_processes else scheduler.all_processes
    n = len(processes)

    if n == 0:
        return {
            "total_processes": 0,
            "total_simulation_time": scheduler.current_time,
            "jains_fairness_index": 1.0,
            "avg_waiting_time": 0.0,
            "avg_turnaround_time": 0.0,
            "throughput_proc_per_sec": 0.0,
            "avg_cpu_utilization_pct": 0.0,
            "context_switch_overhead_pct": 0.0,
            "total_context_switches": scheduler.total_context_switches,
            "total_migrations": scheduler.migration_count,
            "per_cpu_utilization": []
        }

    # 1. Waiting and Turnaround times
    total_waiting_time = sum(p.waiting_time for p in processes)
    turnaround_times = [
        (p.completion_time - p.arrival_time) if p.completion_time else (scheduler.current_time - p.arrival_time)
        for p in processes
    ]
    total_turnaround_time = sum(turnaround_times)

    avg_waiting_time = total_waiting_time / n
    avg_turnaround_time = total_turnaround_time / n

    # 2. Throughput (processes completed per second, 1000 ms = 1s)
    sim_time_sec = scheduler.current_time / 1000.0 if scheduler.current_time > 0 else 1.0
    throughput = len(scheduler.completed_processes) / sim_time_sec

    # 3. Per-CPU Utilization & Context Switch Overhead
    per_cpu_util = []
    total_cpu_active = 0.0
    total_cpu_switch_overhead = 0.0
    total_cpu_time_capacity = scheduler.current_time * scheduler.num_cpus

    for cpu in scheduler.cpus:
        active = cpu.total_active_time
        total_capacity = scheduler.current_time
        util_pct = (active / total_capacity * 100.0) if total_capacity > 0 else 0.0
        per_cpu_util.append(util_pct)

        total_cpu_active += active
        total_cpu_switch_overhead += cpu.total_context_switch_overhead

    avg_cpu_util_pct = (total_cpu_active / total_cpu_time_capacity * 100.0) if total_cpu_time_capacity > 0 else 0.0
    context_switch_overhead_pct = (total_cpu_switch_overhead / total_cpu_time_capacity * 100.0) if total_cpu_time_capacity > 0 else 0.0

    # 4. Jain's Fairness Index
    jains_index = calculate_jains_fairness_index(processes)

    # 5. Priority Proportionality breakdown
    priority_groups: Dict[int, List[Process]] = {}
    for p in processes:
        priority_groups.setdefault(p.nice, []).append(p)

    proportionality: Dict[int, Dict[str, float]] = {}
    for nice_val, procs in sorted(priority_groups.items()):
        avg_cpu_time = sum(p.cpu_time_executed for p in procs) / len(procs)
        avg_weight = sum(p.weight for p in procs) / len(procs)
        proportionality[nice_val] = {
            "count": len(procs),
            "weight": avg_weight,
            "avg_cpu_time": avg_cpu_time,
            "cpu_time_per_weight": avg_cpu_time / avg_weight if avg_weight > 0 else 0.0
        }

    return {
        "total_processes": n,
        "completed_processes": len(scheduler.completed_processes),
        "total_simulation_time_ms": scheduler.current_time,
        "jains_fairness_index": jains_index,
        "avg_waiting_time_ms": avg_waiting_time,
        "avg_turnaround_time_ms": avg_turnaround_time,
        "throughput_proc_per_sec": throughput,
        "avg_cpu_utilization_pct": avg_cpu_util_pct,
        "context_switch_overhead_pct": context_switch_overhead_pct,
        "total_context_switches": scheduler.total_context_switches,
        "total_migrations": scheduler.migration_count,
        "per_cpu_utilization_pct": per_cpu_util,
        "priority_proportionality": proportionality
    }
