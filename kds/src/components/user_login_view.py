from __future__ import annotations

import streamlit as st

from src.data.users import get_sample_users, initialize_user_session, login_user


def render_user_login_view() -> None:
    st.subheader("Kullanici Girisi")
    st.caption("Prototip kullanici paneli icin basit giris ekrani")

    initialize_user_session()
    users = get_sample_users()
    user_options = {f"{user['full_name']} - {user['membership']}": user["user_id"] for user in users}

    st.markdown(
        "Bu prototipte gercek uyelik sistemi yerine ornek kullanicilar secilerek giris yapilir."
    )
    selected_label = st.selectbox("Kullanici sec", list(user_options.keys()))
    selected_user_id = user_options[selected_label]

    if st.button("Panele Gir", use_container_width=True):
        login_user(selected_user_id)
        st.success("Kullanici oturumu baslatildi. Simdi Kullanici Paneli ekranina gecebilirsin.")
