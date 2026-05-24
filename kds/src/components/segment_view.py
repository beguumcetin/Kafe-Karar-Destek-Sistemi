from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.models.segmentation import run_product_segmentation, summarize_segments


def render_segment_view(df: pd.DataFrame) -> None:
    st.subheader("Segmentasyon")
    st.caption("K-Means tabanli urun segmentasyonu ile neden sorusuna yaklasilir")

    segment_df = run_product_segmentation(df, n_clusters=4)
    summary_df = summarize_segments(segment_df)

    if segment_df.empty:
        st.warning("Segmentasyon icin yeterli veri bulunamadi.")
        return

    fig = px.scatter(
        segment_df,
        x="total_quantity",
        y="total_revenue",
        color="segment_name",
        size="average_price",
        hover_name="product_type",
        title="Urun Segment Haritasi",
    )
    fig.update_layout(xaxis_title="Toplam Adet", yaxis_title="Toplam Gelir (TL)")
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.markdown("### Segmentlenmis Urunler")
        st.dataframe(
            segment_df.rename(
                columns={
                    "product_type": "Urun",
                    "total_revenue": "Toplam Gelir (TL)",
                    "total_quantity": "Toplam Adet",
                    "average_price": "Ort. Fiyat",
                    "average_hour": "Ort. Saat",
                    "segment_name": "Segment",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    with col2:
        st.markdown("### Segment Ozeti")
        st.dataframe(
            summary_df.rename(
                columns={
                    "segment_name": "Segment",
                    "product_count": "Urun Sayisi",
                    "avg_revenue": "Ort. Gelir",
                    "avg_quantity": "Ort. Adet",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
