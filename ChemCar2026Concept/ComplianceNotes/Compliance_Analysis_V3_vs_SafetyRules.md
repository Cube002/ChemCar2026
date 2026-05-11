# Compliance Notes: Mehrfachhubsystem vs. ChemCar Safety Rules 2026

**Erstellt:** 09.05.2026  
**Referenz:** ChemCar_2026_Safety_Rules_.pdf (Rev. 1.0.2026)

---

## 1. Übersicht

Diese Datei analysiert das Konzept (Ver3.0) gegen die ChemCar 2026 Safety Rules.  
Jede Regel wird bewertet: **ERFÜLLT**, **TEILWEISE**, **NICHT ERFÜLLT**, **OFFEN**.

---

## 2. Regel-für-Regel-Analyse

### 3. Audits

| Regel | Status | Anmerkungen |
|---|---|---|
| 3.1 Paperwork Audit | **OFFEN** | Certifications Page, Safety Analysis, P·V Berechnung, Relief Sizing, Hydrotest Protocol, Bilder, SDS alle benötigt. Deadline beachten! |
| 3.2 Physical Audit | **OFFEN** | Gedrucktes Safety-Konzept muss bei Competition mitgeführt werden. |

---

### 4. Disallowed Chemical Handling

| Regel | Status | Anmerkungen |
|---|---|---|
| 4.1 Illegal Chemical Storage | **ERFÜLLT** | Chemikalien werden im bereitgestellten Storage-Bereich gelagert, nicht in Hotelzimmern. |
| 4.2 Illegal Testing | **ERFÜLLT** | Tests nur in Laboren mit Chemical-Handling-Fähigkeit. |
| 4.3 Illegal Disposal | **ERFÜLLT** | Entsorgung gemäß regulatorischer Maßnahmen. SDS vorhanden. |

---

### 5. Disallowed Vehicles

| Regel | Status | Anmerkungen |
|---|---|---|
| 5.1 Flames/smoke | **ERFÜLLT** | Keine offenen Flammen. Reaktion ist CO₂-basiert, keine Rauchentwicklung. |
| 5.2 Liquid Discharge | **ERFÜLLT** | Keine flüssige Entladung unter normalen Bedingungen. Bei Notfall: Containment vessel vorgesehen. |
| 5.3 Exhaust | **ERFÜLLT** | CO₂ ist explizit als erlaubtes Gas in kleinen Mengen aufgeführt. |
| 5.4 Open/Improper Containers | **TEILWEISE** | Alle Behälter fest am Fahrzeug montiert. Deckel sicher befestigt. **Noch zu dokumentieren:** Wie genau sind Container gesichert? |
| 5.5 No open containers at start | **TEILWEISE** | Citric-Säure-Tank ist ventilverschlossen → kein offenes Behältnis. **Noch zu prüfen:** Labeling aller Container. |
| 5.6 H₂O₂ ≤ 30% | **ERFÜLLT** | Verwendetes H₂O₂: 3% (deutlich unter 30%). |

---

### 6. Pressure Related Restrictions

| Regel | Status | Anmerkungen |
|---|---|---|
| **6.1 P·V ≤ 50 bar·L** | **TEILWEISE** | **MUSS BERECHNET WERDEN.** Reaktor + Citric-Tank Volumen × max. Druck ≤ 50 bar·L. Druckinhaltsprodukt quantitatativ bestimmen. |
| **6.2 >1 bar Überdruck** | **TEILWEISE** | Beide Tanks (~3 bar) und Reaktor (>1 bar Überdruck) unterliegen den Anforderungen. |
| **6.2.1 Pressure Gauge** | **NICHT ERFÜLLT** | **FEHLT NOCH.** Manometer mit Messbereich bis 2× max. Betriebsdruck (≥6 bar) am Reaktor und Citric-Tank einbauen. |
| **6.2.2 Relief Valve** | **TEILWEISE** | Überdruckventil erwähnt, aber **noch nicht dimensioniert**. P_relief ≤ 1.1 × P_max. Design-Basis: Menge reagierender Edukte, Konzentration, Start-Temperatur, Fehlerfälle (Overcharge). |
| **6.2.3 Relief Location** | **OFFEN** | Relief Valve muss oben am Reaktor sitzen, keine abschließbaren Ventile dazwischen. Röhren dimensionieren. |
| **6.2.4 Proper Charging** | **OFFEN** | Messgeräte (Zylindern, Becher) mit Max-Markierung. Mindestens 1 Beobachter beim Befüllen. Car tag nach Befüllung. |
| **6.2.5 PET-Verbot** | **ERFÜLLT** | **WICHTIG:** V2.1 verwendete PET-Flasche → VERBOTEN. V3.0 verwendet Edelstahl → KONFORM. |
| **Appendix A: Pressure Vessel Test** | **NICHT ERFÜLLT** | **Hydrostatischer Test (Wasser) für jeden Druckbehälter erforderlich.** P_test = 1.2 × P_max. Manometer 1.5–4× P_test. Verformungsmessung mit 0.02 mm Präzision. |

---

### 7. Other Potential Hazards

| Regel | Status | Anmerkungen |
|---|---|---|
| **7.1 Temperature** | **OFFEN** | Reaktion ist **endotherm** → Abkühlung unter 0°C möglich! Oberflächen < 0°C müssen isoliert/abgedeckt werden. |
| **7.2 Electrical** | **TEILWEISE** | T-Flipflop (6V), Transistor, Verkabelung müssen isoliert/abgedeckt sein. Keine Alligator Clips! Banana Plugs oder Binding Posts verwenden. |
| **7.3 Mechanical** | **NICHT ERFÜLLT** | **FEHLEN NOCH.** Schutzbleche für Riemen, Freiläufe, Getriebe und alle Pinch Points einbauen. |
| **7.4 Biohazards** | **ERFÜLLT** | Keine biologischen Organismen im Einsatz. |

---

### 8. Competition Day Rules

| Regel | Status | Anmerkungen |
|---|---|---|
| **8.1 PSA** | **OFFEN** | PPE bereitstellen: Lab coat, Schutzbrille, Handschuhe, ggf. Gesichtsschutz. |
| **8.2 Equipment labeling** | **OFFEN** | Alle Container mit Name der Chemikalie + ChemCar-Team labeln. |
| **8.3 Handling** | **ERFÜLLT** | Transport- Tray vorgeschrieben. Mixing-Bereich wird bereitgestellt. |
| **8.4 Documentation** | **OFFEN** | Alle Safety-Dokumente, SDS, Operating Instructions **gedruckt** mitbringen. |

---

## 3. Zusammenfassung der offenen Punkte

### KRITISCH (muss vor Competition erledigt sein)

| # | Aufgabe | Priorität | Regel |
|---|---|---|---|
| 1 | **P·V-Berechnung quantifizieren** (alle Druckbehälter) | KRI- TISCH | 6.1 |
| 2 | **Relief Valve dimensionieren** (P≤1.1×P_max, Design-Basis) | KRI- TISCH | 6.2.2 |
| 3 | **Hydrostatic Testing Protocol** für jeden Druckbehälter | KRI- TISCH | Appendix A |
| 4 | **Pressure Gauge** (2×P_max) an allen >1 bar Behältern | HOCH | 6.2.1 |
| 5 | **Mechanische Schutzbleche** für Riemen/Freiläufe | HOCH | 7.3 |
| 6 | **Temperaturisolierung** falls <0°C möglich | HOCH | 7.1 |
| 7 | **Proper Charging System** (Messgeräte mit Max-Markierung, Tagging) | HOCH | 6.2.4 |

### WICHTIG

| # | Aufgabe | Priorität | Regel |
|---|---|---|---|
| 8 | Container-Sicherung dokumentieren | MITTEL | 5.4 |
| 9 | Electrical connectors (keine Alligator Clips) | MITTEL | 7.2 |
| 10 | PPE-Auswahl und -Bereitstellung | MITTEL | 8.1 |
| 11 | Container-Labeling-Standard | MITTEL | 8.2 |
| 12 | Gedruckte Safety-Dokumentation | MITTEL | 8.4 |
| 13 | Paperwork Audit fristgerecht einreichen | MITTEL | 3.1 |

### OFFEN (zu klären)

| # | Aufgabe | Regel |
|---|---|---|
| 14 | Relief Valve Position (oben am Reaktor, keine Ventile dazwischen) | 6.2.3 |
| 15 | Blow-off gas treatment (adsorbent material for entrained substance) | 6.2.3 |
| 16 | Iod-Uhr Stoppeaktion: H₂O₂ ≤3% bestätigt? | 5.6 |

---

## 4. Änderungen V2.1 → V3.0 im Safety-Kontext

| Änderung | Safety-Auswirkung |
|---|---|
| PET-Flasche → Edelstahl-Tank | **POSITIV:** PET-Verbot (6.2.5) nun erfüllt |
| Citric-Säure in Tank (gedruckt) | **NEU:** Tank unterliegt Pressure Vessel Rules |
| Überdruckventil erwähnt | **NEU:** Erforderlich für 6.2.2 |
| CO₂-Löslichkeit berücksichtigt | **NEU:** Beeinflusst Eduktmenge und damit P_max |
| Iod-Uhr als optionale Stoppeaktion | **ZUSÄTZLICH:** H₂O₂ SDS, PPE, Entsorgung |
| Endotherme Reaktion | **NEU:** Temperaturisolierung <0°C prüfen (7.1) |

---

## 5. Checklist für Safety Audit

- [ ] Certifications Page (Template)
- [ ] Completed Safety Analysis (Template)
- [ ] P·V quantitatve Design Basis
- [ ] Relief Valve Sizing Calculations
- [ ] Pressure Relief Test Procedure & Results
- [ ] Pressure Vessel Testing Protocol (Hydrotest)
- [ ] Vehicle pictures (current, entire car visible)
- [ ] SDS für alle Chemikalien
- [ ] Gedruckte Safety-Dokumentation für Physical Audit
- [ ] Original-Signaturen der Safety Analysis eingescannt an chemcar@vdi.de
