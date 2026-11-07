"""Base class, tagging and spec loading shared by all system tests."""
import json
import unittest
from pathlib import Path

from .dut import SimulatedDevice, State

SPEC_PATH = Path(__file__).resolve().parent.parent / "config" / "spec.json"


def load_spec():
    return json.loads(SPEC_PATH.read_text())


def tag(*names):
    """Label tests (smoke, regression, fault, performance) for selective runs."""
    def decorator(func):
        func.tags = set(getattr(func, "tags", set())) | set(names)
        return func
    return decorator


class SystemTestCase(unittest.TestCase):
    spec = load_spec()

    def setUp(self):
        self.dut = SimulatedDevice(seed=42, boot_time_s=self.spec["boot"]["simulated_time_s"])
        self.addCleanup(self.dut.shutdown)  # always leave the DUT OFF

    def boot(self):
        self.dut.power_on()
        self.assertEqual(self.dut.state, State.READY)

    def boot_and_run(self):
        self.boot()
        self.dut.start()
        self.assertEqual(self.dut.state, State.RUNNING)
