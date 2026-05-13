import numpy as np
data = np.load('chemcar_results.npz')
t = data['time_s']
v = data['v_vehicle_cm_s'] / 100  # m/s
s = data['s_vehicle_m']
x = data['x_piston_cm']

neg_idx = np.where(v < -0.01)[0]
if len(neg_idx) > 0:
    first_neg = neg_idx[0]
    print(f'First negative v at t={t[first_neg]:.4f}s, v={v[first_neg]:.4f} m/s')
    print(f'  s_vehicle at that point: {s[first_neg]:.4f} m')
    start = max(0, first_neg - 100)
    print(f'\nLast 100 points before negative (from t={t[start]:.4f}):')
    for i in range(start, min(first_neg + 5, len(t))):
        P_r = (data['n_co2_gas_mol'][i] + data['n_air_mol'][i]) * 0.08314 * 293.15 / (3.0 * 0.1)
        print(f't={t[i]:.6f} v={v[i]:.4e} s={s[i]:.4e} x={x[i]:.4f} P={P_r:.4f}')
else:
    print('No negative velocity found')

print(f'\nTotal: {len(t)} steps, {t[-1]:.2f}s')
print(f'Final v: {v[-1]:.4f} m/s, Final s: {s[-1]:.4f} m')
