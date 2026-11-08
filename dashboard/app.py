"""CNT interactive teaching laboratory. Launch from this directory with Streamlit."""

import csv
import io
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from cnt_dashboard.cells import CELLS, PENDING_CELLS, simulate_cell
from cnt_dashboard.protocols import Protocol
from cnt_dashboard import populations
from cnt_dashboard.model_notes import CELL_EQUATIONS, CELL_NOTES, cell_glossary, voltage_references, add_voltage_lines
from cnt_dashboard.population_notes import population_notes
from cnt_dashboard.references import model_references
from cnt_dashboard.experiment_pages import render_single, render_network, voltage_checkboxes
from cnt_dashboard.notebook_catalogue import SINGLE_LABELS, NETWORK_LABELS
from cnt_dashboard.notebook_pages import render_notebook

REPO = "https://github.com/albertoarturovergani/CNT/blob/main/"
st.set_page_config(page_title="CNT · Neural model laboratory", page_icon="🧠", layout="wide")
st.title("Neural model laboratory")
st.caption("COMPUTATIONAL NEUROSCIENCE TUTORIAL · Cells, populations and networks")
st.write("Change an input or a parameter, run the model, and inspect the resulting dynamics.")
spiking_tab, large_scale_tab = st.tabs(["Spiking", "Large Scale"])
with spiking_tab:
    single_cell_tab, spiking_network_tab = st.tabs(["Single cell", "Network"])
with large_scale_tab:
    population_tab, large_network_tab = st.tabs(["Single node", "Network"])


@st.cache_data(show_spinner=False)
def tvb_metadata(name):
    return populations.model_metadata(name)


@st.cache_data(show_spinner=False)
def tvb_notes(name):
    return population_notes(name)


def bibliography(name, population=False):
    with st.expander("Bibliography · original publications and model variants"):
        for i, ref in enumerate(model_references(name, population), 1):
            st.markdown(f"{i}. **{ref['role']}** — {ref['authors']} ({ref['year']}). "
                        f"*{ref['title']}*. {ref['venue']}. [Publication]({ref['url']}).")


def model_notes(name, population=False):
    notes = tvb_notes(name) if population else None
    with st.expander("Model equations", expanded=True):
        for equation in notes["equations"] if population else CELL_EQUATIONS[name]:
            st.latex(equation)
        st.caption(notes["scope"] if population else CELL_NOTES[name])
        if population and notes["note"]:
            st.caption(notes["note"])
    with st.expander("Terms, symbols and units"):
        st.dataframe(notes["glossary"] if population else cell_glossary(name), hide_index=True, width="stretch")
    bibliography(name, population)
    if population:
        with st.expander("Installed TVB class · exact equations and helper functions"):
            st.code(notes["source"], language="python")


def downloads(result, population=False):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    if population:
        states = result["states"]
        names = [f"{name}[mode={mode}]" for name in result["state_variables"]
                 for mode in range(states.shape[2])]
        values = states.reshape(len(states), -1)
    else:
        names = [f"{k} [{result['state_units'][k]}]" for k in result["states"]]
        values = np.column_stack(list(result["states"].values()))
        names.append(f"input [{result['input_unit']}]")
        values = np.column_stack([values, result["drive"]])
    writer.writerow(["time [ms]", *names])
    writer.writerows(np.column_stack([result["time_ms"], values]))
    prefix = "population" if population else "neuron"
    cols = st.columns(3 if not population else 2)
    cols[0].download_button("Download traces · CSV", buffer.getvalue(), f"cnt_{prefix}_traces.csv",
                           "text/csv", key=f"csv-{prefix}")
    cols[1].download_button("Download configuration · JSON",
        json.dumps(result["configuration"], indent=2), f"cnt_{prefix}_configuration.json",
        "application/json", key=f"json-{prefix}")
    if not population:
        cols[2].download_button("Download spikes · CSV", "time_ms\n" +
            "\n".join(str(t) for t in result["spikes_ms"]), "cnt_neuron_spikes.csv", "text/csv")


with single_cell_tab:
    cell_page = st.radio("Single-cell experiment", ["Model explorer", "PyNN notebook", *SINGLE_LABELS], horizontal=True, key="single-cell-page")
    if cell_page == "PyNN notebook":
        render_single()
    elif cell_page in SINGLE_LABELS:
        render_notebook(SINGLE_LABELS[cell_page])
    else:
        controls, output = st.columns([1, 2], gap="large")
        with controls:
            cell_id = st.selectbox("Neuron model", list(CELLS), format_func=lambda k: CELLS[k].label,
                                   key="cell-model")
            spec = CELLS[cell_id]
            st.write(spec.description)
            for path in spec.notebooks:
                st.markdown(f"[Open source notebook]({REPO}{path})")
            with st.form(f"cell-form-{cell_id}"):
                st.subheader("Input protocol")
                waveform = st.selectbox("Waveform", ["step", "ramp", "sine"], key=f"wave-{cell_id}")
                amp = st.number_input(f"Amplitude [{spec.input_unit}]", value=spec.amplitude, format="%.4f")
                duration = st.number_input("Duration [ms]", min_value=20., max_value=2000., value=400., step=20.)
                start = st.number_input("Input starts [ms]", min_value=0., value=50., step=10.)
                stop = st.number_input("Input stops [ms]", min_value=0., value=350., step=10.)
                frequency = st.number_input("Sine frequency [Hz]", min_value=0., value=10., step=1.)
                dt = st.selectbox("Integration step [ms]", [spec.dt_ms, spec.dt_ms / 2, spec.dt_ms / 5])
                with st.expander("Model parameters"):
                    params = {name: st.number_input(f"{name} [{p.unit}]", value=float(p.default),
                              format="%.5f", key=f"param-{cell_id}-{name}") for name, p in spec.parameters.items()}
                submitted = st.form_submit_button("Run single neuron", type="primary")
            if submitted:
                try:
                    with st.spinner("Integrating one neuron with Brian2…"):
                        result = simulate_cell(cell_id, Protocol(duration, dt, start, stop, amp, waveform, frequency), params)
                    st.session_state["cell-result"] = (cell_id, result)
                except Exception as error:
                    st.session_state.pop("cell-result", None)
                    detail = str(error)
                    if "signal only works in main thread" in detail:
                        detail = "Launch the dashboard with 'python launch.py' to initialize Brian2 on the main thread."
                    st.error(f"Simulation did not complete: {detail}")
        with output:
            model_notes(cell_id)
            saved = st.session_state.get("cell-result")
            if saved and saved[0] == cell_id:
                result = saved[1]
                config = result["configuration"]
                protocol = config["protocol"]
                st.subheader(spec.label)
                st.caption(f"Showing completed run · {protocol['amplitude']:g} {spec.input_unit} · "
                           f"dt {protocol['dt_ms']:g} ms · Brian2 {config['version']}")
                a, b, c = st.columns(3)
                a.metric("Detected spikes", len(result["spikes_ms"]))
                b.metric("Whole-run firing rate", f"{len(result['spikes_ms']) / (protocol['duration_ms'] / 1000):.1f} Hz")
                c.metric("Integration step", f"{protocol['dt_ms']:g} ms")
                figure = make_subplots(rows=3, cols=1, shared_xaxes=True,
                    row_heights=[.13, .6, .27], vertical_spacing=.06)
                figure.add_trace(go.Scatter(x=result["spikes_ms"], y=np.zeros(len(result["spikes_ms"])),
                    mode="markers", marker={"symbol": "line-ns", "size": 12, "color": "#fbbf24"}, name="Spikes"), row=1, col=1)
                figure.add_trace(go.Scatter(x=result["time_ms"], y=result["states"]["v"],
                    name="Voltage", line={"color": "#5eead4"}), row=2, col=1)
                figure.add_trace(go.Scatter(x=result["time_ms"], y=result["drive"],
                    name="Input", line={"color": "#a5b4fc"}), row=3, col=1)
                refs = voltage_references(cell_id, config["parameters"])
                add_voltage_lines(figure, voltage_checkboxes(refs, f"voltage-{cell_id}"))
                figure.update_yaxes(title_text="Events", row=1, col=1, showticklabels=False)
                figure.update_yaxes(title_text=result["state_units"]["v"], row=2, col=1)
                figure.update_yaxes(title_text=spec.input_unit, row=3, col=1)
                figure.update_xaxes(title_text="Time [ms]", row=3, col=1)
                figure.update_layout(height=550, template="plotly_dark", margin={"l": 20, "r": 20, "t": 20, "b": 10})
                st.plotly_chart(figure, width="stretch", key="cell-voltage-plot")
                st.caption("Traces contain the recorded state. Threshold/reset models do not simulate an action-potential waveform. "
                           "HH and Morris-Lecar spike counts use voltage crossings, without a voltage reset.")
                if len(result["states"]) > 1:
                    with st.expander("State-space trajectory"):
                        second = st.selectbox("Second state", list(result["states"])[1:], key=f"cell-second-state-{cell_id}")
                        phase = go.Figure(go.Scatter(x=result["states"]["v"], y=result["states"][second], mode="lines"))
                        phase.update_layout(xaxis_title=f"v [{result['state_units']['v']}]",
                            yaxis_title=f"{second} [{result['state_units'][second]}]", template="plotly_dark", height=320)
                        st.plotly_chart(phase, width="stretch")
                downloads(result)
            else:
                st.info("Choose a model and run an experiment to see voltage, spike times and the applied input.")
            st.caption("Inputs retain each model's native units. Matching their numeric amplitudes does not imply equivalent stimulation.")


with population_tab:
    st.write("One isolated TVB node, with zero inter-node weights and coupling gain. "
             "Local population interactions defined inside the selected model remain active.")
    try:
        model_names = populations.available_models()
        pop_controls, pop_output = st.columns([1, 2], gap="large")
        with pop_controls:
            pop_name = st.selectbox("TVB core model", model_names,
                index=model_names.index("Generic2dOscillator") if "Generic2dOscillator" in model_names else 0,
                key="population-model")
            meta = tvb_metadata(pop_name)
            st.caption(f"TVB {meta['version']} · {len(model_names)} registered core models · {meta['modes']} mode(s)")
            with st.expander("Model description and source"):
                st.text(meta["description"])
                st.markdown("[TVB model documentation](https://docs.thevirtualbrain.org/api/tvb.simulator.models.html)")
            with st.form(f"population-form-{pop_name}"):
                pop_duration = st.number_input("Simulation duration [ms]", min_value=10., max_value=2000., value=200., step=10.)
                pop_dt = st.selectbox("TVB integration step [ms]", [.05, .025, .01, .005, .001])
                seed = st.number_input("Initial-condition seed", min_value=0, max_value=2**32-1, value=0, step=1)
                st.caption("Deterministic Heun integration. Drive parameters and state variables retain their model-specific meaning and units.")
                pop_params = {}
                with st.expander("Native TVB parameters"):
                    for name, detail in meta["parameters"].items():
                        vals = detail["values"]
                        help_text = detail["description"]
                        if detail["minimum"] is not None:
                            help_text += f"\nTVB exploration domain: {detail['minimum']} to {detail['maximum']}."
                        if len(vals) == 1:
                            pop_params[name] = [st.number_input(name, value=float(vals[0]), format="%.7f",
                                key=f"tvb-param-{pop_name}-{name}", help=help_text)]
                        else:
                            pop_params[name] = st.text_input(f"{name} · JSON array", value=json.dumps(vals),
                                key=f"tvb-param-{pop_name}-{name}", help=help_text)
                with st.expander("Initial conditions · optional"):
                    explicit = st.checkbox("Set all initial states explicitly", key=f"initial-{pop_name}")
                    initial_values = {name: st.number_input(name, value=float(np.mean(meta["state_ranges"][name])),
                        format="%.7f", key=f"tvb-init-{pop_name}-{name}") for name in meta["state_variables"]}
                    st.caption("Unchecked: seeded samples from TVB's initialization ranges. "
                               "Checked: entered values are applied to all modes.")
                pop_run = st.form_submit_button("Run isolated population", type="primary")
            if pop_run:
                try:
                    overrides = {k: json.loads(v) if isinstance(v, str) else v for k, v in pop_params.items()}
                    with st.spinner("Integrating the native TVB model…"):
                        pop_result = populations.simulate_population(pop_name, pop_duration, pop_dt, overrides,
                            initial_values if explicit else None, int(seed))
                    st.session_state["population-result"] = (pop_name, pop_result)
                except Exception as error:
                    st.session_state.pop("population-result", None)
                    st.error(f"Simulation did not complete: {error}")
        with pop_output:
            model_notes(pop_name, population=True)
            pop_saved = st.session_state.get("population-result")
            if pop_saved and pop_saved[0] == pop_name:
                pop_result = pop_saved[1]
                config = pop_result["configuration"]
                st.subheader(pop_name)
                st.caption(f"Showing completed run · {config['duration_ms']:g} ms · dt {config['dt_ms']:g} ms · "
                           f"seed {config['seed']} · TVB {config['version']}")
                selected = st.multiselect("State variables to plot", pop_result["state_variables"],
                    default=pop_result["state_variables"][:2], key=f"plot-vars-{pop_name}")
                if selected:
                    fig = make_subplots(rows=len(selected), cols=1, shared_xaxes=True, vertical_spacing=.06)
                    for row, variable in enumerate(selected, 1):
                        var_idx = pop_result["state_variables"].index(variable)
                        for mode in range(pop_result["states"].shape[2]):
                            fig.add_trace(go.Scatter(x=pop_result["time_ms"],
                                y=pop_result["states"][:, var_idx, mode], name=f"{variable} · mode {mode}", mode="lines"), row=row, col=1)
                        fig.update_yaxes(title_text=variable, row=row, col=1)
                    fig.update_xaxes(title_text="Time [ms]", row=len(selected), col=1)
                    fig.update_layout(template="plotly_dark", height=max(350, 220 * len(selected)),
                        margin={"l": 20, "r": 20, "t": 20, "b": 10})
                    st.plotly_chart(fig, width="stretch")
                st.caption("Each variable has its own axis. State values use native TVB units, described in the selected model's documentation.")
                if len(pop_result["state_variables"]) >= 2:
                    with st.expander("State-space trajectory · mode 0"):
                        xvar = st.selectbox("Horizontal state", pop_result["state_variables"], key=f"phase-x-{pop_name}")
                        yvar = st.selectbox("Vertical state", pop_result["state_variables"], index=1, key=f"phase-y-{pop_name}")
                        xi, yi = [pop_result["state_variables"].index(v) for v in (xvar, yvar)]
                        phase = go.Figure(go.Scatter(x=pop_result["states"][:, xi, 0], y=pop_result["states"][:, yi, 0], mode="lines"))
                        phase.update_layout(xaxis_title=xvar, yaxis_title=yvar, template="plotly_dark", height=320)
                        st.plotly_chart(phase, width="stretch")
                downloads(pop_result, population=True)
            else:
                st.info("Choose any registered core TVB class, inspect its native parameters, and run an isolated node.")
                st.caption("Some models need a smaller time step or model-specific initial conditions. "
                           "The catalogue includes neural masses, mean-field reductions and phenomenological oscillators.")
    except Exception as error:
        st.error(f"TVB model interface unavailable: {error}")


with spiking_network_tab:
    network_page = st.selectbox("Network experiment", [*NETWORK_LABELS, "PyNN E/I benchmark"], key="spiking-network-page")
    if network_page == "PyNN E/I benchmark":
        render_network()
    else:
        render_notebook(NETWORK_LABELS[network_page])

with large_network_tab:
    st.subheader("Large Scale · Network")
    st.info("Coming next: TVB networks of mean-field, neural-mass and oscillator nodes.")
    st.write("This section will compare connectivity, coupling strengths, delays and external inputs. "
             "For now, use Single node to inspect each native TVB model in isolation.")


with st.expander("Catalogue & roadmap"):
    st.subheader("Teaching sequence")
    st.markdown("1. **Single neuron:** input, membrane dynamics, adaptation and spike generation.\n"
                "2. **Single population:** state variables, local interactions and oscillations.\n"
                "3. **Spiking lessons:** single clique, local model comparison, feedforward decay, divergent/small-world connectivity and E/I benchmarks.\n"
                "4. **Large Scale network, next stage:** compare connectivity while keeping node dynamics and inputs fixed.")
    st.subheader("Single-neuron catalogue")
    st.dataframe([{"model": spec.label, "status": "Runnable with Brian2", "input unit": spec.input_unit}
                  for spec in CELLS.values()] +
                 [{"model": item["model"], "status": item["status"], "input unit": "To verify"} for item in PENDING_CELLS],
                 hide_index=True, width="stretch")
    st.markdown("[Geminiani E-GLIF source](https://github.com/dbbs-lab/cerebellar-models/blob/master/cerebellar_models/nest_models/eglif_cond_alpha_multisyn.nestml) · "
                "[De Grazia E-GLIF source](https://github.com/dbbs-lab/cerebellar-models/blob/master/cerebellar_models/nest_models/eglif_multirec.nestml)")
    st.subheader("Scope of the TVB catalogue")
    st.write("Models are discovered from the installed TVB ModelsEnum registry. "
             "The abstract base class and unregistered contrib or third-party models are outside this first catalogue.")
    st.subheader("Network experiments to add")
    st.write("Start with disconnected nodes, a pair and a ring; then compare random, small-world, "
             "modular and empirical connectivity. Control size, density, weight distribution, "
             "excitation/inhibition, delays and input when comparing topologies.")
    st.markdown(f"[Existing Brian2 notebooks]({REPO}notebooks/numerical-methods/brian2/) · "
                f"[Existing TVB notebooks]({REPO}notebooks/numerical-methods/TVB/)")
