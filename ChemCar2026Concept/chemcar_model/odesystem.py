"""
odesystem.py
Differentialgleichungen für das ChemCar Mehrfachhubsystem.

ARCHITEKTUR:
  Die Richtungsumschaltung wird NICHT als kontinuierliche Zustandsvariable
  modelliert (das bricht den BDF-Jacobian). Stattdessen:

  - Die ODE-Funktion nimmt die aktuelle Richtung als Parameter.
  - Die Simulationsschleife (simulate.py) pausiert bei Events,
    toggle die Richtung, und restartet die Integration.

Zustandsvariablen (Index in y-Vektor):
    [0] n_citric_mol:     Mol Zitronensäure im oberen Tank
    [1] x_piston:         Kolbenposition (m), von 0 bis ROD_LENGTH_M
    [2] v_piston:         Kolbengeschwindigkeit (m/s)
    [3] s_vehicle:        Gesamtdistanz des Fahrzeugs (m)
    [4] v_vehicle:        Fahrzeuggeschwindigkeit (m/s)
    [5] n_co2_gas:        Molzahl CO₂ als Gas im Reaktor (mol)
    [6] n_co2_dissolved:  Molzahl CO₂ gelöst im Wasser (mol)
    [7] n_air:            Mol Luft im Reaktor (konstant, trägt zum Startdruck bei)
    [8] n_exhaust_mol:    Mol Gas in der Auslass-Kammer des Kolbens (mol)

Physik-Modell:
  - Die Versorgungs-Kammer wird durch den Druckminderer konstant auf
    REGULATOR_OUTPUT_BAR gehalten. Kein eigener Zustand nötig.
  - Die Auslass-Kammer enthält n_exhaust_mol Gas. Druck berechnet sich aus
    n*R*T/V_exhaust. Gas entweicht durch Drosselventil.
  - Bei Richtungswechsel werden die Rollen der Kammern getauscht:
    n_exhaust_mol wird auf REGULATOR_OUTPUT_BAR * V_neue_Auslass / (R*T) gesetzt.
  - Kolbenkraft: F = direction * (P_supply - P_exhaust) * A
"""

import numpy as np
from config import *


# ============================================================================
# HILFSFUNKTIONEN
# ============================================================================


def get_reactor_pressure(n_co2, n_air):
    V_headspace = REACTOR_VOLUME_L * REACTOR_HEADSPACE_RATIO
    if V_headspace <= 0.001:
        return MAX_PRESSURE_BAR
    P = (n_co2 + n_air) * GAS_CONSTANT_BAR_L * TEMPERATURE_K / V_headspace
    return np.clip(P, MIN_PRESSURE_BAR, MAX_PRESSURE_BAR)


def get_tank_pressure(m_solution_kg):
    V_liquid_L = m_solution_kg / LIQUID_DENSITY * 1000.0
    V_gas = CITRIC_TANK_VOLUME_L - V_liquid_L
    if V_gas <= 0.001:
        return MAX_PRESSURE_BAR
    V_initial_gas = CITRIC_TANK_VOLUME_L * (1 - CITRIC_TANK_INITIAL_FILL)
    P_tank = TANK_INITIAL_PRESSURE_BAR * V_initial_gas / V_gas
    return np.clip(P_tank, MIN_PRESSURE_BAR, MAX_PRESSURE_BAR)


def get_drip_rate_mol_per_s(n_citric, P_reactor):
    if n_citric <= 0:
        return 0.0

    mass_fraction_initial = (CITRIC_ACID_CONCENTRATION_G_PER_L * CITRIC_TANK_VOLUME_L) / (CITRIC_SOLUTION_MASS_KG * 1000.0)
    m_solution_kg = (n_citric * CITRIC_ACID_MOLAR_MASS / 1000.0) / mass_fraction_initial

    P_tank = get_tank_pressure(m_solution_kg)
    delta_P = P_tank - P_reactor

    if delta_P <= 0.01:
        return 0.0

    A_m2 = VALVE_ORIFICE_AREA_MM2 * 1e-6
    drip_mass_kg_per_s = VALVE_DISCHARGE_COEFF * A_m2 * np.sqrt(2 * LIQUID_DENSITY * delta_P * 1e5)

    citric_mass_kg_per_s = drip_mass_kg_per_s * mass_fraction_initial
    drip_mol_per_s = citric_mass_kg_per_s * 1000.0 / CITRIC_ACID_MOLAR_MASS

    return drip_mol_per_s


def get_co2_dissolved(P_bar, water_volume_L=1.0):
    solubility_mol_per_L_at_1bar = CO2_SOLUBILITY_G_PER_L_AT_1BAR / CO2_MOLAR_MASS
    return solubility_mol_per_L_at_1bar * P_bar * water_volume_L


def get_reactor_water_volume_L(n_citric_remaining):
    n_citric_initial = (CITRIC_SOLUTION_MASS_KG * 
                        (CITRIC_ACID_CONCENTRATION_G_PER_L * CITRIC_TANK_VOLUME_L) / 
                        (CITRIC_SOLUTION_MASS_KG * 1000.0)) * 1000.0 / CITRIC_ACID_MOLAR_MASS
    n_consumed = n_citric_initial - n_citric_remaining
    mass_citric_g = n_consumed * CITRIC_ACID_MOLAR_MASS
    mass_fraction = (CITRIC_ACID_CONCENTRATION_G_PER_L * CITRIC_TANK_VOLUME_L) / (CITRIC_SOLUTION_MASS_KG * 1000.0)
    mass_solution_g = mass_citric_g / mass_fraction
    return max(0.0, mass_solution_g * 0.001)


DEAD_VOLUME_M = 0.005  # physikalisches Totvolumen an den Zylinderenden

def get_exhaust_pressure(n_exhaust, x_piston, direction):
    if direction > 0:
        # V_exhaust_m3 = max(ROD_LENGTH_M - x_piston, DEAD_VOLUME_M) * PISTON_AREA_M2 #this is unphysical, because the piston keeps moving without the volume decreasing!!! TODO
        V_exhaust_m3 = (ROD_LENGTH_M - x_piston + DEAD_VOLUME_M) * PISTON_AREA_M2
    else:
        #V_exhaust_m3 = max(x_piston, DEAD_VOLUME_M) * PISTON_AREA_M2
        V_exhaust_m3 = (x_piston + DEAD_VOLUME_M) * PISTON_AREA_M2

    V_exhaust_L = V_exhaust_m3 * 1000.0
    P_exhaust = n_exhaust * GAS_CONSTANT_BAR_L * TEMPERATURE_K / V_exhaust_L
    return P_exhaust


def get_exhaust_volume_L(x_piston, direction):
    if direction > 0:
        # V_exhaust_m3 = max(ROD_LENGTH_M - x_piston, DEAD_VOLUME_M) * PISTON_AREA_M2
        V_exhaust_m3 = (ROD_LENGTH_M - x_piston + DEAD_VOLUME_M) * PISTON_AREA_M2
    else:
        #V_exhaust_m3 = max(x_piston, DEAD_VOLUME_M) * PISTON_AREA_M2
        V_exhaust_m3 = (x_piston + DEAD_VOLUME_M) * PISTON_AREA_M2
    return V_exhaust_m3 * 1000.0


def get_vehicle_acceleration(v_vehicle, F_drive, F_brake=0.0):
    if v_vehicle < 0:
        F_drive = max(0, F_drive)

    F_roll = VEHICLE_ROLLING_RESISTANCE * VEHICLE_MASS_KG * 9.81
    F_drag_mag = 0.5 * AERODYamic_DRAG_COEFF * 1.2 * WHEEL_CONTACT_AREA_M2 * v_vehicle**2

    # Resistive forces (F_roll, F_drag, F_brake) always oppose direction of motion
    if v_vehicle >= 0:
        F_net = F_drive - F_roll - F_drag_mag - abs(F_brake)
    else:
        F_net = F_drive + F_roll + F_drag_mag + abs(F_brake)

    a_vehicle = F_net / VEHICLE_MASS_KG

    if v_vehicle <= 0.001 and a_vehicle < 0:
        a_vehicle = 0.0

    return np.clip(a_vehicle, -5, 5)


# ============================================================================
# ODE-FUNKTION (direction als Parameter, NICHT als State!)
# ============================================================================


def chemcar_odes(t, y, direction):
    """
    ODE für einen einzelnen Stroke (eine Kolbenrichtung).

    Parameter:
        t:       Zeit (s)
        y:       [n_citric_mol, x_piston, v_piston, s_vehicle, v_vehicle,
                  n_co2_gas, n_co2_dissolved, n_air, n_exhaust_mol]
        direction: +1 oder -1 (Richtung des T-Flipflops; dient als Fallback
                  für die Kammerzuweisung wenn v_piston=0)

    Rueckgabe:
        dydt: Ableitungen

    Der direction-Parameter bestimmt die Kammerzuweisung für die
    gesamte Dauer des solve_ivp-Aufrufs. Mid-stroke-Richtungswechsel
    werden durch die Mechanik korrekt abgebildet: wenn P_exhaust >
    P_supply kehrt sich die Kraft um und der Kolben wird abgebremst.
    """
    # --- Reaktor-Druck ---
    P_reactor = get_reactor_pressure(y[5], y[7])

    # --- Tropfrate ---
    drip_mol = get_drip_rate_mol_per_s(y[0], P_reactor)

    # --- CO2-Produktion ---
    n_co2_prod = STOICH_CO2_PER_CITRIC * drip_mol

    # --- CO2-Lösung (Massenerhaltung: Verschiebung Gas ↔ gelöst) ---
    V_water_L = get_reactor_water_volume_L(y[0])
    n_co2_diss_target = get_co2_dissolved(P_reactor, V_water_L)
    dissolution_tendency = (n_co2_diss_target - y[6]) * 0.5  # mol/s nach Henry
    # Transfer begrenzt durch verfügbares Gas (beim Lösen) oder verfügbare Lösung (beim Entgasen)
    if dissolution_tendency > 0:
        n_co2_transfer = min(dissolution_tendency, max(0.0, y[5] * 10.0))
    else:
        n_co2_transfer = dissolution_tendency  # Entgasen: unbegrenzt (genug gelöst vorhanden)

    # --- Versorgungs-Druck (konstant durch Druckminderer) ---
    P_supply = REGULATOR_OUTPUT_BAR if P_reactor > REGULATOR_OUTPUT_BAR else P_reactor

    # --- Gasfluss vom Reaktor zum Zylinder (piston-demand driven) ---
    dV_supply_dt = direction * y[2] * PISTON_AREA_M2  # m³/s, >0 bei Expansion
    if dV_supply_dt > 0:
        n_dot_demand = P_supply * dV_supply_dt * 1e5 / (R_GAS * TEMPERATURE_K)
        # Smooth blend between dropout (unlimited) and active regulation (sqrt-limited)
        # using a sigmoid centered at REGULATOR_OUTPUT_BAR (width ~0.05 bar).
        # Dies vermeidet die ODE-Diskontinuität beim Übergang.
        delta_P = P_reactor - REGULATOR_OUTPUT_BAR
        blend = 1.0 / (1.0 + np.exp(-delta_P * 100.0))
        n_dot_max_dropout = n_dot_demand * 10.0
        n_dot_max_active = REGULATOR_FLOW_COEFF * np.sqrt(max(0.001, delta_P)) * 1e5 / (R_GAS * TEMPERATURE_K)
        n_dot_max = n_dot_max_dropout * (1.0 - blend) + n_dot_max_active * blend
        n_dot_regulator = min(n_dot_demand, n_dot_max)
    else:
        n_dot_regulator = 0.0

    # --- Überdruckventil ---
    n_co2_relief = 0.0
    if P_reactor > RELIEF_VALVE_SET_BAR:
        n_co2_relief = (P_reactor - RELIEF_VALVE_SET_BAR) * RELIEF_VALVE_FLOW_COEFF * 1e5 / (R_GAS * TEMPERATURE_K)

    # --- Auslass-Kammer ---
    P_exhaust = get_exhaust_pressure(y[8], y[1], direction)

    # --- Kraftbilanz am Kolben ---
    # Der direction-Parameter bestimmt, welche Kammer Auslass ist:
    # direction=+1: linke Kammer = Versorgung (expandiert), rechte = Auslass (komprimiert)
    # direction=-1: rechte Kammer = Versorgung (expandiert), linke = Auslass (komprimiert)
    #
    # Wenn P_exhaust > P_supply kehrt sich die Kraft um und bremst den Kolben
    # (auch wenn direction unverändert bleibt - korrektes physikalisches Verhalten)
    F_pressure = direction * (P_supply - P_exhaust) * 1e5 * PISTON_AREA_M2

    # Sicherheit: Kolben darf nicht aus dem Zylinder gedrückt werden.
    # Falls der Kolben ausserhalb ist (Event verpasst), nur nach innen wirkende Kraft zulassen.
    if y[1] < 0 and F_pressure < 0:
        F_pressure = 0.0
    elif y[1] > ROD_LENGTH_M and F_pressure > 0:
        F_pressure = 0.0

    # Federkraft (nur nahe den Endpunkten)
    # C1-glatter Übergang: smoothstep über SPRING_SMOOTH_WIDTH_M verhindert
    # den Jacobian-Sprung (dF/dx: 0 → -6715), der implizite Solver zerstört.
    # Feder drückt immer in Richtung Zylindermitte:
    #   rechtes Ende (x > 0.28): Feder drückt nach LINKS  → F_spring negativ
    #   linkes Ende (x < 0.02):  Feder drückt nach RECHTS → F_spring positiv
    F_spring = 0.0

    # Rechte Feder
    right_engage = ROD_LENGTH_M - SPRING_ACTIVE_DISTANCE_M
    if y[1] > right_engage:
        compression = y[1] - right_engage
        factor = 1.0
        if y[1] < right_engage + SPRING_SMOOTH_WIDTH_M:
            t = compression / SPRING_SMOOTH_WIDTH_M
            factor = t * t * (3 - 2 * t)
        F_spring = -SPRING_CONSTANT_N_PER_M * compression * factor

    # Linke Feder
    left_engage = SPRING_ACTIVE_DISTANCE_M
    if y[1] < left_engage:
        compression = left_engage - y[1]
        factor = 1.0
        if y[1] > left_engage - SPRING_SMOOTH_WIDTH_M:
            t = compression / SPRING_SMOOTH_WIDTH_M
            factor = t * t * (3 - 2 * t)
        F_spring = SPRING_CONSTANT_N_PER_M * compression * factor

    # Reibung: Coulomb + viskos
    # Reibung wirkt IMMER entgegen der Bewegungsrichtung
    F_friction_coulomb = AXLE_FRICTION_TORQUE_NM * 2 / WHEEL_RADIUS_M
    F_friction_viscous = 1000.0 * y[2]

    if abs(y[2]) > 1e-8:
        F_friction = -F_friction_coulomb * np.sign(y[2]) - F_friction_viscous
    else:
        F_friction = 0.0

    F_net = F_pressure + F_spring + F_friction
    a_piston = F_net / PISTON_VEHICLE_MASS_KG
    a_piston = np.clip(a_piston, -100, 100)

    # --- Fahrzeug-Beschleunigung ---
    # Freilauf (Ratchet): wandelt beide Kolbenrichtungen in Vorwärtsfahrt um
    if (y[2] > 1e-6 and direction > 0) or (y[2] < -1e-6 and direction < 0):
        F_drive = abs(F_pressure) * BELT_TO_WHEEL_RATIO
        F_brake = VEHICLE_MECHANICAL_DAMPING * abs(y[4])
    else:
        F_drive = 0.0
        F_brake = FREEWHEEL_BRAKE_FORCE_N + VEHICLE_MECHANICAL_DAMPING * abs(y[4])

    a_vehicle = get_vehicle_acceleration(y[4], F_drive, F_brake)

    # --- Auslass-Drosselventil ---
    # sqrt(delta_P) hat eine singuläre Ableitung bei delta_P=0 (d(sqrt)/dP → ∞).
    # Fix: np.maximum(delta_P, 0) + EPS — verhindert negative sqrt-Argumente
    # und gibt endliche Ableitung. Der winzige EPS-Beitrag (1e-12) ändert
    # den Durchfluss im Betriebsbereich (delta_P > 0.01 bar) um < 1e-8 %.
    P_ambient = 1.0
    delta_P_exhaust = P_exhaust - P_ambient
    flow_safe = EXHAUST_FLOW_COEFF * np.sqrt(np.maximum(delta_P_exhaust, 0.0) + 1e-12)
    n_flow_throttle = flow_safe * 1e5 / (R_GAS * TEMPERATURE_K)

    # --- Ableitungen ---
    # Regler-Durchfluss begrenzen: nie mehr CO₂ entnehmen als verfügbar
    n_dot_regulator = min(n_dot_regulator, n_co2_prod + max(0.0, y[5]) * 10.0)

    dydt = [
        -drip_mol,                                    # [0] dn_citric/dt
        y[2],                                         # [1] dx_piston/dt = v_piston
        a_piston,                                     # [2] dv_piston/dt = a_piston
        y[4],                                         # [3] ds_vehicle/dt = v_vehicle
        a_vehicle,                                    # [4] dv_vehicle/dt
        n_co2_prod - n_co2_transfer - n_dot_regulator - n_co2_relief,  # [5] dn_co2_gas/dt
        n_co2_transfer,                               # [6] dn_co2_dissolved/dt
        0.0,                                          # [7] n_air (konstant)
        -n_flow_throttle,                             # [8] dn_exhaust/dt
    ]

    return dydt


# ============================================================================
# INITIALISIERUNG
# ============================================================================


def get_initial_state():
    V_headspace = REACTOR_VOLUME_L * REACTOR_HEADSPACE_RATIO
    n_air = REACTOR_INITIAL_PRESSURE_BAR * V_headspace / (GAS_CONSTANT_BAR_L * TEMPERATURE_K)

    mass_fraction = (CITRIC_ACID_CONCENTRATION_G_PER_L * CITRIC_TANK_VOLUME_L) / (CITRIC_SOLUTION_MASS_KG * 1000.0)
    m_citric_initial = CITRIC_SOLUTION_MASS_KG * mass_fraction
    n_citric_initial = m_citric_initial * 1000.0 / CITRIC_ACID_MOLAR_MASS

    # Auslass-Kammer startet bei ambient pressure = 1 bar
    # Startposition x=0: Kolben am linken Ende, Auslass = rechte Kammer
    V_exhaust_initial_L = ROD_LENGTH_M * PISTON_AREA_M2 * 1000.0
    n_exhaust_initial = 1.0 * V_exhaust_initial_L / (GAS_CONSTANT_BAR_L * TEMPERATURE_K)

    y0 = [
        n_citric_initial,    # [0] n_citric_mol
        0.0,                 # [1] x_piston (am linken Ende)
        0.0,                 # [2] v_piston
        0.0,                 # [3] s_vehicle
        0.0,                 # [4] v_vehicle
        0.0,                 # [5] n_co2_gas
        0.0,                 # [6] n_co2_dissolved
        n_air,               # [7] n_air
        n_exhaust_initial,   # [8] n_exhaust_mol
    ]

    return y0


# ============================================================================
# EVENTS
# ============================================================================


def piston_at_end_forward(t, y):
    return y[1] - ROD_LENGTH_M

piston_at_end_forward.terminal = True
# Direction filtering is handled in simulate.py by selecting which event to pass


def piston_at_end_reverse(t, y):
    return y[1] - 0.0

piston_at_end_reverse.terminal = True


def citric_exhausted(t, y):
    return y[0]

citric_exhausted.terminal = True
citric_exhausted.direction = -1
