"""Run the full Bronze -> Silver -> Gold ELT pipeline via Prefect."""

import argparse
import sys
from pathlib import Path

from elt_bronze import bronze_flow
from elt_silver import silver_flow
from elt_gold import gold_flow
from prefect import flow
from run_context import make_run_datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.train_ml_insights import run_training  # noqa: E402


@flow(name="TalentFlow-Full-ELT")
def full_elt_flow(
    run_datetime: str | None = None,
    publish_postgres: bool = False,
    train_ml_insights: bool = False,
):
    run_datetime = run_datetime or make_run_datetime()
    bronze_flow(run_datetime)
    silver_flow(run_datetime)
    gold_flow(run_datetime, publish_postgres=publish_postgres)
    if train_ml_insights:
        run_training()
    return run_datetime


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the full TalentFlow bronze, silver, and gold ELT pipeline."
    )
    parser.add_argument(
        "--publish-postgres",
        action="store_true",
        help="Also publish gold tables into PostgreSQL analytics schema for dashboard caching.",
    )
    parser.add_argument(
        "--train-ml-insights",
        action="store_true",
        help="Train ML models after Gold completes and publish analytics.ml_feature_insights.",
    )
    args = parser.parse_args()
    full_elt_flow(
        publish_postgres=args.publish_postgres,
        train_ml_insights=args.train_ml_insights,
    )
