# Installing CNT: student computers and teaching servers

For the student-facing commands and instructions on opening lessons and experiments,
use the [Ubuntu, Windows and SANDS quick-start guide](quickstart.md).

## Choose the installation scope

| File or environment | Use |
| --- | --- |
| Root `requirements.txt` | JupyterLab, common notebook tools, PyNN/Brian2, TVB including its example data and surface library, and the dashboard |
| `dashboard/requirements.txt` | A smaller installation for the dashboard only |
| `dashboard/requirements-dev.txt` | Dashboard dependencies plus its test runner |
| Separately managed sPyNNaker environment | Optional notebooks that send simulations to SpiNNaker hardware |

The root file includes `dashboard/requirements.txt`; the shared dependencies have one
definition. It lists the libraries used by the checked-in notebooks, including FOOOF
and CSA, rather than packages unrelated to CNT that happen to be installed on a host.
Python 3.11 or 3.12 is recommended for the CPU environment.

## Full course environment

Clone CNT or extract its ZIP archive on the computer where the simulations will run.
Open a terminal in the CNT repository root. On Linux/macOS, check the interpreter
and create the environment there:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

On Windows Command Prompt with Python 3.12, use `py -3.12 -m venv .venv` and
`.venv\Scripts\activate.bat` in place of the two environment commands, then use the
same `python -m pip` commands. Use an available Python 3.11 or 3.12 executable for
environment creation if the default interpreter is older.
The requirements include the TVB example data, which
adds a data download. The geodesic-distance library uses a compiled extension; if no
wheel is available for a platform, its build requires a C++ toolchain.

Some Brian2 notebooks explicitly select the C++ standalone device, which also needs
a supported C++ compiler. The current dashboard uses Brian2's NumPy runtime. A pip
requirements file installs Python dependencies, while native toolchains and optional
hardware access are separate prerequisites for the examples that select them.

Start the installed JupyterLab to use the local notebooks:

```bash
python -m jupyterlab
```

Open a notebook from `notebooks/`. The dashboard uses the same environment:

```bash
cd dashboard
python launch.py
```

Open the local address printed by Streamlit. The course files and model code are
the same on local computers and teaching servers.

If using an existing JupyterLab installation or a hosted service, register the
course environment as a notebook kernel:

```bash
python -m ipykernel install --user --name cnt-cpu --display-name "CNT (Brian2 / TVB)"
```

Select **CNT (Brian2 / TVB)** in that JupyterLab for CPU-based lessons. The new virtual
environment does not inherit an independently installed hardware backend. The introductory
notebooks' existing backend fallback can therefore select Brian2. Examples that use
sPyNNaker-specific `extra_models` still require the hardware kernel.

Once the environment is installed, skip the old notebook cells that install
`tvb-library`/`tvb-framework`. The current examples import the TVB scientific library;
the separate TVB web application is not required for these imports.

## Optional hardware notebooks

On SANDS, select the server-provided **sPyNNaker** kernel for hardware runs. The hardware client,
its PyNN compatibility and machine-access configuration belong to that managed
environment. The root course requirements are intended for the new CPU environment;
they do not install or upgrade the platform kernel. Follow the platform's supported
installation procedure if the hardware client itself needs changing.

Hosting the dashboard on SANDS uses the server CPU for Brian2 and TVB. It does not
submit jobs to the SpiNNaker board.

## Dashboard from hosted JupyterLab

For example, SANDS exposes the same CNT checkout as `work/CNT` in its file browser.
The root requirements and dashboard requirements remain unchanged; only the web
address used to reach the running application differs from a local installation.

Start it from a **JupyterLab terminal**, with the CPU environment activated, rather
than running `launch.py` in a notebook cell. The launcher initializes Brian2 on the
main thread before Streamlit starts its script thread.

A browser on your laptop reaches a remote Streamlit process through JupyterHub's
authenticated proxy. This requires **Jupyter Server Proxy** to be enabled in the
environment running the Jupyter server. Installing it only into a new kernel
environment does not enable it for the existing server.

Before activating the CPU environment, the platform's terminal can report the server
extensions with `jupyter server extension list`. If the proxy is unavailable, request
the supported web-app route from the SANDS administrators. The proxy's availability
on SANDS has not been verified by this repository update.

With the proxy enabled, check the per-user URL prefix:

```bash
printenv JUPYTERHUB_SERVICE_PREFIX
```

It should contain a path such as `/user/YOUR_USERNAME/`. The following command uses
the proxy's **absolute** route and gives Streamlit the same full URL path. Run from
`dashboard/`, with the desired environment active:

```bash
python launch.py \
  --server.headless true \
  --server.address 127.0.0.1 \
  --server.port 8501 \
  --server.baseUrlPath "${JUPYTERHUB_SERVICE_PREFIX%/}/proxy/absolute/8501" \
  --browser.serverAddress sands.cs.man.ac.uk \
  --browser.serverPort 443
```

Open the SANDS address followed by the service prefix and `proxy/absolute/8501/`.
Keep the final slash. JupyterHub also provides this authenticated redirect:
[open the dashboard proxy](https://sands.cs.man.ac.uk/hub/user-redirect/proxy/absolute/8501/).
If port 8501 is already occupied, choose another port and change both its command
option and the port in `baseUrlPath` and the browser URL.

Keep the terminal process running while using the dashboard. Stop it with Ctrl+C.
A proxy 404 means that the web route needs checking; a 502/503 can mean that the
application is not running on the requested port. Do not interpret those responses
as proof that a Python dependency is missing.

For a local computer, use `python launch.py` without the proxy options and open the
local URL it prints. Requirements install libraries; the hosting route determines
how the browser reaches the application.

## References

- [PyNN installation](https://pynn.readthedocs.io/en/latest/installation.html)
- [TVB source and optional data/surface dependencies](https://github.com/the-virtual-brain/tvb-root)
- [Jupyter Server Proxy: arbitrary ports and absolute URLs](https://jupyter-server-proxy.readthedocs.io/en/latest/arbitrary-ports-hosts.html)
- [Jupyter Server Proxy: installation environment](https://jupyter-server-proxy.readthedocs.io/en/latest/install.html)
- [Streamlit configuration and base URL path](https://docs.streamlit.io/develop/api-reference/configuration/config.toml)
