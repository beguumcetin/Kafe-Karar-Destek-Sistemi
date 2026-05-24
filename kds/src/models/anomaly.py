from __future__ import annotations

import pandas as pd


def detect_daily_sales_anomalies(daily_sales_df: pd.DataFrame, z_threshold: float = 2.0) -> pd.DataFrame:
    if daily_sales_df.empty:
        return pd.DataFrame(columns=["transaction_date", "daily_sales", "z_score", "signal"])

    working_df = daily_sales_df.copy().sort_values("transaction_date")
    mean_value = working_df["daily_sales"].mean()
    std_value = working_df["daily_sales"].std(ddof=0)
    working_df["expected_sales"] = mean_value

    if std_value == 0 or pd.isna(std_value):
        working_df["z_score"] = 0.0
    else:
        working_df["z_score"] = (working_df["daily_sales"] - mean_value) / std_value
    working_df["sales_gap"] = working_df["daily_sales"] - working_df["expected_sales"]

    def _label(value: float) -> str:
        if value >= z_threshold:
            return "Beklenenden yuksek satis"
        if value <= -z_threshold:
            return "Beklenenden dusuk satis"
        return "Normal"

    working_df["signal"] = working_df["z_score"].apply(_label)
    return working_df


def detect_hourly_sales_anomalies(df: pd.DataFrame, z_threshold: float = 2.0) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["hour", "hourly_sales", "transaction_count", "z_score", "signal"])

    hourly_df = (
        df.groupby("hour")
        .agg(
            hourly_sales=("sales_amount", "sum"),
            transaction_count=("sales_amount", "size"),
        )
        .reset_index()
        .sort_values("hour")
    )
    mean_value = hourly_df["hourly_sales"].mean()
    std_value = hourly_df["hourly_sales"].std(ddof=0)
    hourly_df["expected_sales"] = mean_value

    if std_value == 0 or pd.isna(std_value):
        hourly_df["z_score"] = 0.0
    else:
        hourly_df["z_score"] = (hourly_df["hourly_sales"] - mean_value) / std_value
    hourly_df["sales_gap"] = hourly_df["hourly_sales"] - hourly_df["expected_sales"]

    hourly_df["signal"] = hourly_df["z_score"].apply(
        lambda value: "Yogun saat anomalisi"
        if value >= z_threshold
        else ("Dusuk saat performansi" if value <= -z_threshold else "Normal")
    )
    return hourly_df


def summarize_anomalies(daily_anomalies_df: pd.DataFrame, hourly_anomalies_df: pd.DataFrame) -> dict[str, object]:
    abnormal_days = daily_anomalies_df[daily_anomalies_df["signal"] != "Normal"].copy()
    abnormal_hours = hourly_anomalies_df[hourly_anomalies_df["signal"] != "Normal"].copy()

    top_day_signal = abnormal_days.sort_values("z_score", key=lambda s: s.abs(), ascending=False).head(1)
    top_hour_signal = abnormal_hours.sort_values("z_score", key=lambda s: s.abs(), ascending=False).head(1)

    return {
        "daily_anomaly_count": int(len(abnormal_days)),
        "hourly_anomaly_count": int(len(abnormal_hours)),
        "top_day_signal": None if top_day_signal.empty else top_day_signal.iloc[0].to_dict(),
        "top_hour_signal": None if top_hour_signal.empty else top_hour_signal.iloc[0].to_dict(),
    }
