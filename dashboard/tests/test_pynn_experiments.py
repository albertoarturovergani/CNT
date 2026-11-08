"""Check notebook stimuli/units, cleanup, and seeded recurrent projections."""

from dataclasses import replace
import brian2
import numpy as np
import pytest
from cnt_dashboard.pynn_experiments import SingleConfig, NetworkConfig, simulate_single, simulate_network


def test_pynn_notebook_records_the_original_stimuli_and_native_units():
    result = simulate_single()
    time = result["time_ms"]
    ac = result["currents"]["AC"][:, 0]
    step = result["currents"]["Step"][:, 0]
    expected_ac = np.where((time >= 100) & (time < 400), 10 * np.sin(2 * np.pi * 10 * (time-100) / 1000), 0)
    np.testing.assert_allclose(ac, expected_ac, atol=1e-12)
    np.testing.assert_allclose(step, np.where((time >= 600) & (time < 610), 10., 0.))
    assert result["signals"]["v"].shape == (801, 1)
    assert len(result["spikes_ms"][0]) > 0
    assert np.count_nonzero(result["signals"]["gsyn_exc"]) == 0
    assert np.count_nonzero(result["signals"]["gsyn_inh"]) == 0
    assert result["configuration"]["parameter_units"]["cm"] == "nF"


def test_pynn_passive_membrane_matches_the_discrete_rc_solution_after_another_run():
    cfg = SingleConfig(duration_ms=20, dt_ms=.1, ac_start_ms=1, ac_stop_ms=5, ac_amplitude_nA=0,
                       step_start_ms=10, step_stop_ms=11, step_amplitude_nA=0)
    result = simulate_single(cfg, {"v_rest": -60., "v_thresh": -30., "tau_m": 10.})
    voltage = result["signals"]["v"][:, 0]
    expected = -60 + (voltage[0] + 60) * (1-.1/10)**np.arange(len(voltage))
    np.testing.assert_allclose(voltage, expected, atol=1e-10)
    assert not len(result["spikes_ms"][0])


def test_pynn_network_replays_connectivity_and_spikes_with_the_same_seed():
    cfg = NetworkConfig(n_cells=50, duration_ms=100, probability=.1, n_external=5,
                        external_probability=.5, external_duration_ms=50, seed=73)
    first, replay = simulate_network(cfg), simulate_network(cfg)
    assert first["connection_counts"] == replay["connection_counts"]
    for name, edges in first["connectivity"].items():
        np.testing.assert_array_equal(edges, replay["connectivity"][name])
        assert len(edges) == first["connection_counts"][name]
        assert np.all(edges[:, 2] >= 0)  # inhibition is the receptor type, not a negative conductance
        np.testing.assert_array_equal(edges[:, 3], cfg.delay_ms)
    assert set(first["connection_counts"]) == {"exc2exc", "exc2inh", "inh2exc", "inh2inh", "ext2exc", "ext2inh"}
    assert len(first["populations"]["exc"]["spikes_ms"]) == 40
    assert len(first["populations"]["inh"]["spikes_ms"]) == 10
    for name, pop in first["populations"].items():
        for a, b in zip(pop["spikes_ms"], replay["populations"][name]["spikes_ms"]):
            np.testing.assert_array_equal(a, b)
        for variable, array in pop["signals"].items():
            np.testing.assert_array_equal(array, replay["populations"][name]["signals"][variable])
            assert np.isfinite(array).all()
    # Input reaches both conductance-based populations, in the expected uS scale.
    assert np.max(first["populations"]["exc"]["signals"]["gsyn_exc"]) > 0
    other = simulate_network(replace(cfg, seed=74))
    assert any(not np.array_equal(a, b) for a, b in zip(first["populations"]["thalamus"]["spikes_ms"], other["populations"]["thalamus"]["spikes_ms"]))


def test_invalid_experiments_fail_before_starting_the_backend():
    with pytest.raises(ValueError, match="AC input"):
        simulate_single(SingleConfig(duration_ms=20))
    with pytest.raises(ValueError, match="probabilities"):
        simulate_network(NetworkConfig(probability=1.1))
    with pytest.raises(ValueError, match="synapses"):
        simulate_network(NetworkConfig(n_cells=3000, probability=1))


def test_disconnected_network_has_no_synaptic_drive_or_spikes_and_exports_empty_edges():
    result = simulate_network(NetworkConfig(n_cells=10, duration_ms=50, probability=0,
        external_probability=0, external_rate_hz=0))
    assert not any(result["connection_counts"].values())
    assert all(edges.shape == (0, 4) for edges in result["connectivity"].values())
    for pop in result["populations"].values():
        assert not any(map(len, pop["spikes_ms"]))
        for name in ("gsyn_exc", "gsyn_inh"):
            if name in pop["signals"]:
                assert not np.count_nonzero(pop["signals"][name])
