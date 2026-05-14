# Report: Solver-Stabilität beim 10mm-Kolben (RMS10X400)

**Datum:** 14.05.2026  
**Autor:** opencode (Simulations-Analyse)

---

## 1. Problembeschreibung

Nach Umstellung des Pneumatikzylinders von 30mm auf 10mm Durchmesser (RMS10X400) zeigte das ODE-System folgende Symptome:

1. **Solver hängt** (`solve_ivp` kehrt nicht zurück) → 97% aller Zeitschritte an einem Punkt
2. **`status=-1` (Integration failed)** ohne ersichtlichen Grund
3. **Plots/CSVs werden mehrere MB groß** durch die extrem vielen Zeitschritte
4. **Simulation bricht frühzeitig ab** mit Meldung "Fahrzeug steht", obwohl noch Druck vorhanden ist

---

## 2. Root Causes

### 2.1 LSODA versagt bei 10mm-Kolben

**Ursache:** LSODA wechselt automatisch zwischen Adams (nicht-steif) und BDF (steif). Bei der Feder-Vorspannung am Hubanfang (x=0, Feder drückt Kolben mit 1.57N an) erkennt LSODA die Steifheit nicht rechtzeitig und bleibt im Adams-Modus mit extrem kleinen Zeitschritten hängen.

**Warum beim 30mm-Kolben OK?**  
Dort war die Federkraft 63.6N (k=3182 N/m) → das System hatte eine klarere Steifheit, die LSODA sofort erkannte.

### 2.2 BDF bricht mit Jacobian-Overflow ab

**Ursache:** Bei Annäherung an die Hubenden wird das Auslassvolumen sehr klein (V = DEAD_VOLUME_M × A). Der numerische Jacobian (finite Differenzen) produziert Einträge:

```
d(a_piston)/d(n_exhaust) = -(R·T/V) · 1e5 · A · direction / m
```

Bei V → 0 geht dieser Term gegen ∞. Der Solver kann die Schrittweite nicht mehr kontrollieren → `status=-1`.

### 2.3 Falsche Endbedingung nach Citric-Exhaustion

**Ursache:** `simulate.py` prüfte `citric_depleted AND abs(v_vehicle) < 0.01`. Direkt nach einem Hub steht das Fahrzeug durch Freilauf-Bremse kurz still → Bedingung feuert sofort → Simulation endet mit nur 9 Hüben, obwohl 2.5 bar Restdruck vorhanden sind.

### 2.4 Kein Fallback-Mechanismus

**Ursache:** Bei `status=-1` wurde die Simulation sofort abgebrochen, ohne einen alternativen Solver zu versuchen.

---

## 3. Guidelines für zukünftige Simulationen

### Regel 1: Immer Solver-Fallback verwenden

```python
solver_configs = [
    {'method': 'BDF',   'rtol': 1e-6, 'atol': 1e-8, 'max_step': 0.01},
    {'method': 'Radau', 'rtol': 1e-5, 'atol': 1e-7, 'max_step': 0.05},
    {'method': 'LSODA', 'rtol': 1e-5, 'atol': 1e-7, 'max_step': 0.01},
]

for cfg in solver_configs:
    sol = solve_ivp(..., **cfg)
    if sol.status != -1:
        break
# Letzter Versuch mit sehr losen Toleranzen
if sol.status == -1:
    sol = solve_ivp(..., method='BDF', rtol=1e-3, atol=1e-4, max_step=0.1)
```

**Nie** ohne Fallback arbeiten. Jeder Solver kann bei steifen ODEs versagen.

### Regel 2: Hydraulische Toträume vergrößern

Bei Kolben mit kleinem Durchmesser (10mm vs 30mm) muss DEAD_VOLUME_M erhöht werden, da  
- V_min = DEAD_VOLUME_M × A  
- dP/dn = R·T / V → je kleiner V, desto steifer das System  
- Faustregel: V_min ≥ 1e-3 L (hier: DEAD_VOLUME_M = 0.020m → V_min = 1.57e-3 L)

### Regel 3: Keine harten Endbedingungen

Statt `citric_depleted AND abs(v_vehicle) < 0.01` (feuert zwischen Hüben):

```python
# Besser: prüfe ob Kolben UND Fahrzeug wirklich stehen
if citric_depleted and abs(y[2]) < 0.001 and abs(y[4]) < 0.001:
    break
# Oder: verlasse dich auf Druck-Schwellwert
if P_current < SPRING_PRELOAD_BAR:
    break
```

### Regel 4: Relief-Valve-Clamping

**Immer** die Entlastung begrenzen:

```python
n_co2_relief = min(n_co2_relief, max(0.0, y[5]) * 10.0)
```

Ohne Clamping kann n_co2_gas negativ werden → P_reactor = 0.1 bar → Regler schließt → Simulation friert.

### Regel 5: Kräfte skalieren bei Geometrieänderung

| Größe | Skalierung bei 30mm → 10mm |
|-------|---------------------------|
| Fläche A | ×(10/30)² = ×1/9 |
| Federkraft | ×A (automatisch, wenn Formel A enthält) |
| Reibung | ×1/9 (sonst dominiert Reibung) |
| Drosselquerschnitt | ×1/9 (sonst entleert sich Kammer zu schnell) |
| Riemensteifigkeit | ×1/9 (sonst übersteigt Riemenkraft Antriebskraft) |
| Fahrzeugdämpfung | ×1/9 (sonst kann Fahrzeug nicht beschleunigen) |

### Regel 6: Bei Verdacht auf Steifheit → BDF statt LSODA

LSODA erkennt Steifheit nicht immer. BDF (oder Radau) sind robuster für chemisch-mechanisch gekoppelte Systeme.

### Regel 7: Output-Downsampling

Bei vielen Zeitschritten (>10k) den Output downsamplen:

```python
stride = max(1, len(t) // 10000)
t_sampled = t[::stride]
y_sampled = y[::stride]
```

---

## 4. Aktueller Status

| Kriterium | Status |
|-----------|--------|
| Simulation läuft 300s durch | ✅ |
| Keine hängenden Solver | ✅ |
| Alle Events werden erkannt | ✅ |
| Fallback bei Solver-Failure | ✅ |
| Plots < 2 MB | ✅ |
| CSV < 5 MB (37k steps) | ✅ |
| Geschwindigkeit | ⚠️ 25s/Hub (langsam, aber stabil) |
| Druckspitze Citric-Exhaustion | ⚠️ 25 bar (geclamped, aber hoch) |
