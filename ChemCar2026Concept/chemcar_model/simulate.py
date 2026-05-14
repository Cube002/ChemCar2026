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
    
    --plot  : Plots generieren und anzeigen, speichert PNG + PDF (optional)
    --time N: Maximale Simulationszeit in Sekunden (default: 600)

ERGEBNISSE:
    chemcar_results.npz   : NumPy-Array mit allen Zeitreihen
    chemcar_results.csv   : CSV-Export für Excel/Analyse
    chemcar_plots.png     : Übersichts-Plots (wenn --plot verwendet)
    chemcar_plots.pdf     : Vektorgrafik zum Zoomen (wenn --plot verwendet)
"""

import numpy as np
from scipy import integrate
import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(__file__))
from config import *
from odesystem import chemcar_odes, get_initial_state, piston_at_end_forward, piston_at_end_reverse, citric_exhausted, get_exhaust_volume_L, get_reactor_pressure, get_reactor_headspace_L
from plotting import plot_results


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
    citric_depleted = False
    
    # --- Hauptschleife: Stroke fuer Stroke ---
    while stroke_count < max_strokes and t_global < t_max:
        # Events: nach Citric-Exhaustion nur noch Piston-End-Events (citric ist terminal)
        if citric_depleted:
            events = [piston_at_end_forward] if direction > 0 else [piston_at_end_reverse]
        else:
            events = [piston_at_end_forward, citric_exhausted] if direction > 0 else [piston_at_end_reverse, citric_exhausted]
        event_forward = direction > 0
        
        P_reactor_pre = get_reactor_pressure(y[5], y[7], y[0])
        P_exhaust_pre = y[8] * GAS_CONSTANT_BAR_L * TEMPERATURE_K / max(get_exhaust_volume_L(y[1], direction), 0.001)
        print(f"  [DBG] Hub {stroke_count+1}: dir={direction:+d}, x={y[1]*100:.2f}cm, v={y[2]*100:.4f}cm/s, P_react={P_reactor_pre:.2f}bar, P_exh={P_exhaust_pre:.2f}bar, n_exh={y[8]:.6f}mol")
        
        # Integration mit Fallback: BDF → Radau → LSODA
        t_span = (t, min(t + 20000.0, t_max))
        
        solver_configs = [
            {'method': 'BDF',   'rtol': 1e-6, 'atol': 1e-8, 'max_step': 0.01},
            {'method': 'Radau', 'rtol': 1e-5, 'atol': 1e-7, 'max_step': 0.05},
            {'method': 'LSODA', 'rtol': 1e-5, 'atol': 1e-7, 'max_step': 0.01},
        ]
        
        sol = None
        for cfg in solver_configs:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                sol = integrate.solve_ivp(
                    fun=lambda t, y: chemcar_odes(t, y, direction),
                    t_span=t_span,
                    y0=list(y),
                    events=events,
                    **cfg,
                )
            if sol.status != -1:
                break
        # If ALL solvers failed, retry BDF with very loose tolerance
        if sol.status == -1:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                sol = integrate.solve_ivp(
                    fun=lambda t, y: chemcar_odes(t, y, direction),
                    t_span=t_span,
                    y0=list(y),
                    method='BDF', events=events,
                    rtol=1e-3, atol=1e-4, max_step=0.1,
                )
        
        # Ergebnisse speichern
        if sol.t.size > 1:
            t_all.extend(sol.t.tolist())
            y_all.append(sol.y.T)
            direction_at_t.extend([direction] * len(sol.t))
        
        print(f"  [DBG]   -> status={sol.status}, steps={sol.t.size}, t_end={sol.t[-1]:.4f}s, x_end={sol.y[1,-1]*100:.2f}cm, v_end={sol.y[2,-1]*100:.4f}cm/s")
        if sol.t_events[0].size > 0:
            print(f"  [DBG]   -> Event[0] at t={sol.t_events[0][0]:.4f}s, x={sol.y_events[0][0][1]*100:.2f}cm")
        if len(sol.t_events) > 1 and sol.t_events[1].size > 0:
            print(f"  [DBG]   -> Event[1] (citric) at t={sol.t_events[1][0]:.4f}s")
        
        # Event prüfen
        if sol.t_events[0].size > 0 and event_forward:
            # rechtes Ende erreicht → toggle zu -1 (links)
            y = sol.y[:, -1].copy()
            t = sol.t[-1]
            t_global = t
            P_react_event = get_reactor_pressure(y[5], y[7], y[0])
            P_supply_event = REGULATOR_OUTPUT_BAR if P_react_event > REGULATOR_OUTPUT_BAR else P_react_event
            direction = -1
            V_new_exhaust_L = get_exhaust_volume_L(y[1], direction)
            y[8] = P_supply_event * V_new_exhaust_L / (GAS_CONSTANT_BAR_L * TEMPERATURE_K)
            stroke_count += 1
            print(f"  Stroke {stroke_count}: Kolben -> LINKS (x = {y[1]*100:.1f} cm)")
            
        elif sol.t_events[0].size > 0 and not event_forward:
            # linkes Ende erreicht → toggle zu +1 (rechts)
            y = sol.y[:, -1].copy()
            t = sol.t[-1]
            t_global = t
            P_react_event = get_reactor_pressure(y[5], y[7], y[0])
            P_supply_event = REGULATOR_OUTPUT_BAR if P_react_event > REGULATOR_OUTPUT_BAR else P_react_event
            direction = +1
            V_new_exhaust_L = get_exhaust_volume_L(y[1], direction)
            y[8] = P_supply_event * V_new_exhaust_L / (GAS_CONSTANT_BAR_L * TEMPERATURE_K)
            stroke_count += 1
            print(f"  Stroke {stroke_count}: Kolben -> RECHTS (x = {y[1]*100:.1f} cm)")
            
        elif not citric_depleted and len(sol.t_events) > 1 and sol.t_events[1].size > 0:
            y = sol.y[:, -1].copy()
            t = sol.t[-1]
            t_global = t
            P_react_now = get_reactor_pressure(y[5], y[7], y[0])
            citric_remaining = y[0] * CITRIC_ACID_MOLAR_MASS
            print(f"\n  [INFO] Zitronensäure aufgebraucht! Rest-Druck: {P_react_now:.2f} bar — treibt Kolben weiter.")
            print(f"  Rest: {citric_remaining:.4f} g")
            citric_depleted = True
            # KEIN break — Rest-Druck im Reaktor/Tank treibt weiter
            
        else:
            if sol.status == 0:
                y = sol.y[:, -1].copy()
                t = sol.t[-1]
                t_global = t
                P_react_event = get_reactor_pressure(y[5], y[7], y[0])
                P_supply_event = REGULATOR_OUTPUT_BAR if P_react_event > REGULATOR_OUTPUT_BAR else P_react_event
                direction *= -1
                V_new_exhaust_L = get_exhaust_volume_L(y[1], direction)
                y[8] = P_supply_event * V_new_exhaust_L / (GAS_CONSTANT_BAR_L * TEMPERATURE_K)
                stroke_count += 1
            else:
                print(f"\n  [WARN] Integration fehlgeschlagen (status={sol.status})")
                break
        
        # Freilauf-Bremse wird jetzt in der ODE modelliert (get_vehicle_acceleration).
        # Keine extra Bremskorrektur nötig.
        
        # Safety clamp: Kolbenposition innerhalb des Zylinders halten
        y[1] = np.clip(y[1], 0.0, ROD_LENGTH_M)
        
        # Backwards detection: terminate if vehicle speed is significantly negative
        if y[4] < -0.01:
            print(f"\n  [WARN] Fahrzeuggeschwindigkeit negativ ({y[4]:.2f} m/s) — Simulation abgebrochen.")
            break
        
        # Stopp: wenn Zitronensäure verbraucht UND Kolben hängt fest (sehr langsam über ganze Strecke)
        if citric_depleted and abs(y[2]) < 0.001 and abs(y[4]) < 0.001:
            print(f"\n  [ENDE] Zitronensäure/Tankdruck verbraucht, Kolben & Fahrzeug stehen. {stroke_count} Hübe abgeschlossen.")
            break
        
        # Stopp: Reaktor-Druck zu niedrig für Feder-Vorspannung
        P_current = get_reactor_pressure(y[5], y[7], y[0])
        
        if P_current < SPRING_PRELOAD_BAR:
            print(f"\n  [ENDE] Reaktor-Druck ({P_current:.2f} bar) unter Feder-Schwelle ({SPRING_PRELOAD_BAR} bar)")
            print(f"  Kolben kann Feder nicht mehr überwinden. {stroke_count} Hübe abgeschlossen.")
            break
    
    # --- Ende-Grund melden (falls kein break gefeuert hat) ---
    if t_global >= t_max:
        P_curr = get_reactor_pressure(y[5], y[7], y[0])
        print(f"\n  [ENDE] Zeitlimit ({t_max:.0f}s) erreicht. Druck: {P_curr:.2f} bar, {y[0]*CITRIC_ACID_MOLAR_MASS:.1f}g Citric übrig.")
        print(f"  {stroke_count} Hübe abgeschlossen.")
    elif stroke_count >= max_strokes:
        print(f"\n  [ENDE] Maximalhübe ({max_strokes}) erreicht.")
    
    # --- Ergebnis zusammenfuegen ---
    if y_all:
        y_all_concat = np.concatenate(y_all, axis=0)
        t_all = np.array(t_all)
        dir_arr = np.array(direction_at_t)
    else:
        y_all_concat = np.array([y])
        t_all = np.array([t_global])
        dir_arr = np.array([direction])
    
    # --- Zusammenfassung ---
    final = y_all_concat[-1]
    P_final = get_reactor_pressure(final[5], final[7], final[0])
    
    print(f"\n  Simulation beendet nach {len(t_all):,} Zeitschritten.")
    print(f"\n  === ERGEBNISZUSAMMENFASSUNG ===")
    print(f"  Gesamtdistanz:        {final[3]:.2f} m")
    print(f"  Simulationszeit:       {t_global:.1f} s")
    print(f"  End-Druck:             {P_final:.2f} bar")
    print(f"  Rest-Zitronensäure:    {final[0] * CITRIC_ACID_MOLAR_MASS:.4f} g")
    print(f"  Anzahl Hübe:           {stroke_count}")
    print(f"  Avg. Zeit pro Hub:     {t_global / max(stroke_count, 1):.2f} s")
    print(f"  Avg. Geschwindigkeit:  {final[3] / max(t_global, 0.001):.3f} m/s")
    
    # Theoretischer Vergleich (inkl. Tank-Gas-Nachströmung)
    theoretical_co2_mol = y_all_concat[0, 0] * STOICH_CO2_PER_CITRIC + y_all_concat[0, 9]
    theoretical_volume_L = theoretical_co2_mol * GAS_CONSTANT_BAR_L * TEMPERATURE_K / REGULATOR_OUTPUT_BAR
    liters_per_meter = PISTON_AREA_M2 * 1000.0
    theoretical_distance = theoretical_volume_L / liters_per_meter
    
    print(f"\n  [THEORETISCH] (ohne Verluste, alle Edukte verbraucht)")
    print(f"  Aus Citric-Reaktion: ~{y_all_concat[0, 0] * STOICH_CO2_PER_CITRIC:.2f} mol")
    print(f"  Aus Tank-Gasraum:    ~{y_all_concat[0, 9]:.2f} mol")
    print(f"  Theoretisches CO2:   ~{theoretical_co2_mol:.2f} mol")
    print(f"  Theoretisches Vol.:   ~{theoretical_volume_L:.1f} L bei {REGULATOR_OUTPUT_BAR} bar")
    print(f"  Theoretische Distanz: ~{theoretical_distance:.1f} m")
    print(f"  (= {theoretical_distance / ROD_LENGTH_M:.0f} Hübe a {ROD_LENGTH_M*100:.0f}cm)")
    
    print("=" * 65)
    
    # Plots
    if plot and len(t_all) > 1:
        plot_results(np.array(t_all), y_all_concat, dir_arr, show=True)
    
    return np.array(t_all), y_all_concat, dir_arr


# ============================================================================
# EXPORT
# ============================================================================
# EXPORT
# ============================================================================


def save_results(t, y, direction_at_t, filename='chemcar_results'):
    """Speichert Ergebnisse als .npz und .csv."""
    P_reactor = np.zeros(len(t))
    for i in range(len(t)):
        P_reactor[i] = get_reactor_pressure(y[i, 5], y[i, 7], y[i, 0])
    
    P_exhaust = np.zeros(len(t))
    for i in range(len(t)):
        d = direction_at_t[i] if i < len(direction_at_t) else (1 if y[i, 2] >= 0 else -1)
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
        'direction': np.array(direction_at_t) if len(direction_at_t) == len(t) else np.zeros(len(t)),
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
    
    t, y, dir_arr = simulate(t_max=args.time, plot=args.plot)
    save_results(t, y, dir_arr)
