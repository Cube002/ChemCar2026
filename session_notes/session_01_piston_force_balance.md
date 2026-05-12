# Session 01: Kolben-Kraftbilanz Korrektur

**Datum:** 11.05.2026
**Status:** Planung

---

## Problemstellung

Das aktuelle Modell (`odesystem.py`) vereinfacht die Kolbenphysik unzulässig:

1. **Auslass-Kammer Druck wird als konstant (1 bar / Ambient) angenommen**
2. **Kolbengeschwindigkeit wird durch "exhaust-limited velocity" erzwungen** statt aus der Kraftbilanz zu resultieren
3. **Keine Kopplung** zwischen Kolbenposition, Auslass-Volumen und Auslass-Druck

---

## Wichtige Klarstellung: Doppeltwirkender Zylinder

Der Festo-Kolben ist **doppeltwirkend** mit **2 Kammern** auf beiden Seiten der Kolbenwirkfläche:

### Kammer 1 (Versorgungs-Kammer)
- Immer mit dem **Druckminderer** verbunden
- Druck durch Regler **konstant bei 2 bar** (REGULATOR_OUTPUT_BAR)
- Funktioniert bereits korrekt

### Kammer 2 (Auslass-Kammer)
- Verbunden mit dem **Drosselventil am Auslass**
- Druck **NICHT konstant** — bestimmt durch:
  - Gasmenge in der Kammer (Mol)
  - Volumen der Kammer (abhängig von Kolbenposition)
  - Gas entweicht langsam durch Drosselventil
- **Dieser Druck muss als Zustandsvariable modelliert werden!**

---

## Korrekte Kraftbilanz am Kolben

```
F_netto = F_supply - P_exhaust * A_piston - F_friction - F_spring

F_supply = REGULATOR_OUTPUT_BAR * 1e5 * A_piston  (konstant)
P_exhaust = n_exhaust * R * T / V_exhaust(x_piston)  (dynamisch!)

V_exhaust depends on direction:
  direction = +1 (nach rechts): V_exhaust = (L_rod - x) * A_piston
  direction = -1 (nach links):  V_exhaust = x * A_piston
```

### Rückkopplungsschleife (korrekt):

```
n_citric → Tropffrate → CO2-Produktion → Reaktor-Druck → Kolbenkraft
                                                                              ↓
    Druckdifferenz ← Kolbenposition ← Fahrzeuglast ← Kolbenkraft ←──────────┘
       ↑                                                              ↓
       └── P_exhaust ← n_exhaust ← Volumenänderung ← Kolbenposition ←┘
```

**Neue Kopplung:** Kolbenposition ändert V_exhaust → ändert P_exhaust → ändert F_netto → ändert Beschleunigung → ändert Kolbenposition.

---

## Plan der Änderungen

### 1. State-Variable hinzufügen
- `[8] n_exhaust_mol`: Molzahl Gas in der Auslass-Kammer
- Initial: n_exhaust ≈ 1 bar * V_initial / (R * T)

### 2. ODE-System aktualisieren (odesystem.py)
- `dydt[8]` = Rate of change of exhaust gas moles
  - Volumenänderung komprimiert/expandiert Gas
  - Drosselventil lässt Gas entweichen
  - `dn_exhaust/dt = (P_exhaust * 1e5 * A_piston * v_piston * direction) / (R_gas * T) - flow_through_throttle`
- `P_exhaust = n_exhaust * R_gas * T / V_exhaust(x, direction)`
- **Kraftbilanz aktualisieren:**
  - `F_netto = (P_supply - P_exhaust) * A_piston - F_friction - F_spring`
  - `a_piston = F_netto / m_total` (m_total = Kolben + äquivalente Fahrzeugmasse)
- **Piston velocity aus ODE berechnen** statt durch "exhaust-limited velocity" erzwungen

### 3. Initialzustand aktualisieren (odesystem.py)
- `n_exhaust` = ambient pressure * initial_volume / (R * T)
- Initialvolume = ROD_LENGTH_M * 0.5 * PISTON_AREA_M2 (Mitte)

### 4. Transition-Handling (simulate.py)
- Bei Richtungsumschaltung: n_exhaust beibehalten (Gas bleibt in Kammer)
- Neue Auslass-Kammer erhält Gasmenge der vorherigen Versorgungs-Kammer
- Bei x=0: direction toggles +1, left chamber becomes exhaust
- Bei x=L: direction toggles -1, right chamber becomes exhaust

### 5. Fahrzeug-Beschleunigung koppeln
- `a_vehicle = F_netto * belt_ratio / vehicle_mass`
- Vehicle velocity integriert aus a_vehicle
- Zwischen Huben: Rollwiderstand und Reibung lassen Fahrzeug abbremsen

---

## Wichtige physikalische Aspekte

### Massenerhaltung am Kolben
- Gas in der Auslass-Kammer wird durch Kolbenbewegung komprimiert/expandiert
- `dV_exhaust/dt = -direction * A_piston * v_piston`
- Volumenabnahme → Druckanstieg → weniger Netto-Kraft
- Volumenzunahme → Druckabfall → mehr Netto-Kraft

### Drosselventil am Auslass
- Flow: `Q = C_exhaust * sqrt(P_exhaust - P_ambient)`
- Limitiert wie schnell Gas entweichen kann
- Bestimmt maximale Kolbengeschwindigkeit **indirekt** (nicht direkt erzwungen)
- Bei schnellem Kolbenbewegung: Druck in Auslass-Kammer sinkt → mehr Netto-Kraft
- Bei langsamem Kolben: Gas entweicht → Druck nahe ambient

### Beschleunigte Masse
- Kolbenmasse: PISTON_MASS_KG
- Fahrzeugmasse: VEHICLE_MASS_KG (über Riemen übersetzt)
- **Gesamtbeschleunigte Masse = Kolben + Fahrzeug (skaliert)**
- `F_netto = (m_piston + m_vehicle_effective) * a_piston`

### Reibung
- Coulomb-Reibung (konstant)
- Viskose Reibung (proportional zu Geschwindigkeit)
- Federkraft an den Enden (1.9 bar Schwelle)

---

## Erwartete Verhaltensänderungen

1. **Glattere Kolbenbewegung** — Beschleunigung aus Kraftbilanz statt erzwungener Geschwindigkeit
2. **Druckaufbau in Auslass-Kammer** bei schneller Kolbenbewegung → natürliche Geschwindigkeitsbegrenzung
3. **Bessere Energieerhaltung** — Kompression/Expansion des Gases korrekt modelliert
4. **Realistischere Übergänge** an den Hubenden
5. **Kopplung zwischen Fahrzeugdynamik und Kolben** — Fahrzeuglast beeinflusst Kolbenbeschleunigung

---

## Zu prüfende Parameter

- EXHAUST_FLOW_COEFF: Muss angepasst werden (aktueller Wert basiert auf vereinfachtem Modell)
- PISTON_MASS_KG: Sollte effektive Masse (Kolben + äquivalentes Fahrzeug) enthalten
- VEHICLE_MASS_KG: Gesamtmasse des Fahrzeugs
- FREEWHEEL_BRAKE_FORCE_N: Bremse zwischen Huben

---

## Nächste Schritte

1. [x] Physik-Dokumentation erstellen
2. [ ] Code-Änderungen an odesystem.py implementieren
3. [ ] Code-Änderungen an simulate.py implementieren
4. [ ] config.py Parameter anpassen falls nötig
5. [ ] Simulation testen und Verhalten analysieren
6. [ ] Plots erzeugen und physikalische Konsistenz prüfen
