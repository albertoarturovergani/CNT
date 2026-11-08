"""One comparison engine shared by the local notebook and the dashboard."""

from importlib.metadata import version
import inspect
import numpy as np
from .cells import CELLS, BRIAN_LOCK, numpy_codegen, simulate_cell
from .protocols import Protocol
from .pynn_experiments import _read_population


def pynn_cell_models():
    import pyNN.brian2 as sim
    from pyNN.standardmodels.base import StandardCellType
    models = []
    for name in sorted(dir(sim)):
        candidate = getattr(sim, name)
        if not isinstance(candidate, type) or not issubclass(candidate, StandardCellType):
            continue
        if candidate is StandardCellType or name.startswith("Standard"):
            continue
        if name.startswith("SpikeSource") or name == "PointNeuron":
            continue
        # Parameterized composition classes are not concrete standard neurons.
        try:
            inspect.signature(candidate).bind()
            instance = candidate()
        except TypeError:
            continue
        if instance.injectable and "v" in instance.recordable:
            models.append(name)
    return models


def comparison_models():
    return {**{f"PyNN · {name}": ("pynn", name) for name in pynn_cell_models()},
            **{f"Brian2 · {spec.label}": ("brian2", key) for key, spec in CELLS.items()}}


def compare_cells(duration_ms=400., start_ms=50., stop_ms=350., amplitude_nA=1.,
                  izh_model_input=10., pynn_dt_ms=.1, selected=None, progress=None):
    """Inject one shared physical current; keep the dimensionless adapter explicit.

No parameter fits, capacitance normalization or conversion of scaled Izhikevich
input to amperes is assumed. Native defaults and integration steps are exported.
    """
    if not np.isfinite([duration_ms, start_ms, stop_ms, amplitude_nA, izh_model_input, pynn_dt_ms]).all():
        raise ValueError("Comparison controls must be finite.")
    if not 0 <= start_ms < stop_ms <= duration_ms <= 1000 or not .005 <= pynn_dt_ms <= .1:
        raise ValueError("Use 0 <= start < stop <= duration <= 1000 ms and PyNN dt between 0.005 and 0.1 ms.")
    if not np.isclose(duration_ms/pynn_dt_ms, round(duration_ms/pynn_dt_ms)):
        raise ValueError("Duration must be a multiple of the PyNN integration step.")
    choices = comparison_models()
    selected = list(choices) if selected is None else list(selected)
    if not selected or set(selected)-choices.keys():
        raise ValueError("Select at least one available comparison model.")
    import brian2 as b
    import pyNN.brian2 as sim
    result = {"populations": {}, "configuration": {"backend": "PyNN/Brian2 + native CNT Brian2 adapters",
        "pynn_version": version("PyNN"), "brian2_version": b.__version__,
        "experiment": {"duration_ms": duration_ms, "start_ms": start_ms, "stop_ms": stop_ms,
            "amplitude_nA": amplitude_nA, "izh_model_input": izh_model_input, "pynn_dt_ms": pynn_dt_ms},
        "models": {}, "notes": ["Equal physical current does not imply equal excitability across different parameterizations.",
            "CNT's dimensionless Izhikevich adapter has an independent model-unit input amplitude.",
            "Without presynaptic spikes, alpha/exponential synapse variants can give identical membrane responses."]}}
    for index, label in enumerate(selected):
        backend, name = choices[label]
        if backend == "pynn":
            # Keep fast channel/recovery dynamics on a finer native clock.
            limit = .01 if name == "HH_cond_exp" else (.025 if name.startswith("EIF") else (.05 if name == "Izhikevich" else .1))
            model_dt = min(pynn_dt_ms, limit)
            with BRIAN_LOCK, numpy_codegen(b):
                sim.setup(timestep=model_dt, min_delay=model_dt, max_delay=100.)
                try:
                    model = getattr(sim, name)
                    pop = sim.Population(1, model(), label=name)
                    pop.record(["v", "spikes"])
                    pulse = sim.DCSource(amplitude=amplitude_nA, start=start_ms, stop=stop_ms)
                    pulse.inject_into(pop)
                    sim.run(duration_ms)
                    output = _read_population(pop)
                    output.update(voltage_unit="mV", input_amplitude=amplitude_nA, input_unit="nA", dt_ms=model_dt)
                    result["configuration"]["models"][label] = {"model": name, "backend": "PyNN / Brian2",
                        "parameters": {key: np.asarray(val).tolist() for key, val in model.default_parameters.items()},
                        "initial_values": {key: np.asarray(val).tolist() for key, val in model.default_initial_values.items()},
                        "dt_ms": model_dt, "input_amplitude": amplitude_nA, "input_unit": "nA"}
                finally:
                    sim.end()
        else:
            spec = CELLS[name]
            amplitude = izh_model_input if spec.input_unit == "model units" else amplitude_nA * {"pA": 1000., "nA": 1., "uA": .001}[spec.input_unit]
            native = simulate_cell(name, Protocol(duration_ms, spec.dt_ms, start_ms, stop_ms, amplitude))
            output = {"time_ms": native["time_ms"], "signals": {key: values[:, None] for key, values in native["states"].items()},
                "spikes_ms": [native["spikes_ms"]], "voltage_unit": native["state_units"]["v"],
                "input_amplitude": amplitude, "input_unit": spec.input_unit, "dt_ms": spec.dt_ms}
            result["configuration"]["models"][label] = native["configuration"]
        if not np.isfinite(output["signals"]["v"]).all():
            raise ValueError(f"{label} diverged; reduce the integration step or input amplitude.")
        result["populations"][label] = output
        if progress is not None:
            progress((index+1)/len(selected), label)
    return result
