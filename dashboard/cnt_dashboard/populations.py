"""Discover the installed TVB core registry and integrate a genuinely isolated node.

The native Simulator handles model-specific pre/post-integration hooks, masks, bounds,
and multi-mode models. We do not approximate TVB dynamics with a generic ODE solver.
"""

from importlib.metadata import version
import inspect
import numpy as np


def available_models():
    from tvb.simulator.models import ModelsEnum
    return sorted(item.value for item in ModelsEnum if item.value != "Model")


def get_model(name):
    from tvb.simulator.models import ModelsEnum
    for item in ModelsEnum:
        if item.value == name and name != "Model":
            return item.get_class()()
    raise ValueError("Unknown TVB core model.")


def model_metadata(name):
    from tvb.basic.neotraits.api import NArray
    model = get_model(name)
    parameters = {}
    for attr in type(model).declarative_attrs:
        trait = getattr(type(model), attr)
        if not isinstance(trait, NArray):
            continue
        raw = getattr(model, attr)
        if raw is None:
            continue
        array = np.asarray(raw)
        if array.dtype.kind not in "fi" or array.ndim != 1:
            continue
        domain = getattr(trait, "domain", None)
        parameters[attr] = {"values": array.tolist(), "description": getattr(trait, "doc", "") or "",
                            "minimum": getattr(domain, "lo", None), "maximum": getattr(domain, "hi", None)}
    model.configure()
    return {"name": name, "description": inspect.getdoc(type(model)) or "",
            "state_variables": list(model.state_variables), "modes": int(model.number_of_modes),
            "state_ranges": {k: np.asarray(v).tolist() for k, v in model.state_variable_range.items()},
            "parameters": parameters, "version": version("tvb-library"),
            "module": type(model).__module__}


def simulate_population(name, duration_ms=200.0, dt_ms=.05, overrides=None, initial=None, seed=0):
    from tvb.datatypes.connectivity import Connectivity
    from tvb.simulator import coupling, integrators, monitors, simulator
    if not np.isfinite([duration_ms, dt_ms]).all() or not 0 < dt_ms <= duration_ms <= 2000:
        raise ValueError("Require 0 < dt <= duration <= 2000 ms.")
    steps = duration_ms / dt_ms
    if steps > 200_000 or not np.isclose(steps, round(steps)):
        raise ValueError("Duration must be a multiple of dt, with at most 200000 steps.")
    if not isinstance(seed, (int, np.integer)) or not 0 <= seed < 2**32:
        raise ValueError("Seed must be an integer between 0 and 2**32-1.")
    metadata = model_metadata(name)
    model = get_model(name)
    for key, values in (overrides or {}).items():
        if key not in metadata["parameters"]:
            raise ValueError(f"Unknown parameter: {key}")
        array = np.asarray(values, dtype=float).reshape(-1)
        expected = len(metadata["parameters"][key]["values"])
        if len(array) != expected or not np.isfinite(array).all():
            raise ValueError(f"{key} requires {expected} finite value(s).")
        trait = getattr(type(model), key)
        setattr(model, key, array.astype(trait.dtype))
    model.configure()
    supplied = initial or {}
    if set(supplied) - set(model.state_variables):
        raise ValueError("Unknown initial state variable.")
    # Explicit initial conditions make model/parameter comparisons reproducible and
    # do not consume or mutate NumPy's process-global random state.
    rng = np.random.default_rng(seed)
    state = np.zeros((1, model.nvar, 1, model.number_of_modes))
    for idx, variable in enumerate(model.state_variables):
        bounds = np.asarray(model.state_variable_range[variable], dtype=float)
        values = supplied.get(variable)
        if values is None:
            state[0, idx, 0, :] = rng.uniform(bounds[0], bounds[1], model.number_of_modes)
        else:
            array = np.asarray(values, dtype=float).reshape(-1)
            if len(array) not in (1, model.number_of_modes) or not np.isfinite(array).all():
                raise ValueError(f"Initial {variable} requires 1 or {model.number_of_modes} finite values.")
            state[0, idx, 0, :] = array
    connectivity = Connectivity(weights=np.zeros((1, 1)), tract_lengths=np.zeros((1, 1)),
        centres=np.zeros((1, 3)), region_labels=np.array(["isolated node"]),
        speed=np.array([3.0]), cortical=np.array([True]), hemispheres=np.array([False]),
        orientations=np.array([[0., 0., 1.]]))
    connectivity.configure()
    native = simulator.Simulator(model=model, connectivity=connectivity,
        coupling=coupling.Linear(a=np.array([0.])),
        integrator=integrators.HeunDeterministic(dt=dt_ms),
        monitors=(monitors.Raw(),), initial_conditions=state, simulation_length=duration_ms)
    native.configure()
    # Raw receives the observer's output. Its default can omit internal states;
    # EpileptorCodim3SlowMod even restricts its selectable variables to x/y/z.
    # An identity observer records every state without changing model dynamics
    # or mutating class-level trait choices shared with other sessions.
    native.model.observe = lambda state: state.copy()
    native.monitors[0].voi = np.arange(model.nvar)
    # Sigmoids in native models legitimately overflow internally before yielding
    # a finite saturated value. Reject non-finite states, not those exponentials.
    with np.errstate(over="ignore", invalid="raise", divide="raise"):
        (time, data), = native.run()
    if not np.isfinite(data).all():
        raise ValueError("Integration diverged. Reduce dt or revise the parameters and initial conditions.")
    return {"time_ms": time, "states": data[:, :, 0, :],
            "state_variables": list(model.state_variables),
            "configuration": {"backend": "TVB", "version": metadata["version"], "model": name,
                "duration_ms": duration_ms, "dt_ms": dt_ms, "seed": seed,
                "integrator": "HeunDeterministic", "weights": [[0.0]], "coupling_gain": 0.0,
                "parameters": {k: np.asarray(getattr(model, k)).tolist() for k in metadata["parameters"]},
                "initial_conditions": state.tolist(),
                "state_variables": list(model.state_variables), "number_of_modes": int(model.number_of_modes)}}
