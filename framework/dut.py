"""Simulated Device Under Test (DUT): a small embedded-controller model.

It has a state machine, sensors, a command interface and fault injection,
so the framework can be demonstrated without real hardware. Swap this class
for a serial/CAN/SSH driver with the same interface to test a real target.
"""
import random
import time
from enum import Enum


class State(Enum):
    OFF = "OFF"
    BOOTING = "BOOTING"
    READY = "READY"
    RUNNING = "RUNNING"
    FAULT = "FAULT"


class DeviceError(Exception):
    """Raised when an operation is not possible in the current device state."""


class InvalidTransition(DeviceError):
    """Raised on an illegal state-machine transition."""


FAULT_CODES = {"E01": "boot failure", "E02": "over-temperature", "E03": "brownout"}


class SimulatedDevice:
    TEMP_LIMIT_C = 85.0
    VOLTAGE_MIN_V = 10.5
    FIRMWARE = "FW-1.4.2"

    TRANSITIONS = {
        State.OFF: {State.BOOTING},
        State.BOOTING: {State.READY, State.FAULT},
        State.READY: {State.RUNNING, State.OFF},
        State.RUNNING: {State.READY, State.FAULT, State.OFF},
        State.FAULT: {State.OFF},
    }

    def __init__(self, seed=None, boot_time_s=0.05):
        self._rng = random.Random(seed)  # seeded => reproducible test runs
        self._boot_time_s = boot_time_s
        self._injected = set()
        self.state = State.OFF
        self.temperature = 25.0
        self.voltage = 12.0
        self.fault_code = None
        self.event_log = []

    # ---- state machine -------------------------------------------------
    def _transition(self, new_state):
        if new_state not in self.TRANSITIONS[self.state]:
            raise InvalidTransition(f"{self.state.value} -> {new_state.value} not allowed")
        self.event_log.append((self.state.value, new_state.value))
        self.state = new_state

    def _fault(self, code):
        self.fault_code = code
        self._transition(State.FAULT)

    def power_on(self):
        self._transition(State.BOOTING)
        time.sleep(self._boot_time_s)
        if "boot_failure" in self._injected:
            self._fault("E01")
        else:
            self._transition(State.READY)

    def start(self):
        self._transition(State.RUNNING)

    def stop(self):
        self._transition(State.READY)

    def power_off(self):
        self._transition(State.OFF)

    def reset(self):
        """Clear a latched fault and return to OFF (fault injection is cleared too)."""
        if self.state is not State.FAULT:
            raise DeviceError("reset is only valid in FAULT state")
        self._injected.clear()
        self.fault_code = None
        self.temperature = 25.0
        self._transition(State.OFF)

    def shutdown(self):
        """Test-teardown helper: force OFF from any state."""
        self.state = State.OFF

    # ---- fault injection ----------------------------------------------
    def inject_fault(self, name):
        if name not in {"boot_failure", "overheat", "brownout"}:
            raise ValueError(f"unknown fault: {name}")
        self._injected.add(name)

    # ---- sensors -------------------------------------------------------
    def read_sensors(self):
        if self.state is State.OFF:
            raise DeviceError("device is OFF")
        if self.state is State.RUNNING:
            self.temperature += 0.3 + self._rng.gauss(0, 0.05)
            if "overheat" in self._injected:
                self.temperature += 15.0
        self.voltage = 12.0 + self._rng.gauss(0, 0.05)
        if "brownout" in self._injected:
            self.voltage = 9.0
        if self.state is State.RUNNING:
            if self.temperature > self.TEMP_LIMIT_C:
                self._fault("E02")
            elif self.voltage < self.VOLTAGE_MIN_V:
                self._fault("E03")
        return {
            "temperature_c": round(self.temperature, 2),
            "voltage_v": round(self.voltage, 3),
            "state": self.state.value,
        }

    # ---- command interface --------------------------------------------
    def send_command(self, cmd):
        if self.state is State.OFF:
            raise DeviceError("device is OFF")
        time.sleep(0.001)  # simulated link latency
        if cmd == "PING":
            return "PONG"
        if cmd == "VERSION":
            return self.FIRMWARE
        if cmd == "STATUS":
            return f"STATE={self.state.value}"
        return "ERR:UNKNOWN_COMMAND"
