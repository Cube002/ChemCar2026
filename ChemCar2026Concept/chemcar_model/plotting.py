"""
plotting.py
Comprehensive plotting for the ChemCar simulation.

Usage:
    from plotting import plot_results
    plot_results(t, y, direction_at_t, show=False)
"""

import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from config import *
from odesystem import get_exhaust_volume_L, get_tank_pressure, get_drip_rate_mol_per_s


def compute_derived(t, y, direction_at_t=None):
    V_headspace = REACTOR_VOLUME_L * REACTOR_HEADSPACE_RATIO
    P_reactor = (y[:, 5] + y[:, 7]) * GAS_CONSTANT_BAR_L * TEMPERATURE_K / V_headspace

    if direction_at_t is not None:
        direction_arr = np.array(direction_at_t)
    else:
        direction_arr = np.where(y[:, 2] >= 0, 1, -1)

    P_exhaust = np.zeros(len(t))
    for i in range(len(t)):
        V = max(get_exhaust_volume_L(y[i, 1], direction_arr[i]), 0.001)
        P_exhaust[i] = y[i, 8] * GAS_CONSTANT_BAR_L * TEMPERATURE_K / V

    P_supply = np.minimum(P_reactor, REGULATOR_OUTPUT_BAR)

    mass_fraction_initial = (CITRIC_ACID_CONCENTRATION_G_PER_L * CITRIC_TANK_VOLUME_L) / (CITRIC_SOLUTION_MASS_KG * 1000.0)
    P_tank = np.zeros(len(t))
    for i in range(len(t)):
        if y[i, 0] > 0:
            m_solution_kg = (y[i, 0] * CITRIC_ACID_MOLAR_MASS / 1000.0) / mass_fraction_initial
            P_tank[i] = get_tank_pressure(m_solution_kg)
        else:
            P_tank[i] = 1.0

    drip = np.zeros(len(t))
    for i in range(len(t)):
        drip[i] = get_drip_rate_mol_per_s(y[i, 0], P_reactor[i])

    n_consumed = np.maximum(y[0, 0] - y[:, 0], 1e-10)
    co2_yield = y[:, 5] + y[:, 6]
    co2_efficiency = np.where(n_consumed > 1e-10, co2_yield / (n_consumed * STOICH_CO2_PER_CITRIC) * 100, 0)
    co2_efficiency[0] = 0

    return P_reactor, P_exhaust, P_supply, P_tank, drip, direction_arr, co2_efficiency


def plot_results(t, y, direction_at_t=None, output_dir=None, show=False):
    if not show:
        import matplotlib
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    P_reactor, P_exhaust, P_supply, P_tank, drip, direction_arr, co2_eff = compute_derived(t, y, direction_at_t)

    n_cols = 3
    n_rows = 3

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 12))
    fig.suptitle('ChemCar Mehrfachhubsystem — Simulationsergebnis', fontsize=14, fontweight='bold')

    # ----- Row 0: Chemistry -----
    # (0,0) Chemical masses
    ax = axes[0, 0]
    ax.plot(t, y[:, 0] * CITRIC_ACID_MOLAR_MASS, 'b-', lw=1.5, label='Zitronensäure (g)')
    ax.plot(t, y[:, 5] * CO2_MOLAR_MASS, 'r--', lw=1.5, label='CO₂ Gas (g)')
    ax.plot(t, y[:, 6] * CO2_MOLAR_MASS, 'orange', lw=1.5, label='CO₂ gelöst (g)')
    ax.set_ylabel('Masse [g]')
    ax.set_title('Chemische Reaktionen')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # (0,1) Total CO₂ balance
    ax = axes[0, 1]
    total_co2_mol = y[:, 5] + y[:, 6]
    ax.plot(t, total_co2_mol, 'g-', lw=2, label='CO₂ gesamt (mol)')
    ax.plot(t, y[:, 8], 'm-', lw=1, label='n_exhaust (mol)')
    max_co2_mol = y[0, 0] * STOICH_CO2_PER_CITRIC
    ax.axhline(y=max_co2_mol, color='gray', ls=':', lw=1, label=f'Theor. max ({max_co2_mol:.2f} mol)')
    ax.set_ylabel('Mol')
    ax.set_title('CO₂-Bilanz')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # (0,2) CO₂ efficiency & drip rate
    ax = axes[0, 2]
    ax2 = ax.twinx()
    ax.plot(t, drip * 1000, 'b-', lw=1.5, label='Tropfrate (mmol/s)')
    ax2.plot(t, co2_eff, 'g--', lw=1.5, label='CO₂-Ausbeute (%)')
    ax.set_ylabel('Tropfrate [mmol/s]')
    ax2.set_ylabel('CO₂-Ausbeute [%]')
    ax.set_title('Zufuhr & Effizienz')
    l1, la1 = ax.get_legend_handles_labels()
    l2, la2 = ax2.get_legend_handles_labels()
    ax.legend(l1 + l2, la1 + la2, fontsize=8, loc='center right')
    ax.grid(True, alpha=0.3)

    # ----- Row 1: Pressures -----
    # (1,0) Reactor pressure
    ax = axes[1, 0]
    ax.plot(t, P_reactor, 'purple', lw=1.5, label='P_Reaktor')
    ax.axhline(y=SPRING_PRELOAD_BAR, color='red', ls='--', lw=1, label=f'Feder ({SPRING_PRELOAD_BAR} bar)')
    ax.axhline(y=REGULATOR_OUTPUT_BAR, color='blue', ls='--', lw=1, label=f'Regler ({REGULATOR_OUTPUT_BAR} bar)')
    ax.axhline(y=RELIEF_VALVE_SET_BAR, color='darkred', ls='-.', lw=1.5, label=f'Relief ({RELIEF_VALVE_SET_BAR} bar)')
    ax.set_ylabel('Druck [bar]')
    ax.set_title('Reaktor-Druck')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # (1,1) Exhaust pressure
    ax = axes[1, 1]
    ax.plot(t, P_exhaust, 'c-', lw=1.5, label='P_Auslass')
    ax.axhline(y=1.0, color='gray', ls=':', lw=1, label='Ambient (1 bar)')
    ax.set_ylabel('Druck [bar]')
    ax.set_title('Auslass-Kammer Druck')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # (1,2) Supply & Tank pressure
    ax = axes[1, 2]
    ax.plot(t, P_supply, 'green', lw=1.5, label='P_Versorgung (Regler out)')
    ax.plot(t, P_tank, 'brown', lw=1, ls='--', label='P_Tank (Citric)')
    ax.axhline(y=TANK_INITIAL_PRESSURE_BAR, color='brown', ls=':', lw=1, alpha=0.5, label=f'Tank Start ({TANK_INITIAL_PRESSURE_BAR} bar)')
    ax.set_ylabel('Druck [bar]')
    ax.set_title('Versorgungs-Drücke')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # ----- Row 2: Mechanics -----
    # (2,0) Piston
    ax = axes[2, 0]
    ax.plot(t, y[:, 1] * 100, 'b-', lw=1.5, label='Position (cm)')
    ax2 = ax.twinx()
    ax2.plot(t, y[:, 2] * 100, 'r-', lw=1, alpha=0.7, label='Geschw. (cm/s)')
    ax.axhline(y=ROD_LENGTH_M * 100, color='gray', ls=':', lw=1)
    ax.axhline(y=0, color='gray', ls=':', lw=1)
    ax.set_ylabel('Position [cm]')
    ax2.set_ylabel('Geschw. [cm/s]')
    ax.set_title('Pneumatik-Zylinder')
    l1, la1 = ax.get_legend_handles_labels()
    l2, la2 = ax2.get_legend_handles_labels()
    ax.legend(l1 + l2, la1 + la2, fontsize=8, loc='upper right')
    ax.grid(True, alpha=0.3)

    # (2,1) Vehicle
    ax = axes[2, 1]
    ax.plot(t, y[:, 3], 'g-', lw=2, label='Distanz (m)')
    ax2 = ax.twinx()
    ax2.plot(t, y[:, 4] * 100, 'orange', lw=1, alpha=0.7, label='Geschw. (cm/s)')
    ax.set_ylabel('Distanz [m]')
    ax2.set_ylabel('Geschw. [cm/s]')
    ax.set_title('Fahrzeugbewegung')
    l1, la1 = ax.get_legend_handles_labels()
    l2, la2 = ax2.get_legend_handles_labels()
    ax.legend(l1 + l2, la1 + la2, fontsize=8, loc='upper left')
    ax.grid(True, alpha=0.3)

    # (2,2) Stroke counter & piston endpoint detail
    ax = axes[2, 2]
    dir_changes = np.diff(direction_arr, prepend=direction_arr[0])
    stroke_num = np.cumsum(np.abs(dir_changes) > 0)
    ax.plot(t, stroke_num, 'k-', lw=1, label='Hub-Nummer')
    ax.set_ylabel('Hub-Nummer')
    ax.set_title('Kolben-Hübe')
    ax.set_xlabel('Zeit [s]')
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(True, alpha=0.3)
    # overlay piston endpoint touches
    near_right = (y[:, 1] > ROD_LENGTH_M - 0.005).astype(int)
    near_left = (y[:, 1] < 0.005).astype(int)
    ax.fill_between(t, 0, near_right * stroke_num.max(), alpha=0.15, color='green', label='Rechts')
    ax.fill_between(t, 0, near_left * stroke_num.max(), alpha=0.15, color='red', label='Links')
    ax.legend(fontsize=8, loc='upper left')

    plt.tight_layout()

    output_dir = output_dir or os.path.dirname(__file__)
    png_path = os.path.join(output_dir, 'chemcar_plots.png')
    pdf_path = os.path.join(output_dir, 'chemcar_plots.pdf')
    fig.savefig(png_path, dpi=150, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    print(f"PNG: {png_path}")
    print(f"PDF: {pdf_path}")

    if show:
        plt.show()
    else:
        plt.close(fig)
