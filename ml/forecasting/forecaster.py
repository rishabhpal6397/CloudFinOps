"""
CloudFinOps – Forecasting orchestrator
======================================

Forecasts every service plus the organization-level total. Trains both
Linear Regression and Random Forest. Stores results in cost_forecasts.

Column contract for cost_forecasts writes:
    forecast_date      -- the future date being forecast
    generated_on       -- today's date
    forecast_period    -- '7d' or '30d'
    service_key        -- specific service, or NULL for org-level
    team_key           -- NULL for Phase 7 (team-level forecasts are Phase 11)
    predicted_cost
    lower_bound
    upper_bound
    model_name         -- 'linear_regression' or 'random_forest'
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Callable

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from ml.common import get_db, load_daily_service_cost
from ml.forecasting import evaluator
from ml.forecasting.models import (
    fit_predict,
    linear_regression,
    random_forest,
)

logger = logging.getLogger(__name__)

ModelFactory = Callable[[], Any]

HORIZONS = {
    "7d":  7,
    "30d": 30,
}
MODELS: dict[str, ModelFactory] = {
    "linear_regression": linear_regression,
    "random_forest":     random_forest,
}
BACKTEST_SIZE = 30


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def _to_int_or_none(value: Any) -> int | None:
    """Convert a value to int, preserving missing values."""
    if value is None:
        return None

    numeric_value = pd.to_numeric(value, errors="coerce")

    if pd.isna(numeric_value):
        return None

    return int(numeric_value)


def _to_float(value: Any) -> float:
    """Convert a value to float."""
    numeric_value = pd.to_numeric(value, errors="coerce")

    if pd.isna(numeric_value):
        raise ValueError(
            f"Expected numeric value, got: {value!r}"
        )

    return float(numeric_value)


def _to_date(value: Any) -> date:
    """Convert a value to a Python date."""
    return pd.Timestamp(value).date()


def run(
    horizons: dict[str, int] | None = None,
    models: dict[str, ModelFactory] | None = None,
    backtest: bool = True,
) -> dict[str, Any]:
    """Run forecasting for all services and org-level totals."""
    horizons = horizons or HORIZONS
    models = models or MODELS

    engine = get_db()
    summary: dict[str, Any] = {"horizons": list(horizons.keys()), "models": {}}

    # -- Load data -----------------------------------------------------
    df = load_daily_service_cost(engine)
    if df.empty:
        raise RuntimeError("No service cost data found.")

    df["full_date"] = pd.to_datetime(df["full_date"])

    # -- Optionally backtest models on service-level data -------------
    if backtest:
        logger.info("Backtesting models on last %d days per service…", BACKTEST_SIZE)
        summary["backtest"] = _backtest_all(df, models)

    # -- Forecast per service and organization ------------------------
    for model_name, factory in models.items():
        logger.info("Forecasting with model: %s", model_name)
        model_summary = _forecast_all_services(df, factory, model_name, horizons)

        org_summary = _forecast_organization(df, factory, model_name, horizons)
        model_summary["org_level"] = {"days_forecast": org_summary["days_forecast"]}

        # Combine service-level and org-level rows before persisting
        service_rows = model_summary.pop("_rows")
        org_rows = org_summary.pop("_rows")
        combined_rows = pd.concat([service_rows, org_rows], ignore_index=True)

        # Persist
        model_summary["rows_written"] = _write_forecasts(
            engine, combined_rows, model_name
        )
        summary["models"][model_name] = model_summary

    return summary


# ---------------------------------------------------------------------------
# Backtesting
# ---------------------------------------------------------------------------
def _backtest_all(df: pd.DataFrame, models: dict[str, ModelFactory]) -> dict[str, dict[str, Any]]:
    results: dict[str, dict] = {}

    for model_name, factory in models.items():
        per_service: list[dict] = []
        for service_name, group in df.groupby("service_name"):
            group = group.sort_values(by="full_date")
            metrics = evaluator.backtest(
                history_dates=group["full_date"],
                history_values=group["daily_cost"],
                estimator=factory(),
                test_size=BACKTEST_SIZE,
            )
            n_test = metrics.get("n_test")

            if n_test is not None and n_test > 0:
                service_metrics = {
                    "service_name" : str(service_name),
                    **metrics,
                }
                per_service.append(service_metrics)

        if not per_service:
            results[model_name] = {"mae": None, "rmse": None, "mape": None}
            continue

        m = pd.DataFrame(per_service)
        mape_values = pd.to_numeric(
            m["mape"],
            errors="coerce",
        ).dropna()

        results[model_name] = {
            "services_evaluated": int(len(m)),
            "mae": round(float(m["mae"].mean()), 4),
            "rmse": round(float(m["rmse"].mean()), 4),
            "mape": (
                round(float(mape_values.mean()), 4)
                if not mape_values.empty
                else None
            ),
        }
    return results


# ---------------------------------------------------------------------------
# Forecast helpers
# ---------------------------------------------------------------------------
def _forecast_all_services(
    df: pd.DataFrame,
    factory: ModelFactory,
    model_name: str,
    horizons: dict[str, int],
) -> dict[str, Any]:
    all_rows: list[pd.DataFrame] = []
    services_ok = 0
    services_skipped = 0

    for service_name, group in df.groupby("service_name"):
        group = group.sort_values("full_date").reset_index(drop=True)
        if len(group) < 60:
            services_skipped += 1
            continue

        service_key = _to_int_or_none(
            group["service_key"].iloc[0]
        )

        if service_key is None:
            services_skipped += 1
            continue

        for period_name, horizon in horizons.items():
            try:
                preds = fit_predict(
                    history_dates=group["full_date"],
                    history_values=group["daily_cost"],
                    horizon=horizon,
                    estimator=factory(),
                    model_name=model_name,
                )
            except Exception as exc:
                logger.warning("Forecast failed for %s / %s: %s",
                               service_name, period_name, exc)
                continue

            preds["forecast_period"] = period_name
            preds["service_key"] = service_key
            preds["team_key"] = None
            all_rows.append(preds)

        services_ok += 1

    if not all_rows:
        return {"services_forecast": 0, "services_skipped": services_skipped,
                "_rows": pd.DataFrame()}

    combined = pd.concat(all_rows, ignore_index=True)
    return {
        "services_forecast": services_ok,
        "services_skipped":  services_skipped,
        "_rows": combined,
    }


def _forecast_organization(
    df: pd.DataFrame,
    factory: ModelFactory,
    model_name: str,
    horizons: dict[str, int],
) -> dict[str, Any]:
    total = (
        df.groupby(
            "full_date",
            as_index=False,
        ).agg(
            daily_cost = ("daily_cost","sum")
        )
    )

    total["full_date"] = pd.to_datetime(
        total["full_date"]
    )

    total = total.sort_values(
        by="full_date"
    ).reset_index(drop=True)

    rows: list[pd.DataFrame] = []
    for period_name, horizon in horizons.items():
        preds = fit_predict(
            history_dates=total["full_date"],
            history_values=total["daily_cost"],
            horizon=horizon,
            estimator=factory(),
            model_name=model_name,
        )
        preds["forecast_period"] = period_name
        preds["service_key"] = None
        preds["team_key"] = None
        rows.append(preds)

    combined = pd.concat(rows, ignore_index=True)
    return {"days_forecast": int(len(combined)), "_rows": combined}


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def _write_forecasts(engine: Engine, df: pd.DataFrame, model_name: str) -> int:
    """Idempotent: delete existing rows for this model, insert fresh."""
    if df is None or df.empty:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM cost_forecasts WHERE model_name = :m"),
                {"m": model_name},
            )
        logger.warning("No forecasts to write for model '%s'", model_name)
        return 0

    generated_on = date.today()

    rows = []

    for r in df.itertuples(index=False):
        rows.append({
            "forecast_date": _to_date(r.forecast_date),

            "generated_on": generated_on,

            "forecast_period": r.forecast_period,

            "service_key": _to_int_or_none(
                r.service_key
            ),

            "team_key": None,

            "predicted_cost": _to_float(
                r.predicted_cost
            ),

            "lower_bound": _to_float(
                r.lower_bound
            ),

            "upper_bound": _to_float(
                r.upper_bound
            ),

            "model_name": r.model_name,
        })

    sql = text("""
        INSERT INTO cost_forecasts (
            forecast_date, generated_on, forecast_period,
            service_key, team_key,
            predicted_cost, lower_bound, upper_bound, model_name
        ) VALUES (
            :forecast_date, :generated_on, :forecast_period,
            :service_key, :team_key,
            :predicted_cost, :lower_bound, :upper_bound, :model_name
        )
    """)

    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM cost_forecasts WHERE model_name = :m"),
            {"m": model_name},
        )
        BATCH = 1000
        inserted = 0
        for start in range(0, len(rows), BATCH):
            conn.execute(sql, rows[start:start + BATCH])
            inserted += len(rows[start:start + BATCH])

    logger.info("Wrote %s forecast rows for model '%s'",
                f"{inserted:,}", model_name)
    return inserted