from __future__ import annotations

import pandas as pd
import streamlit as st

from src.components.anomaly_view import render_anomaly_view
from src.components.forecast_view import render_forecast_view
from src.components.recommendation_view import render_recommendation_view
from src.components.segment_view import render_segment_view


def render_decision_center_view(df: pd.DataFrame) -> None:
    st.subheader("Karar Destek Merkezi")
    st.caption("Tahmin, anomali, segmentasyon ve aksiyon motorunu tek ekranda birlestiren ana karar destek alani")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Tahmin",
            "Anomali",
            "Segmentasyon",
            "Aksiyonlar",
        ]
    )

    with tab1:
        render_forecast_view(df)
    with tab2:
        render_anomaly_view(df)
    with tab3:
        render_segment_view(df)
    with tab4:
        render_recommendation_view(df)
