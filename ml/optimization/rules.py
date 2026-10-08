"""
CloudFinOps – Rule-based optimization detectors
================================================

Each rule is a function that takes a prepared DataFrame and returns a list of
recommendation dicts. All rules follow the same output shape so the
orchestrator can persist them uniformly.

Recommendation dict schema:
    resource_key
    category            -- 'UNDERUTILIZED' | 'UNUSED' | 'OVERSIZED'
                         | 'STORAGE_GROWTH' | 'DATABASE_SPIKE'
    finding             -- human-readable description of what was found
    recommendation      -- human-readable suggested action
    estimated_monthly_saving
    priority            -- 'LOW' | 'MEDIUM' | 'HIGH'
"""

from __future__ import annotations

import logging
from datetime import timedelta

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_int(value: object) -> int:
    """Safely convert a value to int."""
    if value is None:
        raise ValueError(f"Expected numeric value, got: {value!r}")

    try:
        return int(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Expected numeric value, got: {value!r}"
        ) from exc


def _to_float(value: object) -> float:
    """Safely convert a value to float."""
    if value is None:
        raise ValueError(f"Expected numeric value, got: {value!r}")

    try:
        return float(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Expected numeric value, got: {value!r}"
        ) from exc


def _priority_from_saving(monthly_saving: float) -> str:
    if monthly_saving >= 1000:
        return "HIGH"
    if monthly_saving >= 200:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# Rule 1: Recent cost collapse
# ---------------------------------------------------------------------------
def rule_recent_collapse(
    df: pd.DataFrame,
    recent_days: int = 30,
    baseline_days: int = 90,
    ratio_threshold: float = 0.30,
) -> list[dict]:
    """
    Flag resources whose average daily cost in the last `recent_days` is
    less than `ratio_threshold` of their previous `baseline_days` average.
    """
    results: list[dict] = []
    if df.empty:
        return results

    max_date = df["full_date"].max()
    recent_cut = max_date - timedelta(days=recent_days)
    baseline_cut = recent_cut - timedelta(days=baseline_days)

    for (resource_key, resource_id, resource_name), group in df.groupby(
        ["resource_key", "resource_id", "resource_name"]
    ):
        recent = group[group["full_date"] > recent_cut]
        baseline = group[
            (group["full_date"] > baseline_cut) & (group["full_date"] <= recent_cut)
        ]

        if recent.empty or baseline.empty:
            continue

        recent_avg = float(recent["daily_cost"].mean())
        baseline_avg = float(baseline["daily_cost"].mean())

        if baseline_avg <= 0:
            continue

        ratio = recent_avg / baseline_avg
        if ratio >= ratio_threshold:
            continue

        # Estimate saving: assume the resource continues at its baseline cost
        # if right-sized — i.e., we save what we could have avoided by acting
        # at the start of the recent window.
        potential_saving = max(0.0, baseline_avg - recent_avg) * 30.0

        results.append({
            "resource_key":             _to_int(resource_key),
            "category":                 "UNDERUTILIZED",
            "finding": (
                f"Average daily cost fell from ${baseline_avg:.2f} "
                f"(prior {baseline_days}d) to ${recent_avg:.2f} "
                f"(last {recent_days}d), a {int((1 - ratio) * 100)}% drop."
            ),
            "recommendation": (
                "Resource is likely under-utilized. Review whether it should "
                "be downsized to a smaller instance type, stopped, or "
                "decommissioned."
            ),
            "estimated_monthly_saving": round(potential_saving, 2),
            "priority":                 _priority_from_saving(potential_saving),
        })

    logger.info("Rule recent_collapse: %d recommendations", len(results))
    return results


# ---------------------------------------------------------------------------
# Rule 2: Near-zero cost (unused)
# ---------------------------------------------------------------------------
def rule_near_zero_cost(
    df: pd.DataFrame,
    window_days: int = 60,
    daily_threshold: float = 1.0,
) -> list[dict]:
    """
    Flag resources whose average daily cost in the last `window_days` is
    below `daily_threshold` USD — candidates for termination.
    """
    results: list[dict] = []
    if df.empty:
        return results

    max_date = df["full_date"].max()
    cutoff = max_date - timedelta(days=window_days)
    window = df[df["full_date"] > cutoff]

    if window.empty:
        return results

    agg = window.groupby(
        ["resource_key", "resource_id", "resource_name"]
    ).agg(
        daily_cost_avg=("daily_cost", "mean"),
        days_active=("daily_cost", "count"),
    ).reset_index()

    candidates = agg[
        (agg["daily_cost_avg"] < daily_threshold) & (agg["days_active"] >= window_days // 2)
    ]

    for r in candidates.itertuples(index=False):
        # Saving: assume the resource was costing ~$1/day if fully idle but
        # sometimes bursted — saving ~ $0.50/day as a conservative floor.
        potential_saving = max(1.0, float(r.daily_cost_avg)) * 30.0

        results.append({
            "resource_key":             int(r.resource_key),
            "category":                 "UNUSED",
            "finding": (
                f"Average daily cost over the last {window_days} days is only "
                f"${r.daily_cost_avg:.4f} (near zero)."
            ),
            "recommendation": (
                "Resource appears unused. Verify with the owning team and "
                "terminate if not required."
            ),
            "estimated_monthly_saving": round(potential_saving, 2),
            "priority":                 "LOW",
        })

    logger.info("Rule near_zero_cost: %d recommendations", len(results))
    return results


# ---------------------------------------------------------------------------
# Rule 3: Cost-per-unit outliers (oversized)
# ---------------------------------------------------------------------------
def rule_oversized_by_unit_cost(
    df: pd.DataFrame,
    multiplier: float = 2.0,
    min_observations: int = 30,
) -> list[dict]:
    """
    Flag resources whose average `cost_per_unit` is `multiplier`× the median
    for the same service. Detects likely over-provisioning.
    """
    results: list[dict] = []
    if df.empty or "cost_per_unit" not in df.columns:
        return results

    clean = df.dropna(subset=["cost_per_unit"])
    clean = clean[clean["cost_per_unit"] > 0]

    if clean.empty:
        return results

    resource_agg = clean.groupby(
        ["resource_key", "resource_id", "resource_name", "service_name"]
    ).agg(
        avg_cpu=("cost_per_unit", "mean"),
        n=("cost_per_unit", "count"),
        avg_daily_cost=("daily_cost", "mean"),
    ).reset_index()

    resource_agg = resource_agg[resource_agg["n"] >= min_observations]

    for service_name, group in resource_agg.groupby("service_name"):
        median_cpu = float(group["avg_cpu"].median())
        if median_cpu <= 0:
            continue

        outliers = group[group["avg_cpu"] > multiplier * median_cpu]
        for r in outliers.itertuples(index=False):
            avg_cpu = _to_float(r.avg_cpu)
            avg_daily_cost = _to_float(r.avg_daily_cost)    
            # excess = avg_cpu - median_cpu
            # Saving: proportional to the excess cost per unit
            potential_saving = max(
                0.0,
                avg_daily_cost * (1 - median_cpu / avg_cpu)
            ) * 30.0

            results.append({
                "resource_key":             _to_int(r.resource_key),
                "category":                 "OVERSIZED",
                "finding": (
                    f"Average cost per unit is ${r.avg_cpu:.4f} vs "
                    f"service median ${median_cpu:.4f} "
                    f"({avg_cpu / median_cpu:.1f}x)."
                ),
                "recommendation": (
                    f"Consider a smaller instance type or tier for "
                    f"{service_name}. Right-sizing typically saves 30-50% of "
                    f"the excess."
                ),
                "estimated_monthly_saving": round(potential_saving, 2),
                "priority":                 _priority_from_saving(potential_saving),
            })

    logger.info("Rule oversized_by_unit_cost: %d recommendations", len(results))
    return results


# ---------------------------------------------------------------------------
# Rule 4: Storage cost growth
# ---------------------------------------------------------------------------
def rule_storage_growth(
    df: pd.DataFrame,
    storage_categories: tuple[str, ...] = ("Storage",),
    growth_threshold: float = 0.25,
    consecutive_months: int = 3,
) -> list[dict]:
    """
    Flag storage resources whose monthly cost grew >`growth_threshold` for
    `consecutive_months` months in a row.
    """
    results: list[dict] = []
    if df.empty or "service_category" not in df.columns:
        return results

    storage = df[df["service_category"].isin(storage_categories)].copy()
    if storage.empty:
        return results

    storage["year_month"] = pd.to_datetime(storage["full_date"]).dt.to_period("M")
    monthly = storage.groupby(
        ["resource_key", "resource_id", "resource_name", "year_month"]
    )["daily_cost"].sum().reset_index()

    for (resource_key, resource_id, resource_name), group in monthly.groupby(
        ["resource_key", "resource_id", "resource_name"]
    ):
        group = group.sort_values("year_month").reset_index(drop=True)
        if len(group) < consecutive_months + 1:
            continue

        growth_streak = 0
        max_streak = 0
        for i in range(1, len(group)):
            prev = _to_float(group.loc[i - 1, "daily_cost"])
            curr = _to_float(group.loc[i, "daily_cost"])
            if prev > 0 and (curr - prev) / prev > growth_threshold:
                growth_streak += 1
                max_streak = max(max_streak, growth_streak)
            else:
                growth_streak = 0

        if max_streak < consecutive_months:
            continue

        latest_cost = _to_float(group["daily_cost"].iloc[-1])
        earliest_cost = _to_float(group["daily_cost"].iloc[-consecutive_months - 1])
        delta = latest_cost - earliest_cost

        results.append({
            "resource_key":             _to_int(resource_key),
            "category":                 "STORAGE_GROWTH",
            "finding": (
                f"Monthly cost grew from ${earliest_cost:.2f} to "
                f"${latest_cost:.2f} over {consecutive_months} months "
                f"(+{int((latest_cost / earliest_cost - 1) * 100) if earliest_cost else 0}%)."
            ),
            "recommendation": (
                "Review data lifecycle policies — move cold data to cheaper "
                "tiers, expire unused snapshots, and check for orphaned volumes."
            ),
            "estimated_monthly_saving": round(delta * 0.4, 2),  # conservative 40%
            "priority":                 _priority_from_saving(delta * 0.4),
        })

    logger.info("Rule storage_growth: %d recommendations", len(results))
    return results


# ---------------------------------------------------------------------------
# Rule 5: Database cost spikes
# ---------------------------------------------------------------------------
def rule_database_spike(
    df: pd.DataFrame,
    db_categories: tuple[str, ...] = ("Database",),
    spike_threshold: float = 0.30,
) -> list[dict]:
    """
    Flag database resources whose latest month's cost is >`spike_threshold`
    higher than the median of the previous months.
    """
    results: list[dict] = []
    if df.empty or "service_category" not in df.columns:
        return results

    dbs = df[df["service_category"].isin(db_categories)].copy()
    if dbs.empty:
        return results

    dbs["year_month"] = pd.to_datetime(dbs["full_date"]).dt.to_period("M")
    monthly = dbs.groupby(
        ["resource_key", "resource_id", "resource_name", "year_month"]
    )["daily_cost"].sum().reset_index()

    for (resource_key, resource_id, resource_name), group in monthly.groupby(
        ["resource_key", "resource_id", "resource_name"]
    ):
        group = group.sort_values("year_month").reset_index(drop=True)
        if len(group) < 4:
            continue

        baseline_months = group.iloc[:-1]["daily_cost"]
        baseline = _to_float(baseline_months.median())
        latest = _to_float(group["daily_cost"].iloc[-1])

        if baseline <= 0:
            continue
        if (latest - baseline) / baseline <= spike_threshold:
            continue

        delta = latest - baseline
        results.append({
            "resource_key":             _to_int(resource_key),
            "category":                 "DATABASE_SPIKE",
            "finding": (
                f"Latest month cost ${latest:.2f} vs prior median "
                f"${baseline:.2f} (+{int((latest / baseline - 1) * 100)}%)."
            ),
            "recommendation": (
                "Investigate whether the database is running an oversized "
                "instance, has slow queries causing extra I/O, or has an "
                "unusual data volume increase. Consider a reserved instance "
                "or storage tier optimization."
            ),
            "estimated_monthly_saving": round(delta * 0.35, 2),  # conservative 35%
            "priority":                 _priority_from_saving(delta * 0.35),
        })

    logger.info("Rule database_spike: %d recommendations", len(results))
    return results



