import pandas as pd
import numpy as np
import sqlite3
import time
import os

from visualize_data import plot_benchmark_results

# Підготовка даних
print("Генерація даних...")
n_rows = 1_000_000
df = pd.DataFrame({
    'timestamp': pd.date_range('2023-01-01', periods=n_rows, freq='s'),
    'energy_consumption': np.random.uniform(10, 500, size=n_rows),
    'voltage': np.random.uniform(210, 240, size=n_rows),
    'station_id': np.random.randint(1, 50, size=n_rows)
})

results = []

# 1. Тест SQL (SQLite)
print("Тестування SQL (SQLite)...")
db_name = 'energy_data.db'
conn = sqlite3.connect(db_name)

start = time.time()
df.to_sql('energy_table', conn, if_exists='replace', index=False)
sql_write = time.time() - start

start = time.time()
_ = pd.read_sql('SELECT * FROM energy_table', conn)
sql_read = time.time() - start
conn.close()

results.append({
    'Format': 'SQL',
    'Write Time (s)': sql_write,
    'Read Time (s)': sql_read,
    'Size (MB)': os.path.getsize(db_name) / (1024 * 1024)
})

# 2. Тест інших форматів
formats = {
    'CSV': {'write': df.to_csv, 'read': pd.read_csv, 'ext': 'csv', 'args': {'index': False}},
    'Parquet': {'write': df.to_parquet, 'read': pd.read_parquet, 'ext': 'parquet', 'args': {}},
    'HDF5': {'write': df.to_hdf, 'read': pd.read_hdf, 'ext': 'h5', 'args': {'key': 'data', 'mode': 'w'}}
}

for name, tools in formats.items():
    print(f"Тестування {name}...")
    filename = f'data.{tools["ext"]}'

    # Запис
    start = time.time()
    tools['write'](filename, **tools['args'])
    w_time = time.time() - start

    # Читання
    start = time.time()
    _ = tools['read'](filename)
    r_time = time.time() - start

    results.append({
        'Format': name,
        'Write Time (s)': w_time,
        'Read Time (s)': r_time,
        'Size (MB)': os.path.getsize(filename) / (1024 * 1024)
    })


results_df = pd.DataFrame(results)
print("\nРезультати аналізу:")
print(results_df)

# Виклик функції візуалізації
plot_benchmark_results(results_df)
