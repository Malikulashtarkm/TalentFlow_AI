from datetime import datetime, timezone


def make_run_datetime() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def versioned_blob(run_datetime: str, file_name: str) -> str:
    table_name = file_name.rsplit(".", 1)[0]
    return f"{table_name}/run_datetime={run_datetime}/{file_name}"


def latest_blob(file_name: str) -> str:
    table_name = file_name.rsplit(".", 1)[0]
    return f"{table_name}/latest/{file_name}"
