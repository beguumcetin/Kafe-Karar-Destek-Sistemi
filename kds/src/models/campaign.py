from __future__ import annotations

import pandas as pd


def _prepare_campaign_frame(
    df: pd.DataFrame,
    selected_product: str,
    start_date,
    end_date,
) -> pd.DataFrame:
    working_df = df[df["product_type"] == selected_product].copy()
    working_df["transaction_date"] = pd.to_datetime(working_df["transaction_date"])

    date_mask = working_df["transaction_date"].between(
        pd.to_datetime(start_date),
        pd.to_datetime(end_date),
    )
    return working_df[date_mask].copy()


def estimate_uplift_from_discount(discount_rate: float) -> float:
    # Ogrenci projesi icin savunulabilir basit varsayim:
    # Her %1 indirim yaklasik %1.8 talep artis potansiyeli olusturur.
    # Asiri iyimser sonuclari engellemek icin artis %60 ile sinirlanir.
    estimated_uplift = discount_rate * 1.8
    return round(min(estimated_uplift, 60.0), 2)


def calculate_baseline_metrics(
    df: pd.DataFrame,
    selected_product: str,
    start_date,
    end_date,
) -> dict[str, float | int]:
    campaign_df = _prepare_campaign_frame(df, selected_product, start_date, end_date)

    baseline_quantity = float(campaign_df["transaction_qty"].sum())
    baseline_revenue = float(campaign_df["sales_amount"].sum())
    baseline_transactions = int(
        campaign_df["transaction_id"].nunique() if "transaction_id" in campaign_df.columns else len(campaign_df)
    )
    average_unit_price = float(
        baseline_revenue / baseline_quantity if baseline_quantity > 0 else 0
    )
    campaign_days = int((pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1)
    daily_average_quantity = float(
        baseline_quantity / campaign_days if campaign_days > 0 else 0
    )

    return {
        "selected_product": selected_product,
        "campaign_days": campaign_days,
        "baseline_quantity": round(baseline_quantity, 2),
        "baseline_revenue": round(baseline_revenue, 2),
        "baseline_transactions": baseline_transactions,
        "average_unit_price": round(average_unit_price, 2),
        "daily_average_quantity": round(daily_average_quantity, 2),
    }


def simulate_campaign(
    df: pd.DataFrame,
    selected_product: str,
    discount_rate: float,
    start_date,
    end_date,
    uplift_rate: float | None = None,
    scenario_label: str = "Ana Senaryo",
) -> dict[str, float | int | str]:
    baseline = calculate_baseline_metrics(df, selected_product, start_date, end_date)
    effective_uplift = estimate_uplift_from_discount(discount_rate) if uplift_rate is None else float(uplift_rate)

    discounted_unit_price = baseline["average_unit_price"] * (1 - (discount_rate / 100))
    new_quantity = baseline["baseline_quantity"] * (1 + (effective_uplift / 100))
    new_revenue = new_quantity * discounted_unit_price
    revenue_difference = new_revenue - baseline["baseline_revenue"]

    result = {
        **baseline,
        "scenario_label": scenario_label,
        "discount_rate": round(float(discount_rate), 2),
        "uplift_rate": round(float(effective_uplift), 2),
        "discounted_unit_price": round(discounted_unit_price, 2),
        "new_quantity": round(new_quantity, 2),
        "new_revenue": round(new_revenue, 2),
        "revenue_difference": round(revenue_difference, 2),
    }
    return result


def build_scenario_comparison(
    df: pd.DataFrame,
    selected_product: str,
    start_date,
    end_date,
    base_discount_rate: float,
) -> pd.DataFrame:
    scenario_discounts = {
        "Senaryo A": max(base_discount_rate - 5, 0),
        "Senaryo B": base_discount_rate,
        "Senaryo C": min(base_discount_rate + 5, 50),
    }

    scenario_results = []
    for label, discount in scenario_discounts.items():
        simulation = simulate_campaign(
            df=df,
            selected_product=selected_product,
            discount_rate=discount,
            start_date=start_date,
            end_date=end_date,
            scenario_label=label,
        )
        scenario_results.append(
            {
                "Senaryo": label,
                "Indirim Orani (%)": simulation["discount_rate"],
                "Tahmini Talep Artisi (%)": simulation["uplift_rate"],
                "Yeni Satis Adedi": simulation["new_quantity"],
                "Eski Gelir (TL)": simulation["baseline_revenue"],
                "Yeni Gelir (TL)": simulation["new_revenue"],
                "Net Gelir Farki (TL)": simulation["revenue_difference"],
            }
        )

    comparison_df = pd.DataFrame(scenario_results)
    return comparison_df.sort_values("Net Gelir Farki (TL)", ascending=False).reset_index(drop=True)
