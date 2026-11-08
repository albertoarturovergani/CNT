"""Explicit PyNN/Brian2 adapters for CNT's existing introductory notebooks.

No notebook code is executed dynamically. The model, inputs and projections below
come from the linked notebooks. Random streams are explicitly seeded here.
"""

from dataclasses import asdict, dataclass
from importlib.metadata import version
import numpy as np
from .cells import BRIAN_LOCK, numpy_codegen

SOURCE_COMMIT = "1602edba2c021ceeff72e0d9e856c94678cf3b1c"
SINGLE_NOTEBOOK = "notebooks/intro/eg_single-cell.ipynb"
NETWORK_NOTEBOOK = "notebooks/intro/paper_balance-network_sPyNNaker.ipynb"

SINGLE_PARAMETERS = dict(v_rest=-65., v_thresh=-37., v_reset=-80., cm=1., tau_m=20.,
    tau_refrac=.1, tau_syn_E=50., tau_syn_I=5., e_rev_E=0., e_rev_I=-70., i_offset=0.)
NETWORK_PARAMETERS = dict(v_rest=-60., v_thresh=-50., v_reset=-60., cm=.2, tau_m=20.,
    tau_refrac=5., tau_syn_E=5., tau_syn_I=10., e_rev_E=0., e_rev_I=-80., i_offset=0.)
PARAMETER_UNITS = dict(v_rest="mV", v_thresh="mV", v_reset="mV", cm="nF", tau_m="ms",
    tau_refrac="ms", tau_syn_E="ms", tau_syn_I="ms", e_rev_E="mV", e_rev_I="mV", i_offset="nA")
PARAMETER_NAMES = dict(v_rest="Passive resting voltage", v_thresh="Spike threshold", v_reset="Reset voltage",
    cm="Membrane capacitance", tau_m="Membrane time constant", tau_refrac="Absolute refractory period",
    tau_syn_E="Excitatory conductance decay", tau_syn_I="Inhibitory conductance decay",
    e_rev_E="Excitatory reversal potential", e_rev_I="Inhibitory reversal potential", i_offset="Constant injected current")
EQUATIONS = [
    r"C_m\frac{dv}{dt}=\frac{C_m}{\tau_m}(v_{rest}-v)+g_E(e_{rev,E}-v)+g_I(e_{rev,I}-v)+I_{offset}+I_{AC}(t)+I_{step}(t)",
    r"\frac{dg_E}{dt}=-\frac{g_E}{\tau_{syn,E}},\qquad\frac{dg_I}{dt}=-\frac{g_I}{\tau_{syn,I}}",
    r"v>v_{thresh}\;\Longrightarrow\;v\leftarrow v_{reset}\text{ during }\tau_{refrac};\quad "
    r"g_{E/I}\leftarrow g_{E/I}+w_{E/I}\text{ on an arriving spike}",
]


@dataclass(frozen=True)
class SingleConfig:
    duration_ms: float = 800.
    dt_ms: float = 1.
    ac_start_ms: float = 100.
    ac_stop_ms: float = 400.
    ac_amplitude_nA: float = 10.
    ac_frequency_hz: float = 10.
    step_start_ms: float = 600.
    step_stop_ms: float = 610.
    step_amplitude_nA: float = 10.


@dataclass(frozen=True)
class NetworkConfig:
    n_cells: int = 1500
    duration_ms: float = 1000.
    dt_ms: float = 1.
    delay_ms: float = 2.
    probability: float = .02
    exc_weight_uS: float = .004
    inh_weight_uS: float = .051
    n_external: int = 20
    external_rate_hz: float = 100.
    external_duration_ms: float = 50.
    external_probability: float = .01
    external_weight_uS: float = .1
    seed: int = 98766987


def _validate_time(duration, dt):
    if not np.isfinite([duration, dt]).all() or not 0 < dt <= 1 or not 10 <= duration <= 2000:
        raise ValueError("Use duration 10–2000 ms and dt in (0, 1] ms.")
    if not np.isclose(duration / dt, round(duration / dt)):
        raise ValueError("Duration must be a multiple of dt.")


def _cell_parameters(defaults, overrides):
    if set(overrides or {}) - defaults.keys():
        raise ValueError("Unknown PyNN cell parameter.")
    values = {**defaults, **(overrides or {})}
    if not np.isfinite(list(values.values())).all():
        raise ValueError("Cell parameters must be finite.")
    if any(values[k] <= 0 for k in ("cm", "tau_m", "tau_syn_E", "tau_syn_I")) or values["tau_refrac"] < 0:
        raise ValueError("Capacitance and time constants must be positive; refractory time must be nonnegative.")
    if values["v_reset"] >= values["v_thresh"]:
        raise ValueError("Reset voltage must be below the spike threshold.")
    return values


def _read_population(population):
    segment = population.get_data().segments[0]
    signals = {s.name: s for s in segment.analogsignals}
    first = next(iter(signals.values()), None)
    return {"time_ms": np.asarray(first.times.rescale("ms").magnitude) if first is not None else np.array([]),
            "signals": {name: np.asarray(signal.magnitude).copy() for name, signal in signals.items()},
            "spikes_ms": [np.asarray(train.rescale("ms").magnitude).copy() for train in segment.spiketrains]}


def _configuration(notebook, config, parameters):
    return {"backend": "PyNN / Brian2", "pynn_version": version("PyNN"), "brian2_version": version("brian2"),
            "model": "IF_cond_exp", "source_notebook": notebook, "source_commit": SOURCE_COMMIT,
            "experiment": asdict(config), "parameters": parameters, "parameter_units": PARAMETER_UNITS}


def simulate_single(config=SingleConfig(), overrides=None):
    _validate_time(config.duration_ms, config.dt_ms)
    if not np.isfinite(list(asdict(config).values())).all():
        raise ValueError("Input parameters must be finite.")
    if not 0 <= config.ac_start_ms < config.ac_stop_ms <= config.duration_ms:
        raise ValueError("AC input needs 0 <= start < stop <= duration.")
    if not 0 <= config.step_start_ms < config.step_stop_ms <= config.duration_ms or config.ac_frequency_hz < 0:
        raise ValueError("Step input needs 0 <= start < stop <= duration; frequency must be nonnegative.")
    parameters = _cell_parameters(SINGLE_PARAMETERS, overrides)
    import brian2 as b
    import pyNN.brian2 as sim
    with BRIAN_LOCK, numpy_codegen(b):
        sim.setup(timestep=config.dt_ms, min_delay=1., max_delay=100.)
        try:
            cell = sim.Population(1, sim.IF_cond_exp(**parameters), label="cell0")
            cell.record(["v", "gsyn_exc", "gsyn_inh", "spikes"])
            ac = sim.ACSource(start=config.ac_start_ms, stop=config.ac_stop_ms,
                amplitude=config.ac_amplitude_nA, frequency=config.ac_frequency_hz)
            step = sim.StepCurrentSource(times=[config.step_start_ms, config.step_stop_ms],
                amplitudes=[config.step_amplitude_nA, 0.])
            for current in (ac, step):
                current.inject_into(cell)
                current.record()
            sim.run(config.duration_ms)
            result = _read_population(cell)
            # PyNN returns a column of current samples on the simulation clock.
            result["currents"] = {"AC": np.asarray(ac.get_data()).copy(), "Step": np.asarray(step.get_data()).copy()}
            result["configuration"] = _configuration(SINGLE_NOTEBOOK, config, parameters)
            return result
        finally:
            sim.end()


def simulate_network(config=NetworkConfig(), overrides=None):
    _validate_time(config.duration_ms, config.dt_ms)
    if not np.isfinite(list(asdict(config).values())).all():
        raise ValueError("Network parameters must be finite.")
    if not isinstance(config.n_cells, (int, np.integer)) or not 10 <= config.n_cells <= 3000:
        raise ValueError("The dashboard supports 10–3000 neurons.")
    if not 1 <= config.n_external <= 200 or not 0 <= config.seed < 2**32:
        raise ValueError("Use 1–200 external cells and an unsigned 32-bit seed.")
    if not config.dt_ms <= config.delay_ms <= 100 or not np.isclose(config.delay_ms / config.dt_ms, round(config.delay_ms / config.dt_ms)):
        raise ValueError("Synaptic delay must be a multiple of dt, between dt and 100 ms.")
    if not (0 <= config.probability <= 1 and 0 <= config.external_probability <= 1):
        raise ValueError("Connection probabilities must be between 0 and 1.")
    if min(config.exc_weight_uS, config.inh_weight_uS, config.external_weight_uS, config.external_rate_hz) < 0 or not 0 < config.external_duration_ms <= config.duration_ms:
        raise ValueError("Weights/rate must be nonnegative; external stimulation must end within the run.")
    # Bound worst-case dense connectivity to keep this interactive exercise usable.
    if config.n_cells**2 * config.probability > 1_000_000:
        raise ValueError("Reduce size or connection probability to at most 1 million expected recurrent synapses.")
    if config.n_cells * (config.duration_ms / config.dt_ms + 1) * 3 > 15_000_000:
        raise ValueError("Reduce neurons/duration or increase dt: the dashboard records at most 15 million analog values per run.")
    parameters = _cell_parameters(NETWORK_PARAMETERS, overrides)
    import brian2 as b
    import pyNN.brian2 as sim
    from pyNN.random import NumpyRNG, RandomDistribution
    with BRIAN_LOCK, numpy_codegen(b):
        sim.setup(timestep=config.dt_ms, min_delay=config.delay_ms, max_delay=config.delay_ms)
        try:
            # LazyArray can copy RNG state while evaluating a connector. Give
            # each projection/population its own child stream to avoid correlations.
            stream_seeds = [int(child.generate_state(1)[0]) for child in np.random.SeedSequence(config.seed).spawn(9)]
            streams = iter(stream_seeds)
            b.seed(next(streams))
            def new_rng():
                return NumpyRNG(seed=next(streams), parallel_safe=True)
            n_exc = int(round(config.n_cells * 4 / 5))
            pops = {"exc": sim.Population(n_exc, sim.IF_cond_exp(**parameters), label="Excitatory_Cells"),
                    "inh": sim.Population(config.n_cells - n_exc, sim.IF_cond_exp(**parameters), label="Inhibitory_Cells")}
            for pop in pops.values():
                pop.record(["spikes", "v", "gsyn_exc", "gsyn_inh"])
                pop.initialize(v=RandomDistribution("uniform", [parameters["v_reset"], parameters["v_thresh"]], rng=new_rng()))
            projections = {}
            for pre in ("exc", "inh"):
                for post in ("exc", "inh"):
                    projections[f"{pre}2{post}"] = sim.Projection(pops[pre], pops[post],
                        sim.FixedProbabilityConnector(config.probability, rng=new_rng()),
                        receptor_type="excitatory" if pre == "exc" else "inhibitory",
                        synapse_type=sim.StaticSynapse(weight=config.exc_weight_uS if pre == "exc" else config.inh_weight_uS,
                            delay=config.delay_ms))
            pops["thalamus"] = sim.Population(config.n_external,
                sim.SpikeSourcePoisson(rate=config.external_rate_hz, duration=config.external_duration_ms), label="expoisson")
            pops["thalamus"].record("spikes")
            for post in ("exc", "inh"):
                projections[f"ext2{post}"] = sim.Projection(pops["thalamus"], pops[post],
                    sim.FixedProbabilityConnector(config.external_probability, rng=new_rng()), receptor_type="excitatory",
                    synapse_type=sim.StaticSynapse(weight=config.external_weight_uS, delay=config.delay_ms))
            # PyNN can leave empty Brian2 Synapses objects without connect()
            # ever having been called. Brian2 rejects those at before_run.
            # Deactivating an object with zero edges preserves the empty graph.
            for projection in projections.values():
                if len(projection) == 0:
                    for targets in projection._brian2_synapses.values():
                        for synapse in targets.values():
                            synapse.active = False
            sim.run(config.duration_ms)
            connectivity = {}
            for name, projection in projections.items():
                # PyNN/Brian2 0.13 can return scalar attributes for a single
                # connection, breaking get([weight, delay], format='list').
                # The public array format handles scalar attributes correctly.
                # FixedProbabilityConnector creates at most one edge per pair.
                if len(projection) == 0:
                    connectivity[name] = np.empty((0, 4))
                    continue
                matrix = projection.get("weight", format="array")
                pre, post = np.where(np.isfinite(matrix))
                connectivity[name] = np.column_stack([pre, post, matrix[pre, post],
                                                       np.full(len(pre), config.delay_ms)])
            result = {"populations": {name: _read_population(pop) for name, pop in pops.items()},
                      "connectivity": connectivity,
                      "connection_counts": {name: len(proj) for name, proj in projections.items()},
                      "configuration": _configuration(NETWORK_NOTEBOOK, config, parameters)}
            result["configuration"]["adaptations"] = [
                "Independent seeded child streams for PyNN projections/initialization and Brian2 Poisson generator; notebook streams were not all seeded.",
                "External delay is explicitly set to the configured minimum delay (2 ms in the notebook preset).",
                "CPU backend selected explicitly; dashboard plots/downloads replace notebook file writes."]
            result["configuration"]["random_stream_seeds"] = stream_seeds
            return result
        finally:
            sim.end()
