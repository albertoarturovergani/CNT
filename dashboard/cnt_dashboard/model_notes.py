"""Equations and units for the implemented one-compartment models.

These describe the adapters in cells.py, including their reset/detection rules.
They are deliberately independent of Streamlit and the simulator.
"""

from dataclasses import dataclass
from .cells import CELLS


CELL_EQUATIONS = {
    "lif": [r"C\frac{dv}{dt}=g_L(E_L-v)+I(t)",
        r"v\geq V_{th}\;\Longrightarrow\;v\leftarrow V_r,\quad v=V_r\text{ for }t_{ref}"],
    "izhikevich": [r"\frac{dv}{dt}=\frac{0.04v^2+5v+140-u+I(t)}{1\,\mathrm{ms}},\qquad"
        r"\frac{du}{dt}=\frac{a(bv-u)}{1\,\mathrm{ms}}",
        r"v\geq30\;\Longrightarrow\;v\leftarrow c,\quad u\leftarrow u+d"],
    "adex": [r"C\frac{dv}{dt}=g_L(E_L-v)+g_L\Delta_T\exp\!\left(\frac{v-V_T}{\Delta_T}\right)+I(t)-w",
        r"\tau_w\frac{dw}{dt}=a(v-E_L)-w",
        r"v>V_{cut}=V_T+5\Delta_T\;\Longrightarrow\;v\leftarrow V_r,\quad w\leftarrow w+b"],
    "hh": [r"C\frac{dv}{dt}=g_L(E_L-v)-g_{Na}m^3h(v-E_{Na})-g_Kn^4(v-E_K)+I(t)",
        r"\frac{dq}{dt}=\alpha_q(1-q)-\beta_q q,\qquad q\in\{m,h,n\}",
        r"\begin{aligned} \alpha_m&=\frac{1.28}{\operatorname{exprel}((13\,\mathrm{mV}-v+V_T)/(4\,\mathrm{mV}))}\,\mathrm{ms}^{-1}\\"
        r"\beta_m&=\frac{1.4}{\operatorname{exprel}((v-V_T-40\,\mathrm{mV})/(5\,\mathrm{mV}))}\,\mathrm{ms}^{-1}\\"
        r"\alpha_n&=\frac{0.16}{\operatorname{exprel}((15\,\mathrm{mV}-v+V_T)/(5\,\mathrm{mV}))}\,\mathrm{ms}^{-1}\\"
        r"\beta_n&=0.5\exp((10\,\mathrm{mV}-v+V_T)/(40\,\mathrm{mV}))\,\mathrm{ms}^{-1}\\"
        r"\alpha_h&=0.128\exp((17\,\mathrm{mV}-v+V_T)/(18\,\mathrm{mV}))\,\mathrm{ms}^{-1}\\"
        r"\beta_h&=\frac{4}{1+\exp((40\,\mathrm{mV}-v+V_T)/(5\,\mathrm{mV}))}\,\mathrm{ms}^{-1}\end{aligned}",
        r"\operatorname{exprel}(x)=\frac{e^x-1}{x},\qquad\operatorname{exprel}(0)=1"],
    "morris_lecar": [r"C\frac{dv}{dt}=-g_L(v-E_L)-g_{Ca}m_\infty(v)(v-E_{Ca})-g_Kn(v-E_K)+I(t)",
        r"\frac{dn}{dt}=\frac{\cosh((v-V_3)/(2V_4))}{\tau_n}(n_\infty(v)-n)",
        r"m_\infty(v)=\frac{1+\tanh((v-V_1)/V_2)}{2},\qquad "
        r"n_\infty(v)=\frac{1+\tanh((v-V_3)/V_4)}{2}"],
}

PARAMETER_NAMES = {
    "C": "Membrane capacitance", "gL": "Leak conductance", "EL": "Leak reversal potential",
    "Vth": "Spike threshold", "Vr": "Voltage after reset", "tref": "Absolute refractory period",
    "VT": "Exponential onset voltage (AdEx); kinetic voltage shift (HH)",
    "DeltaT": "Exponential slope factor", "tauw": "Adaptation time constant",
    "a": "Recovery rate (Izhikevich); subthreshold adaptation conductance (AdEx)",
    "b": "Recovery coupling (Izhikevich); spike-triggered adaptation increment (AdEx)",
    "c": "Voltage after reset", "d": "Recovery increment after a spike",
    "gNa": "Maximum sodium conductance", "gK": "Maximum potassium conductance",
    "gCa": "Maximum calcium conductance", "ENa": "Sodium reversal potential",
    "EK": "Potassium reversal potential", "ECa": "Calcium reversal potential",
    "V1": "Calcium activation midpoint", "V2": "Calcium activation voltage scale",
    "V3": "Potassium activation midpoint", "V4": "Potassium activation voltage scale",
    "tau_n": "Potassium activation time scale",
}

MODEL_PARAMETER_NAMES = {
    "izhikevich": {"a": "Recovery rate coefficient", "b": "Recovery coupling coefficient"},
    "adex": {"a": "Subthreshold adaptation conductance", "b": "Spike-triggered adaptation increment", "VT": "Exponential spike-onset voltage"},
    "hh": {"VT": "Voltage shift of channel kinetics (not a spike threshold)"},
}

CELL_NOTES = {
    "lif": "During the refractory interval the membrane is clamped to Vr. EL is also the passive resting voltage at zero input.",
    "izhikevich": "This CNT adapter uses scaled, dimensionless voltage/recovery and input variables. "
        "The numerical voltage convention resembles mV, but the simulator declares v and u dimensionless; input is not in pA.",
    "adex": "VT is the onset of exponential spike initiation. The numerical spike cutoff is VT + 5 DeltaT. "
        "EL is a leak reversal potential, not necessarily the equilibrium of the full nonlinear model. No refractory clamp is implemented.",
    "hh": "CNT notebook variant with shifted rate functions and absolute conductances, not the original squid-axon parameter fit. "
        "A crossing of −40 mV counts a spike; the voltage is never reset. VT shifts the channel kinetics and is not a spike threshold. "
        "EL is the leak reversal, not necessarily the resting equilibrium of the full model.",
    "morris_lecar": "This notebook uses absolute capacitance/conductances (uF, mS) and total current (uA). "
        "A crossing of 0 mV counts a spike, with no voltage reset. EL is the leak reversal, not necessarily the full-model resting equilibrium.",
}


def cell_glossary(model_id):
    spec = CELLS[model_id]
    rows = [{"Symbol / code": "t", "Meaning": "Time", "Unit": "ms"},
            {"Symbol / code": "v", "Meaning": "Membrane voltage" if model_id != "izhikevich" else "Scaled voltage", "Unit": "mV" if model_id != "izhikevich" else "model voltage"},
            {"Symbol / code": "I(t)", "Meaning": "Applied input", "Unit": spec.input_unit}]
    if model_id == "izhikevich":
        rows.append({"Symbol / code": "u", "Meaning": "Scaled recovery variable", "Unit": "model recovery"})
    elif model_id == "adex":
        rows.append({"Symbol / code": "w", "Meaning": "Adaptation current", "Unit": "pA"})
    elif model_id in ("hh", "morris_lecar"):
        rows.append({"Symbol / code": "m, h, n" if model_id == "hh" else "n, m_inf, n_inf", "Meaning": "Channel gating / activation fractions", "Unit": "1"})
    for name, param in spec.parameters.items():
        meaning = MODEL_PARAMETER_NAMES.get(model_id, {}).get(name, PARAMETER_NAMES[name])
        if name == "EL" and model_id == "lif":
            meaning += " / passive resting voltage"
        rows.append({"Symbol / code": name, "Meaning": meaning, "Unit": param.unit})
    return rows


@dataclass(frozen=True)
class VoltageReference:
    key: str
    label: str
    value: float
    unit: str
    color: str


def voltage_references(model_id, parameters):
    """Use parameters of the completed run, never the unsubmitted controls."""
    refs = []
    unit = "model voltage" if model_id == "izhikevich" else "mV"
    def add(key, label, value, color):
        refs.append(VoltageReference(key, label, float(value), unit, color))
    if "EL" in parameters:
        add("rest", "Vrest = EL" if model_id == "lif" else "EL · leak reversal", parameters["EL"], "#60a5fa")
    if model_id == "lif":
        add("threshold", "Vthreshold", parameters["Vth"], "#fbbf24")
    elif model_id == "adex":
        add("threshold", "VT · exponential onset", parameters["VT"], "#fbbf24")
        add("detect", "Vdetect = VT + 5 DeltaT", parameters["VT"] + 5 * parameters["DeltaT"], "#fb923c")
    elif model_id in ("hh", "morris_lecar", "izhikevich"):
        add("detect", "Vdetect · spike counting", {"hh": -40, "morris_lecar": 0, "izhikevich": 30}[model_id], "#fb923c")
    if model_id in ("lif", "adex", "izhikevich"):
        add("reset", "Vreset", parameters["c" if model_id == "izhikevich" else "Vr"], "#f472b6")
    return refs


def add_voltage_lines(figure, references, row=2):
    """Merge coincident levels so their labels remain readable; no trace edits."""
    levels = {}
    for ref in references:
        levels.setdefault((ref.value, ref.unit), []).append(ref)
    for (value, unit), refs in levels.items():
        figure.add_hline(y=value, line_dash="dot", line_color=refs[0].color,
            annotation_text=f"{' / '.join(r.label for r in refs)} = {value:g} {unit}",
            annotation_position="top left", row=row, col=1)
    return figure
