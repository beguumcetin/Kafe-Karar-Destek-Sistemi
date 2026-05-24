from __future__ import annotations

from io import StringIO

import pandas as pd
import streamlit as st

from src.data.loader import (
    filter_by_period,
    get_daily_sales,
    get_date_bounds,
    get_peak_hour_for_period,
    get_top_products,
    summarize_sales,
)
from src.models.anomaly import detect_daily_sales_anomalies, detect_hourly_sales_anomalies, summarize_anomalies
from src.models.forecast import holt_winters_forecast, summarize_forecast
from src.models.recommendation import generate_recommendations
from src.models.segmentation import run_product_segmentation


def _build_report_text(summary: dict[str, float | int], forecast_summary: dict[str, float | str], anomaly_summary: dict[str, object], peak_hour: dict[str, int | float]) -> str:
    return (
        "Karar Raporu\n"
        f"- Toplam satis: {summary['total_sales']:,.2f} TL\n"
        f"- Islem sayisi: {summary['transaction_count']}\n"
        f"- Ortalama islem tutari: {summary['average_basket']:,.2f} TL\n"
        f"- Beklenen degisim: %{forecast_summary['trend_percent']}\n"
        f"- Gunluk anomali sayisi: {anomaly_summary['daily_anomaly_count']}\n"
        f"- Saatlik anomali sayisi: {anomaly_summary['hourly_anomaly_count']}\n"
        f"- En yogun saat: {int(peak_hour['hour']):02d}:00\n"
    )


def render_report_view(df: pd.DataFrame) -> None:
    st.subheader("Rapor Ekrani")
    st.caption("Secilen donem icin yoneticiye ozet karar raporu ureten ekran")

    min_date, max_date = get_date_bounds(df)
    selected_range = st.date_input("Rapor donemi", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if len(selected_range) != 2:
        st.warning("Lutfen baslangic ve bitis tarihini birlikte sec.")
        return
    start_date, end_date = selected_range

    filtered_df = filter_by_period(df, start_date, end_date)
    if filtered_df.empty:
        st.warning("Secilen donem icin veri bulunamadi.")
        return

    summary = summarize_sales(filtered_df)
    daily_sales = get_daily_sales(filtered_df)
    forecast_summary = summarize_forecast(daily_sales, holt_winters_forecast(daily_sales, forecast_days=7))
    anomaly_summary = summarize_anomalies(
        detect_daily_sales_anomalies(daily_sales),
        detect_hourly_sales_anomalies(filtered_df),
    )
    segment_df = run_product_segmentation(filtered_df, n_clusters=4)
    peak_hour = get_peak_hour_for_period(filtered_df, start_date, end_date)
    recommendation_df = generate_recommendations(filtered_df, forecast_summary, anomaly_summary, segment_df, peak_hour)
    top_products = get_top_products(filtered_df, top_n=3)
    top_recommendation = recommendation_df.iloc[0] if not recommendation_df.empty else None

    st.markdown("### KPI Ozeti")
    k1, k2, k3 = st.columns(3)
    k1.metric("Toplam Satis", f"{summary['total_sales']:,.2f} TL")
    k2.metric("Islem Sayisi", f"{summary['transaction_count']:,}")
    k3.metric("Ort. Islem Tutari", f"{summary['average_basket']:,.2f} TL")

    st.markdown("### Karar Raporu")
    st.write(_build_report_text(summary, forecast_summary, anomaly_summary, peak_hour))
    if top_recommendation is not None:
        st.info(
            f"Oncelikli aksiyon: {top_recommendation['Oneri']} | Tahmini etki: {top_recommendation['Tahmini Etki']}"
        )

    st.markdown("### Top Urunler")
    st.dataframe(top_products, use_container_width=True, hide_index=True)

    st.markdown("### Onerilen Aksiyonlar")
    st.dataframe(recommendation_df, use_container_width=True, hide_index=True)

    csv_buffer = StringIO()
    recommendation_df.to_csv(csv_buffer, index=False)
    st.download_button(
        "Aksiyon Raporunu CSV Indir",
        data=csv_buffer.getvalue(),
        file_name="karar_destek_raporu.csv",
        mime="text/csv",
    )
