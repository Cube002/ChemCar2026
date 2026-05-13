import numpy as np
data = np.load('chemcar_results.npz')
t = data['time_s']
v = data['v_vehicle_cm_s'] / 100
s = data['s_vehicle_m']
x = data['x_piston_cm']

# Find last stroke (last time x_piston is near 0 or 30)
print(f'Last 10 data points:')
print('idx    t         v_vehicle  s_vehicle  x_piston  P_reactor')
for i in range(max(0, len(t)-10), len(t)):
    P = (data['n_co2_gas_mol'][i] + data['n_air_mol'][i]) * 0.08314 * 293.15 / 0.3
    print(f'{i:5d}  {t[i]:.4f}  {v[i]:+.4e}  {s[i]:.4f}  {x[i]:.4f}  {P:.4f}')

# Find where v crosses zero to negative significantly
neg = np.where(v < -0.1)[0]
if len(neg) > 0:
    first_big_neg = neg[0]
    print(f'\nFirst big negative v at index {first_big_neg}:')
    P = (data['n_co2_gas_mol'][first_big_neg] + data['n_air_mol'][first_big_neg]) * 0.08314 * 293.15 / 0.3
    print(f'  t={t[first_big_neg]:.4f} v={v[first_big_neg]:.4f} x={x[first_big_neg]:.4f} s={s[first_big_neg]:.4f} P={P:.4f}')
    
    # Look at the area around the transition
    start = max(0, first_big_neg - 5)
    end = min(len(t), first_big_neg + 5)
    print(f'\nAround first big negative (from idx {start} to {end}):')
    for i in range(start, end):
        P = (data['n_co2_gas_mol'][i] + data['n_air_mol'][i]) * 0.08314 * 293.15 / 0.3
        print(f'  {i}: t={t[i]:.4f} v={v[i]:+.4e} x={x[i]:.4f} s={s[i]:.4f} P={P:.4f}')
