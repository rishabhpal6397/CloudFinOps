"""
CloudFinOps – Calendar feature engineering
==========================================

Only calendar-derived features are used. This eliminates lag leakage and
makes forecasting any future date trivial — no recursion, no missing-feature
imputation.

Feature list:
    trend_index   days since origin (captures level + linear trend)
    day_of_week   0=Monday … 6=Sunday
    is_weekend    1 if Saturday/Sunday else 0
    month         1–12
    week_of_year  1–53
    day_of_month  1–31
"""

from __future__ import annotations

import pandas as pd

FEATURE_NAMES = [
    "trend_index",
    "day_of_week",
    "is_weekend",
    "month",
    "week_of_year",
    "day_of_month",
]


def build_features(dates: pd.Series, origin: pd.Timestamp) -> pd.DataFrame:
    """
    Build the calendar feature matrix for a Series of dates.

    Parameters
    ----------
    dates : pd.Series of datetime-like
        The dates to compute features for. Can include past and future dates.
    origin : pd.Timestamp
        The reference date for `trend_index`. Must be identical for training
        and prediction, or the model will mis-scale.

    Returns
    -------
    pd.DataFrame with exactly the columns in FEATURE_NAMES.
    """
    d = pd.to_datetime(pd.Series(dates).reset_index(drop=True))
    origin = pd.Timestamp(origin)

    features = pd.DataFrame({
        "trend_index":  (d - origin).dt.days.astype(int),
        "day_of_week":  d.dt.dayofweek.astype(int),
        "is_weekend":   (d.dt.dayofweek >= 5).astype(int),
        "month":        d.dt.month.astype(int),
        "week_of_year": d.dt.isocalendar().week.astype(int),
        "day_of_month": d.dt.day.astype(int),
    })
    return features[FEATURE_NAMES]