from __future__ import annotations

import pandas as pd


def prepare_daily_sales_series(daily_sales_df: pd.DataFrame) -> pd.DataFrame:
    if daily_sales_df.empty:
        return pd.DataFrame(columns=["transaction_date", "daily_sales", "weekday"])

    working_df = daily_sales_df.copy().sort_values("transaction_date")
    working_df["transaction_date"] = pd.to_datetime(working_df["transaction_date"])
    working_df = working_df.set_index("transaction_date")

    full_index = pd.date_range(
        start=working_df.index.min(),
        end=working_df.index.max(),
        freq="D",
    )
    working_df = working_df.reindex(full_index, fill_value=0)
    working_df.index.name = "transaction_date"
    working_df = working_df.reset_index()
    working_df["weekday"] = working_df["transaction_date"].dt.day_name()
    return working_df


def _weekday_mean_fallback(prepared_df: pd.DataFrame, forecast_days: int = 7) -> pd.DataFrame:
    if prepared_df.empty:
        return pd.DataFrame(columns=["date", "predicted_sales", "method"])

    weekday_means = prepared_df.groupby("weekday")["daily_sales"].mean().to_dict()
    recent_mean = prepared_df["daily_sales"].tail(7).mean()
    last_date = prepared_df["transaction_date"].max()
    predictions = []

    for step in range(1, forecast_days + 1):
        next_date = last_date + pd.Timedelta(days=step)
        weekday_name = next_date.day_name()
        weekday_estimate = weekday_means.get(weekday_name, recent_mean)
        predicted_sales = (0.65 * weekday_estimate) + (0.35 * recent_mean)
        predictions.append(
            {
                "date": next_date,
                "predicted_sales": round(max(predicted_sales, 50.0), 2),
                "method": "Hafta gunu ortalamasi + son 7 gun ortalamasi",
            }
        )

    return pd.DataFrame(predictions)


def holt_winters_forecast(daily_sales_df: pd.DataFrame, forecast_days: int = 7) -> pd.DataFrame:
    prepared_df = prepare_daily_sales_series(daily_sales_df)
    if prepared_df.empty:
        return pd.DataFrame(columns=["date", "predicted_sales", "method"])

    sales_series = prepared_df.set_index("transaction_date")["daily_sales"].astype(float)

    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        # Kahve satislari haftalik dongu gosterebildigi icin haftalik sezonsallik eklenir.
        # Additive trend + additive seasonal yapi, ogrenci projesi icin hem aciklanabilir
        # hem de gunluk dalgalanmayi agresif olmayan sekilde yansitmak icin uygundur.
        model = ExponentialSmoothing(
            sales_series,
            trend="add",
            seasonal="add",
            seasonal_periods=7,
            damped_trend=True,
            initialization_method="estimated",
        )
        fitted_model = model.fit(optimized=True, remove_bias=True)
        raw_forecast = fitted_model.forecast(forecast_days)

        recent_mean = sales_series.tail(7).mean()
        floor_value = max(50.0, recent_mean * 0.35)
        cap_value = max(recent_mean * 1.75, 120.0)
        adjusted_forecast = raw_forecast.clip(lower=floor_value, upper=cap_value)

        return pd.DataFrame(
            {
                "date": adjusted_forecast.index,
                "predicted_sales": adjusted_forecast.round(2).values,
                "method": "Holt-Winters Exponential Smoothing",
            }
        )
    except Exception:
        return _weekday_mean_fallback(prepared_df, forecast_days=forecast_days)


def summarize_forecast(daily_sales_df: pd.DataFrame, forecast_df: pd.DataFrame) -> dict[str, float | str]:
    if daily_sales_df.empty or forecast_df.empty:
        return {
            "latest_actual": 0.0,
            "average_forecast": 0.0,
            "trend_percent": 0.0,
            "comment": "Tahmin icin yeterli veri yok.",
            "method": "Yok",
        }

    prepared_df = prepare_daily_sales_series(daily_sales_df)
    latest_actual = float(prepared_df.iloc[-1]["daily_sales"])
    recent_actual_mean = float(prepared_df["daily_sales"].tail(7).mean())
    average_forecast = float(forecast_df["predicted_sales"].mean())
    trend_percent = ((average_forecast - recent_actual_mean) / recent_actual_mean * 100) if recent_actual_mean > 0 else 0.0

    if trend_percent > 5:
        comment = "Kisa vadede satislarda artisa yakin bir egilim var. Stok ve personel planlamasi gozden gecirilebilir."
    elif trend_percent < -5:
        comment = "Kisa vadede satislarda gerileme bekleniyor. Kampanya veya urun gorunurlugu destegi dusunulebilir."
    else:
        comment = "Kisa vadede satislar mevcut seviyeye yakin seyredebilir."

    return {
        "latest_actual": round(latest_actual, 2),
        "recent_actual_mean": round(recent_actual_mean, 2),
        "average_forecast": round(average_forecast, 2),
        "trend_percent": round(trend_percent, 2),
        "comment": comment,
        "method": str(forecast_df["method"].iloc[0]) if "method" in forecast_df.columns else "Bilinmiyor",
    }


def build_forecast_plot_frame(daily_sales_df: pd.DataFrame, forecast_df: pd.DataFrame) -> pd.DataFrame:
    actual_df = prepare_daily_sales_series(daily_sales_df).rename(
        columns={"transaction_date": "date", "daily_sales": "sales"}
    )
    actual_df["series"] = "Gerceklesen"

    predicted_df = forecast_df.rename(columns={"predicted_sales": "sales"}).copy()
    predicted_df["series"] = "Tahmin"

    combined_df = pd.concat(
        [
            actual_df[["date", "sales", "series"]],
            predicted_df[["date", "sales", "series"]],
        ],
        ignore_index=True,
    )
    return combined_df.sort_values("date")
