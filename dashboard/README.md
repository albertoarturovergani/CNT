# CNT neural model dashboard

A teaching interface organized into **Spiking** and **Large Scale**.
Run simulations, vary native parameters and input waveforms, inspect state trajectories,
and download traces and the configuration needed to repeat an experiment. The Spiking
pages translate CNT's introductory notebooks into interactive experiments and link
hardware-only lessons to their original SpiNNaker versions.

## Start the full tutorial

The [step-by-step usage guide](../docs/quickstart.md) covers installation, opening
notebooks and using the dashboard with one shared course environment:

| Platform | Instructions |
| --- | --- |
| Ubuntu | [Local setup and startup](../docs/quickstart.md#ubuntu) |
| Windows | [Command Prompt and PowerShell setup](../docs/quickstart.md#windows) |
| SANDS | [Hosted JupyterLab and conditional proxy route](../docs/quickstart.md#sands-hosted-jupyterlab) |

For a first check, use the local instructions. Dashboard access through SANDS's proxy
is not confirmed. The [dashboard usage section](../docs/quickstart.md#use-the-dashboard)
explains the tabs, run buttons and result downloads.

## Smaller dashboard-only installation

Python 3.11 or 3.12 is recommended for this first version. From the CNT repository:

### Ubuntu / Linux / macOS

```bash
cd dashboard
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python launch.py
```

### Windows PowerShell

From the repository root, with Python 3.11 or 3.12 selected:

```powershell
cd dashboard
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe launch.py
```

If you are already in `dashboard/` with its `.venv` created, run just the last two
commands. PowerShell does not use the bash `source` command.

### Windows Command Prompt

Use the following instead, starting from the repository
root with Python 3.12 installed:

```bat
cd dashboard
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python launch.py
```

Open the local address
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
| Spiking → Single cell → Model explorer | Native Brian2 `NeuronGroup`, explicit `Network` and clock | LIF, Izhikevich, AdEx, Hodgkin-Huxley, Morris-Lecar |
| Spiking → Single cell → PyNN notebook | PyNN with the Brian2 backend | Original `eg_single-cell` AC + step experiment |
| Spiking → Single cell → Single clique | PyNN with the Brian2 backend | Reciprocal excitatory/inhibitory two-cell circuit |
| Spiking → Single cell → Testing cell models network | Shared notebook/dashboard engine | All 10 injectable native PyNN/Brian2 neuron classes plus the 5 CNT Brian2 adapters |
| Spiking → Single cell → STDP | Original notebook link | SpiNNaker experiment; its dendritic-delay rule is preserved |
| Spiking → Network | Source-linked experiment selector | Decaying, Diverging, Small World, Balance network · Brian2, and the existing PyNN E/I benchmark |
| Large Scale → Single node | Native TVB `Simulator` | Every concrete class registered in the installed `ModelsEnum` |
| Large Scale → Network | Placeholder | Future TVB connectivity experiments |
| Catalogue & roadmap (expandable) | Source and implementation status | GLIF/E-GLIF integration and later experiments |

The TVB registry in the tested installation, `tvb-library 2.10.0`, contains 28 concrete
classes. The interface discovers the registry at runtime; it does not embed a fixed
list. Unregistered `contrib`, DSL and external extensions are not automatically included.
The catalogue includes neural masses, mean-field reductions and phenomenological
oscillators; these names describe different modeling assumptions.

### Equations, units, voltage references and bibliography

Selecting a model exposes its equations before running a simulation, with a separate
table of symbols, term descriptions and units, and publications linked by DOI or an
original-source URL. Model-family foundations and later implemented variants are
identified separately. The 28 TVB equation entries were checked against native TVB
2.10.0 derivative functions for the **isolated-node** case; their installed class
source is also available in an expander. Normalized quantities and units not declared
by TVB are labeled explicitly rather than presented as membrane voltage/current.

After a single-cell run, checkboxes show/hide reference lines on the voltage panel.
They use the **completed run's** values and change only the plot. Editing a form
without submitting does not move these lines. Coincident references share one label.

| Reference | Interpretation |
| --- | --- |
| Vrest / EL | Passive resting voltage for LIF/PyNN; leak reversal for nonlinear conductance models |
| Vthreshold | Explicit threshold for LIF/PyNN; AdEx VT is labeled exponential onset |
| Vreset | Reset voltage, only for models with a reset rule |
| Vdetect | Spike-counting cutoff for HH, Morris–Lecar and Izhikevich; AdEx uses VT + 5 DeltaT |

HH and Morris–Lecar have no reset rule. HH's VT shifts the channel kinetics and is
not a detection threshold. Izhikevich's displayed levels use the adapter's scaled
model-voltage convention. There is no universal model parameter called `Vdirect`;
the interface distinguishes resting/leak references from spike detection.

### PyNN notebook experiments

Choose **Single clique**, **Testing cell models network** or **STDP** beside the
existing model explorer/single-cell page. In **Spiking → Network**, choose the
experiment with the selector at the top. A run uses the displayed controls;
plotting controls reuse the completed result.

| Additional lesson | Source | Local behavior |
| --- | --- | --- |
| Single clique | [`eg_single-clique.ipynb`](../notebooks/intro/eg_single-clique.ipynb) | Two default `IF_cond_exp` cells; 1 uS excitatory/inhibitory reciprocal weights; 1 ms delay; 10 nA step to cell0 at 30–40 ms |
| Testing cell models network | **New** [`eg_testing-cell-models-local.ipynb`](../notebooks/intro/eg_testing-cell-models-local.ipynb) | Native PyNN neurons and all existing CNT Brian2 cells, using the same comparison engine as the dashboard |
| Original cell-model comparison | [`eg_testing-cell-models-network.ipynb`](../notebooks/intro/eg_testing-cell-models-network.ipynb) | Link to its synaptic-input/SpiNNaker version, including the four hardware-specific extra models |
| STDP | [`eg_testing-STDP-model-network.ipynb`](../notebooks/intro/eg_testing-STDP-model-network.ipynb) | Link to the original SpiNNaker experiment; no local axonal-delay substitute |
| Decaying network | [`eg_decaying-network.ipynb`](../notebooks/intro/eg_decaying-network.ipynb) | 100 cells; no recurrence; central 40–60% receives five jittered input spikes per source |
| Diverging network | [`eg_diverging-network.ipynb`](../notebooks/intro/eg_diverging-network.ipynb) | 100 excitatory cells; deterministic distance/probability cutoff and distance-dependent delays |
| Small World network | [`eg_small-world-network.ipynb`](../notebooks/intro/eg_small-world-network.ipynb) | Explicit local-plus-rewired E/I edge lists for the CPU backend; source version remains linked |
| Balance network · Brian2 | [`paper_balance-network_brian2.ipynb`](../notebooks/intro/paper_balance-network_brian2.ipynb), [`VAbenchmarks.py`](../notebooks/intro/scripts/VA/VAbenchmarks.py) | COBA script preset: 4000 cells, dt 0.1 ms, 0.2 ms delay, 1000 ms; all spikes and two analog cells per E/I population |

The **new local comparison notebook** discovers all injectable, concrete neuron
classes in the installed PyNN/Brian2 backend. Spike generators and the composable
`PointNeuron` builder are excluded. With PyNN 0.13.0 there are 10 native classes,
plus the 5 separately labeled CNT Brian2 adapters. The dashboard can run a selected
subset. Both interfaces call `cnt_dashboard.cell_comparison.compare_cells`.

This new comparison uses a current step rather than the original notebook's ten
synaptic input spikes. Dimensional models receive a shared current in nA, converted
to pA/uA where needed. CNT's scaled Izhikevich input has an independent model-unit
amplitude. Native parameters/capacitances differ; equal current does not mean equal
I/C or excitability, and synaptic-kernel variants can coincide without presynaptic
input. Maximum PyNN dt is refined for HH (0.01 ms), AdEx (0.025 ms), and Izhikevich
(0.05 ms); actual steps and native parameters are exported. The model inspector
shows native equations, units and model-family publications.

Recorded event counts also retain native detector semantics. PyNN `HH_cond_exp`
can emit multiple above-threshold events during an action potential, whereas CNT's
HH adapter counts crossings. The comparison labels these as recorded events rather
than treating them as interchangeable physiological firing rates.

Portability details for the source notebooks:

- **Single clique:** its weight comments say nS, but native PyNN weights are uS;
  the numerical preset values are preserved as 1 uS.
- **Diverging:** its Gaussian distance expression is a deterministic cutoff, not
  random connection sampling. PyNN rounds the requested delays to the simulation
  clock; nearest-neighbor delays become 4 ms at the 1 ms notebook step.
- **Small World:** PyNN/Brian2 leaves `SmallWorldConnector` unimplemented, so the
  adapter explicitly builds distance `< degree` connections and rewires targets
  over the full population. Self connections and parallel edges are retained.
  The notebook's periodic length is 500, not 100. Delay draws retain the truncated
  normal distribution (mean 1.5, SD 1.75, bounds 0.1–100 ms); backend delay rounding
  depends on dt. Seeded local draws are not a bit-for-bit hardware reproduction.
- **Jittered inputs:** a finer source clock avoids losing coincident-in-bin spikes
  while the neuron clock retains the chosen dt. Requested input times, actual
  recorded events and backend connection delays are available in the exports.
- **STDP:** the original dendritic-delay fraction is 1; PyNN/Brian2 supports only
  0. The page therefore links the original notebook for a SpiNNaker kernel.

Rasters, selected-cell voltage/conductances, state heatmaps and connectivity views
are available for the local network lessons. The Brian2 Balance lesson also shows
the notebook's population PSTH and gE/(gE + gI) analysis. Configuration JSON, event CSV,
exact connectivity CSV and analog NPZ downloads preserve completed-run values.

The 4000-cell COBA preset is a longer CPU experiment. For a quick classroom check,
start with 400 cells and 100 ms, then restore 4000 cells and 1000 ms for the script preset.

The pre-existing single-cell and E/I notebook pages remain available:

| Dashboard page | Notebook | Original preset |
| --- | --- | --- |
| Single cell → PyNN notebook | [`eg_single-cell.ipynb`](../notebooks/intro/eg_single-cell.ipynb) | One `IF_cond_exp`; dt 1 ms; 800 ms; AC 10 nA at 10 Hz from 100–400 ms; step 10 nA from 600–610 ms |
| Spiking → Network | [`paper_balance-network_sPyNNaker.ipynb`](../notebooks/intro/paper_balance-network_sPyNNaker.ipynb) | 1500 `IF_cond_exp`, E:I = 4:1; dt 1 ms; delay 2 ms; 1000 ms; recurrent probability 0.02; weights 0.004/0.051 uS; 20 Poisson cells at 100 Hz for 50 ms |

The dashboard explicitly selects `pyNN.brian2`, including for the notebook whose
filename contains `sPyNNaker`. It preserves the model, cell parameters, stimulus
and six projection types. It does not require SpiNNaker hardware. Source links and
downloaded configurations identify the notebook and source commit. The standalone
Brian2 model explorer remains a separate set of experiments, with different presets.

The network notebook did not seed every random stream. This adapter explicitly
seeds independent child streams for PyNN projections/initialization and Brian2 Poisson generation; random draws
may therefore differ from a notebook run, while repeated dashboard runs with the
same seed reproduce the same connections and spikes. The external projection delay
is explicit (2 ms in the preset). Network topology is currently fixed-probability;
changing size/probability does not preserve in-degree or firing-rate balance.

Plots include the original voltage/spike/input views for the cell, E/I/external
rasters for the network, a binned connection matrix for each projection, and
voltage/conductance traces for a selected recorded cell.
Download configuration JSON, spike CSV and cell trace CSV or all network analog
traces as a compressed NPZ file. The exact network connection list is available as
CSV with pre/post indices, conductance weights and delays. PyNN units are mV, ms, nA, nF and uS. The single-cell
notebook's 0.1 ms refractory setting is retained despite its 1 ms simulation clock;
reduce dt to examine discrete-time effects.

Interactive network runs are limited to 3000 cells, 1 million expected recurrent
connections and 15 million analog samples. Reduce the size/duration, probability,
or increase dt if a limit is reached. Notebook-specific SpiNNaker extra models,
plasticity exercises and other network notebooks still need individual adapters.

### Single neuron model explorer

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
| [`eg_testing-cell-models-network.ipynb`](../notebooks/intro/eg_testing-cell-models-network.ipynb) | Linked original SpiNNaker/synaptic-input comparison. The new local comparison notebook covers all locally supported models with a shared current step. |

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

Extend the first PyNN spiking-network page and add TVB network experiments.
Suggested sequence: disconnected nodes, connected pair, ring,
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

The checks include analytic passive-membrane and TVB Linear solutions, finite
single-cell trajectories with detected spikes, all-state/multi-mode TVB recording,
replay from exported initial conditions, PyNN current-waveform/RC checks, seeded
network replay, and execution of the Streamlit forms. UI checks verify that voltage
checkboxes change the voltage panel without rerunning or modifying a simulation.
These are software and numerical checks, not electrophysiological fitting validation.

The PyNN/Brian2 adapter deactivates empty native synapse objects before a run (they
have no connections), and reads connectivity through PyNN's array format to handle
single-connection projections correctly. Both cases are covered by the checks.
Additional lesson checks verify clique receptors/current timing, feedforward decay,
all five input events per active source, deterministic divergent connectivity,
seeded small-world rewiring, current-unit conversion in the shared comparison,
two-cell analog recording in the 4000-cell benchmark adapter, and link-only STDP.

Verified with Python 3.12, PyNN 0.13.0, Brian2 2.10.1, TVB library 2.10.0, Streamlit 1.67.0,
Plotly 7.1.0 and NumPy 2.3.5. In addition to the tests, all 28 installed TVB classes
completed a default isolated-node run of 200 ms at dt = 0.05 ms with finite states.
Browser layout inspection was unavailable in the development preview environment;
the Streamlit forms and output paths were exercised with Streamlit's AppTest.

Code remains under the CNT repository's GPL-3.0 license. Brian2 and TVB are installed
as dependencies; their source trees and notebooks are not copied into the dashboard.
