# ChemCar Simulation — Persistent Notes

**Stand:** 13.05.2026 (Session 03 in progress)

---

## Session 02: Micro‑Oscillation Debug & Fix (12.05.2026)

### Root Cause of Micro‑Oscillation

**Symptom:** 500 "strokes" in 4.6s (~0.009s each), CSV showed piston moving monotonically 0→30cm.

**Cause:** Event ping‑pong at stroke boundaries. After `piston_at_end_forward` fired at x=30cm,
the next `solve_ivp` started with **both events active** including `piston_at_end_reverse`.
Since `piston_at_end_reverse` = y[1] − 0.0 returned exactly 0 at the initial state,
`solve_ivp` immediately re‑fired → direction toggle → infinite loop feeding `stroke_count`.

**Fix:** Only pass the direction‑appropriate event to `solve_ivp`:
- `direction=+1` → only `piston_at_end_forward` + `citric_exhausted`
- `direction=-1` → only `piston_at_end_reverse` + `citric_exhausted`

### Integration Failure at Stroke 15

**Symptom:** BDF solver returned status=−1 always at stroke 15 (~60s), exactly when
P_reactor reached REGULATOR_OUTPUT_BAR (= 2.0 bar).

**Cause:** The regulator flow equation had a **hard if/else discontinuity** at
P_reactor = REGULATOR_OUTPUT_BAR:
```python
if P_reactor > REGULATOR_OUTPUT_BAR:
    n_dot_regulator = min(demand, sqrt‑limited)   # small flow
else:
    n_dot_regulator = demand                       # unlimited flow
```
A 10× jump in n_dot_regulator at the boundary broke BDF convergence.

**Fix:** Smooth sigmoid blend between both regimes:
```python
blend = 1.0 / (1.0 + np.exp(-(P_reactor - 2.0) * 100.0))
n_dot_max = n_dot_max_dropout * (1-blend) + n_dot_max_active * blend
```

### CO₂ Depletion → Negative Pressure

**Symptom:** P_reactor went to −3.38 bar (n_co2_gas < 0) because regulator extracted
more CO₂ than available.

**Fix:** Clamp n_dot_regulator to available CO₂:
```python
n_dot_regulator = min(n_dot_regulator, n_co2_prod + max(0, n_co2_gas) * 10.0)
```

### Remaining Issues

| Issue | Impact | Status |
|-------|--------|--------|
| Vehicle speed 34 m/s | Unrealistic; freewheel applies full 126 N to 5 kg car with no damping during stroke | Open |
| P_reactor drops below 1.1 bar after ~34 strokes | CO₂ consumption > production; needs drip‑rate tuning | Open |
| P_exhaust spike (377 bar) at stroke ends | Mitigated with 5 mm volume clamp; ODE stiffness persists | Mitigated |

### Parameter Values at Session End

| Param | Value | Note |
|-------|-------|------|
| EXHAUST_FLOW_COEFF | 3.0e‑3 | Adequate; P_exhaust stays ~1 bar mid‑stroke |
| Friction | 1000 N·s/m | Limits terminal velocity to ~0.07 m/s → ~4 s stroke |
| Volume clamp | 5 mm | Prevents P_exhaust → ∞ at stroke ends |
| Regulator blend | sigmoid, width ~0.05 bar | Smooth transition at P_reactor = 2.0 bar |
| Abort threshold | 1.1 bar | Fires when P_reactor drops too low |

### Stroke Performance (Best Strokes)

- **Stroke time:** ~4.0 s per 30 cm stroke (target: ~5 s)
- **Terminal velocity:** ~8 cm/s (rightward) → ~6 cm/s as P_reactor drops
- **P_exhaust mid‑stroke:** ~1.001 bar (throttle handles compression easily)
- **Strokes completed:** 34 before abort at P_reactor < 1.1 bar

---

## Session 03: Spring Physics & Solver Stability (13.05.2026)

### Spring Formula Correction

**Problem:** Spring preload was calculated as absolute 1.9 bar, but one side of the piston
always has 1 bar atmosphere → net preload was only 0.9 bar effective.

**Fix:**
```python
ATMOSPHERIC_PRESSURE = 1.0
SPRING_CONSTANT_N_PER_M = ((SPRING_PRELOAD_BAR - ATMOSPHERIC_PRESSURE) * 1e5 * PISTON_AREA_M2) / SPRING_ACTIVE_DISTANCE_M
```
Result: `k = (1.9 - 1.0) * 1e5 * 7.07e-4 / 0.02 = 3182 N/m`

### C1-Smooth Spring Engagement

**Problem:** Hard if/elif spring engagement at x=0.28 and x=0.02 caused a Jacobian
discontinuity (dF/dx: 0 → -k), breaking Radau/LSODA convergence at higher k values.

**Fix:** Cubic Hermite smoothstep over 1 mm transition zone (`SPRING_SMOOTH_WIDTH_M = 0.001`):
- `f(0) = 0, f'(0) = 0` at engagement point
- `f(h) = -k*h, f'(h) = -k` at full engagement
- Eliminates finite-difference Jacobian errors

### Exhaust Flow Coefficient Restored

`EXHAUST_FLOW_COEFF = 3e-3` (was incorrectly set to 3e-5 in a previous session).
The 3e-5 value caused terminal piston velocity < 0.1 cm/s (impossibly slow).
At 3e-3 the terminal mid-stroke velocity is ~7 cm/s.

### Current Performance

| Metric | Value |
|--------|-------|
| Strokes in 60 s | 11 |
| Time per stroke | ~5.5 s |
| P_reactor | 2.08 → 1.97 bar (slow decline) |
| Terminal v_piston (mid-stroke) | ~7 cm/s |
| Vehicle top speed | ~2.2 cm/s |
| Total distance | 1.15 m |

### Remaining Issues

1. **Vehicle too slow** — VEHICLE_MECHANICAL_DAMPING = 3000 N·s/m caps speed at 2.2 cm/s
2. **P_reactor declining** — drip rate insufficient; CO₂ consumption > production
3. **Vehicle damping between strokes** — FREEWHEEL_BRAKE_FORCE_N = 30 N slows car too much

### Next Tuning Steps

1. **Increase drip rate** (VALVE_ORIFICE_AREA_MM2 or CITRIC_ACID_CONCENTRATION_G_PER_L)
   so CO₂ production exceeds regulator consumption → P_reactor stays above 2 bar
2. **Reduce vehicle damping** — lower VEHICLE_MECHANICAL_DAMPING to ~500 N·s/m
3. **Reduce freewheel brake** — lower FREEWHEEL_BRAKE_FORCE_N

---

## Ursprünglicher Prompt (verbesserungenPrompt.txt — 11.05.2026)

> Originalanforderung: DGL-Modell in `chemcar_model/` analysieren, Simulation zum Laufen bringen,
> Physikverhalten verstehen, übergreifende Notizen führen.
>
> Kernproblem: Alle Gleichungen sind start-bidirektional gekoppelt, schwer stabil zu bekommen.
>
> Rückkopplungsschleife:
> ```
> n_citric → Tropffrate → CO2-Produktion → Reaktor-Druck → Kolbenkraft
>   ↑                                                                    ↓
>   └── Druckdifferenz ← Kolbenposition ← Fahrzeuglast ← Kolbenkraft ←──┘
> ```
>
> Vereinfachungen im aktuellen Code sind problematisch — Kraftbilanz am Kolben muss korrekt sein.

---

## Session 01: Kolben-Kraftbilanz Korrektur (11.05.2026)

### Problemstellung

Das aktuelle Modell (`odesystem.py`) vereinfacht die Kolbenphysik unzulässig:

1. **Auslass-Kammer Druck wird als konstant (1 bar / Ambient) angenommen**
2. **Kolbengeschwindigkeit wird durch "exhaust-limited velocity" erzwungen** statt aus der Kraftbilanz zu resultieren
3. **Keine Kopplung** zwischen Kolbenposition, Auslass-Volumen und Auslass-Druck

### Doppeltwirkender Zylinder — Wichtige Klarstellung

Der Festo-Kolben ist **doppeltwirkend** mit **2 Kammern** auf beiden Seiten der Kolbenwirkfläche:

#### Kammer 1 (Versorgungs-Kammer)
- Immer mit dem **Druckminderer** verbunden
- Druck durch Regler **konstant bei 2 bar** (`REGULATOR_OUTPUT_BAR`)
- Funktioniert bereits korrekt

#### Kammer 2 (Auslass-Kammer)
- Verbunden mit dem **Drosselventil am Auslass**
- Druck **NICHT konstant** — bestimmt durch:
  - Gasmenge in der Kammer (Mol)
  - Volumen der Kammer (abhängig von Kolbenposition)
  - Gas entweicht langsam durch Drosselventil
- **Dieser Druck muss als Zustandsvariable modelliert werden!**

### Korrekte Kraftbilanz am Kolben

```
F_netto = F_supply - P_exhaust * A_piston - F_friction - F_spring

F_supply = REGULATOR_OUTPUT_BAR * 1e5 * A_piston  (konstant)
P_exhaust = n_exhaust * R * T / V_exhaust(x_piston)  (dynamisch!)

V_exhaust depends on direction:
  direction = +1 (nach rechts): V_exhaust = (L_rod - x) * A_piston
  direction = -1 (nach links):  V_exhaust = x * A_piston
```

#### Rückkopplungsschleife (korrekt):

```
n_citric → Tropffrate → CO2-Produktion → Reaktor-Druck → Kolbenkraft
                                                                         ↓
    Druckdifferenz ← Kolbenposition ← Fahrzeuglast ← Kolbenkraft ←──────────┘
       ↑                                                              ↓
       └── P_exhaust ← n_exhaust ← Volumenänderung ← Kolbenposition ←┘
```

**Neue Kopplung:** Kolbenposition ändert V_exhaust → ändert P_exhaust → ändert F_netto → ändert Beschleunigung → ändert Kolbenposition.

### Geplante Änderungen

| # | Änderung | Status |
|---|----------|--------|
| 1 | State-Variable `[8] n_exhaust_mol` hinzufügen | geplant |
| 2 | ODE-System (`odesystem.py`) aktualisieren | geplant |
| 3 | Initialzustand (`get_initial_state`) aktualisieren | geplant |
| 4 | Transition-Handling (`simulate.py`) bei Richtungswechsel | geplant |
| 5 | Fahrzeug-Beschleunigung koppeln | geplant |

### Wichtige physikalische Aspekte

- **Massenerhaltung:** Gas in Auslass-Kammer wird komprimiert/expandiert → `dV_exhaust/dt = -direction * A_piston * v_piston`
- **Drosselventil:** `Q = C_exhaust * sqrt(P_exhaust - P_ambient)` — indirekte Geschwindigkeitsbegrenzung
- **Beschleunigte Masse:** `F_netto = (m_piston + m_vehicle_effective) * a_piston`
- **Reibung:** Coulomb + viskos + Federkraft an Enden (1.9 bar Schwelle)

### Erwartete Verhaltensänderungen

1. Glattere Kolbenbewegung — Beschleunigung aus Kraftbilanz
2. Druckaufbau in Auslass-Kammer bei schneller Bewegung → natürliche Begrenzung
3. Bessere Energieerhaltung
4. Realistischere Übergänge an den Hubenden
5. Kopplung zwischen Fahrzeugdynamik und Kolben

### Zu prüfende Parameter

- `EXHAUST_FLOW_COEFF` — muss angepasst werden
- `PISTON_MASS_KG` — sollte effektive Masse enthalten
- `VEHICLE_MASS_KG` — Gesamtmasse
- `FREEWHEEL_BRAKE_FORCE_N` — Bremse zwischen Huben

---

## Session Summary — Stand 11.05.2026

### Was erledigt wurde

1. **Physik-Dokumentation** — `session_01_piston_force_balance.md` erstellt
2. **config.py** — `PISTON_VEHICLE_MASS_KG` hinzugefügt
3. **odesystem.py** — State-Vector 8→9, `get_exhaust_pressure()`, `get_exhaust_volume_L()`, Kraftbilanz aktualisiert
4. **simulate.py** — `direction_at_t` Liste, Plotting aktualisiert (noch nicht getestet)

### Noch zu tun

1. `python simulate.py --plot` ausführen
2. Physik-Verhalten analysieren (kontinuierliche Fahrt, P_exhaust > 1 bar, Distanz)
3. Parameter-Tuning (`EXHAUST_FLOW_COEFF`, `PISTON_VEHICLE_MASS_KG`, `FREEWHEEL_BRAKE_FORCE_N`)
4. Richtungsübergänge prüfen (n_exhaust konsistent?)
5. Debugging falls Simulation instabil

### Bekannte offene Fragen

1. `direction_at_t` muss bei Event-Toggles aktualisiert werden
2. n_exhaust bei Richtungswechsel — Gasmenge korrekt?
3. START-Verhalten: Kolben startet in Mitte (x=0.15m) — reicht P_exhaust?
4. Fahrzeug-Beschleunigung: `F_drive` ist noch `F_pressure`, nicht `F_net`

---

## Session 04: Kinetische Kopplung Piston-Belt & Parameter-Tuning (13.05.2026)

### Bugfix: Riemen-Kraft Vorzeichen am Kolben

**Problem:** Die Riemenkraft `F_belt` wurde immer negativ auf den Kolben gerechnet
(`F_net = ... - F_belt`), unabhängig von der Bewegungsrichtung. Bei `direction=-1`
(Linkshub) half die Riemenkraft dem Kolben statt zu bremsen → Simulation instabil
(586k steps / 300s).

**Fix:**
```python
# Vorher (falsch): Riemen bremst nur bei Rechtshub
F_net = F_pressure + F_spring + F_friction - F_belt

# Nachher (korrekt): Riemen wirkt immer entgegen der tatsächlichen Bewegung
belt_sign = np.sign(v_piston) if abs(v_piston) > 1e-8 else direction
F_net = F_pressure + F_spring + F_friction - belt_sign * F_belt
```

**Effekt:** Simulation von 587k → 42k Schritte (14× schneller), selbe Physik.

### Kinetische Kopplung (beide Richtungen → Vorwärts)

Der Freilauf-Mechanismus wandelt beide Kolbenrichtungen in Vorwärtsfahrt um:
- `target_v = abs(v_piston) * BELT_TO_WHEEL_RATIO` → immer positive Zielgeschwindigkeit
- `F_belt = (target_v - v_vehicle) * BELT_STIFFNESS * VEHICLE_MASS_KG`
- Antrieb nur wenn `v_vehicle < target_v` (Freilauf sonst)
- Fahrzeug rollt bei stehendem Kolben weiter (Freewheeling im `else`-Zweig)

### Parameter-Tuning

| Parameter | Alt | Neu | Grund |
|-----------|-----|-----|-------|
| `EXHAUST_FLOW_COEFF` | 2.5e-5 | 1.5e-4 | Zu niedrig → Piston auf 2.9 cm/s limitiert |
| `VALVE_ORIFICE_AREA_MM2` | 0.2 | 0.6 | Tropfrate zu gering → P_reactor fällt |
| `TANK_INITIAL_PRESSURE_BAR` | 3.0 | 4.0 | Tankdruck = Reaktor → Tropfstopp |
| `FREEWHEEL_BRAKE_FORCE_N` | 30.0 | 10.0 | Zu aggressive Bremse |
| `VEHICLE_MECHANICAL_DAMPING` | 3000 | 500 | Zu hohe Dämpfung |
| `BELT_STIFFNESS` | inline 500 | config 500 | Als Parameter ausgelagert |

### Aktuelle Performance (300s Simulation)

| Metrik | Vor Tuning | Nach Tuning |
|--------|-----------|-------------|
| Hübe | 35 + 1 | 47 + 1 |
| Gesamtdistanz | 10.20 m | 13.93 m |
| P_reactor (Ende) | 1.37 bar | 1.47 bar |
| P_reactor (nach 60s) | 1.77 bar | 2.56 bar |
| Ø Hubzeit | 8.33 s | 6.25 s |
| Ø Geschwindigkeit | 3.4 cm/s | 4.6 cm/s |
| Kolben-Endspeed | 1.5 cm/s | 2.2 cm/s |
| Zeitschritte | 41.944 | 225.288 |

Die ersten ~23 Hübe laufen bei P_reactor > 2 bar und 5.41 cm/s konstanter Endgeschwindigkeit.
Nach Unterschreiten von REGULATOR_OUTPUT_BAR sinkt die Antriebskraft kontinuierlich.

### Ursache P_reactor-Abfall

1. CO₂ löst sich im Reaktorwasser (Henry) → verzögerter Druckaufbau initial
2. Tankdruck sinkt mit Flüssigkeitsstand → Tropfrate sinkt
3. Bei P_tank ≈ P_reactor stoppt Tropf komplett → keine CO₂-Produktion mehr
4. Regulator verbraucht Rest-CO₂ aus Gasphase → P_reactor fällt weiter

**Mögliche Lösungsansätze:**
- Tank mit CO₂-Druck beaufschlagen (externer Druck)
- CITRIC_TANK_INITIAL_FILL reduzieren → mehr Gasvolumen im Tank
- Niedrigeren REGULATOR_OUTPUT_BAR wählen (z.B. 1.8 bar)

### Bekannte Probleme

1. **Steifigkeit bei P_reactor < 1.5 bar:** Solver braucht 80k Schritte pro Hub
   (Geschwindigkeitsnulldurchgang + geringe Antriebskraft)
2. **P_reactor fällt nach ~25 Hüben unter 2 bar:** Tankdruck sinkt mit
   Flüssigkeitsstand, Tropfrate → 0
3. **Fahrzeuggeschwindigkeit:** 5.41 cm/s ist realistisch, aber Freilauf-Bremse
   (10 N + 500·v) begrenzt Ausrollen zwischen Hüben

---

---

## Session 05: Quantitative Validierung & Reaktionskorrektur (14.05.2026)

### Gefundene Fehler

| # | Fehler | Datei | Fix |
|---|--------|-------|-----|
| 1 | `CITRIC_TANK_INITIAL_FILL = 0.04` → nur 10.8g Citric statt 27g | config.py | `0.10` → 27g |
| 2 | `TANK_INITIAL_PRESSURE_BAR = 3.0` (nicht aktualisiert) | config.py | `4.0` |
| 3 | `NACHTRON_MASS_KG = 0.35` → 10× Konzept-Wert | config.py | `0.05` (50g) |
| 4 | `ATMOSPHERIC_PRESSURE` doppelt definiert | config.py | Zeile 144 entfernt |
| 5 | `theoretical_distance = n * 0.157` Faktor von altem 1cm-Kolben | simulate.py:236 | Korrekte Formel `V / (A*1000)` |
| 6 | `REACTOR_HEADSPACE_RATIO` konstant (ignoriert Flüssigkeitszulauf) | odesystem.py | Dynamischer Headspace via `get_reactor_headspace_L()` |
| 7 | `get_reactor_water_volume_L` ohne Reaktionswasser | odesystem.py | `+ 3*H2O` pro Citric |
| 8 | Alle manuellen Druckberechnungen mit altem Headspace | simulate.py, plotting.py | `get_reactor_pressure(n_co2, n_air, n_citric)` |
| 9 | `IndexError` auf `t_events[1]` nach Citric-Depletion | simulate.py | Guard `not citric_depleted and len(t_events) > 1` |

### Korrigierte Parameter

| Parameter | Alt | Neu | Grund |
|-----------|-----|-----|-------|
| `CITRIC_TANK_INITIAL_FILL` | 0.04 (10.8g) | 0.10 (27.0g) | Konzept: 27g Citronensäure |
| `TANK_INITIAL_PRESSURE_BAR` | 3.0 | 4.0 | Höherer ∆P für Tropfrate |
| `NACHTRON_MASS_KG` | 0.35 (350g) | 0.05 (50g) | 42% Überschuss über Stöchiometrie (~35g) |
| `H2O_MOLAR_MASS` | — | 18.015 | Neu für Reaktionswasser-Tracking |

### Ergebnisse (300s Simulation)

| Metrik | Wert |
|--------|------|
| Start-Zitronensäure | 27.0 g ✅ |
| Citric-Verbrauch | Vollständig nach 138s ✅ |
| Theoretische Distanz | **12.4 m** (= 41 Hübe a 30cm) ✅ |
| Tatsächliche Distanz | 14.24 m (mit Tank-Gas-Nachströmung) |
| Hübe | 50 |
| Ø Hubzeit | 6.0 s |
| P_reactor (Start) | 1.0 bar |
| P_reactor (nach Aufbau) | ~3.8 bar |
| P_reactor (nach Citric-Depletion) | 3.25 bar stabil |
| Abrruch | Simulation Timeout 300s (kein Feder-Abbruch) |
| Fahrzeuggeschwindigkeit | ~4.7 cm/s |

### Verbleibende Beobachtungen

1. **Fahrzeug zu langsam** (4.7 cm/s) → Freilauf-Bremse + Rollwiderstand limitieren
2. **Tropfrate wird durch ∆P ≈ 0.3 bar begrenzt** → Zitronensäure braucht 138s für vollständige Reaktion
3. **P_reactor bleibt > 3.25 bar** → System könnte theoretisch weiterfahren, aber Fahrzeug steht durch Simulations-Timeouts

---

---

## Session 06: 10mm-Kolben RMS10X400 & Solver-Stabilität (14.05.2026)

### Änderungen für 10mm-Kolben

| Parameter | Alt (30mm) | Neu (10mm) | Grund |
|-----------|-----------|------------|-------|
| `PISTON_DIAMETER_MM` | 30.0 | 10.0 | RMS10X400 |
| `EXHAUST_FLOW_COEFF` | 1.5e-4 | 1.7e-5 | Skaliert mit A (1/9) |
| `PISTON_VISCOUS_FRICTION` | 1000 (hardcoded) | 300 | 9× weniger Kraft |
| `BELT_STIFFNESS` | 500 | 60 | Skaliert mit A |
| `FREEWHEEL_BRAKE_FORCE_N` | 10.0 | 1.5 | Skaliert mit A |
| `VEHICLE_MECHANICAL_DAMPING` | 500 | 60 | Skaliert mit A |
| `VEHICLE_ROLLING_RESISTANCE` | 0.08 | 0.05 | Reduziert für kleinere Kraft |
| `DEAD_VOLUME_M` | 0.005 (hardcoded) | 0.020 | Größerer Totraum für 10mm |
| `AXLE_FRICTION_TORQUE_NM` | 0.005 | 0.005 | Unverändert |

### Solver-Änderungen

- **LSODA → BDF**: LSODA blieb bei 10mm-Kolben hängen (97% Zeitschritte an einem Punkt). BDF arbeitet zuverlässig.
- **Solver-Fallback**: Bei BDF status=-1 wird automatisch auf Radau → LSODA → loose BDF zurückgegriffen.
- **n_co2_relief clamping**: Verhindert negative n_co2_gas bei Druck-Spikes.

### Ergebnisse (300s Simulation)

| Metrik | Wert |
|--------|------|
| Hübe | 12 |
| Zeit pro Hub | ~25 s |
| Gesamtdistanz | 2.38 m |
| P_reactor (Ende) | 2.51 bar |
| P_reactor (Spitze) | 25.08 bar (Citric-Exhaustion) |
| Zeitschritte | 37.697 |
| CSV-Größe | ~4 MB |

### Bekannte Probleme

1. **25 bar Druckspitze** bei Citric-Exhaustion (Kopfraum schrumpft durch Flüssigkeitszulauf) → entschärft durch Relief-Valve-Clamping
2. **25 s/Hub** ist langsam → Friction-Tuning nötig (300 N·s/m begrenzt Geschw. auf 1.2 cm/s)

---

## Nächste Schritte

1. [x] Simulation testen nach Korrekturen → läuft stabil
2. [x] Theoretische Distanz korrigiert → 12.4m (für 30mm)
3. [x] Chemische Eduktmengen auf Konzept-Niveau → 27g Citric, 50g NaHCO₃
4. [x] 10mm-Kolben RMS10X400 integriert → Simulation läuft
5. [x] Solver-Fallback für BDF-Abstürze → keine hängenbleibenden Läufe mehr
6. [ ] Fahrzeuggeschwindigkeit optimieren für 30m in 5 Minuten
7. [ ] Tropfrate erhöhen (Ventilquerschnitt oder Tankdruck) für schnellere Reaktion
