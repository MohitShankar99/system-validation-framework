from framework.base import SystemTestCase, tag
from framework.validators import assert_in_range, percentile
import time


class TestSensors(SystemTestCase):

    @tag("regression")
    def test_sensor_readings_stay_within_spec(self):
        self.boot_and_run()
        limits = self.spec["sensors"]
        for i in range(limits["samples"]):
            reading = self.dut.read_sensors()
            with self.subTest(sample=i):
                assert_in_range("temperature_c", reading["temperature_c"],
                                limits["temperature_c"]["min"], limits["temperature_c"]["max"])
                assert_in_range("voltage_v", reading["voltage_v"],
                                limits["voltage_v"]["min"], limits["voltage_v"]["max"])

    @tag("regression")
    def test_temperature_trends_upward_under_load(self):
        self.boot_and_run()
        first = self.dut.read_sensors()["temperature_c"]
        for _ in range(20):
            last = self.dut.read_sensors()["temperature_c"]
        self.assertGreater(last, first)


class TestCommandInterface(SystemTestCase):

    @tag("smoke")
    def test_expected_responses(self):
        self.boot_and_run()
        for cmd, expected in self.spec["commands"]["expected_responses"].items():
            with self.subTest(command=cmd):
                self.assertEqual(self.dut.send_command(cmd), expected)

    @tag("performance")
    def test_command_latency_p95(self):
        self.boot_and_run()
        latencies_ms = []
        for _ in range(self.spec["commands"]["samples"]):
            start = time.perf_counter()
            self.dut.send_command("PING")
            latencies_ms.append((time.perf_counter() - start) * 1000)
        p95 = percentile(latencies_ms, 95)
        self.assertLess(p95, self.spec["commands"]["max_p95_latency_ms"],
                        f"p95 latency {p95:.2f} ms exceeds limit")
