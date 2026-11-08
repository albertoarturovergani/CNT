"""Source-linked CNT notebook experiments, grouped in the teaching order."""

SOURCE_COMMIT = "e3e984796a9f22df462ef2c452bc32ea6b2b27da"
INTRO = "notebooks/intro/"
HARDWARE_MODELS = ["IF_curr_dual_exp", "IFCondExpStoc", "IFCurDelta", "IFCurrExpCa2Adaptive"]

# Controls use (default, minimum, maximum, unit). Unseeded notebook draws become
# seeded in the dashboard; deterministic stimuli/connectivity remain unchanged.
COMMON = {"duration_ms": (250., 70., 2000., "ms"), "dt_ms": (1., .1, 1., "ms"), "seed": (0, 0, 2**32-1, "1")}
EXPERIMENTS = {
    "single_clique": {
        "label": "Single clique", "section": "single", "notebook": INTRO+"eg_single-clique.ipynb",
        "description": "Two IF_cond_exp cells: cell0 excites cell1, cell1 inhibits cell0. A 10 nA current step drives cell0 from 30 to 40 ms.",
        "fields": {**COMMON, "duration_ms": (100., 50., 1000., "ms"), "exc_weight": (1., 0., 5., "uS"),
            "inh_weight": (1., 0., 5., "uS"), "step_amplitude": (10., 0., 50., "nA")},
        "notes": ["Notebook ge/gi comments say nS, but PyNN's conductance weights are in uS. The numeric values 1/1 are preserved as 1 uS."]},
    "cell_models": {
        "label": "Testing cell models network", "section": "single", "notebook": INTRO+"eg_testing-cell-models-local.ipynb",
        "spinnaker_notebook": INTRO+"eg_testing-cell-models-network.ipynb",
        "description": "New local comparison: all injectable neuron classes in the installed PyNN/Brian2 backend, plus the five existing CNT Brian2 cell adapters. One isolated cell per model, driven by a current step.",
        "fields": {"duration_ms": (400., 50., 1000., "ms"), "start_ms": (50., 0., 1000., "ms"),
            "stop_ms": (350., 0., 1000., "ms"), "amplitude_nA": (1., 0., 20., "nA"),
            "izh_model_input": (10., 0., 50., "model units"), "pynn_dt_ms": (.1, .005, .1, "maximum ms")},
        "notes": ["A new notebook and the dashboard share one comparison engine. The original synaptic-input/SpiNNaker exercise remains linked separately.",
            "The physical current is shared across dimensional models and converted to pA/uA for the existing adapters. Their capacitances/parameter sets differ, so equal current is not equal excitability.",
            "CNT's direct Izhikevich adapter uses scaled model input; it has a separate amplitude and is not assigned a physical-current conversion.",
            "Native PyNN defaults are preserved and exported. This is a current-injection comparison: synaptic-kernel variants can coincide without presynaptic input."]},
    "stdp": {
        "label": "STDP", "section": "single", "notebook": INTRO+"eg_testing-STDP-model-network.ipynb", "link_only": True,
        "description": "Two IF_cond_exp cells driven at [30, 40, 50, 60] ms and with a 2 ms input offset; an additive spike-pair synapse connects pre to post.",
        "fields": {"dt_ms": (1., .1, 1., "ms"), "duration_ms": (150., 90., 1000., "ms"), "post_offset_ms": (2., -20., 20., "ms"),
            "starting_weight": (0., 0., 5., "uS"), "w_max": (5., .01, 10., "uS"),
            "tau_plus": (10., .1, 100., "ms"), "tau_minus": (1., .1, 100., "ms"),
            "A_plus": (.5, 0., 1., "1"), "A_minus": (.5, 0., 1., "1")},
        "notes": ["Run the original notebook with a SpiNNaker kernel. It uses dendritic_delay_fraction=1, which the local PyNN/Brian2 STDP implementation does not support. This page links that experiment without changing its learning rule."]},
    "decaying": {
        "label": "Decaying network", "section": "network", "notebook": INTRO+"eg_decaying-network.ipynb",
        "description": "100 excitatory IF_cond_exp cells with no recurrent connections. Five jittered spikes stimulate thalamic sources in the central 40–60% of the line.",
        "fields": {**COMMON, "n_cells": (100, 10, 400, "cells"), "input_weight": (.08, 0., 1., "uS")},
        "notes": ["Input times follow the notebook: sorted absolute normal draws, mean 50 ms and SD 10 ms. The dashboard additionally records the thalamic source spikes."]},
    "diverging": {
        "label": "Diverging network", "section": "network", "notebook": INTRO+"eg_diverging-network.ipynb",
        "description": "100 excitatory cells with distance-threshold recurrent connections and central thalamic input (five jittered spikes per active source, mean 100 ms, SD 25 ms).",
        "fields": {**COMMON, "n_cells": (100, 10, 400, "cells"), "recurrent_weight": (.08, 0., 1., "uS"),
            "input_weight": (.08, 0., 1., "uS"), "width": (1., .1, 5., "index spacing"), "p_threshold": (.2, .01, .99, "1")},
        "notes": ["The notebook uses exp(-d²/(2 width²)) > p_threshold as a deterministic connection test, not Bernoulli sampling. Self connections are excluded; requested delay = 1 + d/0.35 ms in the notebook's numerical distance scale. PyNN rounds to the integration clock (4 ms for nearest neighbours at dt = 1 ms); exports contain the actual backend delay."]},
    "small_world": {
        "label": "Small World network", "section": "network", "notebook": INTRO+"eg_small-world-network.ipynb",
        "description": "100 IF_cond_exp cells on a line with separate excitatory/inhibitory local-plus-rewired projections, normally distributed initial voltages and central thalamic input.",
        "fields": {**COMMON, "n_cells": (100, 10, 400, "cells"), "degree": (1.5, .1, 10., "distance radius"),
            "rewiring": (.01, 0., 1., "probability"), "exc_weight": (.1, 0., 1., "uS"), "inh_weight": (.5, 0., 2., "uS")},
        "notes": ["PyNN/Brian2 SmallWorldConnector is unimplemented. This local adapter builds explicit distance < degree edges and rewires their targets over the full population, with self connections allowed. Hardware-specific random draws are not reproduced.",
            "The original periodic space length is 500, not the 100-cell population size; the default line does not close into a 100-cell ring. Degree is a distance radius, not an integer graph degree.",
            "Delays retain the notebook's truncated normal distribution (mean 1.5, SD 1.75, bounds 0.1–100 ms). Brian2 schedules arrivals on the chosen integration clock; use dt = 0.1 ms to resolve the shortest delays."]},
    "balance_brian2": {
        "label": "Balance network · Brian2", "section": "network", "notebook": INTRO+"paper_balance-network_brian2.ipynb",
        "script": INTRO+"scripts/VA/VAbenchmarks.py",
        "description": "The COBA benchmark launched by the Brian2 notebook's VAbenchmarks.py script: 4000 cells, E:I = 4:1, dt 0.1 ms, delay 0.2 ms, 1000 ms. Spikes from all cells and analog traces from two cells per population.",
        "fields": {"n_cells": (4000, 10, 5000, "cells"), "duration_ms": (1000., 50., 2000., "ms"),
            "dt_ms": (.1, .1, 1., "ms"), "probability": (.02, 0., .04, "probability"),
            "exc_weight": (.004, 0., 1., "uS"), "inh_weight": (.051, 0., 1., "uS"), "seed": (98765, 0, 2**32-1, "1")},
        "notes": ["This notebook invokes PyNN with the Brian2 backend; it is distinct from the 1500-cell sPyNNaker-named notebook already in the dashboard.",
            "COBA is the command shown in the notebook. Seeded independent streams and an explicit external delay of 0.2 ms make local runs reproducible. The script's two analog cells per population are preserved."]},
}

SINGLE_LABELS = {spec["label"]: key for key, spec in EXPERIMENTS.items() if spec["section"] == "single"}
NETWORK_LABELS = {spec["label"]: key for key, spec in EXPERIMENTS.items() if spec["section"] == "network"}
