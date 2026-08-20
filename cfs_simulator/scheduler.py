"""
scheduler.py - Core CFS Multi-CPU Scheduler engine & Load Balancer.

Linux Kernel Mapping:
--------------------
- `CPU`: Represents a CPU core with active execution state and `cfs_rq`.
- `CFSScheduler`: Manages CPU cores, tick dispatch, preemption checks, and multi-CPU load balancing.
- `update_curr()`: Updates runtime statistics and `se.vruntime`.
- `check_preempt_tick()`: Determines if running process should be preempted by a process with smaller vruntime.
- `sched_slice()`: Calculates dynamic time slice based on weight ratios.
- `load_balance()`: Periodically balances runqueue weights across CPU cores (maps to `load_balance()` in kernel/sched/fair.c).
"""

from typing import List, Dict, Optional, Tuple
from cfs_simulator.process import Process, ProcessState, NICE_0_LOAD
from cfs_simulator.run_queue import RunQueue
from cfs_simulator.metrics import calculate_jains_fairness_index


class CPU:
    """
    Simulated CPU core.

    Attributes:
        cpu_id (int): CPU core index (0..N-1).
        run_queue (RunQueue): Per-CPU CFS runqueue.
        running_process (Optional[Process]): Currently executing task on this core.
        total_active_time (float): Accumulated active CPU execution time (ms).
        total_idle_time (float): Accumulated idle CPU time (ms).
        total_context_switch_overhead (float): Time spent performing context switches (ms).
        context_switch_count (int): Count of context switches executed on this core.
        slice_allocated (float): Allocated CFS time slice for currently running task (ms).
        slice_used (float): Time consumed so far in current allocated slice (ms).
        gantt_log (List[Tuple[float, float, int, str]]): List of (start_time, end_time, pid, name) for Gantt chart.
        load_history (List[Tuple[float, float]]): List of (timestamp, queue_load) for heatmap.
    """

    def __init__(self, cpu_id: int):
        self.cpu_id: int = cpu_id
        self.run_queue: RunQueue = RunQueue(cpu_id)
        self.running_process: Optional[Process] = None
        self.total_active_time: float = 0.0
        self.total_idle_time: float = 0.0
        self.total_context_switch_overhead: float = 0.0
        self.context_switch_count: int = 0
        self.slice_allocated: float = 0.0
        self.slice_used: float = 0.0

        # Execution history tracking for visualization
        self.gantt_log: List[Tuple[float, float, int, str]] = []
        self.load_history: List[Tuple[float, float]] = []

    def get_load(self) -> float:
        """
        Calculates total load weight on this CPU core.
        Includes queued processes weight + active running process weight.
        """
        load = self.run_queue.total_weight()
        if self.running_process and self.running_process.state == ProcessState.RUNNING:
            load += self.running_process.weight
        return load

    def get_nr_running(self) -> int:
        """
        Returns total number of runnable tasks (queued + running).
        """
        count = self.run_queue.count()
        if self.running_process and self.running_process.state == ProcessState.RUNNING:
            count += 1
        return count


class CFSScheduler:
    """
    Multi-CPU Completely Fair Scheduler Simulator.

    Attributes:
        num_cpus (int): Number of simulated CPU cores (default 4).
        sched_latency (float): Target scheduling period `sysctl_sched_latency` (default 6.0 ms).
        sched_min_granularity (float): Minimum execution slice `sysctl_sched_min_granularity` (default 0.75 ms).
        sched_nr_latency (int): Process threshold before latency scales linearly (default 8).
        context_switch_cost (float): Time cost penalty incurred per context switch (default 0.1 ms).
        load_balance_interval (float): Period between load balancing checks (default 10.0 ms).
        sleeper_thresh (float): Sleeper fairness latency credit (default 3.0 ms).
    """

    def __init__(
        self,
        num_cpus: int = 4,
        sched_latency: float = 6.0,
        sched_min_granularity: float = 0.75,
        sched_nr_latency: int = 8,
        context_switch_cost: float = 0.1,
        load_balance_interval: float = 10.0,
        sleeper_thresh: float = 3.0,
        verbose: bool = True
    ):
        self.num_cpus: int = num_cpus
        self.cpus: List[CPU] = [CPU(i) for i in range(num_cpus)]
        self.sched_latency: float = sched_latency
        self.sched_min_granularity: float = sched_min_granularity
        self.sched_nr_latency: int = sched_nr_latency
        self.context_switch_cost: float = context_switch_cost
        self.load_balance_interval: float = load_balance_interval
        self.sleeper_thresh: float = sleeper_thresh
        self.verbose: bool = verbose

        # Global simulation state
        self.current_time: float = 0.0
        self.unarrived_processes: List[Process] = []
        self.sleeping_processes: List[Process] = []
        self.completed_processes: List[Process] = []
        self.all_processes: List[Process] = []
        self.vruntime_history: Dict[int, List[Tuple[float, float]]] = {}
        self.fairness_history: List[Tuple[float, float]] = []

        # Load balancing metrics
        self.last_load_balance_time: float = 0.0
        self.migration_count: int = 0
        self.total_context_switches: int = 0
        self.tick_count: int = 0

    def calculate_time_slice(self, process: Process, cpu: CPU) -> float:
        """
        Calculates task execution slice (`sched_slice()` in Linux kernel).
        """
        nr_running = cpu.get_nr_running()
        if nr_running > self.sched_nr_latency:
            period = nr_running * self.sched_min_granularity
        else:
            period = self.sched_latency

        total_weight = cpu.get_load()
        if total_weight <= 0.0:
            return period

        raw_slice = period * (process.weight / total_weight)
        return max(raw_slice, self.sched_min_granularity)

    def select_initial_cpu(self, process: Process) -> CPU:
        """
        Selects target CPU for newly arriving process (`select_task_rq_fair()` in Linux kernel).
        Chooses CPU with smallest current total load weight.
        """
        return min(self.cpus, key=lambda c: c.get_load())

    def add_process(self, process: Process) -> None:
        """
        Registers a process into the simulation system.
        If arrival_time > current_time, buffers process until arrival time.
        """
        self.all_processes.append(process)
        self.vruntime_history[process.pid] = [(process.arrival_time, process.vruntime)]

        if process.arrival_time > self.current_time:
            self.unarrived_processes.append(process)
            self.unarrived_processes.sort(key=lambda p: p.arrival_time)
        else:
            target_cpu = self.select_initial_cpu(process)
            target_cpu.run_queue.enqueue(process, is_waking=False, thresh=self.sleeper_thresh)

    def check_preempt_tick(self, cpu: CPU) -> bool:
        """
        Checks if currently running process should be preempted (`check_preempt_tick()` in kernel).
        """
        if not cpu.running_process:
            return False

        if cpu.slice_used >= cpu.slice_allocated:
            return True

        min_queued = cpu.run_queue.peek_min()
        if min_queued:
            vdiff = cpu.running_process.vruntime - min_queued.vruntime
            if vdiff > self.sched_min_granularity:
                return True

        return False

    def load_balance(self) -> None:
        """
        Multi-CPU Load Balancer (`load_balance()` in `kernel/sched/fair.c`).

        Periodically inspects load distribution across all CPUs.
        Migrates ready tasks from busiest CPU to idlest CPU if load imbalance can be reduced.
        """
        if self.num_cpus <= 1:
            return

        sorted_cpus = sorted(self.cpus, key=lambda c: c.get_load())
        idlest_cpu = sorted_cpus[0]
        busiest_cpu = sorted_cpus[-1]

        idle_load = idlest_cpu.get_load()
        busy_load = busiest_cpu.get_load()
        imbalance = busy_load - idle_load

        # Condition for load balancing migration:
        # Busiest CPU must have at least 1 queued process ready to migrate,
        # and moving candidate task must reduce load imbalance.
        if busiest_cpu.run_queue.count() >= 1 and imbalance > 0.0:
            candidates = busiest_cpu.run_queue.get_all_processes()
            # Find candidate whose weight is less than imbalance to avoid overshooting
            candidate = next(
                (p for p in sorted(candidates, key=lambda p: p.vruntime, reverse=True) if p.weight < imbalance),
                candidates[0] if candidates else None
            )

            if candidate and busiest_cpu.run_queue.remove(candidate):
                # Enqueue on new CPU without artificial vruntime jumps
                idlest_cpu.run_queue.enqueue(candidate, is_waking=False, thresh=self.sleeper_thresh)
                self.migration_count += 1

                if self.verbose:
                    print(
                        f"  [LOAD_BALANCE t={self.current_time:.1f}ms] Migrated {candidate.name} (pid={candidate.pid}, "
                        f"nice={candidate.nice}, weight={candidate.weight:.1f}) from CPU {busiest_cpu.cpu_id} "
                        f"(busy_load={busy_load:.1f}) -> CPU {idlest_cpu.cpu_id} (idle_load={idle_load:.1f})"
                    )

    def step(self, time_step: float = 0.1) -> None:
        """
        Advances simulation time by `time_step` ms.
        """
        self.current_time += time_step
        self.tick_count += 1

        # 1. Process new arrivals
        arrived = []
        still_unarrived = []
        for p in self.unarrived_processes:
            if p.arrival_time <= self.current_time:
                arrived.append(p)
            else:
                still_unarrived.append(p)
        self.unarrived_processes = still_unarrived

        for p in arrived:
            target_cpu = self.select_initial_cpu(p)
            target_cpu.run_queue.enqueue(p, is_waking=False, thresh=self.sleeper_thresh)
            if self.verbose:
                print(f"  [ARRIVAL t={self.current_time:.1f}ms] {p.name} (pid={p.pid}) arrived on CPU {target_cpu.cpu_id}")

        # 2. Wake sleeping I/O processes
        still_sleeping = []
        for p in self.sleeping_processes:
            p.remaining_io_time -= time_step
            if p.remaining_io_time <= 0.0:
                p.remaining_io_time = 0.0
                target_cpu = self.select_initial_cpu(p)
                target_cpu.run_queue.enqueue(p, is_waking=True, thresh=self.sleeper_thresh)
                if self.verbose:
                    print(f"  [WAKE_UP t={self.current_time:.1f}ms] {p.name} (pid={p.pid}) woke up on CPU {target_cpu.cpu_id}")
            else:
                still_sleeping.append(p)
        self.sleeping_processes = still_sleeping

        # 3. Step each CPU core
        for cpu in self.cpus:
            # Record load history for heatmap
            cpu.load_history.append((self.current_time, cpu.get_load()))

            # If CPU is idle, schedule next process from run queue
            if cpu.running_process is None:
                next_task = cpu.run_queue.dequeue_min()
                if next_task:
                    cpu.total_context_switch_overhead += self.context_switch_cost
                    cpu.context_switch_count += 1
                    self.total_context_switches += 1
                    next_task.context_switch_count += 1

                    cpu.running_process = next_task
                    next_task.state = ProcessState.RUNNING

                    if next_task.start_time is None:
                        next_task.start_time = self.current_time

                    cpu.slice_allocated = self.calculate_time_slice(next_task, cpu)
                    cpu.slice_used = 0.0
                    cpu.gantt_log.append((self.current_time, self.current_time + time_step, next_task.pid, next_task.name))
                else:
                    cpu.total_idle_time += time_step
                    continue
            else:
                cpu.gantt_log.append((self.current_time, self.current_time + time_step, cpu.running_process.pid, cpu.running_process.name))

            proc = cpu.running_process
            if not proc:
                continue

            actual_exec = min(time_step, proc.remaining_burst_time)
            proc.update_vruntime(actual_exec)
            cpu.total_active_time += actual_exec
            cpu.slice_used += actual_exec

            for queued_proc in cpu.run_queue.get_all_processes():
                queued_proc.waiting_time += time_step

            # State Checks:
            if proc.remaining_burst_time <= 0.0:
                proc.state = ProcessState.TERMINATED
                proc.completion_time = self.current_time
                self.completed_processes.append(proc)
                cpu.running_process = None
                cpu.slice_used = 0.0

            elif proc.is_io_bound and proc.time_until_next_io <= 0.0:
                proc.state = ProcessState.SLEEPING
                proc.remaining_io_time = proc.io_burst_time
                proc.time_until_next_io = proc.cpu_burst_interval
                self.sleeping_processes.append(proc)
                cpu.running_process = None
                cpu.slice_used = 0.0

            elif self.check_preempt_tick(cpu):
                proc.state = ProcessState.READY
                cpu.run_queue.enqueue(proc, is_waking=False, thresh=self.sleeper_thresh)
                cpu.running_process = None
                cpu.slice_used = 0.0

        # 4. Record vruntime history for all active/queued/running processes
        for p in self.all_processes:
            if p.arrival_time <= self.current_time and p.state != ProcessState.TERMINATED:
                self.vruntime_history[p.pid].append((self.current_time, p.vruntime))

        # 5. Record Jain's Fairness Index progression (vruntime progress rate across active processes)
        active_procs = [p for p in self.all_processes if p.state in (ProcessState.READY, ProcessState.RUNNING) and p.vruntime > 0.0]
        if len(active_procs) >= 2:
            vrates = [p.vruntime / max(0.1, self.current_time - p.arrival_time) for p in active_procs]
            sum_r = sum(vrates)
            sum_sq = sum(r * r for r in vrates)
            j_fairness = (sum_r ** 2) / (len(vrates) * sum_sq) if sum_sq > 0 else 1.0
            self.fairness_history.append((self.current_time, j_fairness))

        # 6. Periodic Load Balance
        if self.current_time - self.last_load_balance_time >= self.load_balance_interval:
            self.load_balance()
            self.last_load_balance_time = self.current_time

    def is_finished(self) -> bool:
        """
        Checks if all processes in simulation have finished execution.
        """
        return len(self.completed_processes) == len(self.all_processes) and len(self.all_processes) > 0

    def run(self, max_duration: float = 10000.0, time_step: float = 0.1) -> float:
        """
        Runs simulation loop until completion or max_duration.
        """
        while not self.is_finished() and self.current_time < max_duration:
            self.step(time_step)
        return self.current_time
