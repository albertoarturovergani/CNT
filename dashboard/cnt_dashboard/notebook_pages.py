"""Source-linked lesson pages and plots for the introductory notebook adapters."""

import csv
import inspect
import io
import json
import math
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from .notebook_catalogue import EXPERIMENTS, SOURCE_COMMIT, HARDWARE_MODELS
from .notebook_experiments import simulate_notebook
from .cell_comparison import comparison_models
from .model_notes import CELL_EQUATIONS, CELL_NOTES, cell_glossary
from .references import model_references

REPO = "https://github.com/albertoarturovergani/CNT/blob/"


def _pynn_unit(name, model_name):
    if name.startswith("tau"):
        return "ms"
    if name in ("v_rest", "v_thresh", "v_reset", "v_spike", "v_offset", "delta_T", "c") or name.startswith("e_rev"):
        return "mV"
    if name == "cm":
        return "nF"
    if name.startswith("gbar") or name == "g_leak":
        return "uS"
    if name.startswith("q_") or (name == "a" and model_name.startswith("EIF")):
        return "nS"
    if name == "i_offset" or (name == "b" and model_name.startswith("EIF")):
        return "nA"
    if model_name == "Izhikevich":
        return "1/ms" if name in ("a", "b") else ("mV/ms" if name == "d" else "native")
    return "native model units"


def _references(experiment_id):
    with st.expander("Bibliography and model sources"):
        st.markdown("Davison A.P., et al. (2009). *PyNN: a common interface for neuronal network simulators*. "
                    "[DOI](https://doi.org/10.3389/neuro.11.011.2008).")
        if experiment_id == "stdp":
            st.markdown("Bi G.Q., Poo M.M. (1998). *Synaptic modifications in cultured hippocampal neurons: dependence on spike timing, synaptic strength, and postsynaptic cell type*. "
                        "[DOI](https://doi.org/10.1523/JNEUROSCI.18-24-10464.1998).")
        elif experiment_id == "small_world":
            st.markdown("Watts D.J., Strogatz S.H. (1998). *Collective dynamics of ‘small-world’ networks*. "
                        "[DOI](https://doi.org/10.1038/30918).")
            st.caption("Model-family foundation; the notebook's two-receptor distance-based construction is a separate teaching setup.")
            st.markdown("[Original connector implementation](https://spynnaker.readthedocs.io/en/7.1.0/_modules/spynnaker/pyNN/models/neural_projections/connectors/small_world_connector/)")
        elif experiment_id == "balance_brian2":
            st.markdown("Vogels T.P., Abbott L.F. (2005). *Signal propagation and logic gating in networks of integrate-and-fire neurons*. "
                        "[DOI](https://doi.org/10.1523/JNEUROSCI.3508-05.2005).")
            st.markdown("Brette R., et al. (2007). *Simulation of networks of spiking neurons: a review of tools and strategies*. "
                        "[DOI](https://doi.org/10.1007/s10827-007-0038-6).")
        st.markdown("[PyNN standard cell models](https://pynn.readthedocs.io/en/latest/reference/neuronmodels.html)")


def _model_inspector():
    with st.expander("Inspect comparison model · equations, parameters and references"):
        choices = comparison_models()
        selected = st.selectbox("Model to inspect", list(choices), key="comparison-inspect")
        backend, name = choices[selected]
        if backend == "brian2":
            for eq in CELL_EQUATIONS[name]:
                st.latex(eq)
            st.caption(CELL_NOTES[name])
            st.dataframe(cell_glossary(name), hide_index=True, width="stretch")
            for ref in model_references(name):
                st.markdown(f"{ref['authors']} ({ref['year']}). *{ref['title']}*. [Publication]({ref['url']}).")
        else:
            import pyNN.brian2 as sim
            model = getattr(sim, name)
            st.caption("The following are the actual Brian2 equations used by this PyNN class. Unit declarations are part of the equations. "
                       "Synaptic state variables receive no presynaptic input in this comparison.")
            st.code(str(model.eqs), language="text")
            st.dataframe([{"Native parameter": key, "Value": value, "Unit": _pynn_unit(key, name)} for key, value in model.default_parameters.items()],
                         hide_index=True, width="stretch")
            with st.expander("Parameter translations and units"):
                st.code(inspect.getsource(model), language="python")
            family = "hh" if name == "HH_cond_exp" else ("izhikevich" if name == "Izhikevich" else ("adex" if name.startswith("EIF") else "lif"))
            for ref in model_references(family):
                st.markdown(f"{ref['authors']} ({ref['year']}). *{ref['title']}*. [Model-family publication]({ref['url']}).")
            st.caption("Family publications identify the model's origin; native PyNN defaults can differ from published fits and the standalone CNT adapters.")


def _downloads(result, experiment_id):
    st.download_button("Download configuration · JSON", json.dumps(result["configuration"], indent=2),
                       f"cnt_{experiment_id}.json", "application/json", key=f"lesson-json-{experiment_id}")
    buffer = io.StringIO(); writer = csv.writer(buffer)
    writer.writerow(["population", "cell_index", "time_ms"])
    for name, pop in result["populations"].items():
        for cell, times in enumerate(pop["spikes_ms"]):
            writer.writerows((name, cell, time) for time in times)
    st.download_button("Download spike events · CSV", buffer.getvalue(), f"cnt_{experiment_id}_spikes.csv",
                       "text/csv", key=f"lesson-spikes-{experiment_id}")
    if result.get("connectivity"):
        edges = io.StringIO(); writer = csv.writer(edges)
        writer.writerow(["projection", "pre_cell", "post_cell", "weight", "weight_unit", "delay_ms"])
        for name, values in result["connectivity"].items():
            unit = result["projections"][name]["weight_unit"]
            writer.writerows((name, int(pre), int(post), weight, unit, delay) for pre, post, weight, delay in values)
        st.download_button("Download connectivity · CSV", edges.getvalue(), f"cnt_{experiment_id}_connections.csv",
                           "text/csv", key=f"lesson-edges-{experiment_id}")
    data = {}
    mapping = {}
    for i, (name, pop) in enumerate(result["populations"].items()):
        key = f"population_{i}"
        mapping[key] = name
        data[key+"_time_ms"] = pop["time_ms"]
        data.update({key+"_"+variable: value for variable, value in pop["signals"].items()})
    data["population_names_json"] = np.asarray(json.dumps(mapping))
    array_buffer = io.BytesIO(); np.savez_compressed(array_buffer, **data)
    st.download_button("Download analog traces · NPZ", array_buffer.getvalue(), f"cnt_{experiment_id}_traces.npz",
                       "application/octet-stream", key=f"lesson-traces-{experiment_id}")


def _comparison_results(result):
    names = list(result["populations"])
    fig = make_subplots(rows=math.ceil(len(names)/2), cols=2, subplot_titles=names, vertical_spacing=.035)
    rows = []
    for i, (name, pop) in enumerate(result["populations"].items()):
        fig.add_trace(go.Scattergl(x=pop["time_ms"], y=pop["signals"]["v"][:, 0], mode="lines", name=name),
                      row=i//2+1, col=i%2+1)
        fig.update_yaxes(title_text=pop["voltage_unit"], row=i//2+1, col=i%2+1)
        fig.update_xaxes(title_text="Time [ms]", row=i//2+1, col=i%2+1)
        rows.append({"Model": name, "Recorded events": len(pop["spikes_ms"][0]), "Input": pop["input_amplitude"],
                     "Input unit": pop["input_unit"], "dt [ms]": pop["dt_ms"]})
    fig.update_layout(template="plotly_dark", height=max(350, 230*math.ceil(len(names)/2)), showlegend=False)
    st.plotly_chart(fig, width="stretch", key="comparison-voltage")
    st.dataframe(rows, hide_index=True, width="stretch")
    st.caption("Recorded events use each implementation's detector. Native PyNN HH_cond_exp reports above-threshold events, "
               "while CNT's HH adapter counts crossings; these event counts are not interchangeable action-potential rates. "
               "Matching physical current also does not match I/C or excitability across parameter sets.")


def _network_results(result, experiment_id):
    pops = result["populations"]
    rows = len(pops)
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, subplot_titles=list(pops), vertical_spacing=.06)
    for row, (name, pop) in enumerate(pops.items(), 1):
        times = np.concatenate(pop["spikes_ms"]) if pop["spikes_ms"] else np.array([])
        indices = np.repeat(np.arange(len(pop["spikes_ms"])), [len(t) for t in pop["spikes_ms"]])
        fig.add_trace(go.Scattergl(x=times, y=indices, mode="markers", marker={"size": 3}, name=name), row=row, col=1)
        fig.update_yaxes(title_text="Cell index", row=row, col=1)
    fig.update_xaxes(title_text="Time [ms]", row=rows, col=1)
    fig.update_layout(template="plotly_dark", height=max(320, rows*180))
    st.plotly_chart(fig, width="stretch", key=f"lesson-raster-{experiment_id}")
    recorded = [name for name, pop in pops.items() if pop["signals"]]
    pop_name = st.selectbox("Recorded population", recorded, key=f"lesson-pop-{experiment_id}")
    pop = pops[pop_name]
    count = pop["signals"]["v"].shape[1]
    cell = st.number_input("Recorded cell index", min_value=0, max_value=count-1, value=0,
                           key=f"lesson-cell-{experiment_id}-{pop_name}-{count}")
    variables = list(pop["signals"])
    traces = make_subplots(rows=len(variables), cols=1, shared_xaxes=True)
    for row, variable in enumerate(variables, 1):
        traces.add_trace(go.Scatter(x=pop["time_ms"], y=pop["signals"][variable][:, cell], name=variable), row=row, col=1)
        traces.update_yaxes(title_text="mV" if variable == "v" else "uS", row=row, col=1)
    traces.update_xaxes(title_text="Time [ms]", row=len(variables), col=1)
    traces.update_layout(template="plotly_dark", height=200*len(variables))
    st.plotly_chart(traces, width="stretch")
    if result.get("currents"):
        current_fig = go.Figure()
        for name, current in result["currents"].items():
            current_fig.add_trace(go.Scatter(x=pop["time_ms"], y=current[:, 0], name=name))
        current_fig.update_layout(template="plotly_dark", xaxis_title="Time [ms]", yaxis_title="Current [nA]", height=250)
        st.plotly_chart(current_fig, width="stretch")
    with st.expander("Population state heatmap"):
        variable = st.selectbox("State variable", variables, key=f"lesson-state-{experiment_id}")
        stride = max(1, math.ceil(len(pop["time_ms"])/2000))
        heat = go.Figure(go.Heatmap(x=pop["time_ms"][::stride], y=np.arange(count), z=pop["signals"][variable][::stride].T,
                                  colorbar={"title": "mV" if variable == "v" else "uS"}))
        heat.update_layout(template="plotly_dark", xaxis_title="Time [ms]", yaxis_title="Recorded cell", height=330)
        st.plotly_chart(heat, width="stretch")
        if stride > 1:
            st.caption(f"Display takes every {stride}th sample; downloads retain every recorded sample.")
    with st.expander("Connectivity"):
        projection = st.selectbox("Projection", list(result["connectivity"]), key=f"lesson-proj-{experiment_id}")
        detail = result["projections"][projection]; edges = result["connectivity"][projection]
        npre, npost = [len(pops[detail[k]]["spikes_ms"]) for k in ("pre", "post")]
        counts, xb, yb = np.histogram2d(edges[:, 0], edges[:, 1], bins=[min(npre, 100), min(npost, 100)],
                                       range=[[-.5, npre-.5], [-.5, npost-.5]])
        graph = go.Figure(go.Heatmap(x=(xb[1:]+xb[:-1])/2, y=(yb[1:]+yb[:-1])/2, z=counts.T, colorbar={"title": "Connections"}))
        graph.update_layout(template="plotly_dark", xaxis_title=f"Pre: {detail['pre']}", yaxis_title=f"Post: {detail['post']}", height=300)
        st.plotly_chart(graph, width="stretch")
        st.caption("Connection counts per bin (up to 100 bins per axis). The CSV retains every individual connection, including parallel edges.")
        st.dataframe([{"Projection": k, "Connections": v} for k, v in result["connection_counts"].items()], hide_index=True)
    if experiment_id == "balance_brian2":
        # Match the notebook's two analyses: population PSTH and conductance ratio.
        psth = go.Figure()
        for name in ("exc", "inh"):
            trains = pops[name]["spikes_ms"]
            bins = np.arange(0, result["configuration"]["experiment"]["duration_ms"]+5, 5.)
            counts = np.histogram(np.concatenate(trains), bins=bins)[0]
            psth.add_trace(go.Scatter(x=(bins[:-1]+bins[1:])/2, y=counts/len(trains)/.005, name=name))
        psth.update_layout(template="plotly_dark", xaxis_title="Time [ms]", yaxis_title="Population rate [Hz]", height=280)
        st.plotly_chart(psth, width="stretch")
        for name in ("exc", "inh"):
            signals = pops[name]["signals"]
            ratio = signals["gsyn_exc"]/(signals["gsyn_exc"]+signals["gsyn_inh"]+1e-12)
            st.write(f"{name.upper()} mean gE/(gE + gI), recorded cells: " + ", ".join(f"{v:.3f}" for v in ratio.mean(axis=0)))


def render_notebook(experiment_id):
    spec = EXPERIMENTS[experiment_id]
    st.subheader(spec["label"])
    st.write(spec["description"])
    if experiment_id == "cell_models":
        st.markdown(f"[New local comparison notebook]({REPO}main/{spec['notebook']}) · "
                    f"[Original SpiNNaker comparison notebook]({REPO}{SOURCE_COMMIT}/{spec['spinnaker_notebook']})")
        st.caption("SpiNNaker-only extra models in the original notebook: " + ", ".join(HARDWARE_MODELS))
        _model_inspector()
    else:
        st.markdown(f"[Original notebook]({REPO}{SOURCE_COMMIT}/{spec['notebook']})")
    if spec.get("script"):
        st.markdown(f"[VAbenchmarks.py used by this notebook]({REPO}{SOURCE_COMMIT}/{spec['script']})")
    if spec.get("link_only"):
        st.info("SpiNNaker notebook · open the original notebook with a SpiNNaker kernel to run this experiment.")
        for note in spec["notes"]:
            st.write(note)
        with st.expander("Original notebook parameters"):
            st.dataframe([{"Parameter": name, "Value": detail[0], "Unit": detail[3]} for name, detail in spec["fields"].items()], hide_index=True)
        _references(experiment_id)
        return
    with st.expander("Protocol and portability notes", expanded=experiment_id in ("cell_models", "small_world")):
        for note in spec["notes"]:
            st.write(note)
        if experiment_id in ("decaying", "diverging", "small_world"):
            st.caption("The local source clock is refined when needed to retain all five jittered input events per active source. "
                       "Neuron integration uses the selected dt; requested and recorded spike times are exported.")
    _references(experiment_id)
    left, right = st.columns([1, 3], gap="large")
    with left:
        with st.form(f"lesson-form-{experiment_id}"):
            values = {}
            selected = None
            if experiment_id == "cell_models":
                choices = list(comparison_models())
                selected = st.multiselect("Models to compare", choices, default=choices, key="lesson-comparison-models")
                st.caption("Maximum PyNN dt is refined automatically for HH, AdEx and Izhikevich; actual steps are shown in the results.")
            for name, (default, minimum, maximum, unit) in spec["fields"].items():
                if name == "dt_ms":
                    options = [.1, .2] if experiment_id == "balance_brian2" else [1., .5, .1]
                    values[name] = st.selectbox(f"Integration step [{unit}]", options, index=options.index(default), key=f"lesson-{experiment_id}-{name}")
                else:
                    values[name] = st.number_input(f"{name} [{unit}]", min_value=minimum, max_value=maximum, value=default,
                        key=f"lesson-{experiment_id}-{name}")
            run = st.form_submit_button("Run experiment", type="primary")
        if run:
            try:
                with st.spinner("Running the source-linked experiment…"):
                    bar = st.progress(0.) if experiment_id == "cell_models" else None
                    callback = (lambda fraction, label: bar.progress(fraction, text=label)) if bar is not None else None
                    st.session_state[f"lesson-result-{experiment_id}"] = simulate_notebook(experiment_id, values, progress=callback, selected=selected)
                    if bar is not None:
                        bar.empty()
            except Exception as error:
                st.session_state.pop(f"lesson-result-{experiment_id}", None)
                st.error(f"Experiment did not complete: {error}")
    with right:
        result = st.session_state.get(f"lesson-result-{experiment_id}")
        if result is None:
            st.info("Run the experiment to display its recorded states and spike events.")
            return
        config = result["configuration"]
        st.caption(f"Completed run · {config['backend']} · {config['experiment']['duration_ms']:g} ms. "
                   "Form edits take effect when you run again.")
        if experiment_id == "cell_models":
            _comparison_results(result)
        else:
            _network_results(result, experiment_id)
        _downloads(result, experiment_id)
