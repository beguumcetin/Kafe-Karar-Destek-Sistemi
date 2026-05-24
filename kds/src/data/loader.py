from __future__ import annotations

from pathlib import Path
from io import StringIO

import pandas as pd
import streamlit as st

from src.utils.constants import FALLBACK_DATA_FILE, PRIMARY_DATA_FILE


COLUMN_ALIASES = {
    "transaction_id": ["transaction_id", "transaction id", "id", "order_id", "sale_id"],
    "transaction_date": ["transaction_date", "transaction date", "date", "sale_date"],
    "transaction_time": ["transaction_time", "transaction time", "time", "sale_time"],
    "transaction_qty": ["transaction_qty", "transaction qty", "quantity", "qty"],
    "unit_price": ["unit_price", "unit price", "price"],
    "store_location": ["store_location", "store location", "branch", "location", "store"],
    "product_category": ["product_category", "product category", "category"],
    "product_type": ["product_type", "product type", "product", "item_name", "coffee_name", "coffee name"],
    "product_detail": ["product_detail", "product detail", "detail", "product_name", "coffee_name", "coffee name"],
    "sales_amount": ["sales_amount", "sales amount", "money", "amount", "revenue"],
    "hour": ["hour", "hour_of_day", "hour of day"],
    "weekday": ["weekday", "day_name", "day"],
    "month_name": ["month_name", "month name", "month"],
}


def _normalize_name(value: str) -> str:
    return str(value).strip().lower().replace("_", " ")


def _resolve_data_path() -> Path:
    if PRIMARY_DATA_FILE.exists():
        return PRIMARY_DATA_FILE
    return FALLBACK_DATA_FILE


def _extract_csv_text_from_rtf(raw_text: str) -> str:
    csv_lines: list[str] = []
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "hour_of_day," in line:
            line = line.split("hour_of_day,", 1)[1]
            line = "hour_of_day," + line
        if line.startswith("{\\rtf") or line == "}":
            continue
        line = line.replace("\\", "").strip()
        if "," in line:
            csv_lines.append(line)
    return "\n".join(csv_lines)


def _read_sales_file(data_path: Path) -> pd.DataFrame:
    raw_text = data_path.read_text(encoding="utf-8", errors="replace")

    if raw_text.lstrip().startswith("{\\rtf"):
        csv_text = _extract_csv_text_from_rtf(raw_text)
        return pd.read_csv(StringIO(csv_text))

    return pd.read_csv(StringIO(raw_text))


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map: dict[str, str] = {}
    normalized_columns = {_normalize_name(col): col for col in df.columns}

    for standard_name, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            source_column = normalized_columns.get(_normalize_name(alias))
            if source_column:
                rename_map[source_column] = standard_name
                break

    standardized_df = df.rename(columns=rename_map).copy()

    if "product_detail" not in standardized_df.columns and "product_type" in standardized_df.columns:
        standardized_df["product_detail"] = standardized_df["product_type"]

    if "product_type" not in standardized_df.columns and "product_detail" in standardized_df.columns:
        standardized_df["product_type"] = standardized_df["product_detail"]

    if "transaction_qty" not in standardized_df.columns:
        standardized_df["transaction_qty"] = 1

    if "unit_price" not in standardized_df.columns and "sales_amount" in standardized_df.columns:
        standardized_df["unit_price"] = standardized_df["sales_amount"] / standardized_df["transaction_qty"].clip(lower=1)

    return standardized_df


def _build_datetime(df: pd.DataFrame) -> pd.DataFrame:
    working_df = df.copy()

    date_source = working_df.get("transaction_date", working_df.get("Date"))
    time_source = working_df.get("transaction_time", working_df.get("Time"))
    hour_source = working_df.get("hour")
    date_series = pd.to_datetime(date_source, errors="coerce")
    time_series = time_source

    if time_series is not None:
        combined = (
            date_series.dt.strftime("%Y-%m-%d").fillna("") + " " + time_series.astype(str).fillna("")
        ).str.strip()
        transaction_datetime = pd.to_datetime(combined, errors="coerce")
    elif hour_source is not None:
        combined = (
            date_series.dt.strftime("%Y-%m-%d").fillna("") + " " + hour_source.astype(str).str.zfill(2) + ":00:00"
        ).str.strip()
        transaction_datetime = pd.to_datetime(combined, errors="coerce")
    else:
        transaction_datetime = pd.to_datetime(date_series, errors="coerce")

    working_df["transaction_date"] = date_series.dt.date
    working_df["transaction_time"] = (
        transaction_datetime.dt.strftime("%H:%M:%S").fillna("00:00:00")
    )
    working_df["transaction_datetime"] = transaction_datetime
    working_df["hour"] = transaction_datetime.dt.hour.fillna(0).astype(int)
    working_df["weekday"] = transaction_datetime.dt.day_name().fillna("Unknown")
    working_df["month"] = transaction_datetime.dt.to_period("M").astype(str)
    working_df["day_of_month"] = transaction_datetime.dt.day.fillna(0).astype(int)
    working_df["week_of_year"] = transaction_datetime.dt.isocalendar().week.fillna(0).astype(int)
    working_df["is_weekend"] = working_df["weekday"].isin(["Saturday", "Sunday"])

    return working_df


def _clean_numeric_fields(df: pd.DataFrame) -> pd.DataFrame:
    working_df = df.copy()
    qty_source = working_df["transaction_qty"] if "transaction_qty" in working_df.columns else pd.Series(1, index=working_df.index)
    price_source = working_df["unit_price"] if "unit_price" in working_df.columns else pd.Series(0, index=working_df.index)
    sales_source = working_df["sales_amount"] if "sales_amount" in working_df.columns else pd.Series(index=working_df.index, dtype=float)

    working_df["transaction_qty"] = pd.to_numeric(qty_source, errors="coerce").fillna(1)
    working_df["unit_price"] = pd.to_numeric(price_source, errors="coerce").fillna(0)
    existing_sales = pd.to_numeric(sales_source, errors="coerce")
    calculated_sales = working_df["transaction_qty"] * working_df["unit_price"]
    working_df["sales_amount"] = existing_sales.fillna(calculated_sales).fillna(0)
    return working_df


def _ensure_text_column(df: pd.DataFrame, column_name: str, default_value: str = "Unknown") -> pd.DataFrame:
    working_df = df.copy()
    if column_name not in working_df.columns:
        working_df[column_name] = default_value
    working_df[column_name] = working_df[column_name].fillna(default_value).astype(str)
    return working_df


@st.cache_data(show_spinner=False)
def load_sales_data() -> tuple[pd.DataFrame, Path]:
    data_path = _resolve_data_path()
    raw_df = _read_sales_file(data_path)
    clean_df = _standardize_columns(raw_df)
    clean_df = _clean_numeric_fields(clean_df)
    clean_df = _build_datetime(clean_df)
    clean_df = _ensure_text_column(clean_df, "product_category")
    clean_df = _ensure_text_column(clean_df, "product_type")
    clean_df = _ensure_text_column(clean_df, "product_detail")
    clean_df = _ensure_text_column(clean_df, "store_location")

    clean_df = clean_df.dropna(subset=["transaction_datetime"]).copy()
    clean_df = clean_df[clean_df["sales_amount"] >= 0].copy()

    return clean_df, data_path


def inspect_sales_columns() -> dict[str, object]:
    data_path = _resolve_data_path()
    raw_df = _read_sales_file(data_path)
    return {
        "path": str(data_path),
        "row_count": int(len(raw_df)),
        "column_count": int(len(raw_df.columns)),
        "columns": list(raw_df.columns),
    }


def summarize_sales(df: pd.DataFrame) -> dict[str, float | int]:
    return {
        "total_sales": float(df["sales_amount"].sum()),
        "transaction_count": int(df["transaction_id"].nunique() if "transaction_id" in df.columns else len(df)),
        "average_basket": float(df["sales_amount"].mean()),
        "total_quantity": float(df["transaction_qty"].sum()),
    }


def get_date_bounds(df: pd.DataFrame) -> tuple[object, object]:
    dates = pd.to_datetime(df["transaction_date"])
    return dates.min().date(), dates.max().date()


def filter_by_period(df: pd.DataFrame, start_date=None, end_date=None) -> pd.DataFrame:
    if start_date is None or end_date is None:
        return df.copy()

    working_df = df.copy()
    working_df["transaction_date"] = pd.to_datetime(working_df["transaction_date"])
    mask = working_df["transaction_date"].between(pd.to_datetime(start_date), pd.to_datetime(end_date))
    return working_df[mask].copy()


def get_daily_sales(df: pd.DataFrame) -> pd.DataFrame:
    daily = (
        df.groupby(pd.to_datetime(df["transaction_date"]))["sales_amount"]
        .sum()
        .reset_index(name="daily_sales")
        .sort_values("transaction_date")
    )
    return daily


def get_forecast_input_frame(df: pd.DataFrame) -> pd.DataFrame:
    forecast_df = get_daily_sales(df).rename(columns={"transaction_date": "date", "daily_sales": "sales"})
    forecast_df["date"] = pd.to_datetime(forecast_df["date"])
    return forecast_df


def get_hourly_sales(df: pd.DataFrame) -> pd.DataFrame:
    hourly = df.groupby("hour").agg(
        hourly_sales=("sales_amount", "sum"),
        transaction_count=("sales_amount", "size"),
    )
    return hourly.reset_index().sort_values("hour")


def get_campaign_baseline_frame(df: pd.DataFrame) -> pd.DataFrame:
    baseline_df = (
        df.groupby("product_type")
        .agg(
            baseline_quantity=("transaction_qty", "sum"),
            baseline_revenue=("sales_amount", "sum"),
            average_unit_price=("unit_price", "mean"),
            transaction_count=("sales_amount", "size"),
        )
        .reset_index()
        .sort_values("baseline_revenue", ascending=False)
    )
    return baseline_df


def get_product_revenue(df: pd.DataFrame) -> pd.DataFrame:
    product_revenue = (
        df.groupby("product_type")
        .agg(
            revenue=("sales_amount", "sum"),
            quantity=("transaction_qty", "sum"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    return product_revenue


def get_top_revenue_product(df: pd.DataFrame) -> dict[str, float]:
    product_revenue = get_product_revenue(df)
    if product_revenue.empty:
        return {"product_type": "Veri yok", "revenue": 0.0}

    top_row = product_revenue.iloc[0]
    return {
        "product_type": str(top_row["product_type"]),
        "revenue": float(top_row["revenue"]),
    }


def get_top_products(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    return get_product_revenue(df).head(top_n)


def get_peak_hour_for_period(df: pd.DataFrame, start_date=None, end_date=None) -> dict[str, int | float]:
    working_df = df.copy()
    working_df["transaction_date"] = pd.to_datetime(working_df["transaction_date"])

    if start_date is not None and end_date is not None:
        date_mask = working_df["transaction_date"].between(pd.to_datetime(start_date), pd.to_datetime(end_date))
        working_df = working_df[date_mask]

    if working_df.empty:
        return {"hour": 0, "sales": 0.0, "transaction_count": 0}

    hour_summary = (
        working_df.groupby("hour")
        .agg(
            sales_amount=("sales_amount", "sum"),
            transaction_count=("sales_amount", "size"),
        )
        .reset_index()
    )
    peak_row = hour_summary.sort_values(["transaction_count", "sales_amount"], ascending=False).head(1)

    if peak_row.empty:
        return {"hour": 0, "sales": 0.0, "transaction_count": 0}

    return {
        "hour": int(peak_row.iloc[0]["hour"]),
        "sales": float(peak_row.iloc[0]["sales_amount"]),
        "transaction_count": int(peak_row.iloc[0]["transaction_count"]),
    }


def get_weekday_sales(df: pd.DataFrame) -> pd.DataFrame:
    weekday_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    weekday_sales = (
        df.groupby("weekday")
        .agg(
            total_sales=("sales_amount", "sum"),
            transaction_count=("sales_amount", "size"),
        )
        .reset_index()
    )
    weekday_sales["weekday"] = pd.Categorical(
        weekday_sales["weekday"],
        categories=weekday_order,
        ordered=True,
    )
    weekday_sales = weekday_sales.sort_values("weekday")
    return weekday_sales


def get_today_like_peak_hour(df: pd.DataFrame) -> dict[str, int | float]:
    weekday_name = pd.Timestamp.today().day_name()
    weekday_df = df[df["weekday"] == weekday_name]

    if weekday_df.empty:
        weekday_df = df

    hour_summary = weekday_df.groupby("hour")["sales_amount"].sum().reset_index()
    peak_row = hour_summary.sort_values("sales_amount", ascending=False).head(1)

    if peak_row.empty:
        return {"hour": 0, "sales": 0.0}

    return {
        "hour": int(peak_row.iloc[0]["hour"]),
        "sales": float(peak_row.iloc[0]["sales_amount"]),
    }
