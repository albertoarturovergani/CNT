# CNT neural model dashboard

A first teaching interface for **one neuron** and **one isolated population or oscillator**.
Run simulations, vary native parameters and input waveforms, inspect state trajectories,
and download traces and the configuration needed to repeat an experiment.

## Run locally

Python 3.11 or 3.12 is recommended for this first version. From the CNT repository:

```bash
cd dashboard
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python launch.py
```

On Windows, activate with `.venv\Scripts\activate` instead. Open the local address
printed by Streamlit. Simulation runs on the machine running Python; students do not
need a SpiNNaker account. A shared classroom deployment would require a Python server.

## Full tutorial or hosted JupyterLab

The root [`requirements.txt`](../requirements.txt) installs the common notebook tools
and this dashboard together, including JupyterLab for students running locally;
this directory's file remains the smaller dashboard-only option. Both use the
same model and application code on local computers or teaching servers.

Start `launch.py` from a JupyterLab terminal. To open the remote dashboard in your
browser, follow the [hosted JupyterLab instructions](../docs/environments.md#dashboard-from-hosted-jupyterlab).
They require Jupyter Server Proxy in the running server environment and configure
Streamlit's URL prefix to match it. A laptop's localhost URL refers to the laptop;
the remote application is reached through the authenticated SANDS route.

## Current implementation

| Interface | Implementation | Scope |
| --- | --- | --- |
| Single neuron | Native Brian2 `NeuronGroup`, explicit `Network` and clock | LIF, Izhikevich, AdEx, Hodgkin-Huxley, Morris-Lecar |
| Population & oscillator | Native TVB `Simulator` | Every concrete class registered in the installed `ModelsEnum` |
| Catalogue & roadmap | Source and implementation status | GLIF/E-GLIF integration and later network experiments |

The TVB registry in the tested installation, `tvb-library 2.10.0`, contains 28 concrete
classes. The interface discovers the registry at runtime; it does not embed a fixed
list. Unregistered `contrib`, DSL and external extensions are not automatically included.
The catalogue includes neural masses, mean-field reductions and phenomenological
oscillators; these names describe different modeling assumptions.

### Single neuron

* Step, ramp and sine inputs, including negative amplitudes.
* Explicit units, editable parameters and integration step.
* Recorded voltage, spike events, input and a state-space trajectory where applicable.
* CSV traces, CSV spike times and a JSON configuration with the Brian2 version.

Inputs remain in each implementation's native units. In particular, the CNT
Izhikevich equations use a dimensionless drive; its amplitude must not be interpreted
as a measured current in pA. The Morris-Lecar notebook uses uA, uF and mS.
Comparing equal numerical amplitudes across these models is not a controlled comparison.

Threshold/reset models retain their recorded state rather than inserting artificial
action-potential peaks. HH and Morris-Lecar detect spikes at -40 mV and 0 mV,
respectively, without resetting the membrane voltage. The displayed rate is the number
of events divided by the entire simulation duration, including baseline periods.

### One TVB node

The connectivity has one node, a zero weight matrix, and zero long-range coupling gain.
Intrinsic interactions between populations inside a model remain active. Parameters
are read from TVB's numerical array traits, with the native documentation available in
the interface. Scalar and one-dimensional numerical parameter arrays are editable.

The native deterministic Heun integrator handles the model's integration hooks,
boundaries and state masks. After configuration, an identity output observer records
all actual state variables and modes; TVB's default observer often records only a
subset or a derived expression, and one class restricts its selectable outputs to
three of its five states. This changes recording, not the model dynamics. The plots
give each state variable a separate axis.

Initial states are drawn from TVB's initialization ranges using a local seeded random
generator, or set explicitly by the student. The export includes the exact initial
array, every editable parameter, TVB version, integration step and coupling settings.
Native state and drive units are model-specific; consult the model description.

Different models have different time scales. A catalogue entry is not a guarantee that
arbitrary parameters, initial states or integration steps produce a stable trajectory.
Numerical failures are reported in the interface; no replacement trajectory is shown.
The first use of a TVB class may compile its numerical implementation.

## Relationship to existing notebooks

| Existing CNT source | Use in this dashboard |
| --- | --- |
| [`eg_single-cell.ipynb`](../notebooks/intro/eg_single-cell.ipynb) | Teaching pattern: one cell, input, voltage and spike events. The new LIF adapter is current-based; that notebook uses a conductance-based PyNN cell. |
| [`1952_HH.ipynb`](../notebooks/numerical-methods/brian2/1952_HH.ipynb) | Same shifted kinetics, conductance values and membrane area, reduced to one cell with an applied waveform. Gates start at their voltage-dependent equilibrium. |
| [`1981_MorrisLecar.ipynb`](../notebooks/numerical-methods/brian2/1981_MorrisLecar.ipynb) | Same two-state equations and parameters, reduced to one cell. Uses Brian2's NumPy runtime and RK4, avoiding the notebook's standalone C++ device switch. |
| [`2007_Izhikevich.ipynb`](../notebooks/numerical-methods/brian2/2007_Izhikevich.ipynb) | Same voltage/recovery equations and spike rule, with a regular-spiking parameter set and a controlled input instead of a recurrent network and random drive. |
| [`D_comparisonModels.ipynb`](../notebooks/numerical-methods/TVB/D_comparisonModels.ipynb) | Expands its explicit model list into discovery of the installed TVB registry. |
| [`eg_testing-cell-models-network.ipynb`](../notebooks/intro/eg_testing-cell-models-network.ipynb) | Reference for a later model-comparison lesson; its SpiNNaker-specific `extra_models` are outside this first adapter. |

AdEx follows the [Brian2 Brette-Gerstner example](https://brian2.readthedocs.io/en/stable/examples/frompapers.Brette_Gerstner_2005.html).
Brian2's [model examples](https://brian2.readthedocs.io/en/stable/examples/index.html)
and TVB's [model API](https://docs.thevirtualbrain.org/api/tvb.simulator.models.html)
provide additional reference material. Existing notebooks are linked rather than
executed or imported, so opening the dashboard does not select a SpiNNaker backend.

The backend functions live in `cnt_dashboard/` and can also be called from a notebook;
the Streamlit interface contains no alternative implementation of the equations.
Use `launch.py` rather than invoking Streamlit directly: Brian2's initial signal
handler must be installed on a main thread before Streamlit creates its script thread.
Single-neuron simulations use an explicit Brian2 network and a lock around its global
code-generation preferences when sessions share a server.

## GLIF and E-GLIF integration

The catalogue explicitly marks these entries as pending:

* **GLIF:** identify the intended formulation. NEST's Allen Institute GLIF models and
  cerebellar GLIF/E-GLIF implementations must not be treated as interchangeable.
* **E-GLIF associated with Alice Geminiani:** use the original implementation and
  published cell-specific fits, including reset and spike-generation rules.
* **Marialaura De Grazia's E-GLIF:** the source is
  [`eglif_multirec.nestml`](https://github.com/dbbs-lab/cerebellar-models/blob/e77be2d0e9ea907a7672c7ab10a9279050fcd024/cerebellar_models/nest_models/eglif_multirec.nestml)
  in `dbbs-lab/cerebellar-models`, associated with De Grazia et al. (2026),
  [A biologically-grounded cerebellar spiking network model with realistic synaptic transmission captures complex circuit dynamics](https://doi.org/10.64898/2026.05.12.724100).
  Its adapter and reference-trace validation are pending.

The laboratory's [NEST model documentation](https://cerebellar-models.readthedocs.io/en/latest/configurations/mouse/nest/parameters.html)
distinguishes the Geminiani and De Grazia variants. Its implementation notes also
discuss leak-current signs and reproducibility differences, which must be resolved
when selecting the exact reference implementation and fitted parameters. A generic
GLIF substitute would not settle those model-specific choices.

Relevant primary sources for E-GLIF are Geminiani et al. (2018),
[Complex Dynamics in Simplified Neuronal Models](https://doi.org/10.3389/fninf.2018.00088),
and Geminiani et al. (2019),
[Complex Electroresponsive Dynamics in Olivocerebellar Neurons](https://doi.org/10.3389/fncom.2019.00035).
The [original network implementation on ModelDB](https://modeldb.science/262456)
is another entry point. These sources are listed for integration, not claimed to be
the implementation currently running in this dashboard.

## Next stage: network dynamics

Add separate spiking and population-network experiments after the isolated-node
interfaces are settled. Suggested sequence: disconnected nodes, connected pair, ring,
random graph, small-world graph, modular graph and empirical connectivity.

For a topology comparison, control node count, density, directedness, weight and delay
distributions, input, local model parameters and excitation/inhibition where applicable.
Then vary a chosen network property and show connectivity, raster or population traces,
rates and synchrony. Spiking and population models require their own observables and
coupling definitions. SpiNNaker integration belongs to a later backend stage.

## Checks

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The checks include the analytic passive-membrane and TVB Linear solutions, finite
single-cell trajectories with detected spikes, all-state/multi-mode TVB recording,
replay from exported initial conditions, and execution of both Streamlit forms.
All 16 tests passed. These are software and numerical checks, not electrophysiological
fitting validation.

Verified with Python 3.12, Brian2 2.10.1, TVB library 2.10.0, Streamlit 1.67.0,
Plotly 7.1.0 and NumPy 2.3.5. In addition to the tests, all 28 installed TVB classes
completed a default isolated-node run of 200 ms at dt = 0.05 ms with finite states.
Browser layout inspection was unavailable in the development preview environment;
the Streamlit forms and output paths were exercised with Streamlit's AppTest.

Code remains under the CNT repository's GPL-3.0 license. Brian2 and TVB are installed
as dependencies; their source trees and notebooks are not copied into the dashboard.
