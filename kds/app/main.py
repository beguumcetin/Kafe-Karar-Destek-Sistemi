from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.components.campaign_view import render_campaign_simulator
from src.components.audience_panel_view import render_audience_panel_view
from src.components.dashboard_view import render_dashboard
from src.components.decision_center_view import render_decision_center_view
from src.components.report_view import render_report_view
from src.data.loader import load_sales_data
from src.utils.constants import APP_CAPTION, APP_TITLE, FALLBACK_DATA_FILE, PRIMARY_DATA_FILE


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="☕",
    layout="wide",
)


def main() -> None:
    df, data_path = load_sales_data()

    st.title(APP_TITLE)
    st.caption(APP_CAPTION)

    with st.sidebar:
        st.markdown("## Navigasyon")
        page = st.radio(
            "Ekran sec",
            options=[
                "Genel Dashboard",
                "Karar Destek Merkezi",
                "Kampanya Simulatoru",
                "Rapor Ekrani",
                "Kullanici / Calisan Paneli",
            ],
        )

        st.markdown("## Veri Durumu")
        if data_path == PRIMARY_DATA_FILE:
            st.success(f"Gercek veri dosyasi kullaniliyor: {data_path.name}")
        else:
            st.info(f"Demo veri kullaniliyor: {FALLBACK_DATA_FILE.name}")
            st.write("Gercek veri icin `data/raw/coffee_sales.csv` dosyasini ekleyebilirsin.")

        st.markdown("## Proje Notu")
        st.write(
            "Bu prototip, ders sunumu icin sade tasarlanmistir. Agir ML modelleri yerine aciklanabilir ve savunulabilir yaklasimlar kullanilir."
        )

    if page == "Genel Dashboard":
        render_dashboard(df)
    elif page == "Karar Destek Merkezi":
        render_decision_center_view(df)
    elif page == "Kampanya Simulatoru":
        render_campaign_simulator(df)
    elif page == "Rapor Ekrani":
        render_report_view(df)
    else:
        render_audience_panel_view(df)


if __name__ == "__main__":
    main()
