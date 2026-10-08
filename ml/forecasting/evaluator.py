"""
CloudFinOps – Forecast evaluation
=================================

Backtests a model on a train/test split of historical data.

Metrics
-------
MAE   – mean absolute error (same units as cost)
RMSE  – root mean squared error (penalises large misses)
MAPE  – mean absolute percentage error (scale-independent)
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from ml.forecasting.features import build_features

logger = logging.getLogger(__name__)


def backtest(
    history_dates: pd.Series,
    history_values: pd.Series,
    estimator,
    test_size: int = 30,
) -> dict[str, float | int | None]:
    """
    Train on all but the last `test_size` days; evaluate on the holdout.

    Returns dict with keys: mae, rmse, mape, n_train, n_test
    """
    dates = pd.to_datetime(pd.Series(history_dates).reset_index(drop=True))
    values = np.asarray(history_values, dtype=float)

    if len(dates) < test_size + 30:
        return {"mae": np.nan, "rmse": np.nan, "mape": np.nan,
                "n_train": 0, "n_test": 0}

    split = len(dates) - test_size
    train_dates, test_dates = dates.iloc[:split], dates.iloc[split:]
    train_values, test_values = values[:split], values[split:]

    origin = pd.Timestamp(dates.min())
    X_train = build_features(train_dates, origin=origin)
    X_test = build_features(test_dates, origin=origin)

    estimator.fit(X_train, train_values)
    preds = estimator.predict(X_test)

    errors = test_values - preds
    abs_errors = np.abs(errors)

    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    # MAPE — guard against zero actuals
    nonzero = test_values != 0
    if nonzero.any():
        mape = float(np.mean(abs_errors[nonzero] / np.abs(test_values[nonzero])) * 100.0)
    else:
        mape = np.nan

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "mape": round(mape, 4) if not np.isnan(mape) else None,
        "n_train": int(len(train_values)),
        "n_test": int(len(test_values)),
    }