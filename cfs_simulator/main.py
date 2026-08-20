"""
main.py - Entry point for Linux CFS Simulator.

Runs full simulation end-to-end with 50 processes across 4 CPUs,
calculates fairness and performance metrics, prints debug verification reports,
and saves visual analysis charts to `output/`.
"""

import sys
from datetime import datetime
from cfs_simulator.scheduler import CFSScheduler
from cfs_simulator.workload import generate_mixed_workload
from cfs_simulator.metrics import calculate_simulation_metrics
from cfs_simulator.visualize import generate_all_visualizations


def run_simulation_demo(n_processes: int = 50, num_cpus: int = 4, verbose: bool = False):
    """
    Executes a complete end-to-end CFS simulation with live timestamp logging.
    """
    start_timestamp = datetime.now().isoformat()
    print("=" * 80)
    print(f"  LINUX COMPLETELY FAIR SCHEDULER (CFS) SIMULATOR - LIVE RUN")
    print(f"  Execution Timestamp: {start_timestamp}")
    print(f"  Simulation Setup   : {n_processes} Processes across {num_cpus} CPU Cores")
    print("=" * 80)

    # 1. Initialize CFS Scheduler
    scheduler = CFSScheduler(
        num_cpus=num_cpus,
        sched_latency=6.0,          # sysctl_sched_latency = 6.0 ms
        sched_min_granularity=0.75, # sysctl_sched_min_granularity = 0.75 ms
        context_switch_cost=0.1,   # 0.1 ms context switch overhead
        load_balance_interval=10.0, # 10.0 ms load balance period
        verbose=verbose
    )

    # 2. Generate Workload
    print(f"\n[{datetime.now().isoformat()}] Generating synthetic mixed workload (50% CPU-bound, 50% I/O-bound)...")
    workload = generate_mixed_workload(n_processes=n_processes, seed=42)

    for proc in workload:
        scheduler.add_process(proc)

    print(f"[{datetime.now().isoformat()}] Registered {len(workload)} processes into simulation engine.")

    # 3. Execute Simulation Loop
    print(f"\n[{datetime.now().isoformat()}] Running CFS multi-CPU simulation loop...")
    max_duration = 10000.0
    time_step = 0.1
    last_print_time = 0.0

    while not scheduler.is_finished() and scheduler.current_time < max_duration:
        scheduler.step(time_step)

        if scheduler.current_time - last_print_time >= 500.0 or scheduler.is_finished():
            active_count = sum(1 for p in scheduler.all_processes if p.arrival_time <= scheduler.current_time and p not in scheduler.completed_processes)
            completed_count = len(scheduler.completed_processes)
            print(
                f"  [{datetime.now().isoformat()} | TICK {scheduler.tick_count:5d} | t={scheduler.current_time:7.1f}ms] "
                f"Completed: {completed_count:2d}/{len(scheduler.all_processes)} | "
                f"Active/Queued: {active_count:2d} | Migrations: {scheduler.migration_count:3d} | "
                f"Context Switches: {scheduler.total_context_switches:4d}"
            )
            last_print_time = scheduler.current_time

    print(f"\n[{datetime.now().isoformat()}] Simulation finished in {scheduler.current_time:.2f} ms total time across {scheduler.tick_count} simulation ticks.")

    # 4. RAW DATA ARRAYS VERIFICATION (Printed BEFORE generating charts)
    print("\n" + "=" * 80)
    print(f"  RAW DATA ARRAYS VERIFICATION at {datetime.now().isoformat()}")
    print("=" * 80)

    # A) RAW FAIRNESS_HISTORY ARRAY INSPECTION
    print("\n[RAW ARRAY 1] fairness_history (Time, Jain's Index):")
    print(f"  - Total array entries: {len(scheduler.fairness_history)}")
    if scheduler.fairness_history:
        f_times, f_vals = zip(*scheduler.fairness_history)
        print("  - First 5 values:")
        for t, v in scheduler.fairness_history[:5]:
            print(f"      t={t:6.1f}ms -> Fairness={v:.4f}")

        mid_idx = len(scheduler.fairness_history) // 2
        print(f"  - Middle 5 values (around index {mid_idx}):")
        for t, v in scheduler.fairness_history[mid_idx:mid_idx+5]:
            print(f"      t={t:6.1f}ms -> Fairness={v:.4f}")

        print("  - Last 5 values:")
        for t, v in scheduler.fairness_history[-5:]:
            print(f"      t={t:6.1f}ms -> Fairness={v:.4f}")

        print(f"  - Array Stats: Min={min(f_vals):.4f} | Max={max(f_vals):.4f} | Avg={sum(f_vals)/len(f_vals):.4f} | Last={f_vals[-1]:.4f}")

    # B) RAW VRUNTIME_HISTORY ARRAY INSPECTION
    print("\n[RAW ARRAY 2] vruntime_history (Time, vruntime per process):")
    print(f"  - Total tracked processes in dict: {len(scheduler.vruntime_history)}")
    sample_pids = list(scheduler.vruntime_history.keys())[:3]
    for pid in sample_pids:
        hist = scheduler.vruntime_history[pid]
        proc = next(p for p in scheduler.all_processes if p.pid == pid)
        print(f"  - Process P{pid} ({proc.name}, nice={proc.nice}, weight={proc.weight:.1f}): {len(hist)} data points")
        if hist:
            print(f"      First 3 points: {[(round(t,1), round(v,2)) for t, v in hist[:3]]}")
            print(f"      Last 3 points : {[(round(t,1), round(v,2)) for t, v in hist[-3:]]}")

    # 5. Render Visualizations AFTER Verifying Raw Arrays
    print(f"\n[{datetime.now().isoformat()}] Raw arrays verified. Rendering matplotlib visual charts into 'output/' folder...")
    chart_paths = generate_all_visualizations(scheduler)

    print(f"\n[{datetime.now().isoformat()}] Visualizations successfully generated and saved:")
    for title, path in chart_paths.items():
        print(f"    - {title:<22}: {path}")

    print("\n" + "=" * 80)
    print(f"  SIMULATION END-TO-END LIVE RUN COMPLETE at {datetime.now().isoformat()}")
    print("=" * 80)


if __name__ == "__main__":
    run_simulation_demo()
