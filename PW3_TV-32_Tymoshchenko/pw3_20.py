import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf


def generate_energy_timeseries(n_points, rho=0.85, noise_level=5, seasonality=40, base_level=200):
    series = np.zeros(n_points)
    errors = np.random.normal(0, noise_level, n_points)

    # Стартуємо з базового рівня
    series[0] = base_level

    for t in range(1, n_points):
        # Додаємо (t - 6), щоб зсунути пік синусоїди ближче до вечора (18:00-20:00)
        seasonal_effect = seasonality * np.sin(2 * np.pi * (t - 6) / 24)

        # Модель AR(1): ряд тепер коливається навколо base_level + seasonal_effect
        target = base_level + seasonal_effect
        series[t] = rho * series[t - 1] + (1 - rho) * target + errors[t]

        # Додатковий запобіжник: фізично енергія не може бути < 0
        if series[t] < 0:
            series[t] = 0

    return series


# 1. Генерація синтетичних даних
n_hours = 240
simulated_data = generate_energy_timeseries(n_hours, base_level=150, seasonality=50)
time_index = pd.date_range(start="2026-03-01", periods=n_hours, freq="h")
df_simulated = pd.DataFrame({'Consumption': simulated_data}, index=time_index)

# 2. Робота з реальним датасетом
try:
    real_df_raw = pd.read_csv('time_series_60min_singleindex.csv',
                              index_col=0,
                              parse_dates=True,
                              nrows=n_hours + 100)

    load_cols = [col for col in real_df_raw.columns if 'load_actual_entsoe_transparency' in col]
    if load_cols:
        real_series = real_df_raw[load_cols[0]].iloc[:n_hours]
        real_series_norm = (real_series - real_series.min()) / (real_series.max() - real_series.min()) * 100 + 100
    else:
        print("Колонку з навантаженням не знайдено.")
        real_series = None
except FileNotFoundError:
    print("Файл не знайдено.")
    real_series = None

# 3. Візуалізація
plt.figure(figsize=(14, 6))
plt.plot(df_simulated.index, df_simulated['Consumption'], label='Згенеровані дані (Позитивні)', color='blue',
         linewidth=2)
if real_series is not None:
    plt.plot(df_simulated.index, real_series_norm.values, label='Реальні дані (нормовані)', color='orange', alpha=0.6)

plt.axhline(y=0, color='black', linestyle='--', alpha=0.3)  # Лінія нуля для контролю
plt.title("Енергоспоживання: порівняння без від'ємних значень")
plt.ylabel("МВт / Умовні одиниці")
plt.legend()
plt.grid(True, alpha=0.2)
plt.show()

# 4. Автокореляція
fig, ax = plt.subplots(1, 2, figsize=(16, 5))
plot_acf(df_simulated['Consumption'], lags=48, ax=ax[0])
ax[0].set_title("ACF: Згенеровані дані")

if real_series is not None:
    plot_acf(real_series.dropna(), lags=48, ax=ax[1])
    ax[1].set_title("ACF: Реальні дані")
plt.show()
