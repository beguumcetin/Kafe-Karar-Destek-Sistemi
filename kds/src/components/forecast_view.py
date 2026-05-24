from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data.loader import get_daily_sales
from src.models.forecast import build_forecast_plot_frame, holt_winters_forecast, summarize_forecast


def render_forecast_view(df: pd.DataFrame) -> None:
    st.subheader("Tahminleme")
    st.caption("Kisa vadeli satis egilimini gosteren basit ve savunulabilir zaman serisi modulu")

    daily_sales = get_daily_sales(df)
    forecast_days = st.slider("Tahmin gun sayisi", min_value=3, max_value=14, value=7)
    forecast_df = holt_winters_forecast(daily_sales, forecast_days=forecast_days)
    forecast_summary = summarize_forecast(daily_sales, forecast_df)
    plot_df = build_forecast_plot_frame(daily_sales.tail(45), forecast_df)

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Son Gerceklesen Gun", f"{forecast_summary['latest_actual']:,.2f} TL")
    metric2.metric("Tahmini Ortalama", f"{forecast_summary['average_forecast']:,.2f} TL")
    metric3.metric("Beklenen Degisim", f"%{forecast_summary['trend_percent']}")

    fig = px.line(
        plot_df,
        x="date",
        y="sales",
        color="series",
        markers=True,
        title="Gerceklesen ve Tahmini Gunluk Satis",
        color_discrete_map={"Gerceklesen": "#1f6f78", "Tahmin": "#d97706"},
    )
    fig.update_layout(xaxis_title="Tarih", yaxis_title="Satis Tutari (TL)")
    st.plotly_chart(fig, use_container_width=True)

    st.info(forecast_summary["comment"])
    st.caption(
        f"Yontem: {forecast_summary['method']}. Haftalik sezonsallik kullanilir; model kurulamiyorsa haftanin gunu ortalamasi ile son 7 gun ortalamasi birlestirilir."
    )

    st.dataframe(
        forecast_df.rename(columns={"date": "Tarih", "predicted_sales": "Tahmini Satis (TL)"}),
        use_container_width=True,
        hide_index=True,
    )
