"""Explicit time axes and stimulus units for reproducible single-cell experiments."""

from dataclasses import asdict, dataclass
import numpy as np


@dataclass(frozen=True)
class Protocol:
    duration_ms: float = 400.0
    dt_ms: float = 0.05
    start_ms: float = 50.0
    stop_ms: float = 350.0
    amplitude: float = 1.0
    kind: str = "step"
    frequency_hz: float = 10.0

    def validate(self):
        values = [self.duration_ms, self.dt_ms, self.start_ms, self.stop_ms,
                  self.amplitude, self.frequency_hz]
        if not np.isfinite(values).all():
            raise ValueError("Protocol values must be finite.")
        if not 0 < self.dt_ms <= self.duration_ms <= 2000:
            raise ValueError("Require 0 < dt <= duration <= 2000 ms.")
        if not 0 <= self.start_ms < self.stop_ms <= self.duration_ms:
            raise ValueError("Require 0 <= start < stop <= duration.")
        if self.kind not in {"step", "ramp", "sine"}:
            raise ValueError("Unknown stimulus waveform.")
        if self.frequency_hz < 0:
            raise ValueError("Frequency must be nonnegative.")
        steps = self.duration_ms / self.dt_ms
        if not np.isclose(steps, round(steps)) or steps > 200_000:
            raise ValueError("Duration must be a multiple of dt, with at most 200000 steps.")

    def samples(self):
        self.validate()
        times = np.arange(round(self.duration_ms / self.dt_ms)) * self.dt_ms
        active = (times >= self.start_ms) & (times < self.stop_ms)
        elapsed = times[active] - self.start_ms
        drive = np.zeros(len(times))
        if self.kind == "step":
            drive[active] = self.amplitude
        elif self.kind == "ramp":
            drive[active] = self.amplitude * elapsed / (self.stop_ms - self.start_ms)
        else:
            drive[active] = self.amplitude * np.sin(2 * np.pi * self.frequency_hz * elapsed / 1000)
        return times, drive

    def as_dict(self):
        return asdict(self)
