# Linux CFS (Completely Fair Scheduler) Simulator

A modular, production-grade Python simulation engine modeling the **Linux Completely Fair Scheduler (CFS)** and multi-CPU load balancer. Built to demonstrate OS kernel scheduling mechanics, priority weighting, virtual runtime convergence, and fairness metrics for systems engineering and kernel design interviews.
---

## 🌟 Key Features

- **Exact Linux CFS Weight Formula**: Implements $weight = \frac{1024}{1.25^{\text{nice}}}$ mapping nice priorities (-20 to +19) to static weights (`sched_prio_to_weight`).
- **Virtual Runtime (vruntime) Engine**: Fair scheduling where the process with the smallest `vruntime` runs next.
- **Sleeper Fairness**: Prevents woken interactive processes from monopolizing CPU resources by clamping `vruntime` against queue `min_vruntime` (`place_entity`).
- **Dynamic Time Slicing**: Dynamic period allocation (`sched_slice`) scaling with total runnable weight and minimum granularity (`sched_min_granularity`).
- **Multi-CPU Core Load Balancing**: Simulates 4 CPU cores with independent run queues (`cfs_rq`) and periodic load balancing migrations (`load_balance`).
- **Performance & Fairness Metrics**: Implements **Jain's Fairness Index**, turnaround times, waiting times, throughput, CPU utilization %, and context switch overhead.
- **Matplotlib Visualizations**: Automated chart generation saving Gantt charts, vruntime convergence graphs, load heatmaps, and fairness trends to `output/`.
- **Unit Testing Suite**: Verified using `unittest` for vruntime non-negativity, starvation prevention, fairness threshold (>0.90), and load balancing effectiveness.

---

## 🏗️ Project Architecture

```
cfs_simulator/
├── __init__.py         # Package initialization
├── process.py          # Process PCB model & Linux nice-to-weight mapping
├── run_queue.py        # Per-CPU min-heap runqueue with min_vruntime tracking
├── scheduler.py        # Core CFS multi-CPU engine, time slicing & load balancer
├── workload.py         # Synthetic workload generators (CPU-bound, I/O-bound, mixed)
├── metrics.py          # Jain's fairness index & performance metric calculations
├── visualize.py        # Matplotlib visualization rendering pipeline
├── main.py             # Entry point running 50-process simulation end-to-end
├── tests/              # Unit test suite verifying scheduler correctness
│   ├── __init__.py
│   ├── test_process.py
│   ├── test_run_queue.py
│   └── test_scheduler.py
└── README.md           # Technical documentation & kernel mapping guide
```

---

## 🐧 Linux Kernel Mapping Guide

This simulator directly mirrors core abstractions, structures, and algorithms from the Linux kernel source code (`kernel/sched/fair.c` & `include/linux/sched.h`):

| Simulator Component | Linux Kernel Structure / Function | Purpose & Description |
| :--- | :--- | :--- |
| `Process` | `struct task_struct` & `struct sched_entity` | Represents an OS process PCB and its scheduling entity (`se`). |
| `Process.weight` | `se.load.weight` | Static process weight derived from nice priority level. |
| `Process.vruntime` | `se.vruntime` | Accumulated virtual execution time in nanoseconds/milliseconds. |
| `RunQueue` | `struct cfs_rq` | Per-CPU CFS runqueue tracking runnable entities. |
| `RunQueue.min_vruntime` | `cfs_rq->min_vruntime` | Monotonic minimum `vruntime` tracking active queue state. |
| `calculate_time_slice()` | `sched_slice()` | Calculates dynamic time slice $T_{\text{slice}} = \text{latency} \times \frac{w_i}{\sum w}$. |
| `update_vruntime()` | `update_curr()` | Advances $vruntime += \Delta t \times \frac{1024.0}{w_i}$ and updates execution stats. |
| `RunQueue.enqueue()` | `place_entity()` | Applies sleeper fairness: $vruntime = \max(vruntime, min\_vruntime - \text{thresh})$. |
| `check_preempt_tick()` | `check_preempt_tick()` | Preempts running task if slice is exhausted or a task with lower `vruntime` is queued. |
| `load_balance()` | `load_balance()` | Equalizes runqueue load weights across CPU cores via task migration. |

---

## ⚖️ Design Tradeoff: Red-Black Tree vs. Min-Heap

| Property | Linux Kernel Red-Black Tree (`rb_root_cached`) | Python Simulator Min-Heap (`heapq`) |
| :--- | :--- | :--- |
| **Pick Next Task** | $O(1)$ via cached leftmost pointer (`rb_leftmost`) | $O(1)$ peek min element |
| **Insert Task** | $O(\log N)$ tree insertion | $O(\log N)$ heap push |
| **Delete Task** | $O(\log N)$ arbitrary tree deletion | $O(N)$ search or $O(1)$ lazy soft-deletion |
| **Space Complexity** | $O(N)$ pointers per node | $O(N)$ array memory footprint |

### Why Min-Heap in Python?
Real Linux CFS uses a Red-Black Tree because arbitrary tasks can block, sleep, or exit at any time, requiring $O(\log N)$ arbitrary node removal. In Python's standard library, binary min-heap (`heapq`) provides C-speed operations for picking the task with minimum `vruntime` ($O(1)$ peek) and enqueuing tasks ($O(\log N)$ push). Soft-deletion is used to support arbitrary task migrations during load balancing without breaking heap invariants.

---

## 🚀 How to Run the Simulator

### Prerequisites
- Python 3.8+
- Matplotlib (`pip install matplotlib` or `uv pip install matplotlib`)

### Run End-to-End Simulation
Run the main script to simulate 50 processes across 4 CPUs and view live metrics:

```bash
python -m cfs_simulator.main
```

### Run Unit Tests
Execute the unit test suite to verify scheduler correctness:

```bash
python -m unittest discover -s cfs_simulator/tests
```

---

## 📊 Interpreting Generated Visualizations

All generated visual charts are saved in the `output/` directory:

1. **Gantt Chart (`output/gantt_chart.png`)**:
   - Visualizes execution timeline of tasks scheduled across CPU 0..3.
   - Shows how higher-priority processes (low nice) get larger time slices while lower-priority tasks run in smaller intervals without starving.

2. **Vruntime Convergence Graph (`output/vruntime_convergence.png`)**:
   - Plots process `vruntime` values over time.
   - Proves fairness: all process lines remain tightly clustered together. High-priority tasks execute more physical time to reach the same `vruntime` as low-priority tasks.

3. **Per-CPU Load Heatmap (`output/cpu_load_heatmap.png`)**:
   - Intensity heatmap showing total load weight on each CPU core over time.
   - Demonstrates multi-CPU load balancing: migrations dynamically redistribute load whenever an imbalance occurs.

4. **Fairness Index Trend (`output/fairness_trend.png`)**:
   - Tracks **Jain's Fairness Index** over simulation timeline.
   - Shows rapid convergence and sustained performance above the $0.90$ fairness threshold.

---

## 🔮 Limitations & Future Work (EEVDF in Linux 6.6+)

### Transition to EEVDF
In Linux kernel 6.6 (October 2023), CFS was replaced after 16 years by **EEVDF** (Earliest Eligible Virtual Deadline First), designed by Peter Zijlstra based on Peter Wandeler's 1995 paper.

### Key Differences & Extension Ideas:
- **CFS Limitations**: CFS handles throughput fairness well, but can introduce latency spikes for interactive tasks because it lacks explicit deadline awareness.
- **EEVDF Core Mechanics**:
  1. **Lag**: Difference between expected fair time allocation and actual time received ($Lag_i = V - vruntime_i$).
  2. **Eligibility**: A task is *eligible* to run only if its $Lag_i \ge 0$.
  3. **Virtual Deadline**: Each task requests a latency slice $q$; its deadline is $V_i = vruntime_i + \frac{q}{w_i}$. EEVDF selects the eligible task with the *earliest virtual deadline*.
  
