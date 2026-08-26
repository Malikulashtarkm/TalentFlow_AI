"""Run TalentFlow ELT repeatedly for short demo schedules.

Example:
    python scripts/run_elt_scheduler.py --every-seconds 120 --publish-postgres

Use Ctrl+C to stop the scheduler.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PIPELINES_DIR = PROJECT_ROOT / "pipelines"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "elt_scheduler.log"

sys.path.insert(0, str(PIPELINES_DIR))

from run_elt import full_elt_flow  # noqa: E402


def log(message: str) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{timestamp}] {message}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the TalentFlow Bronze -> Silver -> Gold ELT on a repeating interval."
    )
    parser.add_argument(
        "--every-seconds",
        type=positive_int,
        default=120,
        help="Seconds to wait between runs. Default: 120 seconds.",
    )
    parser.add_argument(
        "--max-runs",
        type=positive_int,
        default=None,
        help="Optional number of runs before stopping. Omit to run until Ctrl+C.",
    )
    parser.add_argument(
        "--publish-postgres",
        action="store_true",
        help="Also publish Gold tables into PostgreSQL for the Admin dashboard.",
    )
    parser.add_argument(
        "--train-ml-insights",
        action="store_true",
        help="Train ML models after each successful ELT run and publish ML feature insights.",
    )
    args = parser.parse_args()

    log(
        "Scheduler started "
        f"(every={args.every_seconds}s, publish_postgres={args.publish_postgres}, "
        f"train_ml_insights={args.train_ml_insights}, "
        f"max_runs={args.max_runs or 'until stopped'})."
    )

    run_number = 0
    try:
        while args.max_runs is None or run_number < args.max_runs:
            run_number += 1
            started = time.monotonic()
            log(f"Run {run_number} started.")
            try:
                run_datetime = full_elt_flow(
                    publish_postgres=args.publish_postgres,
                    train_ml_insights=args.train_ml_insights,
                )
                elapsed = time.monotonic() - started
                log(f"Run {run_number} completed successfully. run_datetime={run_datetime}; elapsed={elapsed:.1f}s.")
            except Exception as exc:
                elapsed = time.monotonic() - started
                log(f"Run {run_number} failed after {elapsed:.1f}s: {exc}")

            if args.max_runs is not None and run_number >= args.max_runs:
                break

            sleep_for = max(0, args.every_seconds - (time.monotonic() - started))
            log(f"Next run in {sleep_for:.1f}s.")
            time.sleep(sleep_for)
    except KeyboardInterrupt:
        log("Scheduler stopped by user.")
        return 0

    log("Scheduler finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
