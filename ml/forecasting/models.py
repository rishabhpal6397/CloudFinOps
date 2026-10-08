"""
CloudFinOps – Forecast models
=============================

A single generic forecaster that works with any sklearn regressor exposing
`.fit()` and `.predict()`.

Two ready-made estimators:

    linear_regression()  – fast, interpretable, good baseline
    random_forest()      – non-linear, handles month/holiday bumps

Prediction intervals
--------------------
Residual standard deviation from training data × 1.96 yields a 95% interval
under the assumption of normally distributed residuals. Good enough for a
portfolio demo and avoids the complexity of quantile regression.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

from ml.forecasting.features import build_features

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Estimator factories
# ---------------------------------------------------------------------------
def linear_regression() -> LinearRegression:
    return LinearRegression()


def random_forest(n_estimators: int = 200, random_state: int = 42) -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=12,
        min_samples_leaf=3,
        random_state=random_state,
        n_jobs=-1,
    )


# ---------------------------------------------------------------------------
# Generic forecaster
# ---------------------------------------------------------------------------
def fit_predict(
    history_dates: pd.Series,
    history_values: pd.Series,
    horizon: int,
    estimator,
    model_name: str,
) -> pd.DataFrame:
    """
    Fit an estimator on the full history, forecast `horizon` days forward.

    Returns
    -------
    DataFrame with columns:
        forecast_date, predicted_cost, lower_bound, upper_bound, model_name
    """
    if len(history_dates) < 30:
        raise ValueError(
            f"Need at least 30 days of history for forecasting, got {len(history_dates)}"
        )

    origin = pd.Timestamp(pd.to_datetime(history_dates).min())

    X_train = build_features(pd.Series(history_dates), origin=origin)
    y_train = np.asarray(history_values, dtype=float)

    estimator.fit(X_train, y_train)

    # Residual std for intervals
    y_fit = estimator.predict(X_train)
    residuals = y_train - y_fit
    residual_std = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 0.0

    # Future dates
    last_date = pd.Timestamp(pd.to_datetime(history_dates).max())
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon, freq="D")

    X_future = build_features(pd.Series(future_dates), origin=origin)
    y_future = estimator.predict(X_future)

    out = pd.DataFrame({
        "forecast_date":  future_dates,
        "predicted_cost": np.clip(y_future, 0, None),
        "lower_bound":    np.clip(y_future - 1.96 * residual_std, 0, None),
        "upper_bound":    y_future + 1.96 * residual_std,
        "model_name":     model_name,
    })

    # Ensure non-negative bounds
    out["upper_bound"] = out["upper_bound"].clip(lower=out["predicted_cost"])
    out["lower_bound"] = out["lower_bound"].clip(upper=out["predicted_cost"])

    return out