from __future__ import annotations

import math

import pandas as pd

from src.models.campaign import simulate_campaign


def _period_bounds(df: pd.DataFrame) -> tuple[object, object, int]:
    dates = pd.to_datetime(df["transaction_date"])
    start_date = dates.min().date()
    end_date = dates.max().date()
    day_count = max((end_date - start_date).days + 1, 1)
    return start_date, end_date, day_count


def _period_label(start_date, end_date) -> str:
    return f"{pd.to_datetime(start_date).date()} - {pd.to_datetime(end_date).date()}"


def _format_effect(quantity_delta: float, revenue_delta: float) -> str:
    return f"+{quantity_delta:,.0f} adet / {revenue_delta:,.2f} TL etkisi"


def _best_campaign_scenario(df: pd.DataFrame, product_name: str, start_date, end_date) -> dict[str, float | int | str]:
    recent_end = pd.to_datetime(end_date)
    recent_start = max(pd.to_datetime(start_date), recent_end - pd.Timedelta(days=29))
    candidate_discounts = [5, 10, 15]
    simulations = [
        simulate_campaign(
            df=df,
            selected_product=product_name,
            discount_rate=discount_rate,
            start_date=recent_start,
            end_date=recent_end,
            scenario_label=f"%{discount_rate} kampanya",
        )
        for discount_rate in candidate_discounts
    ]
    best_result = max(simulations, key=lambda item: item["revenue_difference"])
    return best_result


def _build_stock_recommendation(row: pd.Series, trend_percent: float, period_days: int, period_text: str) -> dict[str, str]:
    growth_ratio = max(trend_percent / 100, 0.10)
    extra_sales = max(math.ceil((row["total_quantity"] / period_days) * growth_ratio * 7), 1)
    estimated_revenue = extra_sales * row["average_price"]
    stock_ratio = max(round(growth_ratio * 100), 10)

    return {
        "Sinyal": f"{row['product_type']} urununde yukari yonlu talep sinyali var.",
        "Neden": f"{period_text} doneminde {row['segment_name']} segmentinde ve tahmin trendi +%{trend_percent:.1f}.",
        "Oneri": f"{row['product_type']} icin gelecek 7 gun stok seviyesi en az %{stock_ratio} artirilmali.",
        "Tahmini Etki": _format_effect(extra_sales, estimated_revenue),
        "Oncelik": "Yuksek",
    }


def _build_campaign_recommendation(df: pd.DataFrame, row: pd.Series, start_date, end_date, period_text: str) -> dict[str, str]:
    campaign_result = _best_campaign_scenario(df, row["product_type"], start_date, end_date)
    quantity_gain = max(campaign_result["new_quantity"] - campaign_result["baseline_quantity"], 0)
    revenue_gain = campaign_result["revenue_difference"]

    return {
        "Sinyal": f"{row['product_type']} urununde satis dusus riski var.",
        "Neden": f"{period_text} doneminde satis trendi zayif ve urun {row['segment_name']} segmentinde.",
        "Oneri": (
            f"{row['product_type']} icin %{campaign_result['discount_rate']} indirimli kampanya "
            "onumuzdeki 7 gun icin uygulanmali."
        ),
        "Tahmini Etki": _format_effect(quantity_gain, revenue_gain),
        "Oncelik": "Yuksek" if revenue_gain >= 0 else "Orta",
    }


def _build_bundle_recommendation(row: pd.Series, period_days: int, period_text: str) -> dict[str, str]:
    bundle_extra_sales = max(math.ceil((row["total_quantity"] / period_days) * 0.12 * 7), 1)
    bundle_revenue = bundle_extra_sales * row["average_price"]
    return {
        "Sinyal": f"{row['product_type']} urunu orta potansiyel segmentte.",
        "Neden": f"{period_text} doneminde urun {row['segment_name']} segmentinde ve dogrudan fiyat indirimi yerine destekleyici teklif daha uygun.",
        "Oneri": f"{row['product_type']} icin bundle veya cross-sell teklifi hazirlanmali.",
        "Tahmini Etki": _format_effect(bundle_extra_sales, bundle_revenue),
        "Oncelik": "Orta",
    }


def _build_daily_anomaly_recommendation(top_day_signal: dict[str, object]) -> dict[str, str]:
    day_value = pd.to_datetime(top_day_signal["transaction_date"]).date()
    sales_gap = float(top_day_signal.get("sales_gap", 0.0))
    signal = str(top_day_signal["signal"])

    if signal == "Beklenenden yuksek satis":
        return {
            "Sinyal": f"{day_value} tarihinde beklenenden yuksek satis goruldu.",
            "Neden": f"Gunluk satis beklenen seviyeden {sales_gap:,.2f} TL yukari cikti.",
            "Oneri": f"{day_value} tarihindeki fiyat, kampanya, stok ve personel kosullari incelenip benzer donemlere uyarlanmalı.",
            "Tahmini Etki": f"Benzer kosullar tekrarlandiginda +{sales_gap:,.2f} TL firsat olusabilir",
            "Oncelik": "Orta",
        }

    return {
        "Sinyal": f"{day_value} tarihinde beklenenden dusuk satis goruldu.",
        "Neden": f"Gunluk satis beklenen seviyeden {abs(sales_gap):,.2f} TL asagida kaldi.",
        "Oneri": f"{day_value} tarihi icin operasyon, stok, fiyat ve trafik neden analizi yapilmali.",
        "Tahmini Etki": f"Kayip riski yaklasik {abs(sales_gap):,.2f} TL",
        "Oncelik": "Yuksek",
    }


def _build_hourly_anomaly_recommendation(top_hour_signal: dict[str, object], period_text: str) -> dict[str, str]:
    hour_value = int(top_hour_signal["hour"])
    sales_gap = float(top_hour_signal.get("sales_gap", 0.0))
    signal = str(top_hour_signal["signal"])

    if signal == "Yogun saat anomalisi":
        return {
            "Sinyal": f"{hour_value:02d}:00 saatinde olagandisi yogunluk goruldu.",
            "Neden": f"{period_text} icinde bu saatte beklenenin {sales_gap:,.2f} TL uzerinde satis olustu.",
            "Oneri": f"{hour_value:02d}:00 - {hour_value + 1:02d}:00 araligina ek personel ve hazir urun plani eklenmeli.",
            "Tahmini Etki": f"Hizmet hizi korunursa +{sales_gap:,.2f} TL satis korunabilir",
            "Oncelik": "Yuksek",
        }

    return {
        "Sinyal": f"{hour_value:02d}:00 saatinde performans dususu var.",
        "Neden": f"{period_text} icinde bu saatte beklenenin {abs(sales_gap):,.2f} TL altinda satis goruldu.",
        "Oneri": f"{hour_value:02d}:00 - {hour_value + 1:02d}:00 araliginda vitrin, servis hizi ve urun hazirligi kontrol edilmeli.",
        "Tahmini Etki": f"Iyilestirme halinde {abs(sales_gap):,.2f} TL toparlanma potansiyeli var",
        "Oncelik": "Orta",
    }


def generate_recommendations(
    df: pd.DataFrame,
    forecast_summary: dict[str, float | str],
    anomaly_summary: dict[str, object],
    segment_df: pd.DataFrame,
    hourly_peak: dict[str, int | float],
) -> pd.DataFrame:
    recommendations: list[dict[str, str]] = []
    start_date, end_date, period_days = _period_bounds(df)
    period_text = _period_label(start_date, end_date)
    trend_percent = float(forecast_summary.get("trend_percent", 0.0))

    if not segment_df.empty:
        high_demand = segment_df[segment_df["segment_name"] == "Yuksek gelir / yuksek talep"].sort_values("total_revenue", ascending=False)
        low_demand = segment_df[segment_df["segment_name"] == "Dusuk gelir / dusuk talep"].sort_values("total_revenue", ascending=True)
        mid_segment = segment_df[segment_df["segment_name"] == "Kampanya adayi urun"].sort_values("total_revenue", ascending=False)
        stock_risk = segment_df[segment_df["segment_name"] == "Stok riski tasiyan urun"].sort_values("total_revenue", ascending=False)

        if trend_percent < -5:
            for _, row in high_demand.head(2).iterrows():
                recommendations.append(_build_campaign_recommendation(df, row, start_date, end_date, period_text))

        if trend_percent > 5:
            for _, row in high_demand.head(2).iterrows():
                recommendations.append(_build_stock_recommendation(row, trend_percent, period_days, period_text))

        for _, row in low_demand.head(2).iterrows():
            recommendations.append(_build_campaign_recommendation(df, row, start_date, end_date, period_text))

        for _, row in mid_segment.head(2).iterrows():
            recommendations.append(_build_bundle_recommendation(row, period_days, period_text))

        for _, row in stock_risk.head(2).iterrows():
            recommendations.append(_build_stock_recommendation(row, max(trend_percent, 10.0), period_days, period_text))

    top_day_signal = anomaly_summary.get("top_day_signal")
    if top_day_signal:
        recommendations.append(_build_daily_anomaly_recommendation(top_day_signal))

    top_hour_signal = anomaly_summary.get("top_hour_signal")
    if top_hour_signal:
        recommendations.append(_build_hourly_anomaly_recommendation(top_hour_signal, period_text))

    if not recommendations:
        recommendations.append(
            {
                "Sinyal": "Belirgin risk veya firsat sinyali bulunmadi.",
                "Neden": f"{period_text} doneminde tahmin, anomali ve segmentasyon ciktilari kritik esik uretmedi.",
                "Oneri": "Mevcut plan korunup sistem haftalik olarak tekrar izlenmeli.",
                "Tahmini Etki": "Stabil seviye korunursa mevcut satis duzeyi devam eder",
                "Oncelik": "Dusuk",
            }
        )

    recommendation_df = pd.DataFrame(recommendations)
    priority_order = {"Yuksek": 0, "Orta": 1, "Dusuk": 2}
    recommendation_df["priority_rank"] = recommendation_df["Oncelik"].map(priority_order).fillna(9)
    recommendation_df = recommendation_df.drop_duplicates(subset=["Sinyal", "Oneri"]).sort_values("priority_rank")
    return recommendation_df.drop(columns=["priority_rank"]).reset_index(drop=True)
