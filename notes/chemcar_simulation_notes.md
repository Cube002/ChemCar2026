# ChemCar Simulation — Persistent Notes

**Stand:** 12.05.2026

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

## Nächste Schritte

1. [ ] Simulation testen: `python simulate.py --plot`
2. [ ] Ergebnisse analysieren
3. [ ] Bei Problemen: odesystem.py debuggen
4. [ ] Parameter-Tuning
5. [ ] Bei Erfolg: Dokumentation aktualisieren
