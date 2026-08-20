"""
test_scheduler.py - Unit tests verifying CFS scheduler correctness and core requirements.
"""

import unittest
from cfs_simulator.process import Process
from cfs_simulator.scheduler import CFSScheduler
from cfs_simulator.workload import generate_cpu_bound_workload, generate_mixed_workload
from cfs_simulator.metrics import calculate_jains_fairness_index, calculate_simulation_metrics


class TestCFSScheduler(unittest.TestCase):

    def test_vruntime_never_negative(self):
        """Requirement Test 1: Verify vruntime is non-negative throughout execution."""
        scheduler = CFSScheduler(num_cpus=2)
        workload = generate_mixed_workload(n_processes=10, seed=10)

        for p in workload:
            scheduler.add_process(p)

        scheduler.run(max_duration=1000.0)

        for p in scheduler.all_processes:
            self.assertGreaterEqual(p.vruntime, 0.0, f"Process {p.pid} has negative vruntime: {p.vruntime}")

    def test_no_process_starvation(self):
        """Requirement Test 2: Verify no process starves indefinitely."""
        scheduler = CFSScheduler(num_cpus=4)

        # Mix of high and low priority processes
        workload = [
            Process(pid=1, nice=-10, total_burst_time=50.0),
            Process(pid=2, nice=-5, total_burst_time=50.0),
            Process(pid=3, nice=0, total_burst_time=50.0),
            Process(pid=4, nice=5, total_burst_time=50.0),
            Process(pid=5, nice=10, total_burst_time=50.0),
        ]

        for p in workload:
            scheduler.add_process(p)

        scheduler.run(max_duration=2000.0)

        # All processes must complete execution
        self.assertTrue(scheduler.is_finished(), "Not all processes completed; starvation detected!")
        for p in workload:
            self.assertIsNotNone(p.completion_time, f"Process {p.pid} never completed!")
            self.assertGreater(p.cpu_time_executed, 0.0, f"Process {p.pid} received 0 CPU time!")

    def test_fairness_index_above_threshold(self):
        """Requirement Test 3: Verify Jain's Fairness Index stays above 0.90 for a balanced nice distribution."""
        scheduler = CFSScheduler(num_cpus=4)

        # Create balanced workload (nice = 0 for all)
        processes = [
            Process(pid=i, nice=0, total_burst_time=100.0, arrival_time=0.0)
            for i in range(1, 17)
        ]

        for p in processes:
            scheduler.add_process(p)

        scheduler.run(max_duration=2000.0)

        fairness = calculate_jains_fairness_index(scheduler.completed_processes)
        self.assertGreaterEqual(
            fairness,
            0.90,
            f"Jain's Fairness Index {fairness:.3f} fell below 0.90 target for balanced workload!"
        )

    def test_load_balancing_reduces_imbalance(self):
        """Requirement Test 4: Verify load balancing active migration reduces queue load variance."""
        # Scenario A: Load balancing enabled
        sched_with_lb = CFSScheduler(num_cpus=4, load_balance_interval=5.0)

        # Load all 20 processes initially onto CPU 0 artificially to create massive imbalance
        workload = [Process(pid=i, nice=0, total_burst_time=80.0) for i in range(1, 21)]
        for p in workload:
            sched_with_lb.cpus[0].run_queue.enqueue(p)
            sched_with_lb.all_processes.append(p)
            sched_with_lb.vruntime_history[p.pid] = [(0.0, 0.0)]

        # Step scheduler several times to trigger load balancing
        for _ in range(50):
            sched_with_lb.step(time_step=1.0)

        # Check migration occurred
        self.assertGreater(sched_with_lb.migration_count, 0, "Load balancer failed to migrate tasks from overloaded CPU!")

        # Verify tasks distributed across multiple CPUs
        active_cpus = sum(1 for c in sched_with_lb.cpus if c.get_nr_running() > 0 or c.total_active_time > 0)
        self.assertGreater(active_cpus, 1, "Load balancer failed to utilize idle CPUs!")


if __name__ == "__main__":
    unittest.main()
