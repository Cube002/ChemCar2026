"""
config.py
Parameter-Konfiguration für das ChemCar Mehrfachhubsystem.
Alle Werte basieren auf dem Konzeptbericht (Citric Aixpress, 2026)
und den Notizen. Leicht anpassbar für Sensitivitätsanalysen.
"""

# ============================================================================
# CHEMISCHE REAKTOR-PARAMETER
# ============================================================================

# Oberer Tank (Edelstahl) - Zitronensäure-Tank
CITRIC_TANK_VOLUME_L = 2.0        # Gesamtvolumen des Edelstahltanks in Litern
CITRIC_TANK_INITIAL_FILL = 0.9    # Füllfaktor (0-1), 90% gefüllt
CITRIC_SOLUTION_MASS_KG = CITRIC_TANK_VOLUME_L * 1.0 * CITRIC_TANK_INITIAL_FILL  # ~1.8 kg Lösung
TANK_INITIAL_PRESSURE_BAR = 3.0   # Startdruck im Zitronensäure-Tank (bar)

# Zitronensäure-Konzentration in der Lösung (g/L)
# Aus Notizen: 27g Citronensäure für ~10L CO₂ bei 2 bar
CITRIC_ACID_CONCENTRATION_G_PER_L = 135   # 270g / 2L (~13.5% Lösung)
CITRIC_ACID_MOLAR_MASS = 192.12  # g/mol (C₆H₈O₇)

# Untere Tank (Edelstahl) - NaHCO₃-Reaktor
REACTOR_VOLUME_L = 3.0            # Volumen des Reaktors in Litern
REACTOR_HEADSPACE_RATIO = 0.1     # 10% des Volumens ist Gasraum (Luftvorfüllung)
REACTOR_INITIAL_PRESSURE_BAR = 1.0 # Startdruck im Reaktor (bar) - atmosphärisch

# Natron (NaHCO₃) im Reaktor - im Überschuss
NACHTRON_MASS_KG = 0.35           # 350 g NaHCO₃
NACHTRON_MOLAR_MASS = 84.01       # g/mol (NaHCO₃)

# Reaktionsstoichiometrie
# C₆H₈O₇ + 3 NaHCO₃ → Na₃C₆H₅O₇ + 3 CO₂ + 3 H₂O
STOICH_CO2_PER_CITRIC = 3.0       # 3 mol CO₂ pro mol Citric Acid
STOICH_NACHTRON_PER_CITRIC = 3.0  # 3 mol NaHCO₃ pro mol Citric Acid

# CO₂ Löslichkeit in Wasser (Henry's Law)
# ~1.7 g/L bei 20°C und 1 bar
CO2_SOLUBILITY_G_PER_L_AT_1BAR = 1.7
CO2_MOLAR_MASS = 44.01            # g/mol

# Reaktionskinetik
# Die Tropffrate wird durch das Ventil und den Druckgradienten bestimmt
# C_d * A * sqrt(2 * rho * delta_P)
VALVE_DISCHARGE_COEFF = 0.6       # Durchflussbeiwert für Nadelventil
VALVE_ORIFICE_AREA_MM2 = 0.2      # Öffnungsfläche in mm² (Nadelventil, stark gedrosselt)
LIQUID_DENSITY = 1000.0           # kg/m³ (wässrige Lösung)

# ============================================================================
# DRUCKSYSTEM
# ============================================================================

# Druckminderer
REGULATOR_OUTPUT_BAR = 2.0        # Konstante 2 bar am Pneumatikeingang
REGULATOR_FLOW_COEFF = 5e-4       # m³/s / sqrt(bar) — Flow durch Regler (limitiert Stroke-Speed)
REGULATOR_INACTIVE_THRESHOLD_BAR = 1.0  # Unter diesem Druck regelt der Minderer nicht

# Feder-Schwelle am Kolben
SPRING_PRELOAD_BAR = 1.9          # Mindestdruck um Feder zu komprimieren (bar)

# Überdruckventil (Safety Relief Valve)
RELIEF_VALVE_SET_BAR = 4.4        # 1.1 * 4 bar max operating pressure
RELIEF_VALVE_FLOW_COEFF = 0.01    # Flow-Koeffizient für Druckentlastung

# ============================================================================
# PNEUMATIK-ZYLINDER (Festo)
# ============================================================================

ROD_LENGTH_M = 0.30               # Hubweg in Metern (30 cm)
PISTON_DIAMETER_MM = 30.0         # Kolbendurchmesser in mm (Standard Festo)
PISTON_AREA_M2 = 3.14159 * (PISTON_DIAMETER_MM / 1000.0)**2 / 4.0

# Feder-Eigenschaften (pro Feder an jedem Ende)
SPRING_ACTIVE_DISTANCE_M = 0.02   # Feder wirkt in den letzten 2cm des Hubwegs
SPRING_SMOOTH_WIDTH_M = 0.001    # 1 mm C1-Übergangszone (verhindert Jacobian-Sprung)
# Federkonstante berechnet aus Schwellendruck: F_spring_max = k * 0.02 = P * A
# Damit ~1.9 bar nötig sind um Feder ganz zusammenzudrücken
SPRING_CONSTANT_N_PER_M = (SPRING_PRELOAD_BAR * 1e5 * PISTON_AREA_M2) / SPRING_ACTIVE_DISTANCE_M 

# Drosselventil (Exhaust)
# Das Drosselventil am Pneumatikzylinder limitiert den Gasausstrom
# und damit die Stroke-Geschwindigkeit (Ziel wären ~5 Sekunden pro Stroke)
# Flow: m_dot ~ C * sqrt(delta_P) — typisch für Durchfluss durch Öffnung
# Mit physikalischer Feder (k=6715 N/m) und 5kg Fahrzeug:
# - Exhaust-Kammer baut Gegendruck auf → natürliche Geschwindigkeitsbegrenzung
# - Feder+Exhaust bremsen den Kolben sanft an den Hubenden
# - Keine harten if/else Diskontinuitäten — alles physikalisch über Kraftbilanz
EXHAUST_FLOW_COEFF = 3.0e-5     # m³/s / sqrt(bar)
EXHAUST_ORIFICE_AREA_MM2 = 2.0  # Äquivalente Drosselöffnungsfläche in mm²

# Kolben-Masse
PISTON_MASS_KG = 0.5              # Masse des beweglichen Teils

# Effektive beschleunigte Masse (Kolben + äquivalentes Fahrzeug über Riemenübersetzung)
# Da der Kolben über Riemen und Freiläufe das Fahrzeug beschleunigt, muss die Fahrzeugmasse
# als äquivalente Masse am Kolben berücksichtigt werden.
# ============================================================================
# KRAFTÜBERTRAGUNG & FAHRZEUG
# ============================================================================

# Riemen-Übersetzung
# 1:1 - jede Kolbenbewegung wird direkt auf die Räder übertragen
BELT_TO_WHEEL_RATIO = 1.0

# Fahrzeugparameter
VEHICLE_MASS_KG = 5.0             # Gesamtmasse des Fahrzeugs

# Effektive beschleunigte Masse (Kolben + äquivalentes Fahrzeug über Riemenübersetzung)
# Da der Kolben über Riemen und Freiläufe das Fahrzeug beschleunigt, muss die Fahrzeugmasse
# als äquivalente Masse am Kolben berücksichtigt werden.
PISTON_VEHICLE_MASS_KG = PISTON_MASS_KG + VEHICLE_MASS_KG  # Gesamtmasse für Beschleunigung
WHEEL_DIAMETER_M = 0.08           # Raddurchmesser in m (8 cm)
WHEEL_RADIUS_M = WHEEL_DIAMETER_M / 2.0

# Reibung
AXLE_FRICTION_TORQUE_NM = 0.05    # Reibungsmoment an jeder Achse (Nm)
VEHICLE_ROLLING_RESISTANCE = 0.08  # Rollwiderstands-Koeffizient
AERODYamic_DRAG_COEFF = 0.6       # Luftwiderstandsbeiwert
WHEEL_CONTACT_AREA_M2 = 0.002     # Kontaktfläche Rad-Boden

# Freilauf-Bremse (wenn Kolben steht = kein Antrieb)
# Modelliert Lagerreibung, Getriebeverluste, mechanische Dämpfung
FREEWHEEL_BRAQUE_NM = 5.0          # Bremsmoment im Freilauf (Nm)
FREEWHEEL_BRAKE_FORCE_N = 30.0     # Äquivalente Bremskraft am Rad (N)
VEHICLE_MECHANICAL_DAMPING = 3000.0  # Mechanische Dämpfung (N·s/m) - begrenzt Fahrzeuggeschwindigkeit

# ============================================================================
# SIMULATION-PARAMETER
# ============================================================================

SIMULATION_TIME_MAX = 200.0         # Max. Simulationszeit in Sekunden (10 min)
SIMULATION_DT = 0.001               # Schrittweite für BDF-Adaptivschritt (max)
SIMULATION_TOL = 1e-6               # Toleranz des Integrators

# Gaskonstante
R_GAS = 8.314                       # J/(mol·K)
GAS_CONSTANT_BAR_L = 0.08314        # bar·L/(mol·K)

# Standard-Temperatur (K)
TEMPERATURE_K = 293.15              # 20°C

# Numerische Sicherheit
MAX_PRESSURE_BAR = 50.0             # Obere Grenze für Druck (bar)
MIN_PRESSURE_BAR = 0.1              # Untere Grenze
MAX_STATE_VALUE = 1e6               # Obere Grenze für Zustandsvariablen
MIN_STATE_VALUE = -1e6              # Untere Grenze
