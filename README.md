English | [Türkçe](README.tr.md)

# Café Decision Support System

A Streamlit prototype built for a Decision Support Systems course. It uses coffee-shop sales data to go beyond a dashboard of what happened: it forecasts the next days, flags unusual days and hours, groups products by behaviour, simulates promotions and suggests actions. The interface is in Turkish.

The aim is for a manager to be able to answer four questions from the data: what happened, what will happen, why did it happen, and what should I do?

## Data

`kds/data/raw/coffee_sales.csv` holds 3,547 card and cash transactions from 1 March 2024 to 23 March 2025: hour, payment type, amount, product name, time of day and date. The file was saved as RTF, so the loader strips the RTF wrapper before reading it as CSV. If the file is missing, the app falls back to the small `coffee_sales_sample.csv`.

## Screens

The sidebar has five screens:

- **Genel Dashboard (overview):** KPI cards, hourly and daily sales charts, best-selling products and a short sales forecast.
- **Karar Destek Merkezi (decision centre):** four tabs, each with its own method:
  - **Forecast:** Holt-Winters exponential smoothing with weekly seasonality and a damped trend, clipped to a plausible range around recent sales. If the model cannot be fitted, it falls back to the weekday average blended with the last 7 days.
  - **Anomalies:** z-scores on daily and hourly sales to flag unusual days and hours.
  - **Segments:** products grouped by behaviour with a small K-Means written with NumPy.
  - **Recommendations:** a rule-based engine that combines the forecast, anomaly and segment results into suggested actions.
- **Kampanya Simulatoru (campaign simulator):** choose a product, a discount, a date range and an expected demand lift, compare scenarios and save a campaign as active.
- **Rapor Ekrani (report):** a short management summary for a chosen period.
- **Kullanici / Calisan Paneli (customer and staff panel):** a staff view with the busy hour, the active campaign and the top three products, plus a customer view with a sign-in screen. The customers shown there are made-up sample users in `src/data/users.py`, not real data.

## Run it

```bash
cd kds
pip install -r requirements.txt
streamlit run app/main.py
```

Requirements: Streamlit, pandas, NumPy, Plotly and statsmodels.

## Structure

```
kds/
  app/main.py              entry point, navigation
  src/data/                CSV loader (handles the RTF file), sample users
  src/models/              forecast, anomaly, segmentation, campaign, recommendation
  src/components/          one Streamlit view per screen
  src/utils/constants.py   paths and defaults
  data/raw/                coffee_sales.csv and a small sample file
  docs/file_summary.md     short per-file notes (partly out of date, see below)
```

## Limits

This is a student prototype. The explainable methods were chosen on purpose over heavy models, and there is no database, authentication or deployment. The sign-in screen is a demo with sample users, not real authentication. The forecast is not validated against held-out days, and a year of data from one shop is a small base for the weekly seasonality it assumes. `docs/file_summary.md` still describes the forecast as a simple moving average from an earlier version; the code uses Holt-Winters as described above.
