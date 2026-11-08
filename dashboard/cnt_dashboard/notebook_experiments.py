"""Portable, explicit adapters for the CNT introductory notebook experiments.

Notebook output/plotting cells are not executed. Backend-specific changes are
listed in notebook_catalogue.py and exported with each completed experiment.
"""

from importlib.metadata import version
import numpy as np
from .cells import BRIAN_LOCK, numpy_codegen
from .notebook_catalogue import EXPERIMENTS, SOURCE_COMMIT
from .pynn_experiments import _read_population, simulate_network, NetworkConfig


def _json_values(parameters):
    return {name: np.asarray(value).item() if np.asarray(value).ndim == 0 else np.asarray(value).tolist()
            for name, value in parameters.items()}


def experiment_config(experiment_id, overrides=None):
    spec = EXPERIMENTS[experiment_id]
    if set(overrides or {}) - spec["fields"].keys():
        raise ValueError("Unknown experiment parameter.")
    config = {key: detail[0] for key, detail in spec["fields"].items()}
    config.update(overrides or {})
    for key, value in config.items():
        default, minimum, maximum, _ = spec["fields"][key]
        if not np.isfinite(value) or not minimum <= value <= maximum:
            raise ValueError(f"{key} must be between {minimum} and {maximum}.")
        if isinstance(default, int) and not isinstance(value, (int, np.integer)):
            raise ValueError(f"{key} must be an integer.")
    dt = config.get("dt_ms", config.get("pynn_dt_ms"))
    if not np.isclose(config["duration_ms"] / dt, round(config["duration_ms"] / dt)):
        raise ValueError("Duration must be a multiple of dt.")
    if experiment_id == "stdp" and config["starting_weight"] > config["w_max"]:
        raise ValueError("Starting weight must be within the plasticity bounds.")
    return config


def divergent_edges(n_cells, weight=.08, width=1., p_threshold=.2):
    pre, post = np.indices((n_cells, n_cells))
    distance = np.abs(pre-post)
    keep = (distance > 0) & (np.exp(-.5 * (distance / width)**2) > p_threshold)
    return np.column_stack([pre[keep], post[keep], np.full(keep.sum(), weight), 1+distance[keep]/.35])


def small_world_edges(n_cells, degree, rewiring, weight, rng):
    distance = np.abs(np.arange(n_cells)[:, None]-np.arange(n_cells))
    distance = np.minimum(distance, 500-distance)  # notebook's periodic boundary
    pre, post = np.where(distance < degree)
    changed = rng.random(len(post)) < rewiring
    post[changed] = rng.integers(0, n_cells, changed.sum())
    # Truncated, not censored, normal distribution. Independent delay draws per edge.
    delays = rng.normal(1.5, 1.75, len(pre))
    bad = (delays < .1) | (delays > 100)
    while bad.any():
        delays[bad] = rng.normal(1.5, 1.75, bad.sum())
        bad = (delays < .1) | (delays > 100)
    return np.column_stack([pre, post, np.full(len(pre), weight), delays])


def _projection_edges(projection, b, unit):
    """Read the fixed Brian2 backend without collapsing parallel connections.

The adapter uses one ordinary Population at each end, never an Assembly.
PyNN 0.13's list getter fails for scalar attributes of one-edge projections;
its dense array getter also merges multapses. Keep every native edge instead.
"""
    if len(projection) == 0:
        return np.empty((0, 4))
    synapse = projection._brian2_synapses[0][0]
    n = len(projection)
    return np.column_stack([np.asarray(synapse.i[:]), np.asarray(synapse.j[:]),
        np.broadcast_to(np.asarray(synapse.weight[:] / unit), (n,)),
        np.broadcast_to(np.asarray(synapse.delay[:] / b.ms), (n,))])


def _deactivate_empty(projections):
    for projection in projections.values():
        if len(projection) == 0:
            for targets in projection._brian2_synapses.values():
                for synapse in targets.values():
                    synapse.active = False


def _metadata(experiment_id, config):
    spec = EXPERIMENTS[experiment_id]
    return {"backend": "PyNN/Brian2 + native CNT Brian2" if experiment_id == "cell_models" else "PyNN / Brian2",
        "pynn_version": version("PyNN"), "brian2_version": version("brian2"),
        "experiment_id": experiment_id, "source_notebook": spec.get("spinnaker_notebook", spec["notebook"]), "source_commit": SOURCE_COMMIT,
        "experiment": config, "control_units": {k: v[3] for k, v in spec["fields"].items()},
        "adaptations": spec["notes"], "randomness": "Seeded local streams; original unseeded draws are not reproduced."}


def simulate_notebook(experiment_id, overrides=None, *, progress=None, selected=None):
    config = experiment_config(experiment_id, overrides)
    if EXPERIMENTS[experiment_id].get("link_only"):
        raise ValueError("This original notebook requires SpiNNaker; use its source link.")
    if experiment_id == "cell_models":
        from .cell_comparison import compare_cells
        result = compare_cells(**config, selected=selected, progress=progress)
        result["configuration"].update(_metadata(experiment_id, config))
        return result
    if experiment_id == "balance_brian2":
        cfg = NetworkConfig(n_cells=config["n_cells"], duration_ms=config["duration_ms"], dt_ms=config["dt_ms"],
            delay_ms=.2 if config["dt_ms"] <= .2 else config["dt_ms"], probability=config["probability"],
            exc_weight_uS=config["exc_weight"], inh_weight_uS=config["inh_weight"], seed=config["seed"])
        # A coarser dt must not silently alter the script's fixed 0.2 ms delay.
        if config["dt_ms"] > .2 or not np.isclose(.2/config["dt_ms"], round(.2/config["dt_ms"])):
            raise ValueError("The script's delay is 0.2 ms: choose dt = 0.1 or 0.2 ms.")
        result = simulate_network(cfg, record_analog_cells=2)
        result["configuration"].update(_metadata(experiment_id, config))
        result["configuration"]["source_script"] = EXPERIMENTS[experiment_id]["script"]
        result["configuration"]["native_network"] = cfg.__dict__
        result["projections"] = {name: {"pre": "thalamus" if name.startswith("ext") else name.split("2")[0],
            "post": name.split("2")[1], "weight_unit": "uS"} for name in result["connectivity"]}
        for pop in ("exc", "inh"):
            result["populations"][pop]["recorded_indices"] = [0, 1]
        return result

    import brian2 as b
    import pyNN.brian2 as sim
    with BRIAN_LOCK, numpy_codegen(b):
        previous_dt = b.defaultclock.dt
        b.defaultclock.dt = config["dt_ms"] * b.ms
        sim.setup(timestep=config["dt_ms"], min_delay=1., max_delay=100.)
        try:
            b.seed(config["seed"])
            rng = np.random.default_rng(config["seed"])
            pops, projections, descriptors, parameters = {}, {}, {}, {}
            current_sources = {}

            def cell(name, n=1, model="IF_cond_exp"):
                cell_type = getattr(sim, model)
                pops[name] = sim.Population(n, cell_type(), label=name)
                variables = ["v", "gsyn_exc", "gsyn_inh", "spikes"] if model == "IF_cond_exp" else ["v", "spikes"]
                pops[name].record(variables)
                parameters[name] = {"model": model, "values": _json_values(cell_type.default_parameters),
                    "initial_values": _json_values(cell_type.default_initial_values)}
                return pops[name]

            def source(name, times):
                source_dt = min(config["dt_ms"], .1)
                # Preserve all Gaussian input events. A coarse source clock can
                # put two spikes from one cell in one bin, which Brian rejects.
                while any(len(np.unique(np.floor(np.asarray(train)/source_dt + 1e-3))) != len(train) for train in times):
                    source_dt /= 10
                    if source_dt < 1e-6:
                        raise ValueError("Input spikes are too close to resolve on the source clock.")
                b.defaultclock.dt = source_dt * b.ms
                config["source_clock_dt_ms"] = source_dt
                config["input_spike_times_ms"] = [np.asarray(train).tolist() for train in times]
                # PyNN 0.13/Brian2 simplifies the Sequence array incorrectly
                # for a one-source Population. A one-cell view of a two-source
                # parent preserves one logical input; its spare source is silent.
                logical_size = len(times)
                if logical_size == 1:
                    parent = sim.Population(2, sim.SpikeSourceArray(spike_times=[times[0], []]), label=name)
                    pops[name] = parent[:1]
                else:
                    pops[name] = sim.Population(logical_size, sim.SpikeSourceArray(spike_times=times), label=name)
                pops[name].record("spikes")

            def connect(name, pre, post, weight, delay=1., receptor="excitatory", edges=None, plastic=None):
                if edges is None:
                    # Explicit equivalent of one-to-one; avoids PyNN/NumPy's
                    # scalar nonzero error for a one-cell OneToOneConnector.
                    edges = np.column_stack([np.arange(min(len(pops[pre]), len(pops[post]))),
                        np.arange(min(len(pops[pre]), len(pops[post])))])
                connector = sim.FromListConnector(edges)
                synapse = plastic if plastic is not None else sim.StaticSynapse(weight=weight, delay=delay)
                projections[name] = sim.Projection(pops[pre], pops[post], connector, synapse_type=synapse, receptor_type=receptor)
                conductance = parameters[post]["model"] == "IF_cond_exp"
                descriptors[name] = {"pre": pre, "post": post, "receptor": receptor, "weight_unit": "uS" if conductance else "nA"}

            if experiment_id == "single_clique":
                cell("cell0"); cell("cell1")
                connect("cell0_exc_cell1", "cell0", "cell1", config["exc_weight"])
                connect("cell1_inh_cell0", "cell1", "cell0", config["inh_weight"], receptor="inhibitory")
                step = sim.StepCurrentSource(times=[30., 40.], amplitudes=[config["step_amplitude"], 0.])
                step.inject_into(pops["cell0"]); step.record(); current_sources["Step to cell0"] = step
            else:
                n = config["n_cells"]
                name = "Exc" if experiment_id == "diverging" else ("cx" if experiment_id == "small_world" else "network")
                cell(name, n)
                if experiment_id == "small_world":
                    pops[name].initialize(v=rng.normal(-65., 2., n))
                    for receptor, field in (("excitatory", "exc_weight"), ("inhibitory", "inh_weight")):
                        edges = small_world_edges(n, config["degree"], config["rewiring"], config[field], rng)
                        connect("recurrent_"+receptor, name, name, config[field], receptor=receptor, edges=edges)
                elif experiment_id == "diverging":
                    edges = divergent_edges(n, config["recurrent_weight"], config["width"], config["p_threshold"])
                    connect("recurrent_exc", name, name, config["recurrent_weight"], edges=edges)
                times = [[] for _ in range(n)]
                mean, std = (100., 25.) if experiment_id == "diverging" else (50., 10.)
                for i in range(int(n*.4), int(n*.6)):
                    times[i] = np.sort(np.abs(rng.normal(mean, std, 5)))
                source("thalamus", times)
                connect("input", "thalamus", name, config.get("input_weight", .1))
            _deactivate_empty(projections)
            sim.run(config["duration_ms"])
            result = {"populations": {name: _read_population(pop) for name, pop in pops.items()},
                "connectivity": {name: _projection_edges(proj, b, b.uS if descriptors[name]["weight_unit"] == "uS" else b.nA)
                    for name, proj in projections.items()}, "projections": descriptors,
                "connection_counts": {name: len(proj) for name, proj in projections.items()},
                "configuration": {**_metadata(experiment_id, config), "cell_models": parameters}}
            for pop in result["populations"].values():
                if not all(np.isfinite(v).all() for v in pop["signals"].values()):
                    raise ValueError("Integration diverged; reduce dt or revise weights.")
            if current_sources:
                result["currents"] = {name: np.asarray(current.get_data()).copy() for name, current in current_sources.items()}
            return result
        finally:
            sim.end()
            b.defaultclock.dt = previous_dt
