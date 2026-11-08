"""Teaching equations checked against TVB 2.10.0's native derivative functions.

All equations below specialize to the dashboard's isolated node: inter-node
coupling and surface/local coupling are zero. Internal E/I interactions remain.
The installed class source is exposed alongside these notes for version checks.
"""

import inspect
import re
from . import populations


def aligned(*lines):
    return r"\begin{aligned}" + r"\\".join(lines) + r"\end{aligned}"


EQUATIONS = {
    "Linear": [r"\dot{x}=\gamma x"],
    "Generic2dOscillator": [aligned(
        r"\dot V&=d\tau(-fV^3+eV^2+gV+\alpha W+\gamma I)",
        r"\dot W&=\frac d\tau(cV^2+bV-\beta W+a)")],
    "Kuramoto": [r"\dot\theta=\omega"],
    "SupHopf": [aligned(r"\dot x&=(a-x^2-y^2)x-\omega y", r"\dot y&=(a-x^2-y^2)y+\omega x")],
    "Hopfield": [r"\dot x=-x/\tau_x,\qquad\dot\theta=\begin{cases}-\theta/\tau_T&\text{dynamic threshold}\\-x/\tau_x&\text{otherwise (native TVB)}\end{cases}"],
    "WilsonCowan": [aligned(
        r"X_e&=\alpha_e(c_{ee}E-c_{ei}I+P-\theta_e)",
        r"X_i&=\alpha_i(c_{ie}E-c_{ii}I+Q-\theta_i)",
        r"L_\mu(x)&=\frac{c_\mu}{1+\exp[-a_\mu(x-b_\mu)]},\quad\mu\in\{e,i\}",
        r"S_\mu(x)&=\begin{cases}L_\mu(x)-L_\mu(0)&\text{shift\_sigmoid}\\L_\mu(x)&\text{otherwise}\end{cases}",
        r"\tau_e\dot E&=-E+(k_e-r_eE)S_e(X_e)",
        r"\tau_i\dot I&=-I+(k_i-r_iI)S_i(X_i)")],
    "JansenRit": [aligned(
        r"\dot y_0&=y_3,\quad\dot y_1=y_4,\quad\dot y_2=y_5",
        r"\dot y_3&=AaS(y_1-y_2)-2ay_3-a^2y_0",
        r"\dot y_4&=Aa[\mu+a_2JS(a_1Jy_0)]-2ay_4-a^2y_1",
        r"\dot y_5&=Bb\,a_4JS(a_3Jy_0)-2by_5-b^2y_2",
        r"S(v)&=\frac{2\nu_{max}}{1+\exp[r(v_0-v)]}")],
    "ZetterbergJansen": [aligned(
        r"\dot v_j&=y_j\quad(j=1,\ldots,5),\quad q=\sigma(0)",
        r"\dot y_1&=H_ek_e[\gamma_1\sigma(v_2-v_3)+\gamma_{1T}(U+q)]-2k_ey_1-k_e^2v_1",
        r"\dot y_2&=H_ek_e[\gamma_2\sigma(v_1)+\gamma_{2T}(P+q)]-2k_ey_2-k_e^2v_2",
        r"\dot y_3&=H_ik_i\gamma_4\sigma(v_4-v_5)-2k_iy_3-k_i^2v_3",
        r"\dot y_4&=H_ek_e[\gamma_3\sigma(v_2-v_3)+\gamma_{3T}(Q+q)]-2k_ey_4-k_e^2v_4",
        r"\dot y_5&=H_ik_i\gamma_5\sigma(v_4-v_5)-2k_iy_5-k_e^2v_5",
        r"\dot v_6&=y_2-y_3,\quad\dot v_7=y_4-y_5",
        r"\sigma(v)&=\frac{2e_0}{1+\exp[\rho_1(\rho_2-v)]}")],
    "LarterBreakspear": [aligned(
        r"m_j&=\tfrac12[1+\tanh((V-T_j)/d_j)],\quad j\in\{Ca,Na,K\}",
        r"Q_V&=\tfrac{Q_{V,max}}2[1+\tanh((V-V_T)/d_V)]",
        r"Q_Z&=\tfrac{Q_{Z,max}}2[1+\tanh((Z-Z_T)/d_Z)]",
        r"\dot V&=t_{scale}\big[-(g_{Ca}+(1-C)r_{NMDA}a_{ee}Q_V)m_{Ca}(V-V_{Ca})",
        r"&\quad-g_KW(V-V_K)-g_L(V-V_L)",
        r"&\quad-(g_{Na}m_{Na}+(1-C)a_{ee}Q_V)(V-V_{Na})-a_{ie}ZQ_Z+a_{ne}I_{ext}\big]",
        r"\dot W&=t_{scale}\phi(m_K-W)/\tau_K",
        r"\dot Z&=t_{scale}b(a_{ni}I_{ext}+a_{ei}VQ_V)")],
    "ReducedSetFitzHughNagumo": [aligned(
        r"\dot{\boldsymbol\xi}&=\tau(\boldsymbol\xi-e_i\boldsymbol\xi^3/3-\boldsymbol\eta)+K_{11}(\boldsymbol\xi A-\boldsymbol\xi)-K_{12}(\boldsymbol\alpha B-\boldsymbol\xi)+\tau IE_i",
        r"\dot{\boldsymbol\eta}&=(\boldsymbol\xi-b\boldsymbol\eta+m_i)/\tau",
        r"\dot{\boldsymbol\alpha}&=\tau(\boldsymbol\alpha-f_i\boldsymbol\alpha^3/3-\boldsymbol\beta)+K_{21}(\boldsymbol\xi C-\boldsymbol\alpha)+\tau II_i",
        r"\dot{\boldsymbol\beta}&=(\boldsymbol\alpha-b\boldsymbol\beta+n_i)/\tau")],
    "ReducedSetHindmarshRose": [aligned(
        r"\dot{\boldsymbol\xi}&=\boldsymbol\eta-a_i\boldsymbol\xi^3+b_i\boldsymbol\xi^2-\boldsymbol\tau+K_{11}(\boldsymbol\xi A-\boldsymbol\xi)-K_{12}(\boldsymbol\alpha B-\boldsymbol\xi)+IE_i",
        r"\dot{\boldsymbol\eta}&=c_i-d_i\boldsymbol\xi^2-\boldsymbol\eta",
        r"\dot{\boldsymbol\tau}&=rs\boldsymbol\xi-r\boldsymbol\tau-m_i",
        r"\dot{\boldsymbol\alpha}&=\boldsymbol\beta-e_i\boldsymbol\alpha^3+f_i\boldsymbol\alpha^2-\boldsymbol\gamma+K_{21}(\boldsymbol\xi C-\boldsymbol\alpha)+II_i",
        r"\dot{\boldsymbol\beta}&=h_i-p_i\boldsymbol\alpha^2-\boldsymbol\beta",
        r"\dot{\boldsymbol\gamma}&=rs\boldsymbol\alpha-r\boldsymbol\gamma-n_i")],
    "ReducedWongWang": [aligned(
        r"x&=wJ_NS+I_o,\quad H(x)=\frac{ax-b}{1-\exp[-d(ax-b)]}",
        r"\dot S&=-S/\tau_s+(1-S)\gamma H(x)")],
    "MontbrioPazoRoxin": [aligned(r"\tau\dot r&=\Delta/(\pi\tau)+2Vr",
        r"\tau\dot V&=V^2-\pi^2\tau^2r^2+\eta+J\tau r+I")],
    "CoombesByrne": [aligned(r"\dot r&=\Delta/\pi+2Vr-gr",
        r"\dot V&=V^2-\pi^2r^2+\eta+(v_{syn}-V)g", r"\dot g&=\alpha q",
        r"\dot q&=\alpha(k\pi r-g-2q)")],
    "CoombesByrne2D": [aligned(r"g&=k\pi r,\quad\dot r=\Delta/\pi+2Vr-gr",
        r"\dot V&=V^2-\pi^2r^2+\eta+(v_{syn}-V)g")],
    "DumontGutkin": [aligned(
        r"\tau_\mu\dot r_\mu&=\Delta_\mu/(\pi\tau_\mu)+2V_\mu r_\mu,\quad\mu\in\{e,i\}",
        r"\tau_e\dot V_e&=V_e^2+\eta_e-\pi^2\tau_e^2r_e^2+\tau_e(s_{ee}-s_{ei})+I_e",
        r"\tau_i\dot V_i&=V_i^2+\eta_i-\pi^2\tau_i^2r_i^2+\tau_i(s_{ie}-s_{ii})+I_i",
        r"\tau_s\dot s_{ee}&=-s_{ee}+J_{ee}r_e,\quad\tau_s\dot s_{ei}=-s_{ei}+J_{ei}r_i",
        r"\tau_s\dot s_{ie}&=-s_{ie}+J_{ie}r_e,\quad\tau_s\dot s_{ii}=-s_{ii}+J_{ii}r_i")],
}

for _name in ("ReducedWongWangExcInh", "DecoBalancedExcInh"):
    _gain = r"M_i" if _name == "DecoBalancedExcInh" else "1"
    EQUATIONS[_name] = [aligned(
        r"I_e&=W_eI_o+w_pJ_NS_e-J_iS_i+I_{ext},\quad I_i=W_iI_o+J_NS_e-S_i",
        rf"x_e&={_gain}(a_eI_e-b_e),\quad x_i={_gain}(a_iI_i-b_i)",
        r"H_\mu&=\frac{x_\mu}{1-\exp(-d_\mu x_\mu)},\quad\mu\in\{e,i\}",
        r"\dot S_e&=-S_e/\tau_e+(1-S_e)\gamma_eH_e,\quad\dot S_i=-S_i/\tau_i+\gamma_iH_i")]

for _name in ("GastSchmidtKnosche_SD", "GastSchmidtKnosche_SF"):
    _interaction = r"J\tau r(1-A)" if _name.endswith("SD") else r"J\tau r-A"
    EQUATIONS[_name] = [aligned(r"\tau\dot r&=\Delta/(\pi\tau)+2Vr",
        rf"\tau\dot V&=V^2-\pi^2\tau^2r^2+\eta+{_interaction}+I",
        r"\tau_A\dot A&=B,\quad\tau_A\dot B=-2B-A+\alpha r")]

_epileptor_functions = aligned(
    r"f_1&=\begin{cases}-ax_1^2+bx_1&x_1<0\\slope-x_2+0.6(z-4)^2&x_1\geq0\end{cases}",
    r"f_2&=\begin{cases}0&x_2<-0.25\\aa(x_2+0.25)&x_2\geq-0.25\end{cases}",
    r"h_0&=4(x_1-x_0)-0.1z^7\,\mathbf1_{z<0}",
    r"h&=\begin{cases}x_0+3/(1+\exp[-(x_1+0.5)/0.1])&\text{modification}\\h_0&\text{otherwise}\end{cases}")
_epileptor = aligned(r"\dot x_1&=tt(y_1-z+I_{ext}+f_1x_1)",
    r"\dot y_1&=tt(c-dx_1^2-y_1),\quad\dot z=tt\,r(h-z)",
    r"\dot x_2&=tt[-y_2+x_2-x_2^3+I_{ext2}+bb\,g-0.3(z-3.5)]",
    r"\dot y_2&=tt(-y_2+f_2)/\tau,\quad\dot g=-0.01tt(g-0.1x_1)")
EQUATIONS["Epileptor"] = [_epileptor, _epileptor_functions]
EQUATIONS["EpileptorRestingState"] = [_epileptor.replace("(h-z)", "(h_0-z)"), _epileptor_functions,
    aligned(r"\dot x_{rs}&=d_{rs}\tau_{rs}(\alpha_{rs}y_{rs}-f_{rs}x_{rs}^3+e_{rs}x_{rs}^2+\gamma_{rs}I_{rs})",
        r"\dot y_{rs}&=d_{rs}(a_{rs}+b_{rs}x_{rs}-\beta_{rs}y_{rs})/\tau_{rs}")]
EQUATIONS["Epileptor2D"] = [aligned(
    r"F&=\begin{cases}ax_1^2+(d-b)x_1&x_1<0\\-slope-0.6(z-4)^2+dx_1&x_1\geq0\end{cases}",
    r"\dot x_1&=tt(c-z+I_{ext}-Fx_1),\quad\dot z=tt\,r(h-z)"), _epileptor_functions]
# Show only the definitions that each reduction actually uses.
_family_lines = _epileptor_functions.removeprefix(r"\begin{aligned}").removesuffix(r"\end{aligned}")
_h_position = _family_lines.index(r"\\h_0")
_fast_definitions = r"\begin{aligned}" + _family_lines[:_h_position] + r"\end{aligned}"
_h_definitions = r"\begin{aligned}" + _family_lines[_h_position+2:] + r"\end{aligned}"
EQUATIONS["Epileptor"] = [_epileptor, _fast_definitions, _h_definitions]
EQUATIONS["Epileptor2D"][1] = _h_definitions
EQUATIONS["EpileptorRestingState"][1] = _fast_definitions
EQUATIONS["EpileptorRestingState"].append(r"h_0=4(x_1-x_0)-0.1z^7\,\mathbf1_{z<0}")
_codim = aligned(r"\dot x&=-y,\quad\dot y=x^3-\mu_2x-\mu_1-y(\nu+bx+x^2)",
    r"\dot z&=-c[\sqrt{(x-x_s)^2+y^2}-d^*+m\,0.1(z-0.5)^7]",
    r"(\mu_2,-\mu_1,\nu)&=R(E\cos z+F\sin z),\quad m=\mathbf1_{\mathrm{modification}}",
    r"x_s&=\operatorname{Re}(\text{Cardano root selected by }N)\text{ of }x_s^3-\mu_2x_s-\mu_1=0")
EQUATIONS["EpileptorCodim3"] = [_codim]
EQUATIONS["EpileptorCodim3SlowMod"] = [_codim, aligned(
    r"\dot u_A&=c_A,\quad\dot u_B=c_B,\quad A=R(G\cos u_A+H\sin u_A)",
    r"B&=R(L\cos u_B+M\sin u_B),\quad E=A/\|A\|,\quad F=((A\times B)\times A)/\|(A\times B)\times A\|")]

_adaptation = aligned(r"\dot W_\mu&=-W_\mu/\tau_{w,\mu}+b_\mu\nu_\mu+a_\mu(\overline V_\mu-E_{L,\mu})/\tau_{w,\mu},\quad\mu\in\{e,i\}",
    r"\dot{OU}&=-OU/\tau_{OU},\quad(\nu_e,\nu_i)=(E,I)")
EQUATIONS["ZerlautAdaptationFirstOrder"] = [aligned(
    r"F_\mu&=TF_\mu(E,I,\nu_{ext,e\mu},\nu_{ext,i\mu},W_\mu)",
    r"T\dot E&=F_e-E,\quad T\dot I=F_i-I",
    r"u&=w_{noise}OU\text{ (clipped to 0 if }uK_{ext,e}<0\text{)}",
    r"\nu_{ext,ee}&=u+external\_input\_ex\_ex,\quad\nu_{ext,ie}=external\_input\_ex\_in",
    r"\nu_{ext,ei}&=u+external\_input\_in\_ex,\quad\nu_{ext,ii}=external\_input\_in\_in"), _adaptation]
EQUATIONS["ZerlautAdaptationSecondOrder"] = [aligned(
    r"T\dot\nu_\mu&=F_\mu-\nu_\mu+\tfrac12 C_{ee}D_{ee}F_\mu+\tfrac12 C_{ei}(D_{ei}F_\mu+D_{ie}F_\mu)+\tfrac12 C_{ii}D_{ii}F_\mu",
    r"T\dot C_{ee}&=F_e(1/T-F_e)/N_e+(F_e-E)^2+2C_{ee}D_eF_e+2C_{ei}D_iF_e-2C_{ee}",
    r"T\dot C_{ei}&=(F_e-E)(F_i-I)+C_{ee}D_eF_e+C_{ei}D_eF_i+C_{ei}D_iF_e+C_{ii}D_iF_i-2C_{ei}",
    r"T\dot C_{ii}&=F_i(1/T-F_i)/N_i+(F_i-I)^2+2C_{ii}D_iF_i+2C_{ei}D_eF_i-2C_{ii}",
    r"N_e&=N_{tot}(1-g),\quad N_i=N_{tot}g,\quad F_\mu=TF_\mu(E,I,\nu_{ext,e\mu},\nu_{ext,i\mu},W_\mu)",
    r"\nu_{ext,e\mu}&=\max(0,w_{noise}OU+external\_input\_{\mu}\_ex),\quad\nu_{ext,i\mu}=external\_input\_{\mu}\_in"), _adaptation]

EQUATIONS["KIonEx"] = [aligned(
    r"(R_b,c_b)&=\begin{cases}(R_-,c_-)&V\leq V^*\\(R_+,c_+)&V>V^*\end{cases},\quad r=R_-x/\pi",
    r"\dot x&=\Delta+2R_b(V-c_b)x-Jrx",
    r"\dot V&=-(I_{Na}+I_K+I_{Cl}+I_{pump})/C_m-R_bx^2+\eta",
    r"\dot n&=(n_\infty(V)-n)/\tau_n,\quad\dot{DKi}=-(\gamma/\omega_i)(I_K-2I_{pump})",
    r"\dot K_g&=\epsilon(K_{bath}-K_o)"), aligned(
    r"\beta&=\omega_i/\omega_o,\quad K_i=130+DKi,\quad K_o=4.8-\beta DKi+K_g",
    r"Na_i&=16-DKi,\quad Na_o=138+\beta DKi,\quad Cl_i=5,\quad Cl_o=112",
    r"m_\infty&=\frac1{1+\exp((-24-V)/12)},\quad n_\infty=\frac1{1+\exp((-19-V)/18)}",
    r"h(n)&=1.1-\frac1{1+\exp[-8(n-0.4)]}",
    r"I_K&=(g_{K,l}+g_Kn)(V-26.64\ln(K_o/K_i))",
    r"I_{Na}&=(g_{Na,l}+g_{Na}m_\infty h(n))(V-26.64\ln(Na_o/Na_i))",
    r"I_{Cl}&=g_{Cl}(V+26.64\ln(Cl_o/Cl_i))",
    r"I_{pump}&=\frac{\rho}{[1+\exp((21-Na_i)/2)][1+\exp(5.5-K_o)]}")]

NOTES = {
    "Hopfield": "Native TVB uses state labels x/theta and parameter codes taux/tauT. With dynamic disabled it returns the same derivative for both states; the displayed rule preserves that behavior.",
    "ZetterbergJansen": "The installed native derivative uses ke squared (not ki squared) in the v5 restoring term. The equation preserves that implementation. Even at zero coupling its sigmoid contributes sigma(0).",
    "ReducedSetFitzHughNagumo": "Bold symbols are mode vectors; powers are elementwise. A, B, C are the native derived mode-projection matrices, not inter-node connectivity.",
    "ReducedSetHindmarshRose": "Bold tau is a state variable, distinct from a time constant. A, B, C are native derived mode-projection matrices; powers are elementwise.",
    "EpileptorRestingState": "The resting-state variant always uses h0 for the slow variable.",
    "Epileptor2D": "Only x1 and z are state variables in this reduction.",
    "KIonEx": "The native TVB implementation predates the final 2026 publication; that article may contain revised equations. Constants and ion-conversion factors are specified in the installed class source. This isolated-node adapter does not add a Jr(E−V) term to the voltage equation.",
    "ZerlautAdaptationFirstOrder": "TF and mean voltage are the native conductance-based transfer/voltage functions. OU decays deterministically here; no stochastic forcing is added by this dashboard.",
    "ZerlautAdaptationSecondOrder": "TF and mean voltage are native functions. D denotes TVB's finite-difference operators with their 1000 scaling; the mixed-covariance equation follows the native implementation. OU has deterministic decay only. For external-input code names, mu=e corresponds to ex and mu=i to in.",
}

STATE_MEANINGS = {
    "Generic2dOscillator": {"V": "Fast activity variable", "W": "Slow recovery variable"},
    "Kuramoto": {"theta": "Oscillator phase"},
    "WilsonCowan": {"E": "Excitatory population activity", "I": "Inhibitory population activity"},
    "JansenRit": {"y0": "Pyramidal postsynaptic potential", "y1": "Excitatory postsynaptic potential", "y2": "Inhibitory postsynaptic potential",
                  "y3": "Time derivative of y0", "y4": "Time derivative of y1", "y5": "Time derivative of y2"},
}

_epileptor_states = {"x1": "Fast discharge variable", "y1": "Fast recovery variable", "z": "Slow permittivity / excitability variable",
    "x2": "Spike-and-wave variable", "y2": "Spike-and-wave recovery variable", "g": "Filtered fast activity",
    "x_rs": "Resting-state oscillator activity", "y_rs": "Resting-state oscillator recovery"}
for _name in ("Epileptor", "Epileptor2D", "EpileptorRestingState"):
    STATE_MEANINGS[_name] = _epileptor_states
for _name in ("EpileptorCodim3", "EpileptorCodim3SlowMod"):
    STATE_MEANINGS[_name] = {"x": "Fast subsystem coordinate", "y": "Fast subsystem coordinate",
        "z": "Slow coordinate on the bifurcation path", "uA": "Ultra-slow angle controlling path endpoint A",
        "uB": "Ultra-slow angle controlling path endpoint B"}
STATE_MEANINGS["Hopfield"] = {"x": "Neural activity", "theta": "Threshold state"}
STATE_MEANINGS["Linear"] = {"x": "Linear activity variable"}
STATE_MEANINGS["SupHopf"] = {"x": "Real oscillator coordinate", "y": "Imaginary oscillator coordinate"}
STATE_MEANINGS["LarterBreakspear"] = {"V": "Excitatory population voltage variable", "W": "Potassium-channel activation fraction",
    "Z": "Inhibitory population voltage variable"}
STATE_MEANINGS["KIonEx"] = {"x": "Population distribution width variable", "V": "Mean membrane voltage", "n": "Potassium activation fraction",
    "DKi": "Change in intracellular potassium concentration", "Kg": "Glial / bath potassium contribution"}
for _name in ("ZerlautAdaptationFirstOrder", "ZerlautAdaptationSecondOrder"):
    STATE_MEANINGS[_name] = {"E": "Excitatory population firing rate", "I": "Inhibitory population firing rate"}
for _name in ("GastSchmidtKnosche_SD", "GastSchmidtKnosche_SF"):
    STATE_MEANINGS[_name] = {"A": "Synaptic depression variable" if _name.endswith("SD") else "Spike-frequency adaptation variable",
        "B": "Auxiliary adaptation-filter state"}
for _name in ("CoombesByrne", "CoombesByrne2D"):
    STATE_MEANINGS[_name] = {"g": "Population synaptic conductance variable", "q": "Auxiliary synaptic-filter state"}
STATE_MEANINGS["DumontGutkin"] = {"r_e": "Excitatory firing-rate variable", "r_i": "Inhibitory firing-rate variable",
    "V_e": "Excitatory mean-voltage variable", "V_i": "Inhibitory mean-voltage variable",
    "s_ee": "E to E synaptic drive", "s_ei": "I to E synaptic drive", "s_ie": "E to I synaptic drive", "s_ii": "I to I synaptic drive"}
STATE_MEANINGS["ZetterbergJansen"] = {
    **{f"v{i}": f"Postsynaptic potential variable {i}" for i in range(1, 6)},
    **{f"y{i}": f"Time derivative of v{i}" for i in range(1, 6)},
    "v6": "Potential-difference coordinate (derivative y2 − y3)", "v7": "Potential-difference coordinate (derivative y4 − y5)"}
for _name in ("ReducedSetFitzHughNagumo", "ReducedSetHindmarshRose"):
    STATE_MEANINGS[_name] = {"xi": "Excitatory voltage mode", "eta": "Excitatory recovery mode",
        "alpha": "Inhibitory voltage mode", "beta": "Inhibitory recovery mode",
        "tau": "Excitatory slow adaptation mode", "gamma": "Inhibitory slow adaptation mode"}


def _clean_description(text):
    text = re.sub(r":(?:math|class|ref):`([^`]+)`", r"\1", text)
    return " ".join(text.split())


def _parameter_unit(name, description, model):
    # Use explicit native annotations; don't assign mV to normalized variables.
    match = re.search(r"\[([^\]\n]{1,25})\]", description)
    if match and not match.group(1).startswith("0") and "_" not in match.group(1):
        return match.group(1)
    if model == "Kuramoto" and name == "omega":
        return "rad/ms"
    if model == "Linear" and name == "gamma":
        return "1/ms (TVB simulation time)"
    return "native units; not declared by TVB" 


def population_notes(name):
    """All native parameter descriptions remain accessible, including mixed-unit arrays."""
    model = populations.get_model(name)
    meta = populations.model_metadata(name)
    source = inspect.getsource(type(model))
    rows = [{"Symbol / code": "t", "Meaning": "TVB simulation time", "Unit": "ms"}]
    for state in meta["state_variables"]:
        meaning = STATE_MEANINGS.get(name, {}).get(state)
        if not meaning:
            meaning = ({"r": "Population firing rate", "V": "Population voltage variable", "S": "Synaptic gating fraction",
                "S_e": "Excitatory synaptic gating fraction", "S_i": "Inhibitory synaptic gating fraction",
                "W_e": "Excitatory adaptation current", "W_i": "Inhibitory adaptation current",
                "C_ee": "E/E activity covariance", "C_ei": "E/I activity covariance", "C_ii": "I/I activity covariance",
                "ou_drift": "OU drift state (deterministic here)"}.get(state, f"Native {name} state; see class description"))
        unit = "normalized / native model units"
        if name == "Kuramoto":
            unit = "rad"
        elif name == "JansenRit":
            unit = "mV/ms" if state in ("y3", "y4", "y5") else "mV"
        elif name in ("ReducedWongWang", "ReducedWongWangExcInh", "DecoBalancedExcInh"):
            unit = "1 (fraction)"
        elif name.startswith("Zerlaut"):
            unit = "pA" if state in ("W_e", "W_i") else ("1/ms" if state in ("E", "I") else "native state units")
        elif name == "KIonEx" and state == "V":
            unit = "mV"
        elif name == "KIonEx" and state in ("DKi", "Kg"):
            unit = "native concentration units"
        elif name == "KIonEx" and state == "n":
            unit = "1 (gating fraction)"
        rows.append({"Symbol / code": state, "Meaning": meaning, "Unit": unit})
    for param, detail in meta["parameters"].items():
        rows.append({"Symbol / code": param, "Meaning": _clean_description(detail["description"]) or "Native model parameter",
                     "Unit": _parameter_unit(param, detail["description"], name)})
    return {"equations": EQUATIONS.get(name, []), "glossary": rows, "source": source,
            "note": NOTES.get(name, ""), "version": meta["version"],
            "scope": "Equations for one isolated node (inter-node and surface coupling = 0). "
                "Reviewed against TVB 2.10.0. Symbols retain the native parameter names, with subscripts for readability. "
                "Units not specified by TVB are labeled explicitly; these models do not share a universal voltage or input unit."}
