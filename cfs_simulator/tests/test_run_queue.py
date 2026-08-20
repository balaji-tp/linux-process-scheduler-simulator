"""
test_run_queue.py - Unit tests for CFS min-heap runqueue and sleeper fairness.
"""

import unittest
from cfs_simulator.process import Process
from cfs_simulator.run_queue import RunQueue


class TestRunQueue(unittest.TestCase):

    def setUp(self):
        self.rq = RunQueue(cpu_id=0)

    def test_enqueue_dequeue_min_order(self):
        """Verify runqueue always pops task with smallest vruntime."""
        p1 = Process(pid=1, nice=0)
        p1.vruntime = 15.0

        p2 = Process(pid=2, nice=0)
        p2.vruntime = 5.0

        p3 = Process(pid=3, nice=0)
        p3.vruntime = 20.0

        self.rq.enqueue(p1)
        self.rq.enqueue(p2)
        self.rq.enqueue(p3)

        first_popped = self.rq.dequeue_min()
        second_popped = self.rq.dequeue_min()
        third_popped = self.rq.dequeue_min()

        self.assertEqual(first_popped.pid, 2)   # vruntime 5.0
        self.assertEqual(second_popped.pid, 1)  # vruntime 15.0
        self.assertEqual(third_popped.pid, 3)   # vruntime 20.0

    def test_min_vruntime_monotonicity(self):
        """Verify min_vruntime never decreases."""
        self.rq.min_vruntime = 50.0

        p = Process(pid=1, nice=0)
        p.vruntime = 40.0
        self.rq.enqueue(p)

        # min_vruntime should remain at least 50.0
        self.assertGreaterEqual(self.rq.min_vruntime, 50.0)

    def test_sleeper_fairness_clamping(self):
        """Verify woken process vruntime is clamped against (min_vruntime - thresh)."""
        self.rq.min_vruntime = 100.0

        woken_proc = Process(pid=1, nice=0)
        woken_proc.vruntime = 10.0  # Far behind min_vruntime

        thresh = 3.0
        self.rq.enqueue(woken_proc, is_waking=True, thresh=thresh)

        # Should be clamped to max(10.0, 100.0 - 3.0) = 97.0
        expected_vruntime = 100.0 - thresh
        self.assertAlmostEqual(woken_proc.vruntime, expected_vruntime, places=2)


if __name__ == "__main__":
    unittest.main()
