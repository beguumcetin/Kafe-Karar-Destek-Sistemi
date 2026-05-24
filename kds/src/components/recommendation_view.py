from __future__ import annotations

import pandas as pd
import streamlit as st

from src.data.loader import get_daily_sales, get_peak_hour_for_period
from src.models.anomaly import detect_daily_sales_anomalies, detect_hourly_sales_anomalies, summarize_anomalies
from src.models.forecast import holt_winters_forecast, summarize_forecast
from src.models.recommendation import generate_recommendations
from src.models.segmentation import run_product_segmentation


def _render_recommendation_styles() -> None:
    st.markdown(
        """
        <style>
        .recommendation-card {
            background: linear-gradient(180deg, #fffdf8 0%, #f7f2e9 100%);
            border: 1px solid #eadfce;
            border-radius: 18px;
            padding: 18px 18px 16px 18px;
            margin-bottom: 16px;
            box-shadow: 0 6px 18px rgba(80, 60, 40, 0.08);
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .recommendation-badge {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 700;
            margin-bottom: 12px;
        }
        .badge-high {
            background: #fee2e2;
            color: #b91c1c;
        }
        .badge-medium {
            background: #fef3c7;
            color: #b45309;
        }
        .badge-low {
            background: #dcfce7;
            color: #166534;
        }
        .card-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #2d2016;
            margin-bottom: 10px;
        }
        .card-body {
            font-size: 0.97rem;
            color: #4b3b2e;
            line-height: 1.55;
            margin-bottom: 10px;
        }
        .card-label {
            font-weight: 700;
            color: #3a2a1e;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _priority_badge_class(priority: str) -> str:
    if priority == "Yuksek":
        return "badge-high"
    if priority == "Orta":
        return "badge-medium"
    return "badge-low"


def _render_recommendation_cards(recommendation_df: pd.DataFrame) -> None:
    columns = st.columns(2)
    for index, row in recommendation_df.iterrows():
        badge_class = _priority_badge_class(str(row["Oncelik"]))
        card_html = f"""
        <div class="recommendation-card">
            <div class="recommendation-badge {badge_class}">{row["Oncelik"]} Oncelik</div>
            <div class="card-title">{row["Sinyal"]}</div>
            <div class="card-body"><span class="card-label">Oneri:</span> {row["Oneri"]}</div>
            <div class="card-body"><span class="card-label">Tahmini Etki:</span> {row["Tahmini Etki"]}</div>
            <div class="card-body"><span class="card-label">Neden:</span> {row["Neden"]}</div>
        </div>
        """
        with columns[index % 2]:
            st.markdown(card_html, unsafe_allow_html=True)


def render_recommendation_view(df: pd.DataFrame) -> None:
    st.subheader("Oneri / Aksiyon Motoru")
    st.caption("Tahmin, anomali ve segmentasyon sonuclarindan aksiyon ureten kural tabanli karar modulu")
    _render_recommendation_styles()

    daily_sales = get_daily_sales(df)
    forecast_df = holt_winters_forecast(daily_sales, forecast_days=7)
    forecast_summary = summarize_forecast(daily_sales, forecast_df)
    daily_anomalies = detect_daily_sales_anomalies(daily_sales)
    hourly_anomalies = detect_hourly_sales_anomalies(df)
    anomaly_summary = summarize_anomalies(daily_anomalies, hourly_anomalies)
    segment_df = run_product_segmentation(df, n_clusters=4)
    hourly_peak = get_peak_hour_for_period(df)
    recommendation_df = generate_recommendations(df, forecast_summary, anomaly_summary, segment_df, hourly_peak)

    high_priority_count = int((recommendation_df["Oncelik"] == "Yuksek").sum())
    medium_priority_count = int((recommendation_df["Oncelik"] == "Orta").sum())

    m1, m2, m3 = st.columns(3)
    m1.metric("Yuksek Oncelik", high_priority_count)
    m2.metric("Orta Oncelik", medium_priority_count)
    m3.metric("Toplam Oneri", len(recommendation_df))

    st.markdown("### Uygulanabilir Oneriler")
    _render_recommendation_cards(recommendation_df)

    with st.expander("Detay Tablosu"):
        st.dataframe(recommendation_df, use_container_width=True, hide_index=True)
