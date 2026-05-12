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

RÜCKKOPPLUNGSSCHLEIFE (korrigiert):
    n_citric → Tropffrate → CO2-Produktion → Reaktor-Druck → Kolbenkraft
                                                                      ↓
        Druckdifferenz ← Kolbenposition ← Fahrzeuglast ← Kolbenkraft ←──┘
           ↑                                                              ↓
           └── P_exhaust ← n_exhaust ← V_exhaust(x) ← Kolbenposition ←┘
"""

import numpy as np
from config import *


# ============================================================================
# HILFSFUNKTIONEN
# ============================================================================


def get_reactor_pressure(n_co2, n_air):
    """
    Berechnet den Reaktor-Druck aus CO2 und Luft-Molzahl.
    P [bar] = (n_co2 + n_air) * R [bar*L/(mol*K)] * T [K] / V_headspace [L]
    """
    V_headspace = REACTOR_VOLUME_L * (1 - REACTOR_HEADSPACE_RATIO)
    if V_headspace <= 0.001:
        return MAX_PRESSURE_BAR
    P = (n_co2 + n_air) * GAS_CONSTANT_BAR_L * TEMPERATURE_K / V_headspace
    return np.clip(P, MIN_PRESSURE_BAR, MAX_PRESSURE_BAR)


def get_tank_pressure(m_solution_kg):
    """
    Druck im Edelstahltank: Luftvorfüllung bei 3 bar.
    Wenn Flüssigkeit austritt, expandiert die Luft → Druck sinkt.
    P_tank = P_initial * V_initial_gas / V_current_gas
    """
    V_liquid_L = m_solution_kg / LIQUID_DENSITY * 1000.0
    V_gas = CITRIC_TANK_VOLUME_L - V_liquid_L
    if V_gas <= 0.001:
        return MAX_PRESSURE_BAR
    V_initial_gas = CITRIC_TANK_VOLUME_L * (1 - CITRIC_TANK_INITIAL_FILL)
    P_tank = TANK_INITIAL_PRESSURE_BAR * V_initial_gas / V_gas
    return np.clip(P_tank, MIN_PRESSURE_BAR, MAX_PRESSURE_BAR)


def get_drip_rate_mol_per_s(n_citric, P_reactor):
    """
    Tropfrate in mol/s Zitronensäure.

    dm/dt = C_d * A * sqrt(2 * rho * (P_tank - P_reactor))  [kg/s]
    dn/dt = (dm/dt * mass_fraction_citric) / M_citric         [mol/s]
    """
    if n_citric <= 0:
        return 0.0

    # Tank-Druck
    mass_fraction_initial = (CITRIC_ACID_CONCENTRATION_G_PER_L * CITRIC_TANK_VOLUME_L) / (CITRIC_SOLUTION_MASS_KG * 1000.0)
    m_solution_kg = (n_citric * CITRIC_ACID_MOLAR_MASS / 1000.0) / mass_fraction_initial

    P_tank = get_tank_pressure(m_solution_kg)
    delta_P = P_tank - P_reactor

    if delta_P <= 0.01:
        return 0.0

    # dm/dt in kg/s (Torricelli)
    A_m2 = VALVE_ORIFICE_AREA_MM2 * 1e-6
    drip_mass_kg_per_s = VALVE_DISCHARGE_COEFF * A_m2 * np.sqrt(2 * LIQUID_DENSITY * delta_P * 1e5)

    # Zitronensäure-Masse in der Tropfflüssigkeit
    citric_mass_kg_per_s = drip_mass_kg_per_s * mass_fraction_initial

    # Mol/s
    drip_mol_per_s = citric_mass_kg_per_s * 1000.0 / CITRIC_ACID_MOLAR_MASS

    return drip_mol_per_s


def get_co2_dissolved(P_bar):
    """Henry's Law: n_dissolved = solubility * P * water_volume"""
    solubility_mol_per_L_at_1bar = CO2_SOLUBILITY_G_PER_L_AT_1BAR / CO2_MOLAR_MASS
    return solubility_mol_per_L_at_1bar * P_bar * 1.0  # 1 L Wasser


def get_exhaust_pressure(n_exhaust, x_piston, direction):
    """
    Druck in der Auslass-Kammer des doppeltwirkenden Kolbens.

    P_exhaust = n_exhaust * R * T / V_exhaust

    V_exhaust hängt von der Kolbenposition und Richtung ab:
      direction = +1 (nach rechts): rechte Kammer ist Auslass, V = (L - x) * A
      direction = -1 (nach links):  linke Kammer ist Auslass, V = x * A
    """
    if direction > 0:
        V_exhaust_m3 = max(ROD_LENGTH_M - x_piston, 0.0001) * PISTON_AREA_M2
    else:
        V_exhaust_m3 = max(x_piston, 0.0001) * PISTON_AREA_M2

    V_exhaust_L = V_exhaust_m3 * 1000.0  # m³ → L
    P_exhaust = n_exhaust * GAS_CONSTANT_BAR_L * TEMPERATURE_K / V_exhaust_L
    return P_exhaust


def get_exhaust_volume_L(x_piston, direction):
    """Volumen der Auslass-Kammer in Litern."""
    if direction > 0:
        V_exhaust_m3 = max(ROD_LENGTH_M - x_piston, 0.0001) * PISTON_AREA_M2
    else:
        V_exhaust_m3 = max(x_piston, 0.0001) * PISTON_AREA_M2
    return V_exhaust_m3 * 1000.0


def get_vehicle_acceleration(v_vehicle, F_drive, F_brake=0.0):
    """
    Fahrzeugbeschleunigung.
    F_net = F_drive - F_roll - F_drag - F_brake
    """
    # Nur Vorwaerts
    if v_vehicle < 0:
        F_drive = max(0, F_drive)

    F_roll = VEHICLE_ROLLING_RESISTANCE * VEHICLE_MASS_KG * 9.81
    F_drag = 0.5 * AERODYamic_DRAG_COEFF * 1.2 * WHEEL_CONTACT_AREA_M2 * max(0, v_vehicle)**2

    F_net = F_drive - F_roll - F_drag - F_brake
    a_vehicle = F_net / VEHICLE_MASS_KG

    # Kein Rückwärts
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
        direction: +1 oder -1 (wird in der ODE NICHT geändert!)

    Rueckgabe:
        dydt: Ableitungen
    """
    # --- Druck ---
    P_reactor = get_reactor_pressure(y[5], y[7])  # n_co2, n_air

    # --- Tropfrate ---
    drip_mol = get_drip_rate_mol_per_s(y[0], P_reactor)  # mol/s

    # --- CO2-Produktion ---
    n_co2_prod = STOICH_CO2_PER_CITRIC * drip_mol  # mol/s

    # --- CO2-Lösung ---
    n_co2_diss_target = get_co2_dissolved(P_reactor)
    dissolution_rate = (n_co2_diss_target - y[6]) * 0.5  # mol/s

    # --- Gasfluss zum Zylinder (Druckminderer) ---
    # Flow durch Regler: Q = C_reg * sqrt(P_reactor - P_cyl)
    if P_reactor > REGULATOR_OUTPUT_BAR:
        delta_P_reg = P_reactor - REGULATOR_OUTPUT_BAR
        flow_to_cyl_m3_s = REGULATOR_FLOW_COEFF * np.sqrt(max(0.001, delta_P_reg))
    else:
        flow_to_cyl_m3_s = 0.0

    # --- Auslass-Kammer Druck ---
    P_exhaust = get_exhaust_pressure(y[8], y[1], direction)

    # --- Überdruckventil ---
    n_co2_relief = 0.0
    if P_reactor > RELIEF_VALVE_SET_BAR:
        n_co2_relief = (P_reactor - RELIEF_VALVE_SET_BAR) * RELIEF_VALVE_FLOW_COEFF * 1e5 / (R_GAS * TEMPERATURE_K)

    # --- Kraftbilanz am Kolben ---
    # Doppeltwirkender Zylinder:
    #   Kammer 1 (Versorgung): P_supply = REGULATOR_OUTPUT_BAR (konstant)
    #   Kammer 2 (Auslass):    P_exhaust (dynamisch, aus n_exhaust und V_exhaust)

    P_supply = REGULATOR_OUTPUT_BAR if P_reactor > REGULATOR_OUTPUT_BAR else P_reactor

    # Federkraft (nur nahe den Endpunkten)
    F_spring = 0.0
    if y[1] > ROD_LENGTH_M - SPRING_ACTIVE_DISTANCE_M:
        compression = y[1] - (ROD_LENGTH_M - SPRING_ACTIVE_DISTANCE_M)
        F_spring = SPRING_CONSTANT_N_PER_M * compression
    elif y[1] < SPRING_ACTIVE_DISTANCE_M:
        compression = SPRING_ACTIVE_DISTANCE_M - y[1]
        F_spring = SPRING_CONSTANT_N_PER_M * compression

    # Druckkraft: F = (P_supply - P_exhaust) * A_piston * 1e5 (bar → Pa)
    F_pressure = (P_supply - P_exhaust) * 1e5 * PISTON_AREA_M2

    # Reibung: Coulomb + viskos
    F_friction_coulomb = AXLE_FRICTION_TORQUE_NM * 2 / WHEEL_RADIUS_M
    F_friction_viscous = 0.1 * y[2]

    # Gesamt-Reibung (wirkt immer der Bewegung entgegen)
    if abs(y[2]) > 1e-8:
        F_friction = F_friction_coulomb * np.sign(y[2]) + F_friction_viscous
    else:
        # Statischer Reibung: muss erst überwunden werden
        F_friction = 0.0

    # Netto-Kraft am Kolben
    F_net = F_pressure - F_spring - F_friction

    # Beschleunigte Masse: Kolben + äquivalentes Fahrzeug
    a_piston = F_net / PISTON_VEHICLE_MASS_KG
    a_piston = np.clip(a_piston, -100, 100)

    # --- Fahrzeug-Beschleunigung ---
    # Drive-Force vom Kolben über Riemen/Freiläufe zum Fahrzeug
    if y[2] > 1e-6 and direction > 0:
        F_drive = F_pressure * BELT_TO_WHEEL_RATIO
        F_brake = 0.0
    elif y[2] < -1e-6 and direction < 0:
        F_drive = F_pressure * BELT_TO_WHEEL_RATIO
        F_brake = 0.0
    else:
        # Kolben steht oder Richtungsumschlag: Freilauf-Bremse
        F_drive = 0.0
        F_brake = FREEWHEEL_BRAKE_FORCE_N + VEHICLE_MECHANICAL_DAMPING * abs(y[4])

    a_vehicle = get_vehicle_acceleration(y[4], F_drive, F_brake)

    # --- Ableitungen ---
    dydt = [
        -drip_mol,                                    # [0] dn_citric/dt
        y[2],                                         # [1] dx_piston/dt = v_piston
        a_piston,                                     # [2] dv_piston/dt = a_piston
        y[4],                                         # [3] ds_vehicle/dt = v_vehicle
        a_vehicle,                                    # [4] dv_vehicle/dt
        n_co2_prod - flow_to_cyl_m3_s * 1e5 / (R_GAS * TEMPERATURE_K) - n_co2_relief,  # [5] dn_co2_gas/dt
        dissolution_rate,                             # [6] dn_co2_dissolved/dt
        0.0,                                          # [7] n_air (konstant)
    ]

    # --- dn_exhaust/dt: Gas in der Auslass-Kammer ---
    # Zwei Effekte:
    #   1. Volumenänderung durch Kolbenbewegung (Kompression/Expansion)
    #   2. Gasfluss durch Drosselventil
    #
    # dV_exhaust/dt = -direction * A_piston * v_piston
    #   direction=+1, v>0: Kolben bewegt sich weg von Auslass → V nimmt zu → dn/dt < 0
    #   direction=-1, v<0: Kolben bewegt sich zum Auslass → V nimmt ab → dn/dt > 0

    if direction > 0:
        V_exhaust_m3 = max(ROD_LENGTH_M - y[1], 0.0001) * PISTON_AREA_M2
    else:
        V_exhaust_m3 = max(y[1], 0.0001) * PISTON_AREA_M2

    dVdt = -direction * PISTON_AREA_M2 * y[2]  # m³/s

    # Molfluss durch Volumenänderung (ideal gas): dn/dt = P * dV/dt / (R * T)
    n_flow_compression = P_exhaust * 1e5 * dVdt / (R_GAS * TEMPERATURE_K)

    # Molfluss durch Drosselventil: Q = C_exhaust * sqrt(P_exhaust - P_ambient)
    P_ambient = 1.0
    delta_P_exhaust = P_exhaust - P_ambient
    if delta_P_exhaust > 0:
        flow_exhaust_m3_s = EXHAUST_FLOW_COEFF * np.sqrt(delta_P_exhaust)  # m³/s
        n_flow_throttle = flow_exhaust_m3_s * 1e5 / (R_GAS * TEMPERATURE_K)  # mol/s
    else:
        n_flow_throttle = 0.0

    # Gesamte Rate: positive = Gas tritt aus, negative = Gas tritt ein
    dydt.append(-n_flow_compression - n_flow_throttle)  # [8] dn_exhaust/dt

    return dydt


# ============================================================================
# INITIALISIERUNG
# ============================================================================


def get_initial_state():
    """
    Initialer Zustandsvektor.

    WICHTIG: Der Reaktor startet mit Luft bei ~3 bar (nicht mit CO2).
    n_air = P_initial * V_headspace / (R * T)

    n_exhaust_start: Auslass-Kammer startet bei Ambient-Druck (1 bar)
    mit initialem Volumen = halber Hubweg * Kolbenfläche
    """
    V_headspace = REACTOR_VOLUME_L * (1 - REACTOR_HEADSPACE_RATIO)
    n_air = (REACTOR_INITIAL_PRESSURE_BAR - 1.0) * V_headspace / (GAS_CONSTANT_BAR_L * TEMPERATURE_K)

    # Initiale Zitronensäure-Molzahl
    mass_fraction = (CITRIC_ACID_CONCENTRATION_G_PER_L * CITRIC_TANK_VOLUME_L) / (CITRIC_SOLUTION_MASS_KG * 1000.0)
    m_citric_initial = CITRIC_SOLUTION_MASS_KG * CITRIC_TANK_INITIAL_FILL * mass_fraction
    n_citric_initial = m_citric_initial * 1000.0 / CITRIC_ACID_MOLAR_MASS

    # Initiale Mol in der Auslass-Kammer (startet bei ambient pressure = 1 bar)
    V_exhaust_initial_L = (ROD_LENGTH_M / 2.0) * PISTON_AREA_M2 * 1000.0  # m³ → L
    n_exhaust_initial = 1.0 * V_exhaust_initial_L / (GAS_CONSTANT_BAR_L * TEMPERATURE_K)

    y0 = [
        n_citric_initial,    # [0] n_citric_mol
        ROD_LENGTH_M / 2.0,  # [1] x_piston (Mitte)
        0.0,                 # [2] v_piston
        0.0,                 # [3] s_vehicle
        0.0,                 # [4] v_vehicle
        0.0,                 # [5] n_co2_gas (startet bei 0, baut sich auf)
        0.0,                 # [6] n_co2_dissolved
        n_air,               # [7] n_air (trägt zum Startdruck bei)
        n_exhaust_initial,   # [8] n_exhaust_mol (Auslass-Kammer bei 1 bar)
    ]

    return y0


# ============================================================================
# EVENTS
# ============================================================================


def piston_at_end_forward(t, y):
    """Kolben erreicht rechtes Ende (x = ROD_LENGTH_M)."""
    return y[1] - ROD_LENGTH_M

piston_at_end_forward.terminal = True
piston_at_end_forward.direction = 1


def piston_at_end_reverse(t, y):
    """Kolben erreicht linkes Ende (x = 0)."""
    return y[1] - 0.0

piston_at_end_reverse.terminal = True
piston_at_end_reverse.direction = -1


def citric_exhausted(t, y):
    """Zitronensäure aufgebraucht."""
    return y[0]

citric_exhausted.terminal = True
citric_exhausted.direction = -1
