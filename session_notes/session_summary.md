# ChemCar Session Summary — Stand: 11.05.2026

## Ziel
DGL-Modell des ChemCar Mehrfachhubsystems korrigieren, damit der Kolben physikalisch korrekt mit gekoppelter Kraftbilanz simuliert.

---

## Was erledigt wurde

### 1. Physik-Dokumentation
- File: `session_notes/session_01_piston_force_balance.md`
- Dokumentiert das Problem: Auslass-Kammer Druck wurde als konstant angenommen
- Dokumentiert die korrekte Kraftbilanz für doppeltwirkenden Zylinder
- Neue State-Variable `n_exhaust_mol` [8] hinzugefügt

### 2. config.py — geupdated
- `PISTON_VEHICLE_MASS_KG` hinzugefügt (Gesamtmasse für Beschleunigung)
- Berechnet als `PISTON_MASS_KG + VEHICLE_MASS_KG`

### 3. odesystem.py — geupdated (Hauptänderungen)
- State-Vector: 8 → 9 Variablen (neues Element [8] = n_exhaust_mol)
- Neue Funktion `get_exhaust_pressure()`: berechnet P_exhaust aus n_exhaust, x_piston, direction
- Neue Funktion `get_exhaust_volume_L()`: berechnet V_exhaust basierend auf Richtung
- `chemcar_odes()`:
  - Kraftbilanz: `F_net = (P_supply - P_exhaust) * A_piston - F_spring - F_friction`
  - Beschleunigung: `a_piston = F_net / PISTON_VEHICLE_MASS_KG`
  - `dydt[2] = a_piston` (dynamisch, nicht mehr erzwungen!)
  - `dydt[8]`: dn_exhaust/dt mit Kompression + Drosselventil-Flow
- `get_initial_state()`: initialisiert n_exhaust bei ambient pressure

### 4. simulate.py — teilweise geupdated
- `direction_at_t` Liste hinzugefügt für P_exhaust-Berechnung
- Plotting aktualisiert für 5 Plots (inkl. P_exhaust)
- **NOCH NICHT GETESTET** — Code muss ausgeführt und validiert werden

---

## Was NOCH zu tun ist

1. **Simulation testen**: `python simulate.py --plot`
2. **Physik-Verhalten analysieren**:
   - Fährt der Kolben kontinuierlich?
   - Bleibt P_exhaust > 1 bar (realistisch)?
   - Distanz plausibel?
3. **Parameter-Tuning**:
   - EXHAUST_FLOW_COEFF evtl. anpassen
   - PISTON_VEHICLE_MASS_KG überprüfen
   - FREEWHEEL_BRAKE_FORCE_N prüfen
4. **Richtungsübergänge prüfen**:
   - Bei x=0 und x=L: bleibt n_exhaust konsistent?
   - Gasmenge wechselt korrekt zwischen Kammern?
5. **Eventualität**: Wenn Simulation instabil oder keine Bewegung → Debugging

---

## Wichtige physikalische Prinzipien (korrigiert)

### Doppeltwirkender Zylinder
```
Kammer 1 (Versorgung): P = REGULATOR_OUTPUT_BAR (2 bar, konstant)
Kammer 2 (Auslass):    P = n_exhaust * R * T / V_exhaust(x, direction)
```

### Kraftbilanz
```
F_net = (P_supply - P_exhaust) * A_piston - F_friction - F_spring
a_piston = F_net / (m_piston + m_vehicle)
```

### Rückkopplung
```
Kolbenposition → V_exhaust → P_exhaust → F_net → a_piston → v_piston → x_piston
```

### Drosselventil
- Flow: `Q = C_exhaust * sqrt(P_exhaust - P_ambient)`
- **Indirekte** Geschwindigkeitsbegrenzung (nicht direkt erzwungen!)
- Gas entweicht durch Ventil → P_exhaust sinkt → mehr Netto-Kraft

---

## Bekannte offene Fragen

1. Richtungtracking bei Plot: `direction_at_t` muss bei Event-Toggles aktualisiert werden
2. n_exhaust bei Richtungswechsel: Muss geprüft werden ob Gasmenge korrekt bleibt
3. START-Verhalten: Kolben startet in der Mitte (x=0.15m) — reicht P_exhaust für Bewegung?
4. Fahrzeug-Beschleunigung: F_drive ist noch immer F_pressure (nicht F_net) — sollte F_net verwendet werden?

---

## Nächster Schritt beim Restart
1. `python simulate.py --plot` ausführen
2. Fehler analysieren
3. Plots auswerten
4. Bei Problemen: odesystem.py debuggen
