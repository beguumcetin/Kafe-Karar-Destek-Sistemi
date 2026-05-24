from __future__ import annotations

import pandas as pd
import streamlit as st

from src.components.employee_view import render_employee_view
from src.components.user_login_view import render_user_login_view
from src.components.user_panel_view import render_user_panel_view


def render_audience_panel_view(df: pd.DataFrame) -> None:
    st.subheader("Kullanici / Calisan Paneli")
    st.caption("Calisan gorunumu ile son kullanici panelini tek ekranda bir araya getiren sade alan")

    tab1, tab2, tab3 = st.tabs(
        [
            "Calisan Gorunumu",
            "Kullanici Girisi",
            "Kullanici Paneli",
        ]
    )

    with tab1:
        render_employee_view(df)
    with tab2:
        render_user_login_view()
    with tab3:
        render_user_panel_view(df)
