from __future__ import annotations

import pandas as pd
import streamlit as st

from src.data.loader import get_peak_hour_for_period, get_top_products
from src.data.users import get_user_by_id, initialize_user_session, logout_user


def _render_user_styles() -> None:
    st.markdown(
        """
        <style>
        .user-card {
            background: linear-gradient(180deg, #fffdf8 0%, #f4efe5 100%);
            border: 1px solid #eadfce;
            border-radius: 18px;
            padding: 18px;
            margin-bottom: 14px;
        }
        .user-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #2d2016;
            margin-bottom: 8px;
        }
        .user-big {
            font-size: 1.7rem;
            font-weight: 800;
            color: #3c2c1f;
            margin-bottom: 8px;
        }
        .user-text {
            font-size: 0.97rem;
            color: #5b4636;
            line-height: 1.55;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _build_personal_suggestion(user: dict[str, object], active_campaign, peak_hour: dict[str, int | float]) -> str:
    favorite_product = str(user["favorite_product"])
    if active_campaign and active_campaign.get("selected_product") == favorite_product:
        return (
            f"Favori urunun olan {favorite_product} icin aktif kampanya var. "
            f"Yogunluk baslamadan once, yani {int(peak_hour['hour']) - 1:02d}:00 civarinda siparis vermek daha rahat olabilir."
        )
    return (
        f"{favorite_product} senin favori urunun olarak gorunuyor. "
        f"En yogun saat {int(peak_hour['hour']):02d}:00 oldugu icin {user['preferred_time']} araliginda siparis vermek daha uygun olabilir."
    )


def render_user_panel_view(df: pd.DataFrame) -> None:
    st.subheader("Kullanici Paneli")
    st.caption("Son kullaniciya yonelik sade profil ve kampanya ekrani")

    initialize_user_session()
    user = get_user_by_id(st.session_state.get("logged_user_id"))
    _render_user_styles()

    if not user:
        st.warning("Once Kullanici Girisi ekranindan bir kullanici secmelisin.")
        return

    active_campaign = st.session_state.get("active_campaign")
    peak_hour = get_peak_hour_for_period(df)
    top_products = get_top_products(df, top_n=3)
    personal_suggestion = _build_personal_suggestion(user, active_campaign, peak_hour)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(
            f"""
            <div class="user-card">
                <div class="user-title">Profil</div>
                <div class="user-big">{user['full_name']}</div>
                <div class="user-text">E-posta: {user['email']}</div>
                <div class="user-text">Uyelik: {user['membership']}</div>
                <div class="user-text">Favori urun: {user['favorite_product']}</div>
                <div class="user-text">Tercih edilen saat: {user['preferred_time']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if active_campaign:
            st.markdown(
                f"""
                <div class="user-card">
                    <div class="user-title">Aktif Kampanya</div>
                    <div class="user-big">{active_campaign['selected_product']}</div>
                    <div class="user-text">Indirim orani: %{active_campaign['discount_rate']}</div>
                    <div class="user-text">Beklenen talep artisi: %{active_campaign['uplift_rate']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="user-card">
                    <div class="user-title">Aktif Kampanya</div>
                    <div class="user-text">Su anda aktif kampanya tanimlanmamis gorunuyor.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col2:
        st.markdown(
            f"""
            <div class="user-card">
                <div class="user-title">Kisisel Oneri</div>
                <div class="user-text">{personal_suggestion}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="user-card">
                <div class="user-title">Dukkan Bilgisi</div>
                <div class="user-text">En yogun saat: {int(peak_hour['hour']):02d}:00</div>
                <div class="user-text">Bu saatte yaklasik {peak_hour['transaction_count']} islem bekleniyor.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Son Siparisler")
    orders_df = pd.DataFrame(user["recent_orders"]).rename(
        columns={"date": "Tarih", "product": "Urun", "amount": "Tutar (TL)"}
    )
    st.dataframe(orders_df, use_container_width=True, hide_index=True)

    st.markdown("### Populer Urunler")
    st.dataframe(
        top_products.rename(
            columns={"product_type": "Urun", "revenue": "Gelir (TL)", "quantity": "Adet"}
        ),
        use_container_width=True,
        hide_index=True,
    )

    if st.button("Cikis Yap", use_container_width=True):
        logout_user()
        st.success("Kullanici oturumu kapatildi.")
