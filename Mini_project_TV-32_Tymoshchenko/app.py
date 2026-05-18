import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor

st.set_page_config(page_title="Inverter AI Agent", layout="wide")


# ==========================================
# ЛОГІКА ДАНИХ ТА МОДЕЛЮВАННЯ (ML)
# ==========================================

@st.cache_data
def load_data():
    np.random.seed(42)
    date_range = pd.date_range(start="2026-01-01", periods=24 * 30, freq="h")
    data = []
    for dt in date_range:
        h = dt.hour
        load = 0.5 + (2.0 if 8 <= h <= 10 or 18 <= h <= 22 else 0.3) + np.random.uniform(0, 1)
        gen = max(0, np.sin((h - 6) / 12 * np.pi) * 4) if 6 <= h <= 18 else 0
        data.append({"hour": h, "load": load, "gen": gen})
    return pd.DataFrame(data)


def train_model(df):
    X = df[['hour']]
    m_load = RandomForestRegressor(n_estimators=100, random_state=42).fit(X, df['load'])
    m_gen = RandomForestRegressor(n_estimators=100, random_state=42).fit(X, df['gen'])
    return m_load, m_gen


# ==========================================
# ІНТЕРФЕЙС STREAMLIT
# ==========================================

st.title("🔌 AI-Агент планування роботи інвертора")
st.markdown("Оптимізація енергоспоживання: **ML-прогноз + Плавно-циклічна агентна логіка**")

# Сайдбар налаштувань
st.sidebar.header("Параметри системи")
bat_cap = st.sidebar.slider("Ємність АКБ (кВт·год)", 5, 30, 10)
max_pwr = st.sidebar.slider("Макс. потужність інвертора (кВт)", 1, 10, 5)

st.sidebar.subheader("Тарифи купівлі")
night_price = st.sidebar.number_input("Нічний тариф (грн/кВт·год)", value=2.16)
day_price = st.sidebar.number_input("Денний тариф (грн/кВт·год)", value=4.32)

st.sidebar.subheader("Тарифи продажу")
sell_price = st.sidebar.number_input("Зелений тариф / Продаж (грн/кВт·год)", value=4.50)

# Підготовка даних та запуск навчання ШІ
df = load_data()
m_load, m_gen = train_model(df)

hours = list(range(24))
preds_load = m_load.predict(pd.DataFrame({'hour': hours}))
preds_gen = m_gen.predict(pd.DataFrame({'hour': hours}))

# ==========================================
# РОЗРАХУНОК ЛОГІКИ АГЕНТА ТА ЕКОНОМІЇ
# ==========================================

soc = 0.2
soc_history = []
actions = []
grid_flow = []

# Змінні для деталізованого фінансового аналізу
cost_without_ai_total = 0
cost_with_ai_pure_consumption = 0  # Витрати з агентом (тільки купівля енергії)
total_earned_from_sales = 0  # Скільки заробили на продажу

savings_history = []

for h in hours:
    p_load = preds_load[h]
    p_gen = preds_gen[h]
    net = p_gen - p_load

    tariff = day_price if 7 <= h < 23 else night_price

    # Сценарій А: Витрати БЕЗ Агента та АКБ
    cost_without_ai = p_load * tariff
    cost_without_ai_total += cost_without_ai

    # Тимчасові змінні для поточної години
    hourly_purchase_cost = 0
    hourly_sale_profit = 0

    if net > 0:
        charge = min(net, max_pwr, (1 - soc) * bat_cap)
        soc += charge / bat_cap
        actions.append("Заряд (Сонце)")

        remainder = net - charge
        grid_flow.append(-remainder)

        hourly_sale_profit = remainder * sell_price
        total_earned_from_sales += hourly_sale_profit

    else:
        need = abs(net)

        # ПРАВИЛО 1: Плановий нічний заряд (з 00:00 до 05:00)
        if tariff == night_price and h <= 5 and soc < 0.5:
            target_soc = 0.2 + (0.3 * (h + 1) / 6)
            needed_charge = max(0, (target_soc - soc) * bat_cap)
            charge = min(max_pwr, needed_charge)

            soc += charge / bat_cap
            actions.append("Нічний заряд (Мережа)")

            from_grid = need + charge
            grid_flow.append(from_grid)
            hourly_purchase_cost = from_grid * tariff

        # ПРАВИЛО 2: Вечірній розряд у дорогий тариф
        elif tariff > night_price and soc > 0.2:
            discharge = min(need, max_pwr, (soc - 0.2) * bat_cap)
            soc -= discharge / bat_cap
            actions.append("Розряд (Пік)")

            from_grid = need - discharge
            grid_flow.append(from_grid)
            hourly_purchase_cost = from_grid * tariff

        else:
            actions.append("Мережа")
            grid_flow.append(need)
            hourly_purchase_cost = need * tariff

    soc_history.append(soc * 100)

    cost_with_ai_pure_consumption += hourly_purchase_cost

    hourly_savings = cost_without_ai - hourly_purchase_cost + hourly_sale_profit
    savings_history.append(hourly_savings)

# Підсумкові баланси
balance_with_ai_and_sales = cost_with_ai_pure_consumption - total_earned_from_sales
total_saved_and_earned = cost_without_ai_total - balance_with_ai_and_sales

# ==========================================
# ВІЗУАЛІЗАЦІЯ ТА ВІДЖЕТИ ЕКРАНУ
# ==========================================

st.subheader("📊 Деталізований фінансовий аналіз за 24 години")

# Рядок з 5-ти карток метрик для повної прозорості
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="🔴 Витрати без AI",
        value=f"{round(cost_without_ai_total, 2)} грн",
        help="Скільки б ви заплатили, купуючи всю енергію з мережі за фактом споживання."
    )
with col2:
    st.metric(
        label="🔵 Витрати з AI (без продажу)",
        value=f"{round(cost_with_ai_pure_consumption, 2)} грн",
        help="Сума, яку ви реально заплатили за куплену з мережі електроенергію (включаючи нічний заряд АКБ)."
    )
with col3:
    st.metric(
        label="🟢 Зароблено на продажу",
        value=f"{round(total_earned_from_sales, 2)} грн",
        help="Ваш чистий дохід від експорту надлишків сонячної енергії в мережу за Зеленим тарифом."
    )
with col4:
    # Робимо колір або значення за результатом (якщо мінус — ми в плюсі і мережа винна нам)
    st.metric(
        label="Баланс",
        value=f"{round(balance_with_ai_and_sales, 2)} грн",
        help="Фінальний рахунок від енергокомпанії. Якщо значення від'ємне — ви заробили більше, ніж витратили."
    )
with col5:
    st.metric(
        label="🔥 Заощаджено + Зароблено",
        value=f"{round(total_saved_and_earned, 2)} грн",
        delta=f"{round((total_saved_and_earned / cost_without_ai_total) * 100, 1)}% загальний ефект"
    )

# Графік
fig = go.Figure()
fig.add_trace(go.Scatter(x=hours, y=preds_load, name="Прогноз споживання (кВт)", line=dict(color='red', dash='dot')))
fig.add_trace(go.Scatter(x=hours, y=preds_gen, name="Прогноз СЕС (кВт)", fill='tozeroy', line=dict(color='orange')))
fig.add_trace(go.Bar(x=hours, y=soc_history, name="Заряд АКБ (%)", yaxis='y2', opacity=0.3, marker_color='green'))

fig.update_layout(
    title="Плавно-циклічний енергетичний баланс та стан акумулятора",
    xaxis_title="Година доби",
    yaxis_title="Потужність (кВт)",
    yaxis2=dict(title="Заряд АКБ (%)", overlaying='y', side='right', range=[0, 100]),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# Детальна таблиця рішень
with st.expander("👁 Переглянути погодинний план дій агента та фінансовий аналіз"):
    res_df = pd.DataFrame({
        "Година": hours,
        "Дія Агента": actions,
        "Прогноз СЕС (кВт)": np.round(preds_gen, 2),
        "Прогноз Дому (кВт)": np.round(preds_load, 2),
        "Заряд (%)": np.round(soc_history, 1),
        "Мережа (кВт)": np.round(grid_flow, 2),
        "Економія за годину (грн)": np.round(savings_history, 2)
    })
    st.dataframe(res_df, use_container_width=True)