from framework.base import SystemTestCase, tag
from framework.dut import State, InvalidTransition


class TestFaultInjection(SystemTestCase):

    @tag("fault")
    def test_boot_failure_latches_E01(self):
        self.dut.inject_fault("boot_failure")
        self.dut.power_on()
        self.assertEqual(self.dut.state, State.FAULT)
        self.assertEqual(self.dut.fault_code, "E01")

    @tag("fault")
    def test_overtemperature_raises_E02(self):
        self.boot_and_run()
        self.dut.inject_fault("overheat")
        for _ in range(10):
            self.dut.read_sensors()
            if self.dut.state is State.FAULT:
                break
        self.assertEqual(self.dut.state, State.FAULT)
        self.assertEqual(self.dut.fault_code, "E02")

    @tag("fault")
    def test_brownout_raises_E03(self):
        self.boot_and_run()
        self.dut.inject_fault("brownout")
        self.dut.read_sensors()
        self.assertEqual(self.dut.state, State.FAULT)
        self.assertEqual(self.dut.fault_code, "E03")

    @tag("fault", "regression")
    def test_fault_is_latched_until_reset(self):
        self.boot_and_run()
        self.dut.inject_fault("brownout")
        self.dut.read_sensors()
        with self.assertRaises(InvalidTransition):
            self.dut.start()

    @tag("fault", "regression")
    def test_recovery_after_reset(self):
        self.boot_and_run()
        self.dut.inject_fault("overheat")
        while self.dut.state is not State.FAULT:
            self.dut.read_sensors()
        self.dut.reset()
        self.assertEqual(self.dut.state, State.OFF)
        self.assertIsNone(self.dut.fault_code)
        self.boot()  # device must boot cleanly again
