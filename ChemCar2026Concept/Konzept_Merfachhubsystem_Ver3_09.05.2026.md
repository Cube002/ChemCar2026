# Konzept: Mehrfachhubsystem Ver3

**Team:** Citric Aixpress  
**Datum:** 09.05.2026  
**Version:** 3.0

---

## Zielsetzung

Das Fahrzeug soll eine **präzise, reproduzierbare Distanz** zurücklegen, die ausschließlich durch die Menge der eingesetzten Edukte einer chemischen Reaktion bestimmt wird – ohne elektronische Sensorik oder externe Steuerung.

---

## 1. Chemischer Reaktor (Gasquelle)

Der Reaktor besteht aus zwei Behältern:

- **Oberer Tank (Edelstahl):** Enthält Zitronensäure (C₆H₈O₇) in verdünnter wässriger Form, vor dem Start auf **3 bar Druck** gebracht. Durch ein Ventil unten am Behälter tropft die Säure kontrolliert in den Reaktor. Der Überdruck im Edelstahltank gewährleistet das Eintropfen auch bei höherem Reaktordruck.

- **Unterer Reaktor (Edelstahl):** Enthält Natriumhydrogencarbonat (NaHCO₃) in gelöster Form im Überschuss. Die eintropfende Zitronensäure reagiert mit dem Natron zu CO₂, Wasser und Natriumcitrat:

  > C₆H₈O₇ + 3 NaHCO₃ → Na₃C₆H₅O₇ + 3 CO₂↑ + 3 H₂O

  Der **begrenzende Faktor** ist die eintropfende Zitronensäure. Sobald sie vollständig verbraucht ist, endet die Gasproduktion – das **Gesamtgasvolumen ist damit direkt proportional zur eingesetzten Eduktmenge**, was die präzise Steuerung der Fahrstrecke ermöglicht.

- **Wichtiger Hinweis zur CO₂-Löslichkeit:** Ein Teil des produzierten CO₂ löst sich im Wasser (ca. 1,7 g/L bei 20°C und 1 bar ≈ 0,116 mol/L). Dies ist bei der Berechnung der Eduktmenge zu berücksichtigen und muss in Versuchen konkret ermittelt werden.

- Ein **Konstant-Druckminderer** reduziert den Reaktordruck auf konstante **2 bar** am Eingang des Pneumatiksystems, unabhängig vom aktuellen Reaktorinnendruck. Der Druckminderer vergleicht über eine Membran Umgebungsdruck und Systemdruck und passt entsprechend an.

- Ein **Überdruckventil** gewährleistet Sicherheit vor, während und nach der Fahrt und stellt sicher, dass das **Druckinhaltsprodukt 50 bar·L nicht überschreitet**.

---

## 2. Pneumatischer Antrieb (Festo-Kolben)

Ein **doppeltwirkender Pneumatikzylinder** (Festo, Hubweg: **30 cm**) wandelt den Gasfluss in eine gleichmäßige Linearbewegung um.

- An **beiden Endpositionen** des Kolbens befindet sich je eine **Feder**, die so vorgespannt ist, dass der Kolben mindestens **1,9 bar** aufbringen muss, um sie vollständig zusammenzudrücken. Diese Federn dienen gleichzeitig als **mechanischer Endanschlag mit Druckschwelle**.

- Sobald der Kolben am Ende seines Hubs die Feder zusammendrückt, betätigt er einen **Taster (Button 1 / Button 2)**, der das Richtungsumschaltsignal auslöst.

- Ein **Drosselventil (Exhaust)** am Zylinderausgang begrenzt den Abluftfluss und steuert damit die **Kolbengeschwindigkeit**, was eine gleichmäßige Bewegung sicherstellt. Hierbei ist zu gewährleisten, dass der Antrieb neben der Trägheit und Reibung des Fahrzeugs auch das **Reibmoment an den Achsen** dauerhaft überwinden kann.

- **Wichtig:** Der Antrieb muss neben der Trägheit und Reibung des Autos auch in der Lage sein, dauerhaft das Reibmoment zum Bremsen des Autos an der Achse zu überwinden.

---

## 3. Elektronische Steuerung (Richtungsumschaltung)

Die beiden Endlagentaster sind an ein **T-Flipflop** angeschlossen, das von einer **6V-Batterie** versorgt wird. Das Flipflop schaltet bei jedem Tasterdruck seinen Ausgang um (Low ↔ High) und steuert darüber einen **Transistor**, der wiederum ein **elektrisches 3/2-Wege-Ventil (Y-Ventil)** ansteuert.

- **Zustand A (Low):** Druckluft strömt in die linke Kolbenkammer → Kolben fährt nach rechts.
- **Zustand B (High):** Druckluft strömt in die rechte Kolbenkammer → Kolben fährt nach links.

Der Kolben pendelt so **vollautomatisch** hin und her, solange Gas produziert wird. Dabei wird bei **beiden Zuständen** CO₂ über das Drosselventil abgelassen.

### Optional: Stoppeaktion (unter Vorbehalt)

Falls notwendig, kann eine **Iod-Uhr mit Ascorbinsäure** als Timer-Reaktion verwendet werden:

- Zunächst reagiert das gebildete Iod schnell mit Ascorbinsäure zurück zu Iodid-Ionen (keine sichtbare Farbänderung).
- Parallel dazu wird aus Iodid durch Wasserstoffperoxid in saurer Lösung langsam neues Iod gebildet.
- Erst wenn die Ascorbinsäure verbraucht ist, bildet sich der charakteristische **dunkelblaue Iod-Stärke-Komplex**.
- Dieser Farbumschwung wird von einem **optischen Sensor** erfasst und schließt elektrisch das Ventil zwischen Säuretank und Reaktor → der Kolben verharrt in seiner Position.

---

## 4. Kraftübertragung (Riemen & Freilauf)

Der bewegliche Teil des Kolbens ist über einen **Riemen** mit beiden Achsen verbunden. Jede Achse ist mit einem **Freilauf (Einwegkupplung)** ausgestattet, sodass jede Achse nur in **einer Drehrichtung** Kraft überträgt:

- **Vorwärtshub (Kolben nach rechts):** Die **Vorderachse** koppelt ein und treibt das Fahrzeug vorwärts. Die Hinterachse läuft frei.
- **Rückwärtshub (Kolben nach links):** Die **Hinterachse** koppelt ein (Riemen ist gegenläufig verbunden) und treibt das Fahrzeug ebenfalls vorwärts. Die Vorderachse läuft frei.

➜ Das Fahrzeug bewegt sich bei **jedem Kolbenhub** (hin wie her) um **30 cm** vorwärts. Die zurückgelegte Gesamtstrecke ist damit:

> **Gesamtstrecke = Anzahl der Hübe × 30 cm**

Da die Anzahl der Hübe direkt von der produzierten CO₂-Menge abhängt, und diese wiederum von der Eduktmenge, ergibt sich eine **lineare, chemisch gesteuerte Distanzkontrolle**.

---

## Zusammenfassung der Präzisionskette

```
Eduktmenge → CO₂-Volumen → Anzahl Kolbenhübe → Fahrstrecke
```

Jede Größe in dieser Kette ist direkt proportional zur vorherigen – das Konzept ist elegant und theoretisch sehr präzise reproduzierbar.

---

## Reaktionsgleichung

```
C₆H₈O₇ + 3 NaHCO₃ → Na₃C₆H₅O₇ + 3 CO₂↑ + 3 H₂O
```

- Citronensäure : 3 Natriumhydrogencarbonat
- Reaktion verläuft in Wasser **leicht endotherm** → leichtes Abkühlen des Reaktorinhalts zu erwarten
- Produkte: Natriumcitrat, CO₂, Wasser – alles gesundheitlich unbedenklich

---

## Chemikalienübersicht

| Chemikalie | Menge | H-Sätze | P-Sätze |
|---|---|---|---|
| Citronensäure | ca. 1 kg | H315, H335 | P261, P280, P305+P351+P338 |
| Natriumhydrogencarbonat | ca. 1 kg | – | – |
| Ascorbinsäure | TBD | – | – |
| Iodtinktur | 100 ml | H226 | P211 |
| Wasserstoffperoxid 3% | 100 ml | H302+H332, H318 | P280, P302+P352, P305+P351+P338, P310 |

---

## Ablauf der Fahrt

1. **Start:** Ein Ventil wird geöffnet, wodurch gelöste Zitronensäure kontrolliert in den Reaktor fließt und die Reaktion startet. Das Fahrzeug stoppt, sobald die Zitronensäure aufgebraucht ist. Durch ein einstellbares Reibmoment an den Achsen bleibt das Auto nach Stillstand des Kolbens stehen.

2. **Nach der Fahrt:** Zuerst wird der Restdruck über ein gedrosseltes Ablassventil abgelassen und das Fahrzeug drucklos gemacht. Danach können Reaktor und Edelstahltank geleert und neu befült werden.

3. **Außergewöhnliches Beenden:** Zunächst wird das Hauptventil geschlossen, dann wie unter Punkt 2 verfahren.

---

## Vorberechnung (grob)

```
27 g Citronensäure + 35 g Natron → ~10 L CO₂ bei "0 bar"

Bei 2 bar Überdruck: W = P·dV = 2 bar × 5 L = 1000 J

Kolben: Hubweg 0,3 m, Druckfläche ≈ 7,85 cm²
Kolbenkraft: F ≈ 7,85 N

Gasverbrauch pro Hub: ~0,157 L pro Meter Kolbenweg
```

---

## CO₂-Neutralität

Die Reaktion von Citronensäure und Natriumhydrogencarbonat setzt CO₂ frei, das den Treibhauseffekt verstärkt. **CO₂-neutraler Antrieb ist denkbar**, wenn mittels Carbon-Capture-Verfahren CO₂ aus der Atmosphäre extrahiert und in Natriumhydrogencarbonat gebunden wird. Dieser CO₂-negative Speicher kann im ChemCar exakt die Menge CO₂ wieder freisetzen, die vorher aus der Atmosphäre extrahiert wurde.

---

```
==============================================================================
              SCHEMATISCHE DARSTELLUNG: MEHRFACHHUBSYSTEM V3
==============================================================================

   [ 1. CHEMISCHE GASQUELLE ]             [ 3. ELEKTRONIK & VENTIL ]
  +---------------------------+          +------------------------------+
  |    EDELSTAHL-TANK         |          |       6V BATTERIE            |
  | (Citronensäure, 3 bar)    |          |              |               |
  +-------------|-------------+          |       [ T-FLIPFLOP ]         |
                |                        |              |               |
          { VENTIL }                     |       [ TRANSISTOR ]         |
                |                        +--------------|---------------+
                V                                       |
  +---------------------------+                [ 3/2-WEGE-VENTIL (Y) ]
  |    UNTERER REAKTOR        |                           |
  | (NaHCO₃ im Überschuss)    |                           | (Druckluft)
  +-------------|-------------+                           |
                |                                         V
      [ DRUCKREGELREGULATOR ] <----------------------- [ 2. PNEUMATIK-UNIT ]
       (Reduzierung auf 2 bar)                       +----------------------+
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
EDUKT → CO₂ → DRUCK → KOLBEN-HUB → FREILAUF-KOPPLUNG → VORWÄRTS-DRUCK
------------------------------------------------------------------------------
```
