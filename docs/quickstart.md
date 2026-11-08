# Using CNT on Ubuntu, Windows and SANDS

Use the same repository and model code on a student computer or a teaching server.
For a first check, use a local Ubuntu or Windows installation. The SANDS web-app
route below depends on the platform proxy and is not confirmed to work on SANDS.

- [Ubuntu](#ubuntu)
- [Windows](#windows)
- [SANDS: hosted JupyterLab](#sands-hosted-jupyterlab)
- [Use the notebooks](#use-the-notebooks)
- [Use the dashboard](#use-the-dashboard)
- [Reopen or update CNT](#reopen-or-update-cnt)

## Download CNT

Use Python 3.11 or 3.12 for the course environment. With Git installed, open a
terminal in the directory where you want to keep the tutorial:

```bash
git clone --depth 1 https://github.com/albertoarturovergani/CNT.git
cd CNT
```

Alternatively, [download the ZIP](https://github.com/albertoarturovergani/CNT/archive/refs/heads/main.zip)
and extract it. Open a terminal inside the extracted folder, which may be named
`CNT-main`. In the instructions below, **repository root** means the folder containing
`requirements.txt`, `notebooks/` and `dashboard/`.

If you already have a Git checkout, use the update instructions below instead of
cloning another copy. Virtual environments are created separately on each computer.

## Ubuntu

### First installation

From the repository root:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

If the reported Python version is not 3.11 or 3.12, use an available Python 3.11 or
3.12 executable for environment creation. If Ubuntu reports that `venv` or
`ensurepip` is unavailable, install the matching virtual-environment package; for
Ubuntu's default Python this is:

```bash
sudo apt install python3-venv
```

Then repeat the `venv` command. This system-package step applies to your own Ubuntu
computer; the hosted SANDS environment is managed separately.

### Open the notebooks

With the environment active, from the repository root:

```bash
python -m jupyterlab
```

Open the browser address printed in the terminal if a browser window does not open
automatically. Continue with [Use the notebooks](#use-the-notebooks).

### Open the dashboard

As an alternative to starting JupyterLab, use this command from the activated
environment in the repository root:

```bash
cd dashboard
python launch.py
```

Open the local address printed by Streamlit, normally
[http://localhost:8501](http://localhost:8501), **on the same computer**. Leave the
terminal running. To keep JupyterLab and the dashboard open together, use a second
terminal, enter the repository root and activate `.venv` there first.

## Windows

### First installation

Install Python 3.12, or use Python 3.11 with the corresponding launcher option.
The commands in this section are for **Command Prompt (`cmd.exe`)**. You can open
it in the extracted CNT folder by typing `cmd` in File Explorer's address bar.

From the repository root:

```bat
py -3.12 --version
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m pip check
```

If using Python 3.11, replace `-3.12` with `-3.11` in the two launcher commands.

### Open the notebooks

From the repository root, with the environment active:

```bat
python -m jupyterlab
```

Open the address printed in the terminal if necessary, then follow
[Use the notebooks](#use-the-notebooks).

### Open the dashboard

As an alternative, from the repository root with the environment active:

```bat
cd dashboard
python launch.py
```

Open the printed local address in a browser on that Windows computer and keep the
terminal running. Use a second activated terminal if JupyterLab is already running.

### If your terminal is PowerShell

You can use the environment's Python directly, without an activation script. After
creating `.venv`, run these commands from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m jupyterlab
```

Or, for the dashboard, use another PowerShell window opened in the repository root:

```powershell
cd dashboard
..\.venv\Scripts\python.exe launch.py
```

If you are already inside `dashboard/` and created `.venv` **in that directory**,
use its local interpreter instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe launch.py
```

That installs the smaller dashboard-only requirements. Use the repository-root
environment above for the full notebook tutorial. The bash command
`source .venv/bin/activate` is for Ubuntu/Linux, not Windows PowerShell.

## SANDS: hosted JupyterLab

### Install the same course environment

Sign in to [SANDS](https://sands.cs.man.ac.uk/) and open your CNT checkout in its
JupyterLab file browser, for example `work/CNT`. Open a **Terminal** from the
JupyterLab launcher and move to the repository root. The URL in the browser is not
a shell path: use the checkout's actual directory on the server.

If your checkout is in your home directory under `work/CNT`, the command is:

```bash
cd ~/work/CNT
```

Then create the CPU environment and register it with the existing JupyterLab server:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m ipykernel install --user --name cnt-cpu --display-name "CNT (Brian2 / TVB)"
```

Use an available Python 3.11 or 3.12 executable if the default server interpreter
has another version. Keep the platform's hardware environment separate from this installation.

### Open the notebooks on SANDS

Use the **existing SANDS JupyterLab browser window**. Open a notebook from
`notebooks/` and select **CNT (Brian2 / TVB)** as its kernel. You do not need to
launch another JupyterLab server. For notebooks that send jobs to SpiNNaker hardware,
select the platform-provided **sPyNNaker** kernel instead.

### Open the dashboard on SANDS: conditional route

Remote dashboard access requires Jupyter Server Proxy in the environment running
the platform's Jupyter server. Installing Python packages in a notebook kernel alone
does not establish this web route. Its availability on SANDS is not verified; if the
remote dashboard does not open, use the local Ubuntu or Windows procedure above.

Where the platform enables this proxy, check its user prefix in a JupyterLab terminal:

```bash
printenv JUPYTERHUB_SERVICE_PREFIX
```

It should look like `/user/YOUR_USERNAME/`. If it is empty, check the supported app
route with the platform administrator before using the following command. With the
CPU environment activated, start the dashboard from `dashboard/`:

```bash
python launch.py \
  --server.headless true \
  --server.address 127.0.0.1 \
  --server.port 8501 \
  --server.baseUrlPath "${JUPYTERHUB_SERVICE_PREFIX%/}/proxy/absolute/8501" \
  --browser.serverAddress sands.cs.man.ac.uk \
  --browser.serverPort 443
```

With the process running, try the authenticated
[SANDS dashboard redirect](https://sands.cs.man.ac.uk/hub/user-redirect/proxy/absolute/8501/).
This URL is different from a laptop's localhost address. A 404 or 502/503 response
needs the platform route and process checked; the cause cannot be inferred from
the browser response alone. See the [hosted environment notes](environments.md#dashboard-from-hosted-jupyterlab).

## Use the notebooks

1. In JupyterLab's file browser, open the `notebooks/` directory and choose an `.ipynb`
   lesson. Brian2 and TVB examples are under `notebooks/numerical-methods/`.
2. Select the course's Python kernel. On SANDS, use **CNT (Brian2 / TVB)** for CPU
   lessons or **sPyNNaker** for hardware lessons that require it.
3. Read and execute cells in order from the beginning. **Shift+Enter** runs the
   selected cell and advances to the next one.
4. Change a parameter, rerun the cells that depend on it, and compare the plots.
   After installing the root requirements, skip old package-install cells in the
   TVB notebooks.

Some legacy examples select a C++ standalone device or SpiNNaker-specific models.
Those examples also require the relevant compiler or hardware environment, as
described in the [environment guide](environments.md).

## Use the dashboard

Start it with `python launch.py` from a terminal in `dashboard/`, using the environment
chosen above. Open the printed local URL, or the platform's proxy URL for a hosted run.

| Tab | Experiment |
| --- | --- |
| **Single neuron** | Select a model, waveform, input amplitude and timing. Optionally edit model parameters, then press **Run single neuron**. Inspect voltage, spike events, applied input and the available state-space trajectory. |
| **Population & oscillator** | Select a TVB model, duration, integration step and initial-condition seed. Optionally edit native parameters, then press **Run isolated population**. Select the state variables to plot. |
| **Catalogue & roadmap** | Check model availability and the planned extensions. GLIF/E-GLIF and network experiments remain listed as pending. |

Use the CSV and JSON download buttons to save traces, spike times and the completed
run's configuration. Read the units shown for each model before comparing inputs.
After changing a form value, press its **Run** button again to generate a new result.

## Reopen or update CNT

Install packages once for each environment. For a later session, open a terminal
in the repository root and reactivate the environment:

| Platform | Activation |
| --- | --- |
| Ubuntu | `source .venv/bin/activate` |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |
| SANDS terminal | `source .venv/bin/activate` in the server's CNT checkout |

Then start JupyterLab or the dashboard using the relevant instructions above.
PowerShell users can continue using the environment's Python executable directly.
Stop a locally launched JupyterLab or dashboard process with **Ctrl+C** in its terminal.
On SANDS, this refers to the dashboard process you started, not the managed platform.

For an existing Git checkout on `main`, update from the repository root:

```bash
git pull --ff-only
python -m pip install -r requirements.txt
```

Activate the appropriate environment first. A ZIP download is a snapshot; Git's pull
command applies only to a cloned checkout.

## If an application does not start

| Symptom | First check |
| --- | --- |
| `requirements.txt` cannot be found | Run installation from the repository root. |
| `No module named ...` | Use the environment in which you installed the requirements. |
| `signal only works in main thread` | Start `launch.py` from a terminal, rather than running it in a notebook cell. |
| Local browser cannot connect | Check that the process is still running and use the address it printed on that same computer. |
| SANDS browser cannot reach the dashboard | The remote proxy path and process need checking; try the local procedure while resolving platform access. |

When reporting an error, include the command you ran and the error text printed in
its terminal.

## Reference documentation

- [Python virtual environments](https://docs.python.org/3.12/library/venv.html)
- [Starting JupyterLab](https://jupyterlab.readthedocs.io/en/stable/getting_started/starting.html)
- [Jupyter Server Proxy routes](https://jupyter-server-proxy.readthedocs.io/en/latest/arbitrary-ports-hosts.html)
- [Jupyter Server Proxy installation](https://jupyter-server-proxy.readthedocs.io/en/latest/install.html)
