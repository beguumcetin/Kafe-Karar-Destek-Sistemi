from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data.loader import get_daily_sales
from src.models.anomaly import detect_daily_sales_anomalies, detect_hourly_sales_anomalies, summarize_anomalies


def render_anomaly_view(df: pd.DataFrame) -> None:
    st.subheader("Anomali Tespiti")
    st.caption("Z-score yaklasimi ile beklenenden farkli satis davranislari tespit edilir")

    threshold = st.slider("Anomali esigi (z-score)", min_value=1.5, max_value=3.5, value=2.0, step=0.1)
    daily_sales = get_daily_sales(df)
    daily_anomalies = detect_daily_sales_anomalies(daily_sales, z_threshold=threshold)
    hourly_anomalies = detect_hourly_sales_anomalies(df, z_threshold=threshold)
    summary = summarize_anomalies(daily_anomalies, hourly_anomalies)

    col1, col2 = st.columns(2)
    col1.metric("Gunluk Anomali Sayisi", summary["daily_anomaly_count"])
    col2.metric("Saatlik Anomali Sayisi", summary["hourly_anomaly_count"])

    fig = px.scatter(
        daily_anomalies,
        x="transaction_date",
        y="daily_sales",
        color="signal",
        hover_data=["z_score"],
        title="Gunluk Satis Anomali Haritasi",
        color_discrete_map={
            "Normal": "#94a3b8",
            "Beklenenden yuksek satis": "#16a34a",
            "Beklenenden dusuk satis": "#dc2626",
        },
    )
    fig.update_layout(xaxis_title="Tarih", yaxis_title="Gunluk Satis (TL)")
    st.plotly_chart(fig, use_container_width=True)

    row1, row2 = st.columns(2)
    with row1:
        st.markdown("### Gunluk Anomali Listesi")
        st.dataframe(
            daily_anomalies[daily_anomalies["signal"] != "Normal"][
                ["transaction_date", "daily_sales", "z_score", "signal"]
            ].rename(
                columns={
                    "transaction_date": "Tarih",
                    "daily_sales": "Gunluk Satis (TL)",
                    "z_score": "Z-Skor",
                    "signal": "Sinyal",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    with row2:
        st.markdown("### Saatlik Anomali Listesi")
        st.dataframe(
            hourly_anomalies[hourly_anomalies["signal"] != "Normal"][
                ["hour", "hourly_sales", "transaction_count", "z_score", "signal"]
            ].rename(
                columns={
                    "hour": "Saat",
                    "hourly_sales": "Saatlik Satis (TL)",
                    "transaction_count": "Islem Sayisi",
                    "z_score": "Z-Skor",
                    "signal": "Sinyal",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
