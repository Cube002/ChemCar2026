import csv
with open(r'C:\Users\Personal\Documents\Studium\ChemCar\2026\ChemCar2026Concept\chemcar_model\chemcar_results.csv') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    print(f'Total rows: {len(rows)}')

    # Sample positions throughout simulation
    print('--- Position vs Time ---')
    for t_target in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
        for row in rows:
            if float(row['time_s']) >= t_target:
                print(f't={float(row["time_s"]):6.1f}  x={float(row["x_piston_cm"]):7.2f}  v={float(row["v_piston_cm_s"]):7.2f}  P_exh={float(row["P_exhaust_bar"]):8.1f}  P_react={float(row["P_reactor_bar"]):7.3f}  s_car={float(row["s_vehicle_m"]):8.1f}')
                break

    # Find max P_exhaust in each stroke region
    print('\n--- Max P_exhaust peaks ---')
    peaks = []
    for i, row in enumerate(rows):
        pe = float(row['P_exhaust_bar'])
        if pe > 10:
            peaks.append((float(row['time_s']), float(row['x_piston_cm']), pe, float(row['v_piston_cm_s'])))
    for p in peaks[:20]:
        print(f't={p[0]:6.3f}  x={p[1]:7.2f}  P_exh={p[2]:8.1f}  v={p[3]:7.2f}')
    print(f'Total peaks >10 bar: {len(peaks)}')

    # Check vehicle speed
    max_v_car = max(float(r['v_vehicle_cm_s']) for r in rows)
    print(f'\nMax vehicle speed: {max_v_car:.1f} cm/s = {max_v_car/100:.1f} m/s')
