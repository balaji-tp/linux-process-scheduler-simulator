# 🐧 Linux Process Scheduler Simulator

```text
██╗     ██╗███╗   ██╗██╗   ██╗██╗  ██╗
██║     ██║████╗  ██║██║   ██║╚██╗██╔╝
██║     ██║██╔██╗ ██║██║   ██║ ╚███╔╝
██║     ██║██║╚██╗██║██║   ██║ ██╔██╗
███████╗██║██║ ╚████║╚██████╔╝██╔╝ ██╗
╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝

        PROCESS SCHEDULER SIMULATOR
```

### ⚙️ Linux CFS Scheduling • Multi-CPU Load Balancing • Fairness Analysis

**A Python-based educational simulator that models Linux Completely Fair Scheduler (CFS) concepts, virtual runtime scheduling, process priorities, multi-CPU load balancing, and scheduling performance metrics.**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square\&logo=python)
![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualization-orange?style=flat-square\&logo=plotly)
![Linux](https://img.shields.io/badge/Linux-Scheduling-black?style=flat-square\&logo=linux)
![CFS](https://img.shields.io/badge/Scheduler-CFS-green?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-unittest-success?style=flat-square)

---

## 📌 Overview

**Linux Process Scheduler Simulator** is a Python-based simulation of the **Linux Completely Fair Scheduler (CFS)** designed to make operating-system scheduling concepts easier to understand through an executable model and visual analysis.

The simulator creates synthetic CPU-bound and I/O-bound processes, assigns them to multiple CPU cores, schedules them according to **virtual runtime (`vruntime`)**, applies Linux-style priority weights, performs process preemption, balances workload across CPUs, and calculates fairness and performance metrics.

Instead of only studying scheduling theory, this project allows you to **observe how a scheduler behaves over time**.

### 🎯 What This Project Demonstrates

```text
                PROCESS WORKLOAD
                       │
                       ▼
              ┌─────────────────┐
              │ Process Creation │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ CFS Scheduler   │
              │                 │
              │ • vruntime      │
              │ • Nice Weight   │
              │ • Time Slice    │
              │ • Preemption    │
              └────────┬────────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
         ┌────────┐          ┌────────┐
         │ CPU 0  │          │ CPU 1  │
         └────────┘          └────────┘
             │                   │
         ┌────────┐          ┌────────┐
         │ CPU 2  │          │ CPU 3  │
         └────────┘          └────────┘
             │                   │
             └─────────┬─────────┘
                       ▼
              ┌─────────────────┐
              │ Load Balancing  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Metrics &       │
              │ Visualization   │
              └─────────────────┘
```

---

## ✨ Key Features

| Feature                      | Description                                                            |
| ---------------------------- | ---------------------------------------------------------------------- |
| ⚖️ **CFS Scheduling**        | Selects processes based on the lowest virtual runtime                  |
| 🧮 **Virtual Runtime**       | Tracks normalized CPU execution for fairness                           |
| 🎚️ **Nice Priority**        | Maps Linux `nice` values to scheduling weights                         |
| ⏱️ **Dynamic Time Slicing**  | Calculates CPU time based on process weights                           |
| 🔄 **Preemption**            | Switches processes when scheduling conditions require it               |
| 💤 **Sleeper Fairness**      | Prevents newly awakened processes from unfairly dominating CPU time    |
| 🖥️ **Multi-CPU Simulation** | Simulates scheduling across 4 CPU cores                                |
| ⚡ **Load Balancing**         | Migrates processes between CPUs to reduce imbalance                    |
| 📊 **Fairness Metrics**      | Calculates Jain's Fairness Index                                       |
| 📈 **Performance Metrics**   | Measures waiting time, turnaround time, throughput and CPU utilization |
| 🔀 **Process Migration**     | Tracks workload movement between CPU cores                             |
| 🎨 **Visualization**         | Generates Gantt charts, heatmaps and fairness graphs                   |
| 🧪 **Unit Testing**          | Includes Python `unittest` based scheduler tests                       |
| 🔬 **Synthetic Workloads**   | Supports CPU-bound, I/O-bound and mixed workloads                      |

---

# 🏗️ System Architecture

```text
                    ┌─────────────────────────┐
                    │   Workload Generator    │
                    │                         │
                    │ CPU-Bound / I/O-Bound   │
                    │      / Mixed            │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      Process Model       │
                    │                         │
                    │ PID / Nice / Weight     │
                    │ Arrival / Burst / I/O   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      CFS Scheduler      │
                    │                         │
                    │ • vruntime              │
                    │ • Time Slice            │
                    │ • Preemption             │
                    │ • Sleeper Fairness       │
                    └────────────┬────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
           ┌─────────┐      ┌─────────┐      ┌─────────┐
           │  CPU 0  │      │  CPU 1  │      │  CPU 2  │
           │ RunQueue│      │ RunQueue│      │ RunQueue│
           └─────────┘      └─────────┘      └─────────┘
                                                    │
                                               ┌─────────┐
                                               │  CPU 3  │
                                               │ RunQueue│
                                               └────┬────┘
                                                    │
                                                    ▼
                                      ┌────────────────────────┐
                                      │   Multi-CPU Balancer    │
                                      │                         │
                                      │ Process Migration       │
                                      │ Load Redistribution     │
                                      └────────────┬───────────┘
                                                   │
                                                   ▼
                                      ┌────────────────────────┐
                                      │ Metrics & Visualization │
                                      │                         │
                                      │ • Fairness              │
                                      │ • CPU Utilization       │
                                      │ • Waiting Time           │
                                      │ • Turnaround Time        │
                                      │ • Context Switches      │
                                      └────────────────────────┘
```

---

# 🧠 How the Scheduler Works

The simulator follows the major stages of a CFS-style scheduler.

### 1. Process Creation

The workload generator creates processes with properties such as:

```text
PID
Process Name
Nice Value
CPU Burst Time
Arrival Time
I/O Behavior
```

---

### 2. Priority Weight Calculation

Each process receives a scheduling weight based on its Linux-style `nice` value.

The simulator implements the relationship:

```text
weight = 1024 / (1.25 ^ nice)
```

Conceptually:

```text
Lower nice value
       ↓
Higher weight
       ↓
More CPU share

Higher nice value
       ↓
Lower weight
       ↓
Less CPU share
```

---

### 3. Virtual Runtime

The scheduler maintains a `vruntime` value for every runnable process.

A simplified update is:

```text
vruntime += execution_time × (1024 / weight)
```

The scheduler generally selects the process with the **smallest `vruntime`**.

This allows processes with different priorities to receive CPU time proportionally while maintaining fairness.

---

### 4. Dynamic Time Slice

The simulator calculates a process's time slice based on its scheduling weight.

Conceptually:

```text
Time Slice =
Scheduling Period ×
(Process Weight / Total Runnable Weight)
```

This means higher-weight processes receive a larger CPU share.

---

### 5. Process Preemption

The scheduler checks whether:

* The current task has consumed its scheduling slice
* Another runnable process has a lower `vruntime`
* The process should yield the CPU

If required, the scheduler performs a context switch.

---

### 6. Sleeper Fairness

I/O-bound processes frequently leave and re-enter the run queue.

To prevent a newly awakened process from receiving an unfair CPU advantage, the simulator uses a `min_vruntime` based placement mechanism inspired by Linux's `place_entity()` behavior.

---

### 7. Multi-CPU Load Balancing

The simulator uses **4 CPU cores**.

Each CPU maintains an independent run queue:

```text
CPU 0 → Run Queue
CPU 1 → Run Queue
CPU 2 → Run Queue
CPU 3 → Run Queue
```

When one CPU becomes significantly more loaded than another, processes can be migrated to improve workload distribution.

---

# 📊 Workload Generation

The simulator supports three workload types.

### 🧮 CPU-Bound Workload

Represents processes that require long CPU execution periods.

Examples:

* Scientific computation
* Video encoding
* Mathematical processing
* Batch jobs

---

### 💾 I/O-Bound Workload

Represents interactive processes that alternate between CPU execution and I/O waiting.

Examples:

* Web requests
* Database operations
* File operations
* Network applications

---

### 🔀 Mixed Workload

The default simulation uses a mixed workload containing:

```text
50% CPU-Bound Processes
+
50% I/O-Bound Processes
```

The default demo creates:

```text
50 Processes
4 CPU Cores
```

with reproducible workload generation using a fixed random seed.

---

# 🛠️ Tech Stack

| Category                      | Technology                                         |
| ----------------------------- | -------------------------------------------------- |
| **Programming Language**      | Python 3.8+                                        |
| **Scheduling Model**          | Linux CFS-inspired scheduler                       |
| **Data Structure**            | Python `heapq` Min-Heap                            |
| **Visualization**             | Matplotlib                                         |
| **Testing**                   | Python `unittest`                                  |
| **Workload Generation**       | Python `random`                                    |
| **Operating System Concepts** | CPU Scheduling, Process Management, Load Balancing |

---

# 📂 Project Structure

```text
Linux-Process-Scheduler-Simulator/
│
├── cfs_simulator/
│   │
│   ├── __init__.py
│   │      └── Package initialization
│   │
│   ├── process.py
│   │      └── Process model and nice-to-weight mapping
│   │
│   ├── run_queue.py
│   │      └── Per-CPU priority run queue
│   │
│   ├── scheduler.py
│   │      └── CFS scheduling engine and load balancing
│   │
│   ├── workload.py
│   │      └── CPU, I/O and mixed workload generation
│   │
│   ├── metrics.py
│   │      └── Fairness and performance calculations
│   │
│   ├── visualize.py
│   │      └── Matplotlib chart generation
│   │
│   ├── main.py
│   │      └── Simulation entry point
│   │
│   ├── tests/
│   │   ├── test_process.py
│   │   ├── test_run_queue.py
│   │   └── test_scheduler.py
│   │
│   └── README.md
│
├── output/
│   ├── gantt_chart.png
│   ├── vruntime_convergence.png
│   ├── cpu_load_heatmap.png
│   └── fairness_trend.png
│
├── README.md
└── .gitignore
```

---

# 🔄 Request / Scheduling Workflow

```text
Process Creation
       │
       ▼
Calculate Nice Weight
       │
       ▼
Process Enters Run Queue
       │
       ▼
Select Lowest vruntime
       │
       ▼
Calculate Time Slice
       │
       ▼
Execute Process
       │
       ▼
Update vruntime
       │
       ├───────────────┐
       │               │
       ▼               ▼
Process Complete    Process Sleeps
       │               │
       │               ▼
       │          I/O Wait
       │               │
       │               ▼
       │        Re-enter Run Queue
       │               │
       └───────┬───────┘
               ▼
        Load Balancing
               │
               ▼
      Performance Metrics
               │
               ▼
       Visualization
```

---

# 🐧 Linux Kernel Concept Mapping

The project is designed around concepts from the Linux scheduler, particularly the traditional CFS implementation.

| Simulator                | Linux Concept                  | Purpose                                    |
| ------------------------ | ------------------------------ | ------------------------------------------ |
| `Process`                | `task_struct` / `sched_entity` | Represents a schedulable process           |
| `Process.weight`         | `se.load.weight`               | Scheduling weight                          |
| `Process.vruntime`       | `se.vruntime`                  | Virtual execution time                     |
| `RunQueue`               | `cfs_rq`                       | Per-CPU runnable task queue                |
| `min_vruntime`           | `cfs_rq->min_vruntime`         | Tracks minimum virtual runtime             |
| `calculate_time_slice()` | `sched_slice()`                | Determines scheduling slice                |
| `update_vruntime()`      | `update_curr()`                | Updates virtual runtime                    |
| `enqueue()`              | `place_entity()`               | Places a task fairly into the run queue    |
| Preemption logic         | `check_preempt_tick()`         | Determines when a task should be preempted |
| Load balancing           | `load_balance()`               | Redistributes tasks across CPUs            |

> **Note:** This project is an educational simulation. It models important Linux scheduler concepts but is not an implementation of the Linux kernel scheduler itself.

---

# ⚖️ Run Queue Design

The actual Linux scheduler uses a **Red-Black Tree** for its CFS run queue.

This project uses Python's `heapq` implementation of a **min-heap**.

| Operation      | Linux CFS            | Python Simulator |
| -------------- | -------------------- | ---------------- |
| Data Structure | Red-Black Tree       | Min-Heap         |
| Find minimum   | Cached leftmost node | Heap root        |
| Insert         | `O(log N)`           | `O(log N)`       |
| Peek minimum   | `O(1)`               | `O(1)`           |
| Implementation | Kernel-level         | Python           |

### Why use a Min-Heap?

The primary operation of this simulator is selecting the process with the smallest `vruntime`.

Python's `heapq` provides a simple and efficient way to model this behavior while keeping the implementation understandable for students and developers learning OS scheduling.

---

# 📈 Performance Metrics

The simulator calculates several important scheduling metrics.

| Metric                    | Description                                       |
| ------------------------- | ------------------------------------------------- |
| **Jain's Fairness Index** | Measures how evenly CPU resources are distributed |
| **Waiting Time**          | Time spent waiting for CPU execution              |
| **Turnaround Time**       | Time from process arrival to completion           |
| **Throughput**            | Number of completed processes                     |
| **CPU Utilization**       | Percentage of active CPU time                     |
| **Context Switches**      | Number of process switches                        |
| **Process Migrations**    | Number of processes moved between CPUs            |

### Jain's Fairness Index

The simulator uses Jain's Fairness Index:

```text
             (Σxᵢ)²
J = ─────────────────────────
        n × Σ(xᵢ²)
```

Interpretation:

```text
1.0 → Perfect Fairness
0.9 → High Fairness
0.5 → Moderate Fairness
0.0 → Poor Fairness
```

---

# 📊 Simulation Output

After running the simulator, four visualization files are generated inside the `output/` directory.

## 1. Gantt Chart

The Gantt chart shows process execution across the four CPU cores.

![CFS Gantt Chart](output/gantt_chart.png)

### It helps visualize:

* Process execution
* CPU allocation
* Context switches
* Process scheduling
* Multi-core execution

---

## 2. Vruntime Convergence

The virtual runtime graph shows how process `vruntime` values evolve throughout the simulation.

![Vruntime Convergence](output/vruntime_convergence.png)

### It demonstrates:

* Virtual runtime progression
* Priority-aware scheduling
* Fair CPU distribution
* CFS scheduling behavior

---

## 3. CPU Load Heatmap

The heatmap shows the load distribution across all CPU cores over simulation time.

![CPU Load Heatmap](output/cpu_load_heatmap.png)

### It demonstrates:

* CPU utilization
* Load imbalance
* Process migration
* Multi-CPU load balancing

---

## 4. Fairness Trend

The fairness graph tracks Jain's Fairness Index during the simulation.

![Fairness Trend](output/fairness_trend.png)

### It demonstrates:

* Scheduling fairness over time
* Fairness convergence
* CPU resource distribution

---

# 🚀 Quick Start

## Prerequisites

Make sure you have:

* Python **3.8 or newer**
* pip
* Git

Check your Python installation:

```bash
python --version
```

---

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/Linux-Process-Scheduler-Simulator.git
```

```bash
cd Linux-Process-Scheduler-Simulator
```

---

## 2. Install Dependencies

Install Matplotlib:

```bash
pip install matplotlib
```

If you are using a virtual environment:

```bash
python -m venv venv
```

Activate it on Linux/macOS:

```bash
source venv/bin/activate
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Then:

```bash
pip install matplotlib
```

---

## 3. Run the Simulator

From the project root:

```bash
python -m cfs_simulator.main
```

The default simulation runs:

```text
50 Processes
4 CPU Cores
Mixed CPU + I/O Workload
```

The generated charts will be saved to:

```text
output/
```

---

# 🧪 Run Unit Tests

Run all tests using:

```bash
python -m unittest discover -s cfs_simulator/tests
```

The test suite verifies important scheduler behavior including:

* Process creation
* Nice-to-weight calculation
* Virtual runtime behavior
* Run queue operations
* Scheduler behavior
* Fairness
* Load balancing

---

# 🖥️ Example Simulation

The default simulation pipeline looks like:

```text
50 Processes
      │
      ▼
Mixed Workload Generation
      │
      ▼
4 CPU Cores
      │
      ▼
CFS Scheduling
      │
      ├── vruntime
      ├── Nice Weight
      ├── Time Slice
      └── Preemption
      │
      ▼
CPU Load Balancing
      │
      ▼
Performance Analysis
      │
      ├── Waiting Time
      ├── Turnaround Time
      ├── CPU Utilization
      ├── Context Switches
      ├── Migrations
      └── Fairness
      │
      ▼
Visualization
```

---

# 🎓 Learning Outcomes

This project helps demonstrate practical understanding of:

* Operating System process scheduling
* Linux scheduling concepts
* Completely Fair Scheduler
* Virtual runtime
* Process priority
* CPU time allocation
* Context switching
* Process preemption
* Multi-core scheduling
* CPU load balancing
* Scheduling fairness
* Performance measurement
* Python data structures
* Algorithm visualization

---

# 💡 Why This Project?

Operating-system scheduling is usually taught through theoretical algorithms and diagrams.

This project converts those concepts into a working simulation where you can:

```text
CREATE
  ↓
SCHEDULE
  ↓
MEASURE
  ↓
VISUALIZE
  ↓
ANALYZE
```

This makes it useful for:

* Operating Systems coursework
* Linux learning
* Systems programming
* Kernel concepts
* CPU scheduling experiments
* Technical interviews
* Academic demonstrations

---

# 🔮 Future Improvements

### Scheduler Improvements

* [ ] Implement EEVDF scheduling
* [ ] Compare CFS and EEVDF
* [ ] Add Round Robin scheduler
* [ ] Add FCFS scheduler
* [ ] Add SJF scheduler
* [ ] Add Priority Scheduling
* [ ] Compare multiple scheduling algorithms

### Simulation Improvements

* [ ] Interactive process input
* [ ] Configurable CPU core count
* [ ] Configurable scheduling latency
* [ ] Configurable process count
* [ ] Real-time simulation dashboard
* [ ] Export metrics to CSV

### Visualization Improvements

* [ ] Interactive Gantt chart
* [ ] Interactive CPU utilization dashboard
* [ ] Process-level performance comparison
* [ ] Scheduling algorithm comparison charts

---

# 🐧 CFS and EEVDF

This simulator focuses on the **traditional Linux CFS model** for educational purposes.

Modern Linux has moved the fair-class scheduler toward **EEVDF (Earliest Eligible Virtual Deadline First)**.

A future version of this project can compare:

```text
             ┌───────────────┐
             │   Workload    │
             └───────┬───────┘
                     │
             ┌───────┴────────┐
             ▼                ▼
       ┌───────────┐    ┌───────────┐
       │    CFS    │    │   EEVDF   │
       └─────┬─────┘    └─────┬─────┘
             │                │
             ▼                ▼
       Fairness         Fairness
       Latency          Latency
       Throughput       Throughput
             │                │
             └───────┬────────┘
                     ▼
              Comparison
```

This would make the project more useful for studying the evolution of Linux CPU scheduling.

---

# 📁 Generated Output Files

After running the simulator:

```text
output/
│
├── gantt_chart.png
├── vruntime_convergence.png
├── cpu_load_heatmap.png
└── fairness_trend.png
---

# ⭐ Support

If this project helped you understand Linux process scheduling, consider giving the repository a ⭐ on GitHub.

---

## 📄 License

This project is intended for **educational and learning purposes**.

---

<div align="center">

### 🐧 Linux Process Scheduler Simulator

**Simulate • Measure • Visualize • Understand**

⭐ Star the repository if you find it useful!

</div>
