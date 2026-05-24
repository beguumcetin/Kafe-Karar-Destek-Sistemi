from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data.loader import (
    get_daily_sales,
    get_hourly_sales,
    get_product_revenue,
    get_top_revenue_product,
    get_weekday_sales,
    summarize_sales,
)
from src.models.forecast import (
    build_forecast_plot_frame,
    holt_winters_forecast,
    summarize_forecast,
)


def _format_weekday_name(value: str) -> str:
    weekday_map = {
        "Monday": "Pazartesi",
        "Tuesday": "Sali",
        "Wednesday": "Carsamba",
        "Thursday": "Persembe",
        "Friday": "Cuma",
        "Saturday": "Cumartesi",
        "Sunday": "Pazar",
    }
    return weekday_map.get(value, value)


def _build_metric_section(df: pd.DataFrame) -> None:
    summary = summarize_sales(df)
    top_product = get_top_revenue_product(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Toplam Satis Tutari", f"{summary['total_sales']:,.2f} TL")
    col2.metric("Toplam Islem Sayisi", f"{summary['transaction_count']:,}")
    col3.metric("Ortalama Islem Tutari", f"{summary['average_basket']:,.2f} TL")
    col4.metric(
        "En Cok Gelir Getiren Urun",
        top_product["product_type"],
        delta=f"{top_product['revenue']:,.2f} TL",
    )


def _build_hourly_sales_chart(hourly_sales: pd.DataFrame):
    fig = px.bar(
        hourly_sales,
        x="hour",
        y="hourly_sales",
        color="hourly_sales",
        color_continuous_scale="Teal",
        title="Saatlik Satis Dagilimi",
    )
    fig.update_layout(
        xaxis_title="Saat",
        yaxis_title="Satis Tutari (TL)",
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def _build_daily_trend_chart(daily_sales: pd.DataFrame):
    fig = px.line(
        daily_sales,
        x="transaction_date",
        y="daily_sales",
        markers=True,
        title="Gunluk Satis Trendi",
    )
    fig.update_traces(line_color="#1f6f78", marker_color="#0b3c49")
    fig.update_layout(
        xaxis_title="Tarih",
        yaxis_title="Satis Tutari (TL)",
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def _build_product_revenue_chart(product_revenue: pd.DataFrame):
    fig = px.bar(
        product_revenue.head(10),
        x="product_type",
        y="revenue",
        color="revenue",
        color_continuous_scale="Blues",
        title="Urun Bazli Gelir Grafigi",
    )
    fig.update_layout(
        xaxis_title="Urun",
        yaxis_title="Gelir (TL)",
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def _build_weekday_intensity_chart(weekday_sales: pd.DataFrame):
    chart_df = weekday_sales.copy()
    chart_df["weekday_label"] = chart_df["weekday"].astype(str).map(_format_weekday_name)

    fig = px.bar(
        chart_df,
        x="weekday_label",
        y="transaction_count",
        color="transaction_count",
        color_continuous_scale="Sunset",
        title="Gunlere Gore Yogunluk Analizi",
    )
    fig.update_layout(
        xaxis_title="Gun",
        yaxis_title="Islem Sayisi",
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def _build_forecast_chart(forecast_plot_df: pd.DataFrame):
    fig = px.line(
        forecast_plot_df,
        x="date",
        y="sales",
        color="series",
        markers=True,
        title="Kisa Vadeli Satis Tahmini",
        color_discrete_map={
            "Gerceklesen": "#1f6f78",
            "Tahmin": "#d97706",
        },
    )
    fig.update_layout(
        xaxis_title="Tarih",
        yaxis_title="Satis Tutari (TL)",
        legend_title="Veri",
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def render_dashboard(df: pd.DataFrame) -> None:
    st.subheader("Yonetici Dashboard")
    st.caption("Satis performansi, yogunluk analizi ve urun gelir dagilimini gosteren yonetici ekrani")

    daily_sales = get_daily_sales(df)
    hourly_sales = get_hourly_sales(df)
    product_revenue = get_product_revenue(df)
    weekday_sales = get_weekday_sales(df)
    forecast_df = holt_winters_forecast(daily_sales, forecast_days=7)
    forecast_summary = summarize_forecast(daily_sales, forecast_df)
    forecast_plot_df = build_forecast_plot_frame(daily_sales.tail(30), forecast_df)

    _build_metric_section(df)

    st.markdown("### Genel Satis Analizi")
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.plotly_chart(_build_hourly_sales_chart(hourly_sales), use_container_width=True)
    with row1_col2:
        st.plotly_chart(_build_daily_trend_chart(daily_sales), use_container_width=True)

    st.markdown("### Urun ve Yogunluk Analizi")
    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        st.plotly_chart(_build_product_revenue_chart(product_revenue), use_container_width=True)
    with row2_col2:
        st.plotly_chart(_build_weekday_intensity_chart(weekday_sales), use_container_width=True)

    st.markdown("### Kisa Vadeli Tahmin")
    st.caption(f"Yontem: {forecast_summary['method']}. Haftalik dalgalanmayi dikkate alan daha stabil kisa vadeli tahmin kullanilir.")
    forecast_col1, forecast_col2 = st.columns([1.3, 0.7])
    with forecast_col1:
        st.plotly_chart(_build_forecast_chart(forecast_plot_df), use_container_width=True)
    with forecast_col2:
        st.metric("Son Gerceklesen Gun", f"{forecast_summary['latest_actual']:,.2f} TL")
        st.metric("Tahmini Gunluk Ortalama", f"{forecast_summary['average_forecast']:,.2f} TL")
        st.metric("Beklenen Degisim", f"%{forecast_summary['trend_percent']}")
        st.info(forecast_summary["comment"])

    st.markdown("### Ozet Tablo")
    summary_table = product_revenue.head(10).rename(
        columns={
            "product_type": "Urun",
            "revenue": "Toplam Gelir (TL)",
            "quantity": "Toplam Adet",
        }
    )
    st.dataframe(summary_table, use_container_width=True, hide_index=True)
