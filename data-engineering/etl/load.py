"""
CloudFinOps – ETL: Load stage
=============================

Two responsibilities:

1. Persist the processed DataFrame to disk (CSV).
2. Load the processed DataFrame into the MySQL star schema.

The DB loader is idempotent: dimensions are upserted, fact rows are fully
refreshed via TRUNCATE + batch INSERT.
"""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine
from tqdm import tqdm

logger = logging.getLogger(__name__)

FACT_BATCH_SIZE = 5000


# ===========================================================================
# Disk persistence (unchanged behaviour from Phase 2)
# ===========================================================================
def save_processed(df: pd.DataFrame, output_dir: str | Path) -> dict[str, Path]:
    """Persist the processed DataFrame as CSV. Returns artifact paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "billing_data_clean.csv"
    df.to_csv(csv_path, index=False)
    logger.info("Wrote processed CSV: %s (%s rows)", csv_path, f"{len(df):,}")
    return {"processed_csv": csv_path}


def save_stats(stats: dict, output_dir: str | Path, name: str = "cleaning_stats.json") -> Path:
    """Persist cleaning statistics as JSON."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / name
    with path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, default=str)
    logger.info("Wrote cleaning stats: %s", path)
    return path


# ===========================================================================
# MySQL loading
# ===========================================================================
def load_to_mysql(
    df: pd.DataFrame,
    engine: Engine,
    source_file: str | None = None,
    reset_facts: bool = True,
) -> dict[str, int]:
    """
    Load a processed DataFrame into the MySQL star schema.

    Parameters
    ----------
    df : pd.DataFrame
        Output of transform + enrich. Must contain all columns produced by
        the ETL pipeline.
    engine : Engine
        SQLAlchemy engine pointing at the target database.
    source_file : str | None
        Value stored in fact_cost.source_file for lineage.
    reset_facts : bool
        If True (default), TRUNCATE fact_cost before inserting. Dimensions
        are always upserted (INSERT IGNORE) and never truncated.

    Returns
    -------
    dict with counts: rows_in, rows_loaded, date_dim_size, and per-dimension sizes.
    """
    df = df.copy()
    df["billing_date"] = pd.to_datetime(df["billing_date"]).dt.date

    # -- 1. dim_date: extend to cover [min_date - 1y, max_date + 1y] ---------
    min_d = df["billing_date"].min()
    max_d = df["billing_date"].max()
    date_lo = date(min_d.year - 1, 1, 1)
    date_hi = date(max_d.year + 1, 12, 31)
    _upsert_dim_date(engine, date_lo, date_hi)
    logger.info("dim_date covered: %s → %s", date_lo, date_hi)

    # -- 2. Upsert dimensions, then select back their surrogate keys ---------
    provider_map = _upsert_dim_provider(engine, df)
    account_map  = _upsert_dim_account(engine, df, provider_map)
    service_map  = _upsert_dim_service(engine, df)
    region_map   = _upsert_dim_region(engine, df)
    team_map     = _upsert_dim_team(engine, df)
    env_map      = _upsert_dim_environment(engine, df)
    resource_map = _upsert_dim_resource(engine, df, provider_map)

    # -- 3. Map dimension keys onto the DataFrame ----------------------------
    df["date_key"]        = df["billing_date"].apply(lambda d: d.year * 10000 + d.month * 100 + d.day)
    df["provider_key"]    = df["provider"].map(provider_map)
    df["account_key"]     = df["account_id"].map(account_map)
    df["service_key"]     = df["service"].map(service_map)
    df["region_key"]      = df["region"].map(region_map)
    df["team_key"]        = df["team"].map(team_map)
    df["environment_key"] = df["environment"].map(env_map)
    df["resource_key"]    = df["resource_id"].map(resource_map)

    # Fail loudly if any mapping produced a null key
    key_cols = [
        "date_key", "provider_key", "account_key", "service_key",
        "region_key", "team_key", "environment_key", "resource_key",
    ]
    null_keys = df[key_cols].isna().any()
    if null_keys.any():
        raise RuntimeError(f"Unmapped dimension keys: {list(null_keys[null_keys].index)}")

    # -- 4. Optionally truncate fact_cost ------------------------------------
    if reset_facts:
        with engine.begin() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            conn.execute(text("TRUNCATE TABLE fact_cost"))
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        logger.info("Truncated fact_cost")

    # -- 5. Insert fact rows in batches --------------------------------------
    rows_loaded = _insert_fact_rows(engine, df, source_file)
    logger.info("Loaded %s fact rows", f"{rows_loaded:,}")

    return {
        "rows_in":         len(df),
        "rows_loaded":     rows_loaded,
        "providers":       len(provider_map),
        "accounts":        len(account_map),
        "services":        len(service_map),
        "regions":         len(region_map),
        "teams":           len(team_map),
        "environments":    len(env_map),
        "resources":       len(resource_map),
    }


# ---------------------------------------------------------------------------
# Dimension upserts
# ---------------------------------------------------------------------------
def _upsert_dim_date(engine: Engine, date_lo: date, date_hi: date) -> None:
    """Populate dim_date for every day in [date_lo, date_hi]."""
    rows: list[tuple] = []
    d = date_lo
    while d <= date_hi:
        rows.append((
            d.year * 10000 + d.month * 100 + d.day,
            d,
            d.year,
            (d.month - 1) // 3 + 1,
            d.month,
            d.strftime("%B"),
            d.day,
            d.weekday(),
            d.strftime("%A"),
            d.weekday() >= 5,
            f"{d.year:04d}-{d.month:02d}",
        ))
        d += timedelta(days=1)

    sql = text("""
        INSERT IGNORE INTO dim_date
            (date_key, full_date, `year`, `quarter`, `month`, month_name,
             `day`, day_of_week, day_name, is_weekend, `year_month`)
        VALUES (:dk, :fd, :yr, :q, :m, :mn, :dy, :dow, :dn, :we, :ym)
    """)

    with engine.begin() as conn:
        conn.execute(sql, [
            {"dk": r[0], "fd": r[1], "yr": r[2], "q": r[3], "m": r[4],
             "mn": r[5], "dy": r[6], "dow": r[7], "dn": r[8],
             "we": r[9], "ym": r[10]}
            for r in rows
        ])


def _upsert_dim_provider(engine: Engine, df: pd.DataFrame) -> dict[str, int]:
    pairs = (
        df[["provider", "provider_display_name"]]
        .drop_duplicates(subset=["provider"])
        .itertuples(index=False, name=None)
    )
    sql = text("""
        INSERT IGNORE INTO dim_provider (provider_name, provider_display)
        VALUES (:name, :disp)
    """)
    with engine.begin() as conn:
        conn.execute(sql, [{"name": n, "disp": d} for n, d in pairs])
    return _select_map(engine, "dim_provider", "provider_name", "provider_key")


def _upsert_dim_account(engine: Engine, df: pd.DataFrame, provider_map: dict[str, int]) -> dict[str, int]:
    pairs = df[["account_id", "provider"]].drop_duplicates(subset=["account_id"])
    rows = [
        {"aid": r.account_id, "pid": provider_map[r.provider]}
        for r in pairs.itertuples(index=False)
    ]
    sql = text("""
        INSERT IGNORE INTO dim_account (account_id, provider_key)
        VALUES (:aid, :pid)
    """)
    with engine.begin() as conn:
        conn.execute(sql, rows)
    return _select_map(engine, "dim_account", "account_id", "account_key")


def _upsert_dim_service(engine: Engine, df: pd.DataFrame) -> dict[str, int]:
    pairs = (
        df[["service", "service_category"]]
        .drop_duplicates(subset=["service"])
    )
    sql = text("""
        INSERT IGNORE INTO dim_service (service_name, service_category)
        VALUES (:name, :cat)
    """)
    with engine.begin() as conn:
        conn.execute(sql, [
            {"name": r.service, "cat": r.service_category}
            for r in pairs.itertuples(index=False)
        ])
    return _select_map(engine, "dim_service", "service_name", "service_key")


def _upsert_dim_region(engine: Engine, df: pd.DataFrame) -> dict[str, int]:
    codes = df["region"].drop_duplicates().tolist()
    sql = text("INSERT IGNORE INTO dim_region (region_code) VALUES (:code)")
    with engine.begin() as conn:
        conn.execute(sql, [{"code": c} for c in codes])
    return _select_map(engine, "dim_region", "region_code", "region_key")


def _upsert_dim_team(engine: Engine, df: pd.DataFrame) -> dict[str, int]:
    names = df["team"].drop_duplicates().tolist()
    sql = text("INSERT IGNORE INTO dim_team (team_name) VALUES (:name)")
    with engine.begin() as conn:
        conn.execute(sql, [{"name": n} for n in names])
    return _select_map(engine, "dim_team", "team_name", "team_key")


def _upsert_dim_environment(engine: Engine, df: pd.DataFrame) -> dict[str, int]:
    names = df["environment"].drop_duplicates().tolist()
    sql = text("INSERT IGNORE INTO dim_environment (environment_name) VALUES (:name)")
    with engine.begin() as conn:
        conn.execute(sql, [{"name": n} for n in names])
    return _select_map(engine, "dim_environment", "environment_name", "environment_key")


def _upsert_dim_resource(engine: Engine, df: pd.DataFrame, provider_map: dict[str, int]) -> dict[str, int]:
    pairs = df[["resource_id", "resource_name", "provider"]].drop_duplicates(subset=["resource_id"])
    rows = [
        {"rid": r.resource_id, "rname": r.resource_name, "pid": provider_map[r.provider]}
        for r in pairs.itertuples(index=False)
    ]
    sql = text("""
        INSERT IGNORE INTO dim_resource (resource_id, resource_name, provider_key)
        VALUES (:rid, :rname, :pid)
    """)
    with engine.begin() as conn:
        conn.execute(sql, rows)
    return _select_map(engine, "dim_resource", "resource_id", "resource_key")


def _select_map(engine: Engine, table: str, name_col: str, key_col: str) -> dict:
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT {name_col}, {key_col} FROM {table}"))
        return {row[0]: row[1] for row in result}


# ---------------------------------------------------------------------------
# Fact inserts
# ---------------------------------------------------------------------------
def _insert_fact_rows(engine: Engine, df: pd.DataFrame, source_file: str | None) -> int:
    sql = text("""
        INSERT INTO fact_cost (
            date_key, provider_key, account_key, service_key, region_key,
            team_key, environment_key, resource_key,
            usage_quantity, usage_unit, cost, currency, cost_per_unit,
            tags, source_file
        ) VALUES (
            :date_key, :provider_key, :account_key, :service_key, :region_key,
            :team_key, :environment_key, :resource_key,
            :usage_quantity, :usage_unit, :cost, :currency, :cost_per_unit,
            :tags, :source_file
        )
    """)

    total = len(df)
    inserted = 0

    with engine.begin() as conn:
        for start in tqdm(range(0, total, FACT_BATCH_SIZE), desc="Loading fact_cost"):
            batch = df.iloc[start:start + FACT_BATCH_SIZE]
            conn.execute(sql, [
                {
                    "date_key":        int(r.date_key),
                    "provider_key":    int(r.provider_key),
                    "account_key":     int(r.account_key),
                    "service_key":     int(r.service_key),
                    "region_key":      int(r.region_key),
                    "team_key":        int(r.team_key),
                    "environment_key": int(r.environment_key),
                    "resource_key":    int(r.resource_key),
                    "usage_quantity":  float(r.usage_quantity),
                    "usage_unit":      r.usage_unit,
                    "cost":            float(r.cost),
                    "currency":        r.currency,
                    "cost_per_unit":   None if pd.isna(r.cost_per_unit) else float(r.cost_per_unit),
                    "tags":            r.tags,
                    "source_file":     source_file,
                }
                for r in batch.itertuples(index=False)
            ])
            inserted += len(batch)

    return inserted