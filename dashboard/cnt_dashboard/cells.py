"""One spatial compartment, native Brian2 integration, no implicit simulator fallback.

HH, Morris-Lecar and Izhikevich equations are adapted from CNT's Brian2 notebooks.
The HH notebook uses shifted kinetics and a particular conductance parametrization;
this adapter preserves that variant rather than labeling it the original squid fit.
AdEx follows the Brian2 Brette-Gerstner example. See dashboard/README.md for sources.
"""

from dataclasses import dataclass
from contextlib import contextmanager
from threading import RLock
import numpy as np
from .protocols import Protocol

BRIAN_LOCK = RLock()


@contextmanager
def numpy_codegen(brian):
    previous = brian.prefs.codegen.target
    brian.prefs.codegen.target = "numpy"
    try:
        yield
    finally:
        brian.prefs.codegen.target = previous


@dataclass(frozen=True)
class Parameter:
    default: float
    unit: str


@dataclass(frozen=True)
class CellSpec:
    label: str
    description: str
    input_unit: str
    amplitude: float
    dt_ms: float
    parameters: dict
    notebooks: tuple = ()


CELLS = {
    "lif": CellSpec("Leaky integrate-and-fire", "Passive membrane with a threshold and reset.",
        "pA", 300.0, .05, {
            "C": Parameter(200, "pF"), "gL": Parameter(10, "nS"),
            "EL": Parameter(-65, "mV"), "Vth": Parameter(-50, "mV"),
            "Vr": Parameter(-65, "mV"), "tref": Parameter(2, "ms")},
        ("notebooks/intro/eg_single-cell.ipynb",)),
    "izhikevich": CellSpec("Izhikevich", "Quadratic voltage dynamics and spike-triggered recovery.",
        "model units", 10.0, .05, {
            "a": Parameter(.02, "1"), "b": Parameter(.2, "1"),
            "c": Parameter(-65, "1"), "d": Parameter(8, "1")},
        ("notebooks/numerical-methods/brian2/2007_Izhikevich.ipynb",)),
    "adex": CellSpec("Adaptive exponential integrate-and-fire", "Exponential spike initiation and adaptation.",
        "pA", 800.0, .025, {
            "C": Parameter(281, "pF"), "gL": Parameter(30, "nS"),
            "EL": Parameter(-70.6, "mV"), "VT": Parameter(-50.4, "mV"),
            "DeltaT": Parameter(2, "mV"), "tauw": Parameter(144, "ms"),
            "a": Parameter(4, "nS"), "b": Parameter(80.5, "pA"),
            "Vr": Parameter(-70.6, "mV")}),
    "hh": CellSpec("Hodgkin-Huxley · CNT notebook variant", "One compartment with sodium, potassium and leak currents.",
        "nA", .4, .01, {
            "C": Parameter(200, "pF"), "gL": Parameter(10, "nS"),
            "gNa": Parameter(20000, "nS"), "gK": Parameter(6000, "nS"),
            "EL": Parameter(-65, "mV"), "ENa": Parameter(50, "mV"),
            "EK": Parameter(-90, "mV"), "VT": Parameter(-63, "mV")},
        ("notebooks/numerical-methods/brian2/1952_HH.ipynb",)),
    "morris_lecar": CellSpec("Morris-Lecar", "Two state variables: voltage and potassium activation.",
        "uA", 300.0, .025, {
            "C": Parameter(20, "uF"), "gL": Parameter(2, "mS"),
            "gCa": Parameter(4, "mS"), "gK": Parameter(8, "mS"),
            "EL": Parameter(-50, "mV"), "ECa": Parameter(100, "mV"),
            "EK": Parameter(-70, "mV"), "V1": Parameter(10, "mV"),
            "V2": Parameter(15, "mV"), "V3": Parameter(-1, "mV"),
            "V4": Parameter(14.5, "mV"), "tau_n": Parameter(15, "ms")},
        ("notebooks/numerical-methods/brian2/1981_MorrisLecar.ipynb",)),
}

# These are deliberately separate from runnable models: matching equations, authorship,
# reset rules and reference traces is required before adding a scientific adapter.
PENDING_CELLS = [
    {"model": "GLIF family", "status": "Select the intended GLIF formulation and source implementation."},
    {"model": "E-GLIF · Alice Geminiani", "status": "Integrate and validate the original implementation and cell-specific fits."},
    {"model": "E-GLIF · Marialaura De Grazia", "status": "Source identified: dbbs-lab/cerebellar-models, eglif_multirec.nestml. Native adapter and validation pending."},
]


def simulate_cell(model_id: str, protocol: Protocol, overrides=None):
    """Return raw state samples and detected spike times, with an exportable configuration."""
    import brian2 as b
    if model_id not in CELLS:
        raise ValueError("Unknown cell model.")
    spec = CELLS[model_id]
    times, drive = protocol.samples()
    if protocol.dt_ms > spec.dt_ms:
        raise ValueError(f"Use dt <= {spec.dt_ms} ms for this model.")
    values = {name: p.default for name, p in spec.parameters.items()}
    if set(overrides or {}) - values.keys():
        raise ValueError("Unknown model parameter.")
    values.update(overrides or {})
    if not np.isfinite(list(values.values())).all():
        raise ValueError("Parameters must be finite.")
    for name in ("C", "DeltaT", "tauw", "tau_n", "V2", "V4"):
        if name in values and values[name] <= 0:
            raise ValueError(f"{name} must be positive.")
    for name in ("gL", "gNa", "gK", "gCa"):
        if name in values and values[name] < 0:
            raise ValueError(f"{name} must be nonnegative.")
    if values.get("tref", 0) < 0:
        raise ValueError("Refractory time cannot be negative.")
    namespace = {name: value * (1 if spec.parameters[name].unit == "1" else
                 getattr(b, spec.parameters[name].unit)) for name, value in values.items()}
    unit = 1 if spec.input_unit == "model units" else getattr(b, spec.input_unit)
    with BRIAN_LOCK, numpy_codegen(b):
        clock = b.Clock(dt=protocol.dt_ms * b.ms)
        namespace["stimulus"] = b.TimedArray(drive * unit, dt=clock.dt)
        if model_id == "lif":
            eqs = "dv/dt = (gL*(EL-v) + stimulus(t))/C : volt (unless refractory)"
            group = b.NeuronGroup(1, eqs, threshold="v >= Vth", reset="v=Vr",
                                  refractory=namespace["tref"], method="euler", clock=clock, namespace=namespace)
            group.v = namespace["EL"]
            states, units = ["v"], {"v": "mV"}
        elif model_id == "izhikevich":
            group = b.NeuronGroup(1, """
                dv/dt = (0.04*v**2 + 5*v + 140 - u + stimulus(t))/ms : 1
                du/dt = a*(b*v-u)/ms : 1
                """, threshold="v >= 30", reset="v=c; u+=d", method="euler", clock=clock, namespace=namespace)
            group.v = -65
            group.u = values["b"] * -65
            states, units = ["v", "u"], {"v": "model voltage", "u": "model recovery"}
        elif model_id == "adex":
            group = b.NeuronGroup(1, """
                dv/dt = (gL*(EL-v)+gL*DeltaT*exp((v-VT)/DeltaT)+stimulus(t)-w)/C : volt
                dw/dt = (a*(v-EL)-w)/tauw : amp
                """, threshold="v > VT+5*DeltaT", reset="v=Vr; w+=b", method="euler", clock=clock, namespace=namespace)
            group.v = namespace["EL"]
            states, units = ["v", "w"], {"v": "mV", "w": "pA"}
        elif model_id == "hh":
            group = b.NeuronGroup(1, """
                dv/dt = (gL*(EL-v)-gNa*m**3*h*(v-ENa)-gK*n**4*(v-EK)+stimulus(t))/C : volt
                dm/dt = am*(1-m)-bm*m : 1
                dn/dt = an*(1-n)-bn*n : 1
                dh/dt = ah*(1-h)-bh*h : 1
                am = 1.28/exprel((13*mV-v+VT)/(4*mV))/ms : Hz
                bm = 1.4/exprel((v-VT-40*mV)/(5*mV))/ms : Hz
                an = .16/exprel((15*mV-v+VT)/(5*mV))/ms : Hz
                bn = .5*exp((10*mV-v+VT)/(40*mV))/ms : Hz
                ah = .128*exp((17*mV-v+VT)/(18*mV))/ms : Hz
                bh = 4/(1+exp((40*mV-v+VT)/(5*mV)))/ms : Hz
                """, threshold="v > -40*mV", refractory="v > -40*mV",
                method="exponential_euler", clock=clock, namespace=namespace)
            group.v = namespace["EL"]
            # Equilibrated gates avoid the all-zero initial-gate transient in the notebook.
            for gate in ("m", "n", "h"):
                setattr(group, gate, f"a{gate}/(a{gate}+b{gate})")
            states, units = ["v", "m", "n", "h"], {"v": "mV", "m": "1", "n": "1", "h": "1"}
        else:
            group = b.NeuronGroup(1, """
                dv/dt = (-gL*(v-EL)-gCa*m_inf*(v-ECa)-gK*n*(v-EK)+stimulus(t))/C : volt
                dn/dt = cosh((v-V3)/(2*V4))*(n_inf-n)/tau_n : 1
                m_inf = .5*(1+tanh((v-V1)/V2)) : 1
                n_inf = .5*(1+tanh((v-V3)/V4)) : 1
                """, threshold="v > 0*mV", refractory="v > 0*mV", method="rk4", clock=clock, namespace=namespace)
            group.v = namespace["EL"]
            group.n = "n_inf"
            states, units = ["v", "n"], {"v": "mV", "n": "1"}
        monitor = b.StateMonitor(group, states, record=True, clock=clock)
        spikes = b.SpikeMonitor(group)
        network = b.Network(group, monitor, spikes)
        network.run(protocol.duration_ms * b.ms, namespace={})
        output = {}
        for state in states:
            scale = getattr(b, units[state]) if units[state] in {"mV", "pA"} else 1
            output[state] = np.asarray(getattr(monitor, state)[0] / scale)
        if not all(np.isfinite(array).all() for array in output.values()):
            raise ValueError("Integration diverged. Reduce dt or revise the parameters.")
        return {"time_ms": np.asarray(monitor.t / b.ms), "states": output,
                "state_units": units, "drive": drive, "input_unit": spec.input_unit,
                "spikes_ms": np.asarray(spikes.t / b.ms),
                "configuration": {"backend": "Brian2", "version": b.__version__, "model": model_id,
                    "parameters": values, "parameter_units": {k: v.unit for k, v in spec.parameters.items()},
                    "protocol": protocol.as_dict(), "input_unit": spec.input_unit}}
