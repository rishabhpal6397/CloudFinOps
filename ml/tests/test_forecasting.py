"""Tests for the forecasting pipeline."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from ml.forecasting import evaluator, features
from ml.forecasting.models import fit_predict, linear_regression, random_forest


def _make_series(days: int = 200) -> tuple[pd.Series, pd.Series]:
    base = date(2026, 1, 1)
    dates = [
        base + timedelta(days=i)
        for i in range(days)
    ]

    rng = np.random.default_rng(42)

    values = [
        (
            100
            + 0.5 * i
            + (10 if d.weekday() >= 5 else 0)
            + rng.normal(0, 2)
        )
        for i, d in enumerate(dates)
    ]

    return (
        pd.Series(pd.to_datetime(dates)),
        pd.Series(values),
    )


def test_build_features_columns():
    dates = pd.date_range("2026-01-01", periods=10)
    f = features.build_features(pd.Series(dates), origin=pd.Timestamp("2026-01-01"))
    assert list(f.columns) == features.FEATURE_NAMES
    assert f["trend_index"].iloc[0] == 0
    assert f["trend_index"].iloc[-1] == 9
    assert f["is_weekend"].iloc[0] in (0, 1)


def test_linear_regression_forecast_shape():
    dates, values = _make_series()
    out = fit_predict(dates, values, horizon=7, estimator=linear_regression(),
                      model_name="linear_regression")
    assert len(out) == 7
    for col in ("forecast_date", "predicted_cost", "lower_bound",
                "upper_bound", "model_name"):
        assert col in out.columns
    assert (out["predicted_cost"] >= 0).all()
    assert (out["lower_bound"] <= out["predicted_cost"]).all()
    assert (out["upper_bound"] >= out["predicted_cost"]).all()


def test_random_forest_forecast_shape():
    dates, values = _make_series()
    out = fit_predict(dates, values, horizon=30, estimator=random_forest(n_estimators=50),
                      model_name="random_forest")
    assert len(out) == 30


def test_backtest_metrics_are_reasonable():
    dates, values = _make_series()
    m = evaluator.backtest(
        dates,
        values, 
        estimator=linear_regression(), 
        test_size=30
        )
    n_test = m["n_test"]
    mae = m["mae"]
    mape = m["mape"]
    
    assert n_test == 30

    assert mae is not None
    assert mae < 20  # noise is small relative to signal

    assert mape is not None
    assert 0 <= mape < 30


def test_insufficient_history_raises():
    dates = pd.date_range("2026-01-01", periods=5)
    values = pd.Series([10.0] * 5)
    try:
        fit_predict(pd.Series(dates), values, horizon=7,
                    estimator=linear_regression(), model_name="lr")
        assert False, "Expected ValueError"
    except ValueError:
        pass