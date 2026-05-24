from __future__ import annotations

import pandas as pd
import streamlit as st

from src.data.loader import get_peak_hour_for_period


def _render_employee_styles() -> None:
    st.markdown(
        """
        <style>
        .employee-card {
            background: linear-gradient(135deg, #f7efe4, #fffaf4);
            border: 1px solid #eadfce;
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 14px;
        }
        .employee-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #5b4636;
            margin-bottom: 10px;
        }
        .employee-big {
            font-size: 2.3rem;
            font-weight: 800;
            color: #2d2016;
            line-height: 1.1;
        }
        .employee-sub {
            font-size: 1rem;
            color: #6b5a4d;
            margin-top: 8px;
        }
        .employee-list-item {
            font-size: 1.1rem;
            padding: 8px 0;
            border-bottom: 1px solid #efe6da;
            color: #33261c;
        }
        .employee-note {
            font-size: 1.1rem;
            line-height: 1.6;
            color: #3d3026;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _build_period_selector(df: pd.DataFrame) -> tuple[object, object]:
    min_date = pd.to_datetime(df["transaction_date"]).min().date()
    max_date = pd.to_datetime(df["transaction_date"]).max().date()

    selected_range = st.date_input(
        "Donem secimi",
        value=(max_date, max_date),
        min_value=min_date,
        max_value=max_date,
        help="Bugun veya secilen donem icin operasyon bilgisini gosterir.",
    )

    if len(selected_range) != 2:
        st.warning("Lutfen baslangic ve bitis tarihini birlikte sec.")
        st.stop()

    start_date, end_date = selected_range
    if start_date > end_date:
        st.error("Baslangic tarihi bitis tarihinden buyuk olamaz.")
        st.stop()

    return start_date, end_date


def _build_top_products_for_period(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    working_df = df.copy()
    working_df["transaction_date"] = pd.to_datetime(working_df["transaction_date"])
    date_mask = working_df["transaction_date"].between(pd.to_datetime(start_date), pd.to_datetime(end_date))
    filtered_df = working_df[date_mask]

    if filtered_df.empty:
        return pd.DataFrame(columns=["product_type", "quantity"])

    top_products = (
        filtered_df.groupby("product_type")
        .agg(quantity=("transaction_qty", "sum"), revenue=("sales_amount", "sum"))
        .reset_index()
        .sort_values(["quantity", "revenue"], ascending=False)
        .head(3)
    )
    return top_products


def _build_operational_note(peak_info: dict[str, int | float], active_campaign) -> str:
    hour_text = f"{peak_info['hour']:02d}:00"
    if active_campaign:
        return (
            f"{hour_text} saatinde hazirlik seviyesini arttirin. "
            f"{active_campaign['selected_product']} urununde aktif kampanya oldugu icin bu urun icin stok ve servis hazirligini one alin."
        )
    return (
        f"{hour_text} saatinden once kasa ve servis alanini hazirlayin. "
        "Ek urun ve bardak hazirligini yogunluk baslamadan tamamlamak operasyonu rahatlatir."
    )


def render_employee_view(df: pd.DataFrame) -> None:
    st.subheader("Calisan Bilgi Ekrani")
    st.caption("Teknik olmayan personel icin hizli okunabilir operasyon panosu")

    _render_employee_styles()
    start_date, end_date = _build_period_selector(df)
    peak_info = get_peak_hour_for_period(df, start_date=start_date, end_date=end_date)
    top_products = _build_top_products_for_period(df, start_date, end_date)
    active_campaign = st.session_state.get("active_campaign")
    operational_note = _build_operational_note(peak_info, active_campaign)

    info_col1, info_col2 = st.columns([1.1, 0.9])

    with info_col1:
        st.markdown("### Yogunluk Bilgisi")
        st.markdown(
            f"""
            <div class="employee-card">
                <div class="employee-title">En Yogun Saat</div>
                <div class="employee-big">{peak_info['hour']:02d}:00</div>
                <div class="employee-sub">Bu zaman diliminde yaklasik {peak_info['transaction_count']} islem bekleniyor.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Top 3 Satilan Urun")
        if top_products.empty:
            st.warning("Secilen donem icin urun bilgisi bulunamadi.")
        else:
            product_lines = "".join(
                [
                    f'<div class="employee-list-item">{index + 1}. {row["product_type"]} - {row["quantity"]:,.0f} adet</div>'
                    for index, (_, row) in enumerate(top_products.iterrows())
                ]
            )
            st.markdown(f'<div class="employee-card">{product_lines}</div>', unsafe_allow_html=True)

    with info_col2:
        st.markdown("### Aktif Kampanya")
        if active_campaign:
            st.markdown(
                f"""
                <div class="employee-card">
                    <div class="employee-title">Uygulanacak Kampanya</div>
                    <div class="employee-big">{active_campaign['selected_product']}</div>
                    <div class="employee-sub">Indirim: %{active_campaign['discount_rate']}</div>
                    <div class="employee-sub">Beklenen talep artisi: %{active_campaign['uplift_rate']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="employee-card">
                    <div class="employee-title">Uygulanacak Kampanya</div>
                    <div class="employee-big">Aktif kampanya yok</div>
                    <div class="employee-sub">Yonetici ekrani uzerinden kampanya tanimlandiginda burada gorunur.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### Kisa Operasyonel Oneri")
        st.markdown(
            f"""
            <div class="employee-card">
                <div class="employee-note">{operational_note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
