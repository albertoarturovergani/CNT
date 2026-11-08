from pathlib import Path
import json
from unittest.mock import patch
import brian2  # Initialize on the main thread, as launch.py does for the real app.
import numpy as np
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_both_experiment_forms_run_and_render_without_errors():
    app = AppTest.from_file(str(APP)).run(timeout=60)
    assert not app.exception
    assert not app.error
    app.button(key="FormSubmitter:cell-form-lif-Run single neuron").click().run(timeout=60)
    assert not app.exception
    assert not app.error
    assert len(app.metric) == 3
    app.button(key="FormSubmitter:population-form-Generic2dOscillator-Run isolated population").click().run(timeout=60)
    assert not app.exception
    assert not app.error
    assert "population-result" in app.session_state
    app.selectbox(key="cell-model").select("hh").run(timeout=60)
    app.button(key="FormSubmitter:cell-form-hh-Run single neuron").click().run(timeout=60)
    assert not app.exception
    assert not app.error
    stop = next(item for item in app.number_input if item.label == "Input stops [ms]")
    stop.set_value(10.)
    app.button(key="FormSubmitter:cell-form-hh-Run single neuron").click().run(timeout=60)
    assert not app.exception
    assert any("start < stop" in item.value for item in app.error)
    assert "cell-result" not in app.session_state


def _voltage_plot(app):
    charts = [json.loads(chart.proto.spec) for chart in app.get("plotly_chart")]
    return next(chart for chart in charts if any(trace.get("name") == "Voltage" for trace in chart["data"]))


def test_voltage_checkboxes_redraw_completed_run_without_simulating_again():
    from cnt_dashboard.cells import simulate_cell
    with patch("cnt_dashboard.cells.simulate_cell", wraps=simulate_cell) as run:
        app = AppTest.from_file(str(APP)).run(timeout=60)
        app.button(key="FormSubmitter:cell-form-lif-Run single neuron").click().run(timeout=60)
        assert not app.exception
        before = _voltage_plot(app)
        # Rest and reset share one line; threshold is a separate level.
        assert len(before["layout"]["shapes"]) == 2
        assert all(shape["yref"] == "y2" for shape in before["layout"]["shapes"])
        recorded = app.session_state["cell-result"][1]["states"]["v"].copy()
        # Change an unsubmitted control; displayed references still belong to the old run.
        app.number_input(key="param-lif-Vth").set_value(-45.).run(timeout=60)
        assert any(shape["y0"] == -50 for shape in _voltage_plot(app)["layout"]["shapes"])
        app.checkbox(key="voltage-lif-threshold").uncheck().run(timeout=60)
        after = _voltage_plot(app)
        assert len(after["layout"]["shapes"]) == 1
        np.testing.assert_array_equal(recorded, app.session_state["cell-result"][1]["states"]["v"])
        assert before["data"] == after["data"]
        assert run.call_count == 1
        assert not app.error
        assert {"Spiking", "Large Scale", "Single cell", "Single node", "Network"}.issubset({tab.label for tab in app.tabs})


def test_pynn_single_and_network_pages_run_and_export():
    app = AppTest.from_file(str(APP)).run(timeout=60)
    app.radio(key="single-cell-page").set_value("PyNN notebook").run(timeout=60)
    app.button(key="FormSubmitter:pynn-single-form-Run PyNN single cell").click().run(timeout=60)
    assert not app.exception
    assert not app.error
    assert "pynn-single-result" in app.session_state
    assert len(_voltage_plot(app)["layout"]["shapes"]) == 3
    app.checkbox(key="pynn-single-voltage-reset").uncheck().run(timeout=60)
    assert len(_voltage_plot(app)["layout"]["shapes"]) == 2
    app.number_input(key="pynn-network-n_cells").set_value(50)
    app.number_input(key="pynn-network-duration_ms").set_value(100.)
    app.button(key="FormSubmitter:pynn-network-form-Run PyNN network").click().run(timeout=60)
    assert not app.exception
    assert not app.error, [error.value for error in app.error]
    assert "pynn-network-result" in app.session_state
    assert len(app.get("download_button")) >= 6
    # A selected trace from a different population is a display-only change.
    app.selectbox(key="pynn-network-trace-pop").select("inh").run(timeout=60)
    assert not app.exception
    assert not app.error
