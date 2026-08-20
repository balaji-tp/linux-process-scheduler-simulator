"""
test_process.py - Unit tests for Process PCB and weight calculations.
"""

import unittest
from cfs_simulator.process import Process, ProcessState, nice_to_weight, NICE_0_LOAD


class TestProcess(unittest.TestCase):

    def test_nice_to_weight_nice_zero(self):
        """Verify nice 0 maps to exactly NICE_0_LOAD (1024.0)."""
        weight = nice_to_weight(0)
        self.assertAlmostEqual(weight, 1024.0, places=2)

    def test_nice_to_weight_higher_priority(self):
        """Verify lower nice value yields higher weight."""
        weight_nice_minus_5 = nice_to_weight(-5)
        weight_nice_0 = nice_to_weight(0)
        self.assertGreater(weight_nice_minus_5, weight_nice_0)

    def test_nice_to_weight_lower_priority(self):
        """Verify higher nice value yields lower weight."""
        weight_nice_5 = nice_to_weight(5)
        weight_nice_0 = nice_to_weight(0)
        self.assertLess(weight_nice_5, weight_nice_0)

    def test_vruntime_update_high_weight_vs_low_weight(self):
        """Verify high weight process accumulates vruntime slower than low weight process."""
        p_high = Process(pid=1, nice=-5, total_burst_time=100.0)
        p_low = Process(pid=2, nice=5, total_burst_time=100.0)

        exec_time = 10.0
        delta_high = p_high.update_vruntime(exec_time)
        delta_low = p_low.update_vruntime(exec_time)

        self.assertLess(delta_high, delta_low)
        self.assertLess(p_high.vruntime, p_low.vruntime)

    def test_nice_clamping(self):
        """Verify nice values outside [-20, 19] are clamped."""
        p_out_low = Process(pid=1, nice=-50)
        p_out_high = Process(pid=2, nice=50)

        self.assertEqual(p_out_low.nice, -20)
        self.assertEqual(p_out_high.nice, 19)


if __name__ == "__main__":
    unittest.main()
