from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.models.campaign import (
    build_scenario_comparison,
    estimate_uplift_from_discount,
    simulate_campaign,
)
from src.utils.constants import PROMOTION_DEFAULTS


def _initialize_campaign_state() -> None:
    if "active_campaign" not in st.session_state:
        st.session_state.active_campaign = None


def _render_input_panel(df: pd.DataFrame) -> tuple[str, int, object, object]:
    min_date = pd.to_datetime(df["transaction_date"]).min().date()
    max_date = pd.to_datetime(df["transaction_date"]).max().date()
    products = sorted(df["product_type"].dropna().unique().tolist())

    input_col1, input_col2 = st.columns([1.2, 1])
    with input_col1:
        selected_product = st.selectbox("Urun secimi", products)
        discount_rate = st.slider(
            "Indirim orani (%)",
            min_value=0,
            max_value=50,
            value=PROMOTION_DEFAULTS["discount_rate"],
            help="Bu oran secilen urun icin uygulanacak kampanya indiriminin yuzdesidir.",
        )
    with input_col2:
        date_range = st.date_input(
            "Analiz donemi",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        if len(date_range) != 2:
            st.warning("Lutfen baslangic ve bitis tarihini birlikte sec.")
            st.stop()
        start_date, end_date = date_range
        if start_date > end_date:
            st.error("Baslangic tarihi bitis tarihinden buyuk olamaz.")
            st.stop()

    return selected_product, discount_rate, start_date, end_date


def _render_main_metrics(simulation_result: dict[str, float | int | str]) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Baz Satis Bilgisi", f"{simulation_result['baseline_quantity']:,.0f} adet")
    col2.metric("Tahmini Satis Artisi", f"%{simulation_result['uplift_rate']}")
    col3.metric("Tahmini Yeni Satis Adedi", f"{simulation_result['new_quantity']:,.0f} adet")
    col4.metric(
        "Net Gelir Farki",
        f"{simulation_result['revenue_difference']:,.2f} TL",
        delta=f"{simulation_result['new_revenue']:,.2f} TL yeni gelir",
    )


def _render_financial_summary(simulation_result: dict[str, float | int | str]) -> None:
    st.markdown("### Gelir Ozetleri")
    finance_col1, finance_col2, finance_col3 = st.columns(3)
    finance_col1.metric("Eski Gelir", f"{simulation_result['baseline_revenue']:,.2f} TL")
    finance_col2.metric("Yeni Gelir", f"{simulation_result['new_revenue']:,.2f} TL")
    finance_col3.metric("Indirimli Birim Fiyat", f"{simulation_result['discounted_unit_price']:,.2f} TL")


def _render_baseline_table(simulation_result: dict[str, float | int | str]) -> None:
    baseline_table = pd.DataFrame(
        [
            ["Secilen urun", simulation_result["selected_product"]],
            ["Analiz suresi", f"{simulation_result['campaign_days']} gun"],
            ["Baz satis adedi", simulation_result["baseline_quantity"]],
            ["Baz islem sayisi", simulation_result["baseline_transactions"]],
            ["Ortalama birim fiyat", f"{simulation_result['average_unit_price']:,.2f} TL"],
            ["Gunluk ortalama satis adedi", simulation_result["daily_average_quantity"]],
        ],
        columns=["Gosterge", "Deger"],
    )
    st.dataframe(baseline_table, use_container_width=True, hide_index=True)


def _render_scenario_chart(scenario_df: pd.DataFrame) -> None:
    fig = px.bar(
        scenario_df,
        x="Senaryo",
        y="Net Gelir Farki (TL)",
        color="Net Gelir Farki (TL)",
        text="Indirim Orani (%)",
        color_continuous_scale="RdYlGn",
        title="Senaryo Karsilastirmasi (A / B / C)",
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(
        xaxis_title="Senaryo",
        yaxis_title="Net Gelir Farki (TL)",
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_assumptions(discount_rate: float) -> None:
    estimated_uplift = estimate_uplift_from_discount(discount_rate)
    st.info(
        f"Varsayim: Her %1 indirim icin yaklasik %1.8 talep artisi ongorulur. "
        f"Bu nedenle secilen % {discount_rate} indirim icin tahmini talep artisi % {estimated_uplift} olarak alinmistir. "
        "Model, ders projesine uygun olarak sade ve aciklanabilir tutulmustur."
    )


def render_campaign_simulator(df: pd.DataFrame) -> None:
    st.subheader("Kampanya Simulasyonu")
    st.caption("Indirim kararlarinin satis adedi ve gelir etkisini karsilastiran sade yonetici ekranı")

    _initialize_campaign_state()
    selected_product, discount_rate, start_date, end_date = _render_input_panel(df)

    # Varsayim: Indirim arttikca talep artar. Bu iliski dogrusal ve sinirli kabul edilir.
    # Varsayim: Kampanya etkisi yalnizca secilen urunun kendi satislari uzerinden hesaplanir.
    simulation_result = simulate_campaign(
        df=df,
        selected_product=selected_product,
        discount_rate=discount_rate,
        start_date=start_date,
        end_date=end_date,
        scenario_label="Senaryo B",
    )
    scenario_df = build_scenario_comparison(
        df=df,
        selected_product=selected_product,
        start_date=start_date,
        end_date=end_date,
        base_discount_rate=discount_rate,
    )

    if simulation_result["baseline_quantity"] == 0:
        st.warning("Secilen urun ve tarih araliginda yeterli satis verisi bulunamadi.")
        return

    _render_main_metrics(simulation_result)
    _render_financial_summary(simulation_result)

    detail_col1, detail_col2 = st.columns([1, 1.2])
    with detail_col1:
        st.markdown("### Baz Satis Bilgisi")
        _render_baseline_table(simulation_result)
    with detail_col2:
        _render_scenario_chart(scenario_df)

    st.markdown("### Senaryo Tablosu")
    st.dataframe(scenario_df, use_container_width=True, hide_index=True)

    _render_assumptions(discount_rate)

    action_col1, action_col2 = st.columns([1, 1.4])
    with action_col1:
        if st.button("Kampanyayi Aktif Yap", use_container_width=True):
            st.session_state.active_campaign = simulation_result
            st.success("Bu kampanya aktif kampanya olarak kaydedildi.")
    with action_col2:
        if st.session_state.active_campaign:
            active_campaign = st.session_state.active_campaign
            st.success(
                f"Aktif kampanya: {active_campaign['selected_product']} | "
                f"%{active_campaign['discount_rate']} indirim | "
                f"{active_campaign['new_revenue']:,.2f} TL tahmini gelir"
            )
