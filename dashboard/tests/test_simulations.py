"""Numerical and integration checks, including models with multiple state variables/modes."""

import numpy as np
import pytest
from cnt_dashboard.cells import CELLS, simulate_cell
from cnt_dashboard.protocols import Protocol
from cnt_dashboard.populations import available_models, simulate_population, model_metadata


def test_protocol_is_half_open_and_preserves_sign():
    time, drive = Protocol(20, .05, 5, 10, -12).samples()
    assert np.all(drive[(time >= 5) & (time < 10)] == -12)
    assert np.all(drive[(time < 5) | (time >= 10)] == 0)
    with pytest.raises(ValueError):
        Protocol(20, .05, 10, 5).samples()


def test_lif_matches_passive_membrane_solution():
    # 50 pA is subthreshold: compare with the analytic RC charging curve.
    protocol = Protocol(40, .01, 0, 40, 50)
    result = simulate_cell("lif", protocol)
    expected = -65 + 5 * (1 - np.exp(-result["time_ms"] / 20))
    np.testing.assert_allclose(result["states"]["v"], expected, atol=.001)
    assert len(result["spikes_ms"]) == 0


@pytest.mark.parametrize("model_id", list(CELLS))
def test_cell_default_protocol_has_finite_states_and_spikes(model_id):
    spec = CELLS[model_id]
    protocol = Protocol(100, spec.dt_ms, 10, 90, spec.amplitude)
    result = simulate_cell(model_id, protocol)
    assert len(result["time_ms"]) == round(100 / spec.dt_ms)
    assert len(result["spikes_ms"]) > 0
    assert all(np.isfinite(array).all() for array in result["states"].values())
    assert all(len(array) == len(result["time_ms"]) for array in result["states"].values())


def test_cell_rejects_a_step_too_large_for_its_kinetics():
    with pytest.raises(ValueError, match="dt"):
        simulate_cell("hh", Protocol(100, .1, 10, 90, .4))


def test_tvb_linear_matches_analytic_solution():
    result = simulate_population("Linear", 20, .01, {"gamma": [-.1]}, {"x": 1.})
    expected = np.exp(-.1 * result["time_ms"])
    np.testing.assert_allclose(result["states"][:, 0, 0], expected, atol=1e-6)
    assert result["configuration"]["weights"] == [[0.]]
    assert result["configuration"]["coupling_gain"] == 0.


@pytest.mark.parametrize("name", ["Generic2dOscillator", "Epileptor", "EpileptorCodim3SlowMod", "ReducedSetFitzHughNagumo"])
def test_tvb_records_every_state_and_mode(name):
    metadata = model_metadata(name)
    result = simulate_population(name, 5, .01)
    assert result["states"].shape == (500, len(metadata["state_variables"]), metadata["modes"])
    assert np.isfinite(result["states"]).all()


def test_tvb_seed_and_exported_initial_conditions_reproduce_the_trajectory():
    first = simulate_population("Generic2dOscillator", 5, .01, seed=12)
    second = simulate_population("Generic2dOscillator", 5, .01, seed=12)
    np.testing.assert_array_equal(first["states"], second["states"])
    config = first["configuration"]
    initial = {name: config["initial_conditions"][0][idx][0]
               for idx, name in enumerate(config["state_variables"])}
    replay = simulate_population(config["model"], 5, .01, config["parameters"], initial)
    np.testing.assert_array_equal(first["states"], replay["states"])


def test_tvb_catalogue_excludes_the_abstract_model():
    names = available_models()
    assert "Model" not in names
    assert {"JansenRit", "MontbrioPazoRoxin", "WilsonCowan"}.issubset(names)
