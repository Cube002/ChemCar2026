# Sicherheits-Compliance-Analyse

**Team:** Citric Aixpress  
**Konzept:** Mehrfachhubsystem Ver3  
**Datum:** 09.05.2026  
**Referenz:** ChemCar 2026 Safety Rules (Rev. 1.0.2026)

---

## 1. Chemikalien (Sections 4, 5, 8)

### Erfüllt:
- **5.1 (Flammen/Rauch):** Keine offenen Flammen, keine Rauchentwicklung. ✓
- **5.3 (Abgase):** CO₂ und Wasser dampf sind explizit als erlaubte Emissionen gelistet. ✓
- **5.6 (Wasserstoffperoxid < 30%):** Wird 3% H₂O₂ verwendet (nur für optionale Stoppeaktion). ✓
- **Chemikalienliste:** Alle verwendeten Chemikalien sind in der Konzept-PDF mit H/P-Sätzen und Mengen gelistet. ✓

### Muss angepasst/ergänzt werden:
- **4.3 (Entsorgung):** Muss im Konzept dokumentiert werden, wie die Chemikalien entsorgt werden. → *Notiz: Entsorgungskonzept muss ergänzt werden.*
- **8.2 (Kennzeichnung):** Alle Container müssen beschriftet sein. → *Muss im Betrieb gewährleistet werden.*
- **Ascorbinsäure/Iod/H₂O₂:** Nur für optionale Stoppeaktion; Menge TBD. → *Entscheidung treffen, ob Stoppeaktion benötigt wird.*

---

## 2. Druckbehälter & Sicherheit (Section 6)

### Erfüllt:
- **6.1 (50 bar·L Limit):** Fahrzeug ist mit Überdruckventil ausgestattet. Druckinhalt muss berechnet und dokumentiert werden. → *Quantitative Berechnung muss ergänzt werden.*
- **6.2 (Überdruck > 1 bar):** Anforderungen an Druckbehälter gelten.

### Muss angepasst/ergänzt werden:
- **6.2.1 (Manometer):** Alle Behälter mit > 1 bar Überdruck benötigen ein Manometer bis 2× dem max. Betriebsdruck. → *Manometer spezifizieren und einbauen.*
- **6.2.2 (Notfall-Druckentlastung):** Industry-Standard Relief Valve bei ≤ 1,1× max. Betriebsdruck erforderlich. → *Relief Valve dimensionieren (Größe, Typ, Set-Point) und Berechnung dokumentieren.*
- **6.2.3 (Position des Relief Valves):** Muss oben am Behälter ohne absperrbare Ventile sitzen. → *Bauweise muss entsprechend ausgelegt werden.*
- **6.2.4 (Lademanagement):** System zur sicheren Mengenbestimmung der Edukte. → *Messvorrichtungen (Zollstock, Messkolben) mit Max-Markierung spezifizieren.*
- **6.2.5 (Verbotene Materialien):** **PET ist explizit verboten** für Druckgase!

### ⚠️ KRITISCH – Muss geändert werden:
- **6.2.5 & Appendix A (Materialverbot):** Das Konzept verwendet eine **PET-Flasche** für den oberen Tank. **PET (polyethylene terephthalate) ist für Druckgas-Anwendungen verboten** wegen mikroskopischer Defekte, die zu Hoop-Stress-Failure führen.
  - **Lösung:** Oberen Tank aus **Edelstahl** umstellen (wie in der PDF des Konzeptberichts bereits beschrieben).
  - **Druckbehälter-Test:** Jeder Druckbehälter muss nach Appendix A hydrostatisch getestet werden.

---

## 3. Container-Sicherheit (Section 5)

### Erfüllt:
- **5.4 (Sicher befestigte Container):** Edelstahltank und Reaktor müssen sicher am Fahrzeug befestigt werden. → *Muss im Design berücksichtigt werden.*
- **5.5 (Keine offenen Container an der Startlinie):** Start über Ventil/Spritze am Fahrzeug. ✓ (im Konzept beschrieben)

### Muss angepasst/ergänzt werden:
- **5.4 (Deckel):** Deckel muss auch bei Umkippen des Fahrzeugs Chemikalien zurückhalten. → *Verschlusssystem spezifizieren.*

---

## 4. Temperatur (Section 7)

### Erfüllt:
- Reaktion verläuft **leicht endotherm** → Abkühlung des Reaktorinhalts zu erwarten, aber keine extremen Temperaturen.

### Muss angepasst/ergänzt werden:
- **7.1 (Oberflächen > 60°C oder < 0°C):** Bei starker Abkühlung durch endotherme Reaktion muss der Reaktor ggf. isoliert werden, um Kontaktverbrennungen/Kälteverbrennungen zu verhindern. → *Temperaturmessung im Testphase durchführen.*
- **7.2 (Elektrische Sicherheit):** T-Flipflop, Transistor, Batterie müssen isoliert/abgedeckt sein. Alligator-Clips sind verboten. → *Robuste Steckverbinder (Banana Plugs o.ä.) verwenden.*

---

## 5. Mechanische Sicherheit (Section 7)

### Muss ergänzt werden:
- **7.3 (Bewegte Teile):** Riemen, Freiläufe, Kolbenstange müssen durch Schutzhauben gegen Kontakt und Einklemmpunkte geschützt werden. → *Schutzbleche/Käfige spezifizieren.*

---

## 6. Wettbewerbstag (Section 8)

### Erfüllt:
- **8.4 (Dokumentation):** Konzeptdokument liegt vor. → *Ausdrucke müssen zum Wettbewerb mitgebracht werden.*

### Muss ergänzt werden:
- **3.1 (Paperwork Audit):** Folgende Dokumente sind bis Frist einzureichen:
  - [ ] Certifications Page
  - [ ] Safety analysis (quantitativ)
  - [ ] Druckentlastung-Berechnung
  - [ ] Pressure Relief Device Sizing
  - [ ] Druckentlastung-Testprotokoll
  - [ ] Pressure Vessel Testing Protocol (Appendix A)
  - [ ] Fahrzeugfoto
  - [ ] SDS aller Chemikalien
- **3.2 (Physical Audit):** Druckkonzept muss vor Ort ausgedruckt vorliegen.
- **8.1 (PSA):** Laborkittel, Schutzbrille, Handschuhe, Gesichtsschutz bereitstellen.
- **8.3 (Containment):** Spill-Containment-Vessels für Chemikalien-Vorbereitung.

---

## 7. Zusammenfassung der kritischen Punkte

| Nr. | Regel | Status | Maßnahme |
|---|---|---|---|
| 1 | 6.2.5 / Appendix A: PET-Verbot | ❌ KRITISCH | Oberen Tank auf Edelstahl umstellen (bereits in PDF erwähnt) |
| 2 | 6.2.1: Manometer | ❌ Erforderlich | Manometer spezifizieren (Bereich: bis 4 bar) |
| 3 | 6.2.2: Relief Valve dimensionieren | ❌ Erforderlich | Berechnung + Dimensionsauswahl |
| 4 | 6.2.3: Relief Valve Position | ❌ Erforderlich | Oben am Reaktor, kein Ventil dazwischen |
| 5 | 6.2.4: Lademanagement | ❌ Erforderlich | Messvorrichtung mit Max-Markierung |
| 6 | Appendix A: Hydrotest | ❌ Erforderlich | Testprotokoll für jeden Druckbehälter |
| 7 | 7.3: Mechanischer Schutz | ❌ Erforderlich | Schutzhauben für Riemen, Freiläufe, Kolben |
| 8 | 7.1: Temperaturisolierung | ⚠️ Zu prüfen | Endotherme Reaktion → Temperatur messen |
| 9 | 3.1: Paperwork Audit | ❌ Erforderlich | Alle Dokumente zusammenstellen |
| 10 | 4.3: Entsorgungskonzept | ⚠️ Zu ergänzen | Entsorgung der Chemikalien dokumentieren |

---

## 8. Was bereits gut gelöst ist

- **CO₂-Neutralitätskonzept** (Carbon-Capture-Ansatz) ist innovativ und gut dokumentiert.
- **Chemikalienwahl** ist sicherheitstechnisch attraktiv (ungiftig, Lebensmittelqualität).
- **Reaktionsprinzip** (gesteuertes Eintropfen) verhindert schlagartige Druckanstiege.
- **Überdruckventil** ist im Konzept bereits vorgesehen.
- **Keine offenen Flammen/Rauch** → erfüllt Regel 5.1.
- **CO₂-Emission** ist explizit als erlaubte harmless Emission gelistet (5.3).
- **Startmechanismus** über Ventil/Spritze am Fahrzeug → erfüllt Regel 5.5.
