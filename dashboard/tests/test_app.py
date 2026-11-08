from pathlib import Path
import brian2  # Initialize on the main thread, as launch.py does for the real app.
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
