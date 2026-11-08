# Computational Neuroscience Tutorial 
This tutorial has been designed for the following classes:

- [25-26] Introduction to Algorithms for Modeling Virtual Brain Twins, Psy MSc, IUSS/UNIPV
- [23-24-25-26] Brain modelling, AI BSc, Human-Centered-IA, UNIMI/PV/B
- [22-23-24] Numerical methods in Neuroscience, Physics MSc, UNIPI, Pisa, Italy
- [21-22-23-24] Biorobotics and Complex Systems, Physics MSc, UNIPI, Pisa, Italy
- [21-22-23] Neural Modeling for Neural Engineering, PhD in Biorobotics, SSSA, Pisa
- [2021] Large Scale Network Simulations, PhD in Neuroscience, INT, Marseille, France

## Introduction to

- Spiking Neural Networks (SNNs) by using PyNN language and/or Brian2 stand-alone simulator

PyNN is a Python library for simulating neural networks. It provides a common interface for a variety of neural simulators, such as NEURON, NEST, and Brian, making it easy to switch between them without having to change the model code. PyNN allows users to define and simulate neural networks using a high-level, neuron-centric interface, similar to the way models are described in neuroscience literature. It is used in many research and education projects to study neural systems, and can be used to simulate models of the brain, as well as artificial neural networks. Brian is a simulator for spiking neural networks. It is written in the Python programming language and is available on almost all platforms. 

- Neural mass modelling with The Virtual Brain simulator 

TheVirtualBrain is a framework for the simulation of the dynamics of large-scale brain networks with biologically realistic connectivity. TheVirtualBrain uses tractographic data (DTI/DSI) to generate connectivity matrices and build cortical and subcortical brain networks. The connectivity matrix defines the connection strengths and time delays via signal transmission between all network nodes. Various neural mass models are available in the repertoire of TheVirtualBrain and define the dynamics of a network node. Together, the neural mass models at the network nodes and the connectivity matrix define the Virtual Brain. TheVirtualBrain simulates and generates the time courses of various forms of neural activity including Local Field Potentials (LFP) and firing rate, as well as brain imaging data such as EEG, MEG and BOLD activations as observed in fMRI. TheVirtualBrain is foremost a scientific simulation platform and provides all means necessary to generate, manipulate and visualize connectivity and network dynamics. In addition, TheVirtualBrain comprises a set of classical time series analysis tools, structural and functional connectivity analysis tools, as well as parameter exploration facilities by launching parallel simulations on a cluster.

## Interactive neural model dashboard

The [`dashboard/`](dashboard/) provides **Spiking** pages for single-compartment neurons
and the existing PyNN single-cell/E/I network experiments, and **Large Scale** pages
for isolated TVB population models or oscillators (with a network placeholder).
It includes explicit equations, terms/units, bibliography, editable inputs/parameters,
voltage-reference checkboxes, state traces and result downloads. See the
[dashboard instructions](dashboard/README.md) for installation, current model coverage
and the network-development roadmap.

Spiking lessons also include Single clique, a
[new local cell-model comparison notebook](notebooks/intro/eg_testing-cell-models-local.ipynb),
Decaying, Diverging, Small World and the 4000-cell Brian2 COBA benchmark. SpiNNaker-only
models and the original STDP experiment are linked to their source notebooks.

## Student quick start: run locally

The tutorial can run on a student's computer with Python 3.11 or 3.12. The root
[`requirements.txt`](requirements.txt) installs JupyterLab, the common notebook tools,
PyNN/Brian2, TVB example data and surface support, and the dashboard. It includes the
smaller dashboard requirements file.

Choose the instructions for your computer or teaching server:

| Platform | Step-by-step guide |
| --- | --- |
| Ubuntu | [Install, open notebooks and launch the dashboard](docs/quickstart.md#ubuntu) |
| Windows | [Command Prompt and PowerShell instructions](docs/quickstart.md#windows) |
| SANDS / JupyterLab | [Select a kernel and check the hosted dashboard route](docs/quickstart.md#sands-hosted-jupyterlab) |

Download CNT with Git, or [download and extract the ZIP](https://github.com/albertoarturovergani/CNT/archive/refs/heads/main.zip):

```bash
git clone --depth 1 https://github.com/albertoarturovergani/CNT.git
cd CNT
```

### Ubuntu / Linux / macOS

From the repository root, install the course and open the notebooks:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m jupyterlab
```

For the dashboard, use a terminal in the repository root with the environment active:

```bash
cd dashboard
python launch.py
```

### Windows PowerShell

With Python 3.11 or 3.12 selected, run from the repository root. These commands use
the environment's Python directly, so an activation script is unnecessary:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m jupyterlab
```

For the dashboard, use another PowerShell window in the repository root:

```powershell
cd dashboard
..\.venv\Scripts\python.exe launch.py
```

If `.venv` was instead created inside `dashboard/`, use
`.\.venv\Scripts\python.exe launch.py` from that directory. The
[Windows guide](docs/quickstart.md#windows) includes installation for that case and
the Command Prompt alternative. `source .venv/bin/activate` is a bash command.

In either local setup, open a notebook from `notebooks/` in JupyterLab or open the
local browser URL printed by the dashboard launcher. Keep its terminal running.
See the
[usage guide](docs/quickstart.md#use-the-dashboard) for running experiments and
downloading results, or the [environment guide](docs/environments.md) for more detail.

### SANDS / hosted JupyterLab

Use the same root requirements in a dedicated CPU environment, register it as the
**CNT (Brian2 / TVB)** kernel and open the notebooks in SANDS's existing JupyterLab
window. Follow the [SANDS instructions](docs/quickstart.md#sands-hosted-jupyterlab).
The dashboard additionally needs the platform's authenticated proxy route, whose
availability is not confirmed. Use the local Ubuntu or Windows procedure if that
remote route is unavailable.

## Optional: SpiNNaker hardware examples

Some notebooks use sPyNNaker-specific neuron or plasticity models and require a
SpiNNaker hardware environment. On [SANDS](https://sands.cs.man.ac.uk/), select the
managed **sPyNNaker** kernel for the
[hardware balanced-network example](notebooks/intro/paper_balance-network_sPyNNaker.ipynb).
Platform access uses [EBRAINS](https://www.ebrains.eu/) credentials. The common
student setup and dashboard use Brian2/TVB on the CPU. The same repository can be
used locally or on a teaching server; see the
[hosted JupyterLab notes](docs/environments.md#dashboard-from-hosted-jupyterlab).

For course issues, write to albertoarturo.vergani@unipv.it.

## Content:
- [Main Course Notebook](notebooks/intro/CNT_notebook.ipynb)
- [Example: Blank Network](notebooks/intro/eg_blank-network.ipynb)
- [Example: Decaying Network](notebooks/intro/eg_decaying-network.ipynb)
- [Example: Diverging Network](notebooks/intro/eg_diverging-network.ipynb)
- [Example: Entry Network](notebooks/intro/eg_entry-network.ipynb)
- [Example: Single Cell](notebooks/intro/eg_single-cell.ipynb)
- [Example: Single Clique](notebooks/intro/eg_single-clique.ipynb)
- [Example: Small-World Network](notebooks/intro/eg_small-world-network.ipynb)
- [Testing: Cell Models in the Network](notebooks/intro/eg_testing-cell-models-network.ipynb)
- [Testing: All locally supported PyNN/Brian2 and CNT Brian2 cell models](notebooks/intro/eg_testing-cell-models-local.ipynb)
- [Testing: STDP Model in the Network](notebooks/intro/eg_testing-STDP-model-network.ipynb)
- [Exercise: Network A](notebooks/intro/ex_network_A.ipynb)
- [Exercise: Network B](notebooks/intro/ex_network_B.ipynb)
- [Paper: Balanced Network (brian2)](notebooks/intro/paper_balance-network_brian2.ipynb)
- [Paper: Balanced Network (sPyNNaker)](notebooks/intro/paper_balance-network_sPyNNaker.ipynb)
- [Examples with Brian2](notebooks/numerical-methods/brian2/)
- [TVB Models](notebooks/numerical-methods/TVB/)
- [Utility Functions for Numerical Methods](notebooks/numerical-methods/utils.py)


## Knowledge assumptions: 

- basis of spiking neural network theory (https://neuronaldynamics.epfl.ch/online/index.html) or (https://neuromatch.io/academy/)
- familiarity with physical quantities related to electric circuits (e.g., voltages, conductances, currents, etc)
- basic python coding (numpy, work with dictionaries, some matplotlib tools, etc)

## Links
- [PyNN](http://neuralensemble.org/docs/PyNN/index.html)
- [SpiNNaker](http://apt.cs.manchester.ac.uk/projects/SpiNNaker/)
- [EBRAINS](https://ebrains.eu/)
- [The Human Brain Project](https://www.humanbrainproject.eu/en/)
