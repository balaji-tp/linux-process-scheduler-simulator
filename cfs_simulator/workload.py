"""
workload.py - Synthetic workload generators for CPU-bound, I/O-bound, and mixed scenarios.

Provides reproducible task set generators simulating real-world OS process populations:
- CPU-Bound Heavy Workload: Scientific computing, video encoding, long continuous loops.
- I/O-Bound Workload: Web servers, database queries, file transfers (short CPU bursts + sleep).
- Mixed Workload: Heterogeneous desktop/server environment combining background batch jobs and interactive tasks.
"""

import random
from typing import List
from cfs_simulator.process import Process


def generate_cpu_bound_workload(
    n_processes: int = 20,
    min_burst: float = 80.0,
    max_burst: float = 200.0,
    seed: int = 42
) -> List[Process]:
    """
    Generates a CPU-bound workload of heavy computational processes.

    Nice value distribution:
    - ~20% high priority (nice -10 to -1)
    - ~60% normal priority (nice 0)
    - ~20% low priority (nice 1 to 10)

    Args:
        n_processes: Total number of processes to create.
        min_burst: Minimum CPU burst execution time (ms).
        max_burst: Maximum CPU burst execution time (ms).
        seed: Random seed for reproducible generation.

    Returns:
        List[Process]: List of Process instances ready for simulation.
    """
    random.seed(seed)
    processes: List[Process] = []

    for i in range(1, n_processes + 1):
        # Nice distribution
        r = random.random()
        if r < 0.2:
            nice = random.randint(-10, -1)
        elif r < 0.8:
            nice = 0
        else:
            nice = random.randint(1, 10)

        burst = random.uniform(min_burst, max_burst)
        arrival = random.uniform(0.0, 5.0)

        proc = Process(
            pid=i,
            name=f"CPU_Task_{i}",
            nice=nice,
            total_burst_time=burst,
            arrival_time=arrival,
            is_io_bound=False
        )
        processes.append(proc)

    return processes


def generate_io_bound_workload(
    n_processes: int = 20,
    min_burst: float = 30.0,
    max_burst: float = 90.0,
    seed: int = 42
) -> List[Process]:
    """
    Generates an I/O-bound workload of interactive processes.

    Processes alternate between short CPU execution intervals and I/O wait periods.

    Args:
        n_processes: Total number of processes.
        min_burst: Minimum total CPU execution required (ms).
        max_burst: Maximum total CPU execution required (ms).
        seed: Random seed for reproducibility.

    Returns:
        List[Process]: List of I/O-bound Process instances.
    """
    random.seed(seed)
    processes: List[Process] = []

    for i in range(1, n_processes + 1):
        nice = random.choice([0, 0, 0, -5, 5])
        burst = random.uniform(min_burst, max_burst)
        arrival = random.uniform(0.0, 10.0)

        proc = Process(
            pid=i,
            name=f"IO_Task_{i}",
            nice=nice,
            total_burst_time=burst,
            arrival_time=arrival,
            is_io_bound=True,
            io_burst_time=random.uniform(15.0, 35.0),
            cpu_burst_interval=random.uniform(5.0, 15.0)
        )
        processes.append(proc)

    return processes


def generate_mixed_workload(
    n_processes: int = 50,
    seed: int = 42
) -> List[Process]:
    """
    Generates a realistic mixed synthetic workload combining:
    - 50% CPU-bound batch tasks
    - 50% I/O-bound interactive tasks
    with diverse nice priority distributions (-15 to +15) and arrival times.

    Args:
        n_processes: Total processes count (default 50).
        seed: Random seed for reproducible generation.

    Returns:
        List[Process]: Mixed population of Process instances.
    """
    random.seed(seed)
    processes: List[Process] = []

    nice_levels = [-15, -10, -5, 0, 0, 0, 0, 5, 10, 15]

    for i in range(1, n_processes + 1):
        is_io = (i % 2 == 0)
        nice = random.choice(nice_levels)

        if is_io:
            burst = random.uniform(40.0, 120.0)
            arrival = random.uniform(0.0, 15.0)
            proc = Process(
                pid=i,
                name=f"Mixed_IO_{i}",
                nice=nice,
                total_burst_time=burst,
                arrival_time=arrival,
                is_io_bound=True,
                io_burst_time=random.uniform(10.0, 30.0),
                cpu_burst_interval=random.uniform(4.0, 12.0)
            )
        else:
            burst = random.uniform(100.0, 300.0)
            arrival = random.uniform(0.0, 15.0)
            proc = Process(
                pid=i,
                name=f"Mixed_CPU_{i}",
                nice=nice,
                total_burst_time=burst,
                arrival_time=arrival,
                is_io_bound=False
            )

        processes.append(proc)

    return processes
