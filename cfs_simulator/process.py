"""
process.py - Process model and Process Control Block (PCB) representation.

Linux Kernel Mapping:
--------------------
- Process maps to Linux kernel's `struct task_struct` (task descriptor).
- Scheduling attributes (vruntime, weight, nice) map to `struct sched_entity` (se).
  In the kernel, `task_struct` contains a `struct sched_entity se` embedded field
  which is the entity inserted into the CFS runqueue (`cfs_rq`).
"""

from enum import Enum, auto
from typing import Optional

# Constant for Nice 0 weight in Linux CFS (sched_prio_to_weight)
NICE_0_LOAD = 1024.0


class ProcessState(Enum):
    """
    Process Lifecycle States mapping to Linux task states:
    - READY: Task is in runqueue waiting for CPU execution (TASK_RUNNING in rq).
    - RUNNING: Task is actively executing on a CPU core (TASK_RUNNING on CPU).
    - SLEEPING: Task is waiting for I/O completion (TASK_INTERRUPTIBLE / TASK_UNINTERRUPTIBLE).
    - TERMINATED: Task has completed its total execution burst (TASK_DEAD / EXIT_ZOMBIE).
    """
    READY = auto()
    RUNNING = auto()
    SLEEPING = auto()
    TERMINATED = auto()


def nice_to_weight(nice: int) -> float:
    """
    Calculates process weight based on nice value using Linux's sched_prio_to_weight formula:
    weight = 1024 / (1.25 ^ nice)

    Linux Kernel Concept:
    Each nice level change corresponds to roughly ~10% difference in CPU execution time.
    1.25^1 ≈ 1.25, so incrementing nice by +1 decreases CPU share by ~20%, while
    decrementing by -1 increases CPU share by ~25% (1.25x).

    Args:
        nice: Priority offset integer ranging from -20 (highest priority) to +19 (lowest priority).

    Returns:
        float: Process static weight for CFS calculations.
    """
    clamped_nice = max(-20, min(19, nice))
    return NICE_0_LOAD / (1.25 ** clamped_nice)


class Process:
    """
    Process Control Block (PCB) representing an OS process scheduled by CFS.

    Attributes:
        pid (int): Process Identifier.
        name (str): Human-readable process label.
        nice (int): Priority nice value (-20 to +19).
        weight (float): Process weight calculated from nice value.
        vruntime (float): Virtual runtime accumulated by the process (maps to se.vruntime).
        remaining_burst_time (float): Total remaining CPU execution time required (ms).
        total_burst_time (float): Initial total CPU execution time required (ms).
        state (ProcessState): Current process state (READY, RUNNING, SLEEPING, TERMINATED).
        arrival_time (float): Simulation timestamp when process arrived.
        start_time (Optional[float]): Timestamp when process first received CPU execution.
        completion_time (Optional[float]): Timestamp when process finished execution.
        waiting_time (float): Total accumulated time spent in READY state in runqueue.
        cpu_time_executed (float): Total actual CPU time consumed so far (ms).
        context_switch_count (int): Number of context switches experienced by process.
        assigned_cpu (Optional[int]): ID of the CPU core currently running/queueing this process.
        is_io_bound (bool): True if process exhibits periodic I/O behavior.
        io_burst_time (float): Duration process sleeps during an I/O operation (ms).
        cpu_burst_interval (float): Duration process runs on CPU before triggering I/O (ms).
        time_until_next_io (float): Counter tracking time left in current CPU burst before I/O.
        remaining_io_time (float): Counter tracking time left in current SLEEPING state.
    """

    def __init__(
        self,
        pid: int,
        name: str = "",
        nice: int = 0,
        total_burst_time: float = 100.0,
        arrival_time: float = 0.0,
        is_io_bound: bool = False,
        io_burst_time: float = 20.0,
        cpu_burst_interval: float = 10.0,
    ):
        self.pid: int = pid
        self.name: str = name if name else f"P{pid}"
        self.nice: int = max(-20, min(19, nice))
        self.weight: float = nice_to_weight(self.nice)

        # Linux CFS Scheduling Entity state (se.vruntime)
        self.vruntime: float = 0.0

        # Execution tracking
        self.total_burst_time: float = total_burst_time
        self.remaining_burst_time: float = total_burst_time
        self.cpu_time_executed: float = 0.0

        # Process state and timestamps
        self.state: ProcessState = ProcessState.READY
        self.arrival_time: float = arrival_time
        self.start_time: Optional[float] = None
        self.completion_time: Optional[float] = None
        self.waiting_time: float = 0.0
        self.context_switch_count: int = 0
        self.assigned_cpu: Optional[int] = None

        # I/O behavior characteristics
        self.is_io_bound: bool = is_io_bound
        self.io_burst_time: float = io_burst_time
        self.cpu_burst_interval: float = cpu_burst_interval
        self.time_until_next_io: float = cpu_burst_interval if is_io_bound else float('inf')
        self.remaining_io_time: float = 0.0

    def update_vruntime(self, exec_time: float) -> float:
        """
        Updates process vruntime based on actual execution time:
        vruntime += exec_time * (NICE_0_WEIGHT / process.weight)

        Linux Kernel Mapping:
        Maps to `update_curr()` in `kernel/sched/fair.c`:
        ```c
        calc_delta_fair(delta_exec, se) = delta_exec * (NICE_0_LOAD / se->load.weight)
        se->vruntime += calc_delta_fair(delta_exec, se);
        ```

        High weight (low nice) processes accumulate vruntime slowly, receiving more CPU time.
        Low weight (high nice) processes accumulate vruntime rapidly, receiving less CPU time.

        Args:
            exec_time: Actual physical time spent executing on CPU core (ms).

        Returns:
            float: Incremental delta added to vruntime.
        """
        delta_vruntime = exec_time * (NICE_0_LOAD / self.weight)
        self.vruntime += delta_vruntime
        self.cpu_time_executed += exec_time
        self.remaining_burst_time = max(0.0, self.remaining_burst_time - exec_time)

        if self.is_io_bound and self.time_until_next_io != float('inf'):
            self.time_until_next_io -= exec_time

        return delta_vruntime

    def __repr__(self) -> str:
        return (
            f"<Process pid={self.pid} name='{self.name}' nice={self.nice} "
            f"weight={self.weight:.1f} vruntime={self.vruntime:.2f} "
            f"rem={self.remaining_burst_time:.1f}ms state={self.state.name}>"
        )
