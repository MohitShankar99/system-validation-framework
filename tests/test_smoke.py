from framework.base import SystemTestCase, tag
from framework.dut import State, InvalidTransition, DeviceError
from framework.validators import timed, assert_in_range


class TestBootAndStateMachine(SystemTestCase):

    @tag("smoke")
    def test_boot_reaches_ready(self):
        self.boot()
        self.assertIsNone(self.dut.fault_code)

    @tag("smoke", "performance")
    def test_boot_time_within_spec(self):
        with timed() as t:
            self.dut.power_on()
        assert_in_range("boot_time_s", t["s"], 0, self.spec["boot"]["max_time_s"])

    @tag("smoke")
    def test_full_lifecycle(self):
        self.boot_and_run()
        self.dut.stop()
        self.assertEqual(self.dut.state, State.READY)
        self.dut.power_off()
        self.assertEqual(self.dut.state, State.OFF)

    @tag("regression")
    def test_illegal_transitions_rejected(self):
        with self.assertRaises(InvalidTransition):
            self.dut.start()            # OFF -> RUNNING is illegal
        self.boot()
        with self.assertRaises(InvalidTransition):
            self.dut.power_on()         # READY -> BOOTING is illegal

    @tag("regression")
    def test_no_io_while_off(self):
        with self.assertRaises(DeviceError):
            self.dut.read_sensors()
        with self.assertRaises(DeviceError):
            self.dut.send_command("PING")
