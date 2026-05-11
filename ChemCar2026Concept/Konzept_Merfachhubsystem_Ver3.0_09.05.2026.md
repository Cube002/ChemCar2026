# Konzept: Mehrfachhubsystem — Ver3.0 (Citric Aixpress)

## Zielsetzung

Das Fahrzeug soll eine **präzise, reproduzierbare Distanz** zurücklegen, die ausschließlich durch die Menge der eingesetzten Edukte einer chemischen Reaktion bestimmt wird – ohne elektronische Sensorik oder externe Steuerung.

---

## 1. Chemischer Reaktor (Gasquelle)

Das Reaktordesign wurde im Vergleich zu V2.1 grundlegend geändert:

### 1.1. Citronensäure-Tank (Edelstahl)

- **Material:** Edelstahl (PET verboten nach Safety Rules 6.2.5 / Appendix A)
- **Inhalt:** Verdünnte Citronensäure (C₆H₈O₇) in Wasser
- **Druck:** Vor dem Start auf **3 bar** gebracht
- **Funktionsweise:** Der Überdruck im Tank treibt die Citronensäure kontinuierlich durch ein Ventil am Boden an. Die Tropfgeschwindigkeit wird durch den Druckgradienten zwischen Tank und Reaktor geregelt.
- **Sicherheitsaspekt:** Bei Erreichen von 3 bar im Reaktor unterbricht der Druckgradient vorübergehend das Eintropfen → Selbstregulierung.

### 1.2. Reaktor (Edelstahl)

- **Inhalt:** Im Überschuss vorliegendes, gelöstes Natriumhydrogencarbonat (NaHCO₃)
- **Reaktion:**

  > C₆H₈O₇ + 3 NaHCO₃ → Na₃C₆H₅O₇ + 3 CO₂↑ + 3 H₂O

- **Begrenzender Faktor:** Die Zitronensäure. Sobald sie vollständig eingetroffen und reagiert ist, endet die Gasproduktion.
- **Reaktionstemperatur:** Leicht endotherm → geringe Abkühlung des Reaktorinhalts zu erwarten.

### 1.3. CO₂-Löslichkeit im Wasser

- Löslichkeit: **1,7 g/L bei 20°C und 1 bar** → ca. **0,116 mol CO₂ pro Liter Wasser** gelöst.
- Es ist zu erwarten, dass **mehr Zitronensäure benötigt** wird als theoretisch berechnet, da ein Teil des CO₂ im Wasser gelöst bleibt.
- Dieser Faktor muss durch Versuche konkret ermittelt und bei der Auslegung berücksichtigt werden.

### 1.4. CO₂-Neutralität (Ausblick)

- Mittels **Carbon-Capture-Verfahren** kann CO₂ aus der Atmosphäre extrahiert und in NaHCO₃ gebunden werden.
- Dieser CO₂-negative Speicher gibt in unserem ChemCar exakt die gleiche Menge CO₂ frei, die vorher extrahiert wurde → **CO₂-neutraler Antrieb** ist denkbar.

### 1.5. Druckminderer

- Reduziert den Reaktordruck auf konstante **2 bar** am Eingang des Pneumatiksystems.
- Funktioniert über eine Membran, die Umgebungsdruck und Systemdruck vergleicht.

### 1.6. Überdruckventil (Safety)

- Gewährleistet permanente Sicherheit vor, während und nach der Fahrt.
- Stellt sicher, dass das **Druckinhaltsprodukt (P·V) nicht 50 bar·L überschreitet** (Safety Rule 6.1).

---

## 2. Pneumatischer Antrieb (Festo-Kolben)

Ein **doppeltwirkender Pneumatikzylinder** (Festo, **Hubweg: 30 cm**) wandelt den Gasfluss in eine gleichmäßige Linearbewegung um.

- An **beiden Endpositionen** des Kolbens befindet sich je eine **Feder**, die so vorgespannt ist, dass der Kolben mindestens **1,9 bar** aufbringen muss, um sie vollständig zusammenzudrücken. Diese Federn dienen gleichzeitig als **mechanischer Endanschlag mit Druckschwelle**.
- Sobald der Kolben am Ende seines Hubs die Feder zusammendrückt, betätigt er einen **Taster (Button 1 / Button 2)**, der das Richtungsumschaltsignal auslöst.
- Ein **Drosselventil (Exhaust)** am Zylinderausgang begrenzt den Abluftfluss und steuert damit die **Kolbengeschwindigkeit** (~5 Sekunden pro Stroke), was eine gleichmäßige Bewegung sicherstellt.
- Der Antrieb muss neben der Trägheit und Reibung des Autos auch das **Reibmoment an der Achse** dauerhaft überwinden können.

---

## 3. Elektronische Steuerung (Richtungsumschaltung)

Die beiden Endlagentaster sind an ein **T-Flipflop** angeschlossen, das von einer **6V-Batterie** versorgt wird. Das Flipflop schaltet bei jedem Tasterdruck seinen Ausgang um (Low ↔ High) und steuert darüber einen **Transistor**, der wiederum ein **elektrisches 3/2-Wege-Ventil (Y-Ventil)** ansteuert.

- **Zustand A (Low):** Druckluft strömt in die linke Kolbenkammer → Kolben fährt nach rechts.
- **Zustand B (High):** Druckluft strömt in die rechte Kolbenkammer → Kolben fährt nach links.

Der Kolben pendelt so vollautomatisch hin und her, solange Gas produziert wird. Dabei wird bei **beiden Zuständen** CO₂ über das Drosselventil abgelassen.

### 3.1. Stoppeaktion (unter Vorbehalt)

Falls notwendig, kann eine **Iod-Uhr als Timer-Reaktion** verwendet werden:

- **Reaktion 1 (schnell):** Iod reagiert mit Ascorbinsäure (Vitamin C) zurück zu Iodid-Ionen.
- **Reaktion 2 (langsam):** Iodid-Ionen werden durch verdünntes Wasserstoffperoxid (H₂O₂) in saurer Lösung wieder zu elementarem Iod oxidiert.
- **Farbumschlag:** Sobald die Ascorbinsäure verbraucht ist, bildet sich ein dunkelblauer Iod-Stärke-Komplex.
- **Sensor:** Ein optischer Sensor erfasst den Farbumschlag und schließt elektrisch das Ventil zwischen Säuretank und Reaktor → Kolben verharrt in Position, Systemdruck steigt nicht weiter an.

> **Hinweis:** Wasserstoffperoxid ≤ 3% (Safety Rule 5.6). Iodtinktur und Ascorbinsäure sind nicht gesundheitsschädlich.

---

## 4. Kraftübertragung (Riemen & Freilauf)

Der bewegliche Teil des Kolbens ist über einen **Riemen** mit beiden Achsen verbunden. Jede Achse ist mit einem **Freilauf (Einwegkupplung)** ausgestattet, sodass jede Achse nur in **einer Drehrichtung** Kraft überträgt:

- **Vorwärtshub (Kolben nach rechts):** Die **Vorderachse** koppelt ein und treibt das Fahrzeug vorwärts. Die Hinterachse läuft frei.
- **Rückwärtshub (Kolben nach links):** Die **Hinterachse** koppelt ein (Riemen ist gegenläufig verbunden) und treibt das Fahrzeug ebenfalls vorwärts. Die Vorderachse läuft frei.

➜ Das Fahrzeug bewegt sich bei **jedem Kolbenhub** (hin wie her) um jeweils **30 cm** vorwärts. Die zurückgelegte Gesamtstrecke ist damit:

> **Gesamtstrecke = Anzahl der Hübe × 30 cm**

Da die Anzahl der Hübe direkt von der produzierten CO₂-Menge abhängt, und diese wiederum von der Eduktmenge, ergibt sich eine **lineare, chemisch gesteuerte Distanzkontrolle**.

---

## 5. Ablauf der Fahrt

1. **Start:** Ein Ventil wird geöffnet → Citronensäure tropft in den Reaktor → Reaktion startet → Fahrzeug bewegt sich.
2. **Normaler Stopp:** Fahrzeug stoppt automatisch, sobald die Zitronensäure vollständig abreagiert ist. Durch ein einstellbares Reibmoment an den Achsen bleibt das Auto nach Stillstand des Kolbens stehen.
3. **Nach der Fahrt:** Restdruck über gedrosseltes Ablassventil abbauen → Fahrzeug drucklos machen → Reaktor und Säuretank leeren und neu befüllen.
4. **Außerordentliche Beendigung:** Hauptventil schließen → wie unter 3. weiterfahren.

---

## 6. Zusammenfassung der Präzisionskette

```
Eduktmenge → CO₂-Volumen (netto) → Anzahl Kolbenhübe → Fahrstrecke
```

Jede Größe in dieser Kette ist direkt proportional zur vorherigen – das Konzept ist elegant und theoretisch sehr präzise reproduzierbar.

**Wichtige Einflussfaktoren:**
- CO₂-Löslichkeit im Wasser (~0,116 mol/L bei 20°C, 1 bar)
- Reibung und Trägheit des Fahrzeugs
- Drosselventil-Einstellung (~5 s pro Stroke)
- Federkennlinie und Ansprechdruck (1,9 bar)

---

## 7. Sicherheitsaspekte (Auswahl)

| Anforderung | Umsetzung |
|---|---|
| PET-Verbot (Safety 6.2.5) | Alle Behälter aus Edelstahl |
| P·V ≤ 50 bar·L | Überdruckventil dimensioniert |
| Relief Valve ≤ 1.1× P_max | Druckinhaltsprodukt berechnet |
| Pressure Gauge (2× P_max) | Manometer am Reaktor |
| CO₂-Abgas (Safety 5.3) | CO₂ ist explizit erlaubt |
| Keine offenen Behälter am Start | Ventil-geschlossenes System |
| Temperatur (endotherm) | < 0°C möglich → Isolierung prüfen |
| Elektrische Isolierung | Alle Leitungen isoliert/abgedeckt |
| Mechanische Absicherung | Schutzbleche für Riemen/Freiläufe |

---

## 8. Chemikalienliste

| Chemikalie | Menge | H-/P-Sätze |
|---|---|---|
| Citronensäure (C₆H₈O₇) | 1 kg | H315, H335 / P261, P280 |
| Natriumhydrogencarbonat (NaHCO₃) | 1 kg | – |
| Ascorbinsäure (C₆H₈O₆) | TBD | – |
| Iodtinktur | 100 mL | H226 / P211 |
| Wasserstoffperoxid 3% (H₂O₂) | 100 mL | H302+H332, H318 / P280, P310 |

---

## 9. Schematische Darstellung

```
==============================================================================
            SCHEMATISCHE DARSTELLUNG: MEHRFACHHUBSYSTEM V3
==============================================================================

   [ 1. CHEMISCHE GASQUELLE ]             [ 3. ELEKTRONIK & VENTIL ]
  +---------------------------+          +------------------------------+
  |    CITRIC-SAURER-TANK     |          |       6V BATTERIE            |
  |  (Edelstahl, 3 bar)       |          |              |               |
  +-------------|-------------+          |       [ T-FLIPFLOP ]         |
                |                        |              |               |
          { DRUCKTROPFVENTIL }          |       [ TRANSISTOR ]         |
                |                        +--------------|---------------+
                V                                       |
  +---------------------------+                [ 3/2-WEGE-VENTIL (Y) ]
  |    UNTERER REAKTOR        |                           |
  | (NaHCO3 + Citric -> CO2)  |                           | (Druckluft)
  +-------------|-------------+                           |
                |                                         V
      [ DRUCKREGULATOR ] <----------------------- [ 2. PNEUMATIK-UNIT ]
       (Reduzierung auf 2 bar)                     +----------------------+
                                                  |   FESTO KOLBEN       |
                                                  |  (Hubweg: 30 cm)     |
                                                  |                      |
                                                  | [BUTTON 1] + [SPRING]|
                                                  |          <->         |
                                                  | [BUTTON 2] + [SPRING]|
                                                  |          |           |
                                                  | [DROSSELVENTIL/EXH] |
                                                  +----------|-----------+
                                                             | (Kraftfluss)
                                                             V
==============================================================================
                   [ 4. KRAFTÜBERTRAGUNG / ANTRIEB ]
==============================================================================

          ACHSE A (VORNE)                        ACHSE B (HINTEN)
      +-----------------------+               +-----------------------+
      |  [ FREILAUF-KUPPLUNG] | <---(RIEMEN)--|  [ FREILAUF-KUPPLUNG] |
      +-----------|-----------+               +-----------|-----------+
                   |                                       |
               [ RAD A ]                               [ RAD B ]

------------------------------------------------------------------------------
LOGIK-FLUSS:
EDUKT -> CO2 -> DRUCK -> KOLBEN-HUB -> FREILAUF-KOPPLUNG -> VORWARTS-DRUCK
------------------------------------------------------------------------------
```
