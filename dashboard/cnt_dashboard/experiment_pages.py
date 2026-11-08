"""Streamlit pages for the PyNN experiments, separate from simulation code."""

import csv
import io
import json
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from . import pynn_experiments as experiments
from .model_notes import VoltageReference, add_voltage_lines

REPO = "https://github.com/albertoarturovergani/CNT/blob/"


def voltage_checkboxes(refs, prefix):
    st.caption("Voltage references · display only")
    cols = st.columns(min(3, len(refs)))
    selected = []
    for i, ref in enumerate(refs):
        if cols[i % len(cols)].checkbox(f"{ref.label} · {ref.value:g} {ref.unit}", value=True,
                                      key=f"{prefix}-{ref.key}"):
            selected.append(ref)
    return selected


def _notes(notebook, network=False):
    st.markdown(f"[Source notebook]({REPO}{experiments.SOURCE_COMMIT}/{notebook}) · "
                f"[Latest notebook]({REPO}main/{notebook})")
    st.caption("PyNN API · Brian2 CPU backend · IF_cond_exp · native PyNN units")
    with st.expander("Equations, terms and units", expanded=False):
        for eq in experiments.EQUATIONS:
            st.latex(eq)
        if network:
            st.caption("In this network there is no AC or step current. Recurrent and Poisson spike arrivals change the conductances.")
        else:
            st.latex(r"I_{AC}(t)=A\sin[2\pi f(t-t_{start})/1000]\;\mathbf1_{t_{start}\leq t<t_{stop}},\quad f\text{ in Hz},\ t\text{ in ms}")
            st.caption("No synaptic projections in this single-cell experiment: gE and gI remain zero. "
                       "The default refractory period (0.1 ms) is shorter than the notebook's 1 ms integration step; "
                       "spike times therefore have the backend's discrete-time resolution.")
        rows = [{"Symbol / code": key, "Meaning": experiments.PARAMETER_NAMES[key], "Unit": unit}
                for key, unit in experiments.PARAMETER_UNITS.items()]
        rows += [{"Symbol / code": "v", "Meaning": "Membrane voltage", "Unit": "mV"},
                 {"Symbol / code": "gE, gI, wE, wI", "Meaning": "Synaptic conductances and conductance increments", "Unit": "uS"},
                 {"Symbol / code": "I_AC, I_step", "Meaning": "Injected currents", "Unit": "nA"},
                 {"Symbol / code": "t", "Meaning": "Time", "Unit": "ms"}]
        st.dataframe(rows, hide_index=True, width="stretch")
    with st.expander("Bibliography"):
        st.markdown("1. Davison A.P., et al. (2009). **PyNN: a common interface for neuronal network simulators.** "
                    "Frontiers in Neuroinformatics 2:11. [DOI](https://doi.org/10.3389/neuro.11.011.2008).")
        st.markdown("2. Lapicque L. (1907). **Recherches quantitatives sur l’excitation électrique des nerfs traitée comme une polarisation.** "
                    "Journal de Physiologie et de Pathologie Générale 9:620–635. "
                    "[Original text](https://fr.wikisource.org/wiki/Recherches_quantitatives_sur_l%27excitation_%C3%A9lectrique_des_nerfs_trait%C3%A9e_comme_une_polarisation).")
        if network:
            st.markdown("3. Vogels T.P., Abbott L.F. (2005). **Signal propagation and logic gating in networks of integrate-and-fire neurons.** "
                        "The Journal of Neuroscience 25:10786–10795. [DOI](https://doi.org/10.1523/JNEUROSCI.3508-05.2005).")
            st.caption("The notebook is a CNT benchmark variant, with its own size, weights and stimulation; it is not labeled a reproduction of every published configuration.")


def _parameter_inputs(defaults, prefix):
    with st.expander("PyNN cell parameters"):
        return {name: st.number_input(f"{name} [{experiments.PARAMETER_UNITS[name]}]", value=float(value),
                format="%.5f", key=f"{prefix}-{name}") for name, value in defaults.items()}


def _downloads(result, prefix, network=False):
    cfg = result["configuration"]
    st.download_button("Download configuration · JSON", json.dumps(cfg, indent=2), f"cnt_{prefix}.json",
                       "application/json", key=f"config-{prefix}")
    spike_csv = io.StringIO()
    writer = csv.writer(spike_csv)
    writer.writerow(["population", "cell_index", "time_ms"])
    pops = result["populations"] if network else {"cell0": result}
    for name, pop in pops.items():
        for i, spikes in enumerate(pop["spikes_ms"]):
            writer.writerows((name, i, float(t)) for t in spikes)
    st.download_button("Download spikes · CSV", spike_csv.getvalue(), f"cnt_{prefix}_spikes.csv",
                       "text/csv", key=f"spikes-{prefix}")
    if not network:
        trace_csv = io.StringIO()
        writer = csv.writer(trace_csv)
        writer.writerow(["time_ms", "v_mV", "gE_uS", "gI_uS", "AC_nA", "step_nA"])
        writer.writerows(np.column_stack([result["time_ms"], result["signals"]["v"][:, 0],
            result["signals"]["gsyn_exc"][:, 0], result["signals"]["gsyn_inh"][:, 0],
            result["currents"]["AC"][:, 0], result["currents"]["Step"][:, 0]]))
        st.download_button("Download traces · CSV", trace_csv.getvalue(), f"cnt_{prefix}_traces.csv",
                           "text/csv", key=f"traces-{prefix}")
    else:
        edges_csv = io.StringIO()
        writer = csv.writer(edges_csv)
        writer.writerow(["projection", "pre_cell_index", "post_cell_index", "weight_uS", "delay_ms"])
        for projection, edges in result["connectivity"].items():
            writer.writerows((projection, int(pre), int(post), weight, delay) for pre, post, weight, delay in edges)
        st.download_button("Download connectivity · CSV", edges_csv.getvalue(), f"cnt_{prefix}_connectivity.csv",
                           "text/csv", key=f"edges-{prefix}")
        buffer = io.BytesIO()
        arrays = {f"{name}_{signal}": values for name, pop in pops.items() for signal, values in pop["signals"].items()}
        arrays.update({f"{name}_time_ms": pop["time_ms"] for name, pop in pops.items() if len(pop["time_ms"])})
        np.savez_compressed(buffer, **arrays)
        st.download_button("Download all analog traces · NPZ", buffer.getvalue(), f"cnt_{prefix}_traces.npz",
                           "application/octet-stream", key=f"traces-{prefix}")


def render_single():
    st.subheader("PyNN · single-cell notebook")
    st.write("The notebook's conductance-based leaky integrate-and-fire cell, driven by AC current (100–400 ms) "
             "and a current step (600–610 ms). Controls start from the original notebook values.")
    _notes(experiments.SINGLE_NOTEBOOK)
    left, right = st.columns([1, 2], gap="large")
    with left:
        with st.form("pynn-single-form"):
            dt = st.selectbox("PyNN integration step [ms]", [1., .5, .1], key="pynn-single-dt")
            duration = st.number_input("Duration [ms]", min_value=20., max_value=2000., value=800., step=20., key="pynn-single-duration")
            st.caption("AC current")
            ac_start = st.number_input("Start [ms]", value=100., key="pynn-ac-start")
            ac_stop = st.number_input("Stop [ms]", value=400., key="pynn-ac-stop")
            ac_amp = st.number_input("Amplitude [nA]", value=10., key="pynn-ac-amp")
            frequency = st.number_input("Frequency [Hz]", min_value=0., value=10., key="pynn-ac-frequency")
            st.caption("Current step")
            step_start = st.number_input("Start [ms]", value=600., key="pynn-step-start")
            step_stop = st.number_input("Stop [ms]", value=610., key="pynn-step-stop")
            step_amp = st.number_input("Amplitude [nA]", value=10., key="pynn-step-amp")
            parameters = _parameter_inputs(experiments.SINGLE_PARAMETERS, "pynn-single")
            run = st.form_submit_button("Run PyNN single cell", type="primary")
        if run:
            try:
                cfg = experiments.SingleConfig(duration, dt, ac_start, ac_stop, ac_amp, frequency, step_start, step_stop, step_amp)
                with st.spinner("Running the notebook experiment with PyNN / Brian2…"):
                    st.session_state["pynn-single-result"] = experiments.simulate_single(cfg, parameters)
            except Exception as error:
                st.session_state.pop("pynn-single-result", None)
                st.error(f"PyNN simulation did not complete: {error}")
    with right:
        result = st.session_state.get("pynn-single-result")
        if result is None:
            st.info("Run the notebook preset to display voltage, spikes, injected currents and conductances.")
            return
        cfg = result["configuration"]
        pars = cfg["parameters"]
        st.caption(f"Completed run · PyNN {cfg['pynn_version']} / Brian2 {cfg['brian2_version']} · "
                   f"{cfg['experiment']['duration_ms']:g} ms · dt {cfg['experiment']['dt_ms']:g} ms")
        st.metric("Detected spikes", len(result["spikes_ms"][0]))
        refs = [VoltageReference("rest", "Vrest", pars["v_rest"], "mV", "#60a5fa"),
                VoltageReference("threshold", "Vthreshold", pars["v_thresh"], "mV", "#fbbf24"),
                VoltageReference("reset", "Vreset", pars["v_reset"], "mV", "#f472b6")]
        selected = voltage_checkboxes(refs, "pynn-single-voltage")
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[.13, .6, .27], vertical_spacing=.06)
        spikes = result["spikes_ms"][0]
        fig.add_trace(go.Scatter(x=spikes, y=np.zeros(len(spikes)), mode="markers", name="Spikes",
                                marker={"symbol": "line-ns", "size": 10}), row=1, col=1)
        fig.add_trace(go.Scatter(x=result["time_ms"], y=result["signals"]["v"][:, 0], name="Voltage"), row=2, col=1)
        for name, current in result["currents"].items():
            fig.add_trace(go.Scatter(x=result["time_ms"], y=current[:, 0], name=f"{name} current"), row=3, col=1)
        add_voltage_lines(fig, selected)
        fig.update_yaxes(title_text="mV", row=2, col=1)
        fig.update_yaxes(title_text="nA", row=3, col=1)
        fig.update_xaxes(title_text="Time [ms]", row=3, col=1)
        fig.update_layout(height=550, template="plotly_dark")
        st.plotly_chart(fig, width="stretch", key="pynn-single-plot")
        with st.expander("Synaptic conductances"):
            conductance = go.Figure()
            for variable in ("gsyn_exc", "gsyn_inh"):
                conductance.add_trace(go.Scatter(x=result["time_ms"], y=result["signals"][variable][:, 0], name=variable))
            conductance.update_layout(xaxis_title="Time [ms]", yaxis_title="Conductance [uS]", template="plotly_dark", height=300)
            st.plotly_chart(conductance, width="stretch")
        _downloads(result, "pynn_single")


def render_network():
    st.subheader("PyNN · E/I network notebook")
    st.write("CNT's Vogels–Abbott benchmark variant: recurrent excitatory and inhibitory IF_cond_exp populations "
             "with a 4:1 ratio, fixed-probability connections and a short external Poisson stimulus.")
    _notes(experiments.NETWORK_NOTEBOOK, network=True)
    st.caption("Notebook preset: 1500 cells · 2% recurrent connectivity · wE = 0.004 uS · wI = 0.051 uS · "
               "20 external cells at 100 Hz for the first 50 ms. Explicit seeding makes dashboard reruns reproducible; "
               "individual random connections/spikes may differ from the original notebook.")
    left, right = st.columns([1, 2], gap="large")
    with left:
        with st.form("pynn-network-form"):
            values = {}
            fields = [
                ("n_cells", "Neurons", 10, 3000, 1500, 10),
                ("duration_ms", "Duration [ms]", 50., 2000., 1000., 50.),
                ("probability", "Recurrent connection probability", 0., 1., .02, .01),
                ("exc_weight_uS", "Excitatory weight [uS]", 0., 1., .004, .001),
                ("inh_weight_uS", "Inhibitory weight [uS]", 0., 1., .051, .001),
                ("external_probability", "External connection probability", 0., 1., .01, .01),
                ("external_rate_hz", "External rate [Hz]", 0., 1000., 100., 10.),
                ("external_duration_ms", "External stimulus duration [ms]", 1., 2000., 50., 10.),
                ("seed", "Random seed", 0, 2**32-1, 98766987, 1),
            ]
            for key, label, minimum, maximum, value, step in fields:
                values[key] = st.number_input(label, min_value=minimum, max_value=maximum, value=value, step=step, key=f"pynn-network-{key}")
            values["dt_ms"] = st.selectbox("Integration step [ms]", [1., .5, .1], key="pynn-network-dt")
            with st.expander("Delay and external population"):
                values["delay_ms"] = st.number_input("Synaptic delay [ms]", min_value=.1, max_value=100., value=2., step=.1, key="pynn-network-delay")
                values["n_external"] = st.number_input("External Poisson cells", min_value=1, max_value=200, value=20, key="pynn-network-external-n")
                values["external_weight_uS"] = st.number_input("External weight [uS]", min_value=0., value=.1, step=.01, key="pynn-network-external-w")
            parameters = _parameter_inputs(experiments.NETWORK_PARAMETERS, "pynn-network")
            run = st.form_submit_button("Run PyNN network", type="primary")
        if run:
            try:
                with st.spinner("Running the E/I network with PyNN / Brian2…"):
                    st.session_state["pynn-network-result"] = experiments.simulate_network(experiments.NetworkConfig(**values), parameters)
            except Exception as error:
                st.session_state.pop("pynn-network-result", None)
                st.error(f"PyNN network did not complete: {error}")
    with right:
        result = st.session_state.get("pynn-network-result")
        if result is None:
            st.info("Run the notebook preset or reduce the neuron count for a smaller classroom experiment.")
            st.caption("Large Scale → Network is reserved for future TVB network experiments. Further spiking notebooks can be added here after their backend requirements are checked.")
            return
        cfg = result["configuration"]
        experiment = cfg["experiment"]
        st.caption(f"Completed run · {experiment['n_cells']} neurons · {experiment['duration_ms']:g} ms · "
                   f"seed {experiment['seed']} · PyNN {cfg['pynn_version']} / Brian2 {cfg['brian2_version']}")
        metrics = st.columns(2)
        for i, name in enumerate(("exc", "inh")):
            pop = result["populations"][name]
            rate = sum(map(len, pop["spikes_ms"])) / len(pop["spikes_ms"]) / (experiment["duration_ms"] / 1000)
            metrics[i].metric(f"{name.upper()} mean firing rate", f"{rate:.2f} Hz")
        raster = make_subplots(rows=3, cols=1, shared_xaxes=True, subplot_titles=["Excitatory", "Inhibitory", "External Poisson"])
        for row, name in enumerate(("exc", "inh", "thalamus"), 1):
            trains = result["populations"][name]["spikes_ms"]
            x = np.concatenate(trains)
            y = np.repeat(np.arange(len(trains)), [len(t) for t in trains])
            raster.add_trace(go.Scattergl(x=x, y=y, mode="markers", marker={"size": 2}, name=name), row=row, col=1)
            raster.update_yaxes(title_text="Cell", row=row, col=1)
        raster.update_xaxes(title_text="Time [ms]", row=3, col=1)
        raster.update_layout(height=600, template="plotly_dark")
        st.plotly_chart(raster, width="stretch", key="pynn-network-raster")
        with st.expander("Connectivity", expanded=False):
            projection = st.selectbox("Projection", list(result["connectivity"]), key="pynn-network-projection")
            edges = result["connectivity"][projection]
            pre, post = projection.split("2")
            pre = "thalamus" if pre == "ext" else pre
            n_pre = len(result["populations"][pre]["spikes_ms"])
            n_post = len(result["populations"][post]["spikes_ms"])
            counts, xbins, ybins = np.histogram2d(edges[:, 0], edges[:, 1],
                bins=[min(n_pre, 100), min(n_post, 100)], range=[[-.5, n_pre-.5], [-.5, n_post-.5]])
            matrix = go.Figure(go.Heatmap(x=(xbins[:-1]+xbins[1:])/2, y=(ybins[:-1]+ybins[1:])/2,
                z=counts.T, colorscale="Viridis", colorbar={"title": "Connections"}))
            matrix.update_layout(xaxis_title=f"Presynaptic {pre} cell index", yaxis_title=f"Postsynaptic {post} cell index",
                                 template="plotly_dark", height=350)
            st.plotly_chart(matrix, width="stretch")
            st.caption("All connections are included. Populations larger than 100 cells are grouped into bins; "
                       "color shows the number of connections in each bin. Download the exact connection list as CSV.")
        with st.expander("Voltage and synaptic conductances", expanded=True):
            pop_name = st.selectbox("Recorded population", ["exc", "inh"], key="pynn-network-trace-pop")
            pop = result["populations"][pop_name]
            count = pop["signals"]["v"].shape[1]
            cell = st.number_input("Recorded cell index", min_value=0, max_value=count-1,
                                   value=0, key=f"pynn-network-trace-cell-{pop_name}-{count}")
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True)
            for row, (variable, unit) in enumerate((("v", "mV"), ("gsyn_exc", "uS"), ("gsyn_inh", "uS")), 1):
                fig.add_trace(go.Scatter(x=pop["time_ms"], y=pop["signals"][variable][:, cell], name=variable), row=row, col=1)
                fig.update_yaxes(title_text=unit, row=row, col=1)
            fig.update_xaxes(title_text="Time [ms]", row=3, col=1)
            fig.update_layout(height=500, template="plotly_dark")
            st.plotly_chart(fig, width="stretch")
        st.dataframe([{"Projection": name, "Synapses": count} for name, count in result["connection_counts"].items()], hide_index=True)
        _downloads(result, "pynn_network", network=True)
