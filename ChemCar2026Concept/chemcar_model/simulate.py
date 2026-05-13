"""
simulate.py
Hauptsimulation des ChemCar Mehrfachhubsystems.

ARCHITEKTUR: Stroke-by-Stroke Integration mit Event Detection.

Da die Richtungsumschaltung diskret ist (T-Flipflop + Button), wird sie
NICHT in der ODE modelliert. Stattdessen:

  Loop:
    1. solve_ivp starten mit aktueller direction (+1 oder -1)
    2. Bis Event: Piston-Ende oder Citric Exhausted
    3. Event verarbeiten:
       - Piston-Ende: direction toggle, y0 aktualisieren, t umsetzen
       - Citric Exhausted: Simulation beenden
    4. Repeat

DIESER ANSATZ IST NOTWENDIG, WEIL:
  - Richtung ist ein diskretes Signal, keine kontinuierliche Variable
  - BDF-Jacobian bricht bei diskreten Sprüngen in den Ableitungen
  - Event-basierte Umschaltung ist numerisch stabil und physikalisch korrekt

AUFRUF:
    python simulate.py [--plot] [--time N]
    
    --plot  : Plots generieren und als PNG speichern (optional)
    --time N: Maximale Simulationszeit in Sekunden (default: 600)

ERGEBNISSE:
    chemcar_results.npz   : NumPy-Array mit allen Zeitreihen
    chemcar_results.csv   : CSV-Export für Excel/Analyse
    chemcar_plots.png     : 4 Plots (wenn --plot verwendet)
"""

import numpy as np
from scipy import integrate
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from config import *
from odesystem import chemcar_odes, get_initial_state, piston_at_end_forward, piston_at_end_reverse, citric_exhausted, get_exhaust_volume_L


# ============================================================================
# SIMULATION
# ============================================================================


def simulate(t_max=SIMULATION_TIME_MAX, plot=False):
    """
    Führt die vollständige Simulation durch.
    
    Parameter:
        t_max:  Maximale Simulationszeit in Sekunden
        plot:   Plots generieren?
    
    Rueckgabe:
        t_all:  Gesamt-Zeitarray (s)
        y_all:  Gesamt-Zustandsarray (n x 8)
    """
    # Initialzustand
    y = get_initial_state()
    t = 0.0
    direction = 1  # +1 = nach rechts, -1 = nach links
    stroke_count = 0
    t_global = 0.0
    
    # Speicher
    t_all = []
    y_all = []
    direction_at_t = []
    
    print("=" * 65)
    print("  CHEMCAR MEHRFACHHUBSYSTEM — SIMULATION")
    print("=" * 65)
    print(f"  Start-Zitronensaure:    {y[0] * CITRIC_ACID_MOLAR_MASS:.4f} g")
    print(f"  Start-Kolbenposition:   {y[1]*100:.1f} cm ({y[1]/ROD_LENGTH_M*100:.0f}% des Hubs)")
    print(f"  Hubweg pro Stroke:      {ROD_LENGTH_M*100:.0f} cm")
    print(f"  Max Simulationszeit:    {t_max:.0f} s")
    print(f"  Feder-Schwelle:         {SPRING_PRELOAD_BAR} bar")
    print(f"  Regulator-Ausgang:      {REGULATOR_OUTPUT_BAR} bar")
    print(f"  Relief Valve Set-Point: {RELIEF_VALVE_SET_BAR} bar")
    print("-" * 65)
    
    max_strokes = 500  # Safety limit
    
    # --- Hauptschleife: Stroke fuer Stroke ---
    while stroke_count < max_strokes and t_global < t_max:
        # Events fuer diesen Stroke (nur das richtungs-passende aktiv)
        if direction > 0:
            events = [piston_at_end_forward, citric_exhausted]
            event_forward = True
        else:
            events = [piston_at_end_reverse, citric_exhausted]
            event_forward = False
        
        # Integration
        t_span = (t, min(t + 30000.0, t_max - t_global))
        
        sol = integrate.solve_ivp(
            fun=lambda t, y: chemcar_odes(t, y, direction),
            t_span=t_span,
            y0=list(y),
            method='Radau',
            events=events,
            rtol=1e-6,
            atol=1e-8,
            max_step=0.005,
        )
        
        # Ergebnisse speichern
        if sol.t.size > 1:
            V_headspace = REACTOR_VOLUME_L * REACTOR_HEADSPACE_RATIO
            P = (sol.y[5, :] + sol.y[7]) * GAS_CONSTANT_BAR_L * TEMPERATURE_K / V_headspace
            
            t_all.extend(sol.t.tolist())
            y_all.append(sol.y.T)
            direction_at_t.extend([direction] * len(sol.t))
        
        # Event prüfen
        if sol.t_events[0].size > 0 and event_forward:
            # rechtes Ende erreicht → toggle zu -1 (links)
            y = sol.y[:, -1]
            t = sol.t[-1]
            t_global = t
            direction = -1
            V_new_exhaust_L = y[1] * PISTON_AREA_M2 * 1000.0
            y[8] = 1.0 * V_new_exhaust_L / (GAS_CONSTANT_BAR_L * TEMPERATURE_K)
            stroke_count += 1
            print(f"  Stroke {stroke_count}: Kolben -> LINKS (x = {y[1]*100:.1f} cm)")
            
        elif sol.t_events[0].size > 0 and not event_forward:
            # linkes Ende erreicht → toggle zu +1 (rechts)
            y = sol.y[:, -1]
            t = sol.t[-1]
            t_global = t
            direction = +1
            V_new_exhaust_L = (ROD_LENGTH_M - y[1]) * PISTON_AREA_M2 * 1000.0
            y[8] = 1.0 * V_new_exhaust_L / (GAS_CONSTANT_BAR_L * TEMPERATURE_K)
            stroke_count += 1
            print(f"  Stroke {stroke_count}: Kolben -> RECHTS (x = {y[1]*100:.1f} cm)")
            
        elif sol.t_events[1].size > 0:
            y = sol.y[:, -1]
            t = sol.t[-1]
            t_global = t
            stroke_count += 1
            citric_remaining = y[0] * CITRIC_ACID_MOLAR_MASS
            print(f"\n  [ERFOG] Zitronensäure aufgebraucht nach {stroke_count} Hueben!")
            print(f"  Rest: {citric_remaining:.4f} g")
            
        else:
            if sol.status == 0:
                y = sol.y[:, -1]
                t = sol.t[-1]
                t_global = t
                direction *= -1
                # Neue Auslass-Kammer = alte Versorgung (2 bar)
                if direction > 0:
                    V_new_exhaust_L = (ROD_LENGTH_M - y[1]) * PISTON_AREA_M2 * 1000.0
                else:
                    V_new_exhaust_L = y[1] * PISTON_AREA_M2 * 1000.0
                y[8] = 1.0 * V_new_exhaust_L / (GAS_CONSTANT_BAR_L * TEMPERATURE_K)
                stroke_count += 1
            else:
                print(f"\n  [WARN] Integration fehlgeschlagen (status={sol.status})")
                break
        
        # Freilauf-Bremse: Wenn Kolben steht, bremst das Fahrzeug ab
        # Modelliert: Lagerreibung, Getriebeverluste, mechanische Dämpfung
        if y[4] > 0.001:
            brake_decel = (FREEWHEEL_BRAKE_FORCE_N + VEHICLE_ROLLING_RESISTANCE * VEHICLE_MASS_KG * 9.81) / VEHICLE_MASS_KG
            # Bremszeit bis zum Stillstand
            t_stop = y[4] / brake_decel
            # Aggressivere Dämpfung: Fahrzeug kommt zwischen Huben fast zum Stillstand
            decay_factor = np.exp(-min(t_stop, 3.0) / max(t_stop * 0.5, 0.05))
            y[4] *= decay_factor
            if y[4] < 0.001:
                y[4] = 0.0
        
        # Safety clamp: Kolbenposition innerhalb des Zylinders halten
        y[1] = np.clip(y[1], 0.0, ROD_LENGTH_M)
        
        # Backwards detection: terminate if vehicle speed is significantly negative
        if y[4] < -0.01:
            print(f"\n  [WARN] Fahrzeuggeschwindigkeit negativ ({y[4]:.2f} m/s) — Simulation abgebrochen.")
            break
        
        # Coast-to-stop: nach Zitronensäure-Verbrauch warten bis Fahrzeug steht
        if y[0] < 1e-10 and abs(y[4]) < 0.01:
            print(f"\n  [ENDE] Zitronensäure verbraucht, Fahrzeug steht. {stroke_count} Hübe abgeschlossen.")
            break
        
        # Safety: Breche ab wenn Druck zu niedrig oder Pistenv steht
        V_headspace = REACTOR_VOLUME_L * REACTOR_HEADSPACE_RATIO
        P_current = (y[5] + y[7]) * GAS_CONSTANT_BAR_L * TEMPERATURE_K / V_headspace if V_headspace > 0 else 0
        
        if P_current < 1.1 and y[0] > 1e-10:
            print(f"\n  [WARN] Reaktor-Druck ({P_current:.2f} bar) unter Feder-Schwelle")
            print(f"  Kolben bewegt sich nicht mehr. {stroke_count} Hübe abgeschlossen.")
            break
    
    # --- Ergebnis zusammenfuegen ---
    if y_all:
        y_all_concat = np.concatenate(y_all, axis=0)
        t_all = np.array(t_all)
    else:
        y_all_concat = np.array([y])
        t_all = np.array([t_global])
    
    # --- Zusammenfassung ---
    final = y_all_concat[-1]
    P_final = (final[5] + final[7]) * GAS_CONSTANT_BAR_L * TEMPERATURE_K / (REACTOR_VOLUME_L * REACTOR_HEADSPACE_RATIO)
    
    print(f"\n  Simulation beendet nach {len(t_all):,} Zeitschritten.")
    print(f"\n  === ERGEBNISZUSAMMENFASSUNG ===")
    print(f"  Gesamtdistanz:        {final[3]:.2f} m")
    print(f"  Simulationszeit:       {t_global:.1f} s")
    print(f"  End-Druck:             {P_final:.2f} bar")
    print(f"  Rest-Zitronensäure:    {final[0] * CITRIC_ACID_MOLAR_MASS:.4f} g")
    print(f"  Anzahl Hübe:           {stroke_count}")
    print(f"  Avg. Zeit pro Hub:     {t_global / max(stroke_count, 1):.2f} s")
    print(f"  Avg. Geschwindigkeit:  {final[3] / max(t_global, 0.001):.3f} m/s")
    
    # Theoretischer Vergleich
    theoretical_co2_mol = y_all_concat[0, 0] * STOICH_CO2_PER_CITRIC
    theoretical_volume_L = theoretical_co2_mol * GAS_CONSTANT_BAR_L * TEMPERATURE_K / REGULATOR_OUTPUT_BAR
    theoretical_distance = theoretical_co2_mol * 0.157
    
    print(f"\n  [THEORETISCH] (ohne Verluste, alle Edukte verbraucht)")
    print(f"  Theoretisches CO2:    ~{theoretical_co2_mol:.2f} mol")
    print(f"  Theoretisches Vol.:   ~{theoretical_volume_L:.1f} L bei {REGULATOR_OUTPUT_BAR} bar")
    print(f"  Theoretische Distanz: ~{theoretical_distance:.1f} m")
    
    print("=" * 65)
    
    # Plots
    if plot and len(t_all) > 1:
        V_headspace = REACTOR_VOLUME_L * REACTOR_HEADSPACE_RATIO
        P_reactor = (y_all_concat[:, 5] + y_all_concat[:, 7]) * GAS_CONSTANT_BAR_L * TEMPERATURE_K / V_headspace
        
        P_exhaust = np.zeros(len(t_all))
        for i in range(len(t_all)):
            d = direction_at_t[i] if i < len(direction_at_t) else direction
            P_exhaust[i] = y_all_concat[i, 8] * GAS_CONSTANT_BAR_L * TEMPERATURE_K / max(get_exhaust_volume_L(y_all_concat[i, 1], d), 0.001)
        plot_results(t_all, y_all_concat, P_exhaust)
    
    return np.array(t_all), y_all_concat


# ============================================================================
# PLOTTING
# ============================================================================


def plot_results(t, y, P_exhaust):
    """
    Erzeugt 4 Plots und speichert als PNG.
    
    y columns (9 Zustandsvariablen):
        [0] n_citric_mol
        [1] x_piston_m
        [2] v_piston_m_s
        [3] s_vehicle_m
        [4] v_vehicle_m_s
        [5] n_co2_gas_mol
        [6] n_co2_dissolved_mol
        [7] n_air_mol
        [8] n_exhaust_mol
    """
    V_headspace = REACTOR_VOLUME_L * REACTOR_HEADSPACE_RATIO
    P_reactor = (y[:, 5] + y[:, 7]) * GAS_CONSTANT_BAR_L * TEMPERATURE_K / V_headspace
    
    fig, axes = plt.subplots(5, 1, figsize=(14, 20), sharex=True)
    fig.suptitle('ChemCar Mehrfachhubsystem — Simulationsergebnis', fontsize=14, fontweight='bold')
    
    # Plot 1: Zitronensäure + CO2
    ax1 = axes[0]
    ax1.plot(t, y[:, 0] * CITRIC_ACID_MOLAR_MASS, 'b-', linewidth=1.5, label='Zitronensäure (g)')
    ax1.plot(t, y[:, 5] * CO2_MOLAR_MASS, 'r--', linewidth=1.5, label='CO2 (Gas, g)')
    ax1.plot(t, y[:, 6] * CO2_MOLAR_MASS, 'orange', linewidth=1.5, label='CO2 (gelöst, g)')
    ax1.set_ylabel('Masse [g]')
    ax1.set_title('Chemische Reaktionen')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Reaktor-Druck
    ax2 = axes[1]
    ax2.plot(t, P_reactor, 'purple', linewidth=1.5)
    ax2.axhline(y=SPRING_PRELOAD_BAR, color='red', linestyle='--', linewidth=1, label=f'Feder-Schwelle ({SPRING_PRELOAD_BAR} bar)')
    ax2.axhline(y=REGULATOR_OUTPUT_BAR, color='blue', linestyle='--', linewidth=1, label=f'Regulator ({REGULATOR_OUTPUT_BAR} bar)')
    ax2.axhline(y=RELIEF_VALVE_SET_BAR, color='darkred', linestyle='-.', linewidth=1.5, label=f'Relief Valve ({RELIEF_VALVE_SET_BAR} bar)')
    ax2.set_ylabel('Druck [bar]')
    ax2.set_title('Reaktor-Druck')
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Auslass-Kammer Druck
    ax3 = axes[2]
    ax3.plot(t, P_exhaust, 'c-', linewidth=1.5, label='P_Auslass')
    ax3.axhline(y=1.0, color='gray', linestyle=':', linewidth=1, label='Ambient (1 bar)')
    ax3.set_ylabel('Druck [bar]')
    ax3.set_title('Auslass-Kammer Druck')
    ax3.legend(loc='upper right', fontsize=9)
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Kolbenposition + Geschwindigkeit
    ax4 = axes[3]
    ax4.plot(t, y[:, 1] * 100, 'b-', linewidth=1.5, label='Kolbenposition')
    ax4.plot(t, y[:, 2] * 100, 'r-', linewidth=1, alpha=0.7, label='Kolbengeschw.')
    ax4.axhline(y=ROD_LENGTH_M * 100, color='gray', linestyle=':', linewidth=1)
    ax4.axhline(y=0, color='gray', linestyle=':', linewidth=1)
    ax4.set_ylabel('Position [cm] / Geschw. [cm/s]')
    ax4.set_title('Pneumatik-Zylinder')
    ax4.legend(loc='upper right', fontsize=9)
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: Fahrzeugdistanz + Geschwindigkeit
    ax5 = axes[4]
    ax5.plot(t, y[:, 3], 'g-', linewidth=2, label='Fahrzeugdistanz')
    ax5.plot(t, y[:, 4] * 100, 'orange', linewidth=1, alpha=0.7, label='Fahrzeuggeschw. [cm/s]')
    ax5.set_xlabel('Zeit [s]')
    ax5.set_ylabel('Distanz [m] / Geschw. [cm/s]')
    ax5.set_title('Fahrzeugbewegung')
    ax5.legend(loc='upper right', fontsize=9)
    ax5.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    output_path = os.path.join(os.path.dirname(__file__), 'chemcar_plots.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nPlots gespeichert: {output_path}")
    plt.close()


# ============================================================================
# EXPORT
# ============================================================================


def save_results(t, y, filename='chemcar_results'):
    """Speichert Ergebnisse als .npz und .csv."""
    V_headspace = REACTOR_VOLUME_L * REACTOR_HEADSPACE_RATIO
    P_reactor = (y[:, 5] + y[:, 7]) * GAS_CONSTANT_BAR_L * TEMPERATURE_K / V_headspace
    
    P_exhaust = np.zeros(len(t))
    for i in range(len(t)):
        d = 1 if y[i, 2] >= 0 else -1
        P_exhaust[i] = y[i, 8] * GAS_CONSTANT_BAR_L * TEMPERATURE_K / max(get_exhaust_volume_L(y[i, 1], d), 0.001)
    
    data = {
        'time_s': t,
        'n_citric_g': y[:, 0] * CITRIC_ACID_MOLAR_MASS,
        'x_piston_cm': y[:, 1] * 100,
        'v_piston_cm_s': y[:, 2] * 100,
        's_vehicle_m': y[:, 3],
        'v_vehicle_cm_s': y[:, 4] * 100,
        'n_co2_gas_mol': y[:, 5],
        'n_co2_dissolved_mol': y[:, 6],
        'P_reactor_bar': P_reactor,
        'P_exhaust_bar': P_exhaust,
        'n_air_mol': y[:, 7],
        'n_exhaust_mol': y[:, 8],
    }
    npz_path = os.path.join(os.path.dirname(__file__), filename + '.npz')
    np.savez(npz_path, **data)
    print(f"Ergebnisse (.npz): {npz_path}")
    
    csv_path = os.path.join(os.path.dirname(__file__), filename + '.csv')
    with open(csv_path, 'w') as f:
        f.write('time_s,n_citric_g,x_piston_cm,v_piston_cm_s,s_vehicle_m,v_vehicle_cm_s,n_co2_gas_mol,n_co2_dissolved_mol,P_reactor_bar,P_exhaust_bar,n_air_mol,n_exhaust_mol\n')
        for i in range(len(t)):
            f.write(f'{t[i]:.6f},{y[i,0]*CITRIC_ACID_MOLAR_MASS:.6f},{y[i,1]*100:.6f},{y[i,2]*100:.6f},{y[i,3]:.6f},{y[i,4]*100:.6f},{y[i,5]:.8f},{y[i,6]:.8f},{P_reactor[i]:.4f},{P_exhaust[i]:.4f},{y[i,7]:.8f},{y[i,8]:.8f}\n')
    print(f"Ergebnisse (.csv): {csv_path}")


# ============================================================================
# MAIN
# ============================================================================


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='ChemCar Mehrfachhubsystem Simulation')
    parser.add_argument('--plot', action='store_true', help='Plots generieren')
    parser.add_argument('--time', type=float, default=SIMULATION_TIME_MAX, help='Max Simulationszeit (s)')
    args = parser.parse_args()
    
    t, y = simulate(t_max=args.time, plot=args.plot)
    save_results(t, y)
