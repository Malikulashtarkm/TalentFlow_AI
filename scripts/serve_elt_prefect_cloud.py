"""Serve TalentFlow ELT as a Prefect deployment for Cloud UI demos.

Run this after logging in to Prefect Cloud:
    prefect cloud login
    python scripts/serve_elt_prefect_cloud.py

Keep this process running during the demo. Use Ctrl+C to stop it.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PIPELINES_DIR = PROJECT_ROOT / "pipelines"

sys.path.insert(0, str(PIPELINES_DIR))

from run_elt import full_elt_flow  # noqa: E402


if __name__ == "__main__":
    full_elt_flow.serve(
        name="talentflow-elt-every-2-min-demo",
        interval=120,
        parameters={"publish_postgres": True, "train_ml_insights": False},
        tags=["talentflow", "demo", "etl", "ml-ready"],
        pause_on_shutdown=False,
    )
