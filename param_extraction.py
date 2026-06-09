import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from pathlib import Path
from dataclasses import dataclass, asdict

# Physical constants
k_B = 1.38e-23
c = 3e8
e = 1.6e-19
hbar = 1.06e-34
Phi_0 = 2.067e-15
mu_0 = 4 * np.pi * 1e-7

WHH_FACTOR = 0.693

@dataclass
class SCParameters:
    Sample: str
    Bc20: float
    Tc: float
    Rsheet: float
    d: float
    dBc2_dT: float
    rho_n: float
    D_e: float
    Delta_0: float
    xi_0: float
    N_0: float
    lambda_0: float
    L_k: float

def import_dat_files(directory, channel=1):
    data_dir = Path(directory) / "data"
    frames = []

    files = sorted(data_dir.glob("*.dat"))
    files = [file for file in files if "300Kstart" not in file.name]

    for n, file in enumerate(files):
        df = pd.read_csv(file, skiprows=list(range(17)) + [18])
        df["n"] = n
        frames.append(df)

    raw = pd.concat(frames, ignore_index=True)

    df = pd.DataFrame({
        "R": raw[f"Channel {channel} Resistance"],
        "T": raw["Temperature (K)"].round(2),
        "B": (raw["Magnetic Field (Oe)"] * 1e-4).round(2),
        "n": raw["n"],
    })

    return df.replace([np.inf, -np.inf], np.nan).dropna()

def find_Rnormal(R, T, dT=0.5, T_normal=40):
    # Find normal state resistance defined as resistance at
    # temperature T_normal +/- dT.
    mask = (T > T_normal - dT) & (T < T_normal + dT)
    return np.mean(R[mask])

def find_Tc(RTc, R, T, tolerance=0.1):
    dR = RTc * tolerance
    mask = (R > RTc - dR) & (R < RTc + dR)
    return np.mean(T[mask])

def fit_BTc(Tc, B, r=0.5):
    Tc = np.asarray(Tc)
    B = np.asarray(B)

    Tc_inter = np.nanmin(Tc) + (np.nanmax(Tc) - np.nanmin(Tc)) * r
    mask = Tc < Tc_inter

    coeffs = np.polyfit(Tc[mask], B[mask], deg=1)
    return coeffs, Tc_inter

def find_rho_n(Rsheet, d): return Rsheet * d
def find_D_e(dBc2_dT): return (4 * k_B / (np.pi * e)) / dBc2_dT
def find_Delta_0(Tc): return (3.52 * k_B * Tc) / 2
def find_xi_0(Bc20): return np.sqrt(Phi_0 / (2 * np.pi * Bc20))
def find_N_0(rho_n, D_e): return (4 * k_B) / ((e**2) * rho_n * D_e)
def find_lambda_0(rho_n, Delta_0): return np.sqrt((hbar * rho_n) / (np.pi * mu_0 * Delta_0))
def find_L_k(Rsheet, Delta_0): return (hbar * Rsheet) / (np.pi * Delta_0)

def plot_R_vs_T(df, df_results, sample_id, Rsheet, criterion, outdir, xlims=[0, 40]):
    fig, ax = plt.subplots()

    for n, df_sub in df.groupby("n"):
        B = df_results.loc[df_results["n"] == n, "B"].iloc[0]
        ax.plot(df_sub["T"], df_sub["R"], label=f"{B:.2f} T")

    ax.plot(df_sub["T"], np.full(len(df_sub), Rsheet * criterion), color="k")

    ax.set_xlabel(r"temperature, $T$ (K)")
    ax.set_ylabel(r"sheet resistance, $R_{sq}$ ($\Omega$)")
    ax.set_title(f"{sample_id}, sc_criterion: {criterion}")
    ax.set_xlim(*xlims)
    ax.legend(loc="lower right")

    fig.tight_layout()
    fig.savefig(Path(outdir) / "Rsq_vs_T.png", dpi=300)
    plt.close(fig)

def plot_B_vs_Tc(df_results, coeffs, Tc_intersection, sample_id, outdir):
    fig, ax = plt.subplots(figsize=(6, 4))

    Tc = np.asarray(df_results["Tc"])
    B = np.asarray(df_results["B"])

    slope, intercept = coeffs
    fit_mask = Tc < Tc_intersection

    # measured points
    ax.scatter(Tc, B, label="Measured", zorder=10)

    # fit region
    Tc_fit = np.linspace(np.nanmin(Tc[fit_mask]), np.nanmax(Tc[fit_mask]), 200)
    B_fit = slope * Tc_fit + intercept
    ax.plot(Tc_fit, B_fit, "--", label="Linear fit")
    ax.axvline(Tc_intersection, color="k", linestyle=":", label=rf"$T_{{cut}}$ = {Tc_intersection:.2f} K")

    ax.set_xlabel(r"critical temperature, $T_c$ (K)")
    ax.set_ylabel(r"magnetic field, $B$ (T)")
    ax.set_title(sample_id)
    ax.legend()

    fig.tight_layout()
    fig.savefig(Path(outdir) / "Bc2_vs_Tc.png", dpi=300)
    plt.close(fig)

def main(sample_id, dir_path, channel, dimensions,
         approximate_B_c2=False, sc_criterion=0.9, T_normal=40):

    # print(f"Analyzing {sample_id}.")

    w, l, d = dimensions
    n_squares = l / w

    df = import_dat_files(dir_path, channel=channel)
    df["R"] /= n_squares
    df.to_csv(Path(dir_path) / "RvsTvsB.csv", index=False)

    results = []
    Rsheet = np.nan
    Tc0 = np.nan

    for n, df_sub in df.groupby("n"):
        B_mean = df_sub["B"].mean()

        if n == 0:
            df_sub.to_csv(Path(dir_path) / "RvsT.csv", index=False)
            Rsheet = find_Rnormal(df_sub["R"], df_sub["T"], T_normal=T_normal)

        RTc = Rsheet * sc_criterion if np.isfinite(Rsheet) else np.nan
        Tc = find_Tc(RTc, df_sub["R"], df_sub["T"])

        if n == 0:
            Tc0 = Tc

        results.append({"n": n, "B": B_mean, "Tc": Tc})

    df_results = pd.DataFrame(results)
    df_results.to_csv(Path(dir_path) / "Bc2vsTc.csv", index=False)

    plot_R_vs_T(df, df_results, sample_id, Rsheet, sc_criterion, dir_path)

    try:
        coeffs, Tc_inter = fit_BTc(df_results["Tc"], df_results["B"])
        plot_B_vs_Tc(df_results, coeffs, Tc_inter, sample_id, dir_path)
        Bc20 = coeffs[1] * WHH_FACTOR
        dBc2_dT = -coeffs[0]
    except Exception:
        Bc20 = np.nan
        dBc2_dT = np.nan

    rho_n = find_rho_n(Rsheet, d)
    D_e = find_D_e(dBc2_dT)
    Delta_0 = find_Delta_0(Tc0)
    xi_0 = find_xi_0(Bc20)
    N_0 = find_N_0(rho_n, D_e)
    lambda_0 = find_lambda_0(rho_n, Delta_0)
    L_k = find_L_k(Rsheet, Delta_0)

    params = SCParameters(
        Sample=sample_id,
        Bc20=Bc20,
        Tc=Tc0,
        Rsheet=Rsheet,
        d=d,
        dBc2_dT=dBc2_dT,
        rho_n=rho_n,
        D_e=D_e,
        Delta_0=Delta_0,
        xi_0=xi_0,
        N_0=N_0,
        lambda_0=lambda_0,
        L_k=L_k,
    )

    ### SI Units

    units = {
        'Sample': '-',
        'Bc20': 'T',
        'Tc': 'K',
        'Rsheet': 'Ohm/sq',
        'd': 'm',
        'dBc2_dT': 'T/K',
        'rho_n': 'Ohm*m',
        'D_e': 'm^2/s',
        'Delta_0': 'J',
        'xi_0': 'm',
        'N_0': '1/m^3',
        'lambda_0': 'm',
        'L_k': 'H/sq',
    }

    values = asdict(params)
    df_out_SI = pd.DataFrame([units, values])
    df_out_SI.to_csv(Path(dir_path) / "superconducting-parameter-extraction-SI.csv", index=False)

    ### Customary Units

    params_display = {
        'Sample': sample_id,
        'Bc20': Bc20,                 # T
        'Tc': Tc0,                    # K
        'Rsheet': Rsheet,             # Ohm/sq
        'd': d * 1e9,                 # m -> nm
        'dBc2_dT': dBc2_dT,           # T/K
        'rho_n': rho_n,               # Ohm*m
        'D_e': D_e * 1e4,             # m^2/s -> cm^2/s
        'Delta_0': Delta_0,           # J
        'xi_0': xi_0 * 1e9,           # m -> nm
        'N_0': N_0 / 1e6,             # 1/m^3 -> 1/cm^3
        'lambda_0': lambda_0 * 1e9,   # m -> nm
        'L_k': L_k * 1e9,             # H/sq -> nH/sq
    }

    units = {
        'Sample': '-',
        'Bc20': 'T',
        'Tc': 'K',
        'Rsheet': 'Ohm/sq',
        'd': 'nm',
        'dBc2_dT': 'T/K',
        'rho_n': 'Ohm*m',
        'D_e': 'cm^2/s',
        'Delta_0': 'J',
        'xi_0': 'nm',
        'N_0': '1/cm^3',
        'lambda_0': 'nm',
        'L_k': 'nH/sq',
    }

    df_out = pd.DataFrame([units, params_display])
    df_out.to_csv(Path(dir_path) / "superconducting-parameter-extraction-results.csv", index=False)

    # df_out = df_out.map(lambda x: f"{x:.3g}" if isinstance(x, (int, float)) else x)
    # markdown_table = df_out.to_markdown(index=False)
    # print()
    # print(markdown_table)

    return df_out_SI, df_out


if __name__ == "__main__":
    main(
        sample_id="RAC017",
        dir_path="RAC017/",
        channel=2,
        dimensions=(50e-6, 1e-3, 7e-9), # m
        T_normal=40 # K
    )