import importlib
import os
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PIPELINES = ROOT / "pipelines"


def load_elt_silver():
    os.environ.setdefault("AZURE_STORAGE_CONNECTION_STRING", "UseDevelopmentStorage=true")
    if str(PIPELINES) not in sys.path:
        sys.path.insert(0, str(PIPELINES))
    return importlib.import_module("elt_silver")


def test_scd2_expiring_existing_row_uses_naive_utc_timestamp(tmp_path):
    elt_silver = load_elt_silver()

    candidate_id = "11111111-1111-1111-1111-111111111111"
    initial = pd.DataFrame(
        [
            {
                "candidate_id": candidate_id,
                "name": "Asha",
                "city": "Pune",
            }
        ]
    )
    first_snapshot = elt_silver._apply_scd2_snapshot(initial, None)

    existing_path = tmp_path / "candidates_secure.parquet"
    first_snapshot.drop(columns=["_needs_encryption"]).to_parquet(existing_path, index=False)

    changed = pd.DataFrame(
        [
            {
                "candidate_id": candidate_id,
                "name": "Asha",
                "city": "Bengaluru",
            }
        ]
    )

    result = elt_silver._apply_scd2_snapshot(changed, str(existing_path))
    expired = result[result["is_current"] == False]

    assert len(expired) == 1
    assert expired["end_date"].notna().all()
    assert result["end_date"].dt.tz is None
