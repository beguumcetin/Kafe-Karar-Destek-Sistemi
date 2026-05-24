from __future__ import annotations

import streamlit as st


SAMPLE_USERS = [
    {
        "user_id": "u001",
        "full_name": "Ayse Yilmaz",
        "email": "ayse@example.com",
        "membership": "Gold",
        "favorite_product": "Latte",
        "preferred_time": "08:00 - 10:00",
        "recent_orders": [
            {"date": "2025-03-20", "product": "Latte", "amount": 38.70},
            {"date": "2025-03-17", "product": "Cappuccino", "amount": 35.90},
            {"date": "2025-03-14", "product": "Latte", "amount": 38.70},
        ],
    },
    {
        "user_id": "u002",
        "full_name": "Mehmet Kaya",
        "email": "mehmet@example.com",
        "membership": "Silver",
        "favorite_product": "Americano with Milk",
        "preferred_time": "10:00 - 12:00",
        "recent_orders": [
            {"date": "2025-03-21", "product": "Americano with Milk", "amount": 33.80},
            {"date": "2025-03-18", "product": "Espresso", "amount": 24.00},
            {"date": "2025-03-13", "product": "Americano", "amount": 28.90},
        ],
    },
    {
        "user_id": "u003",
        "full_name": "Zeynep Demir",
        "email": "zeynep@example.com",
        "membership": "Standard",
        "favorite_product": "Hot Chocolate",
        "preferred_time": "17:00 - 19:00",
        "recent_orders": [
            {"date": "2025-03-22", "product": "Hot Chocolate", "amount": 38.70},
            {"date": "2025-03-19", "product": "Cocoa", "amount": 38.70},
            {"date": "2025-03-15", "product": "Hot Chocolate", "amount": 38.70},
        ],
    },
]


def initialize_user_session() -> None:
    if "logged_user_id" not in st.session_state:
        st.session_state.logged_user_id = None


def get_sample_users() -> list[dict[str, object]]:
    return SAMPLE_USERS


def get_user_by_id(user_id: str | None) -> dict[str, object] | None:
    if not user_id:
        return None
    for user in SAMPLE_USERS:
        if user["user_id"] == user_id:
            return user
    return None


def login_user(user_id: str) -> None:
    st.session_state.logged_user_id = user_id


def logout_user() -> None:
    st.session_state.logged_user_id = None
