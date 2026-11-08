"""Teaching content covers selectable models and uses model-specific references."""

from plotly.subplots import make_subplots
import plotly.graph_objects as go
from cnt_dashboard.cells import CELLS
from cnt_dashboard.model_notes import CELL_EQUATIONS, cell_glossary, voltage_references, add_voltage_lines
from cnt_dashboard.populations import available_models, model_metadata
from cnt_dashboard.population_notes import population_notes
from cnt_dashboard.references import model_references


def test_all_selectable_models_have_equations_units_and_publications():
    for name, spec in CELLS.items():
        assert CELL_EQUATIONS[name]
        rows = cell_glossary(name)
        assert set(spec.parameters).issubset({row["Symbol / code"] for row in rows})
        assert all(row["Meaning"] and row["Unit"] for row in rows)
        assert model_references(name)
    for name in available_models():
        notes = population_notes(name)
        assert notes["equations"]
        assert model_references(name, population=True)
        meta = model_metadata(name)
        assert set(meta["parameters"]) | set(meta["state_variables"]) <= {row["Symbol / code"] for row in notes["glossary"]}
        assert all(row["Meaning"] and row["Unit"] for row in notes["glossary"])


def test_reference_lines_use_native_spike_rules_and_only_the_voltage_axis():
    hh = voltage_references("hh", {k: v.default for k, v in CELLS["hh"].parameters.items()})
    assert {r.key for r in hh} == {"rest", "detect"}
    assert next(r.value for r in hh if r.key == "detect") == -40
    adex = voltage_references("adex", {k: v.default for k, v in CELLS["adex"].parameters.items()})
    assert next(r.value for r in adex if r.key == "detect") == -40.4
    figure = make_subplots(rows=3, cols=1)
    figure.add_trace(go.Scatter(x=[0, 1], y=[-70, -60]), row=2, col=1)
    before = figure.data[0].to_plotly_json()
    add_voltage_lines(figure, hh)
    assert all(shape.yref == "y2" for shape in figure.layout.shapes)
    assert figure.data[0].to_plotly_json() == before
