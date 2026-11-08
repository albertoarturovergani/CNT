"""Scientific/protocol checks for the additional source-linked lessons."""

import brian2
import numpy as np
import pytest
from cnt_dashboard.cells import CELLS, simulate_cell
from cnt_dashboard.protocols import Protocol
from cnt_dashboard.cell_comparison import comparison_models, compare_cells, pynn_cell_models
from cnt_dashboard.notebook_experiments import simulate_notebook, divergent_edges, small_world_edges


def test_clique_preserves_reciprocal_receptors_weights_and_current_step():
    result = simulate_notebook("single_clique")
    assert result["connection_counts"] == {"cell0_exc_cell1": 1, "cell1_inh_cell0": 1}
    assert result["projections"]["cell0_exc_cell1"]["receptor"] == "excitatory"
    assert result["projections"]["cell1_inh_cell0"]["receptor"] == "inhibitory"
    for edges in result["connectivity"].values():
        np.testing.assert_allclose(edges, [[0, 0, 1., 1.]])
    current = result["currents"]["Step to cell0"][:, 0]
    times = result["populations"]["cell0"]["time_ms"]
    np.testing.assert_array_equal(current, np.where((times >= 30) & (times < 40), 10., 0.))


def test_decaying_network_is_feedforward_and_retains_five_events_per_active_source():
    result = simulate_notebook("decaying")
    assert set(result["connectivity"]) == {"input"}
    assert result["connection_counts"]["input"] == 100
    trains = result["populations"]["thalamus"]["spikes_ms"]
    assert [len(t) for t in trains] == [0]*40+[5]*20+[0]*40
    voltage = result["populations"]["network"]["signals"]["v"]
    np.testing.assert_allclose(voltage[:, :40], -65.)
    np.testing.assert_allclose(voltage[:, 60:], -65.)


def test_diverging_connections_follow_the_notebooks_deterministic_cutoff():
    edges = divergent_edges(100)
    assert len(edges) == 198
    np.testing.assert_array_equal(np.abs(edges[:, 0]-edges[:, 1]), 1.)
    np.testing.assert_allclose(edges[:, 2], .08)
    np.testing.assert_allclose(edges[:, 3], 1+1/.35)
    result = simulate_notebook("diverging", {"n_cells": 20})
    actual = result["connectivity"]["recurrent_exc"]
    expected = divergent_edges(20)
    expected[:, 3] = np.rint(expected[:, 3])  # PyNN rounds to the native 1 ms clock
    np.testing.assert_allclose(actual[np.lexsort((actual[:, 1], actual[:, 0]))],
                               expected[np.lexsort((expected[:, 1], expected[:, 0]))])


def test_small_world_preserves_period_500_local_graph_and_seeded_rewiring():
    local = small_world_edges(100, 1.5, 0., .1, np.random.default_rng(23))
    assert len(local) == 298  # 100 self edges + 99 edges in each direction
    assert not np.any((local[:, 0] == 0) & (local[:, 1] == 99))
    assert np.all((local[:, 3] >= .1) & (local[:, 3] <= 100))
    first = small_world_edges(100, 1.5, 1., .1, np.random.default_rng(23))
    replay = small_world_edges(100, 1.5, 1., .1, np.random.default_rng(23))
    np.testing.assert_array_equal(first, replay)
    np.testing.assert_array_equal(first[:, 0], local[:, 0])
    assert np.any(np.abs(first[:, 0]-first[:, 1]) > 1)
    result = simulate_notebook("small_world", {"n_cells": 20})
    assert len(result["connectivity"]["recurrent_excitatory"]) == 58
    assert len(result["connectivity"]["recurrent_inhibitory"]) == 58


def test_local_comparison_discovers_neurons_and_preserves_current_units():
    names = pynn_cell_models()
    assert {"HH_cond_exp", "EIF_cond_exp_isfa_ista", "Izhikevich", "IF_curr_delta"} <= set(names)
    assert not any(name.startswith("SpikeSource") or name in ("PointNeuron", "StandardCellType") for name in names)
    choices = comparison_models()
    native_labels = {name: label for label, (backend, name) in choices.items() if backend == "brian2"}
    assert set(native_labels) == set(CELLS)
    result = compare_cells(duration_ms=50, start_ms=10, stop_ms=40, amplitude_nA=.05,
        selected=["PyNN · IF_cond_exp", native_labels["lif"], native_labels["izhikevich"]])
    lif = result["populations"][native_labels["lif"]]
    assert lif["input_amplitude"] == 50 and lif["input_unit"] == "pA"
    expected = simulate_cell("lif", Protocol(50, CELLS["lif"].dt_ms, 10, 40, 50))
    np.testing.assert_array_equal(lif["signals"]["v"][:, 0], expected["states"]["v"])
    assert result["populations"][native_labels["izhikevich"]]["input_unit"] == "model units"
    assert np.isfinite(result["populations"]["PyNN · IF_cond_exp"]["signals"]["v"]).all()


def test_script_benchmark_records_two_analog_cells_but_all_spikes():
    result = simulate_notebook("balance_brian2", {"n_cells": 50, "duration_ms": 100.})
    assert len(result["populations"]["exc"]["spikes_ms"]) == 40
    assert len(result["populations"]["inh"]["spikes_ms"]) == 10
    for name in ("exc", "inh"):
        assert result["populations"][name]["signals"]["v"].shape == (1001, 2)
    assert result["configuration"]["native_network"]["delay_ms"] == .2
    assert result["configuration"]["source_script"].endswith("VAbenchmarks.py")


def test_hardware_stdp_is_linked_without_substituting_its_dendritic_delay():
    with pytest.raises(ValueError, match="requires SpiNNaker"):
        simulate_notebook("stdp")
