"""
run_queue.py - Per-CPU CFS Run Queue implementation using Python min-heap.

DESIGN TRADEOFF DOCUMENTATION (Red-Black Tree vs Min-Heap):
------------------------------------------------------------
Real Linux Kernel Implementation:
  In the Linux kernel (`kernel/sched/fair.c`), the CFS runqueue (`struct cfs_rq`) is structured
  as a self-balancing Red-Black Tree (`struct rb_root_cached`), ordered by `se.vruntime`.
  - Insert Task (`enqueue_entity`): O(log N)
  - Delete Arbitrary Task (`dequeue_entity`): O(log N)
  - Pick Leftmost Task (`pick_next_entity`): O(1) via cached pointer (`rb_leftmost`).

Python Simulator Implementation (Min-Heap via `heapq`):
  In this simulator, we use Python's built-in `heapq` module to implement a binary min-heap.
  - Insert Task: O(log N)
  - Pick Minimum `vruntime` Task: O(1) peek, O(log N) pop.
  - Delete Arbitrary Task (e.g., for multi-CPU migration): O(N) search or lazy soft deletion.

Why Heap instead of RB-Tree in Python?
  1. Standard Library Simplicity: Python does not provide a native C-speed balanced BST in standard library.
  2. Performance for Min-Retrieval: Min-heap provides O(1) inspection of the next task to run, matching
     CFS's `rb_leftmost` cache behavior.
  3. Educational Clarity: Cleanly demonstrates CFS core principle—always select task with minimum vruntime.
"""

import heapq
from typing import List, Optional, Tuple
from cfs_simulator.process import Process, ProcessState, NICE_0_LOAD


class RunQueue:
    """
    Per-CPU CFS Run Queue (`cfs_rq`).

    Manages runnable processes ordered by virtual runtime (`vruntime`).
    Tracks `min_vruntime` to preserve monotonic progression and enforce sleeper fairness.

    Attributes:
        cpu_id (int): Core ID this run queue belongs to.
        min_vruntime (float): Monotonic minimum vruntime tracking runqueue state (`cfs_rq->min_vruntime`).
        heap (List[Tuple[float, int, Process]]): Min-heap of tuples (vruntime, sequence_id, Process).
        _entry_finder (dict[int, Tuple[float, int, Process]]): Mapping pid -> heap entry for fast removal.
    """

    def __init__(self, cpu_id: int):
        self.cpu_id: int = cpu_id
        self.min_vruntime: float = 0.0
        self.heap: List[Tuple[float, int, Process]] = []
        self._entry_sequence: int = 0
        self._removed_pids: set = set()

    def update_min_vruntime(self, current_running: Optional[Process] = None) -> float:
        """
        Updates cfs_rq->min_vruntime monotonically.

        Linux Kernel Concept:
        `min_vruntime` tracks the minimum virtual runtime among all runnable entities on this CPU.
        It must never decrease (monotonic non-decreasing). When a CPU is active, `min_vruntime`
        advances as the running task's vruntime increases and new minimums are exposed in the queue.

        Args:
            current_running: The process currently executing on the CPU (if any).

        Returns:
            float: The updated min_vruntime value.
        """
        candidates: List[float] = [self.min_vruntime]

        if current_running and current_running.state == ProcessState.RUNNING:
            candidates.append(current_running.vruntime)

        # Inspect leftmost process in queue without popping
        active_heap = [entry for entry in self.heap if entry[2].pid not in self._removed_pids]
        if active_heap:
            candidates.append(active_heap[0][0])

        new_min = max(candidates)
        self.min_vruntime = max(self.min_vruntime, new_min)
        return self.min_vruntime

    def enqueue(self, process: Process, is_waking: bool = False, thresh: float = 3.0) -> None:
        """
        Enqueues a process into the CFS run queue (`enqueue_entity` / `place_entity`).

        Sleeper Fairness Concept:
        When an I/O-bound process sleeps for a long time, its vruntime stops advancing while other
        processes' vruntimes increase with CPU time. Upon waking, the sleeping task's vruntime would
        be far smaller than `min_vruntime`. Without intervention, it would monopolize the CPU for a long period.
        Linux CFS prevents this in `place_entity()` by setting:
            vruntime = max(vruntime, min_vruntime - thresh)
        where `thresh` is typically half of `sched_latency` (e.g. 3ms). This gives sleeping processes a slight
        priority boost (for interactive responsiveness) without starving other tasks.

        Args:
            process: The Process instance to enqueue.
            is_waking: True if the process is waking up from SLEEPING state.
            thresh: Max latency credit allowed for sleeping tasks (ms).
        """
        if is_waking:
            # Enforce sleeper fairness (place_entity in kernel/sched/fair.c)
            vruntime_floor = max(0.0, self.min_vruntime - thresh)
            process.vruntime = max(process.vruntime, vruntime_floor)

        # Set task state to READY
        process.state = ProcessState.READY
        process.assigned_cpu = self.cpu_id

        # Clean up any previous removal marker for this PID
        self._removed_pids.discard(process.pid)

        self._entry_sequence += 1
        entry = (process.vruntime, self._entry_sequence, process)
        heapq.heappush(self.heap, entry)

        # Recalculate min_vruntime
        self.update_min_vruntime()

    def dequeue_min(self) -> Optional[Process]:
        """
        Picks and removes the process with the smallest vruntime (`pick_next_entity`).

        Returns:
            Optional[Process]: The process with lowest vruntime, or None if queue is empty.
        """
        while self.heap:
            vruntime, seq, process = heapq.heappop(self.heap)
            if process.pid in self._removed_pids:
                self._removed_pids.remove(process.pid)
                continue
            
            # Recalculate min_vruntime after removing task
            self.update_min_vruntime()
            return process

        return None

    def peek_min(self) -> Optional[Process]:
        """
        Returns the process with the smallest vruntime without removing it from queue.

        Returns:
            Optional[Process]: Process reference or None if empty.
        """
        while self.heap:
            vruntime, seq, process = self.heap[0]
            if process.pid in self._removed_pids:
                heapq.heappop(self.heap)
                self._removed_pids.remove(process.pid)
                continue
            return process
        return None

    def remove(self, process: Process) -> bool:
        """
        Removes an arbitrary process from the run queue (e.g. for CPU load balancing migration).

        Uses soft deletion to maintain heap invariants cleanly.

        Args:
            process: The process to remove.

        Returns:
            bool: True if process was present in queue and marked removed.
        """
        # Check if process is present in heap
        present = any(p.pid == process.pid for _, _, p in self.heap if p.pid not in self._removed_pids)
        if present:
            self._removed_pids.add(process.pid)
            self.update_min_vruntime()
            return True
        return False

    def get_all_processes(self) -> List[Process]:
        """
        Returns list of all active non-removed processes currently in runqueue.
        """
        return [p for _, _, p in self.heap if p.pid not in self._removed_pids]

    def total_weight(self) -> float:
        """
        Calculates aggregate static weight of all runnable processes in runqueue (`cfs_rq->load.weight`).
        Used to calculate per-process dynamic time slices (`sched_slice`).

        Returns:
            float: Total weight sum.
        """
        return sum(p.weight for p in self.get_all_processes())

    def count(self) -> int:
        """
        Returns count of active ready processes in queue (`cfs_rq->nr_running`).
        """
        return len(self.get_all_processes())

    def is_empty(self) -> bool:
        """
        Returns True if queue contains no active processes.
        """
        return self.count() == 0

    def __repr__(self) -> str:
        return (
            f"<RunQueue cpu={self.cpu_id} nr_running={self.count()} "
            f"total_weight={self.total_weight():.1f} min_vruntime={self.min_vruntime:.2f}>"
        )
