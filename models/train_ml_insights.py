import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

try:
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        confusion_matrix,
        f1_score,
        mean_absolute_error,
        r2_score,
        roc_auc_score,
    )
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
except ModuleNotFoundError as exc:
    missing = exc.name or "scikit-learn"
    raise SystemExit(
        f"Missing ML dependency: {missing}. Run `pip install -r requirements.txt` first."
    ) from exc


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = PROJECT_ROOT / "models" / "artifacts"
load_dotenv(PROJECT_ROOT / "config" / ".env")


FEATURE_QUERY = """
WITH latest_education AS (
    SELECT DISTINCT ON (candidate_id)
           candidate_id,
           degree,
           university,
           passing_year,
           gpa
    FROM public.candidate_education
    ORDER BY candidate_id, passing_year DESC NULLS LAST, edu_id DESC
),
login_counts AS (
    SELECT candidate_id, COUNT(*) AS login_count
    FROM public.login_logs
    GROUP BY candidate_id
)
SELECT
    f.feedback_id,
    f.rating,
    f.decision,
    s.status AS interview_status,
    s.interview_date,
    c.candidate_id,
    c.city,
    c.state,
    c.country,
    c.expected_salary,
    e.degree,
    e.university,
    e.passing_year,
    e.gpa,
    COALESCE(l.login_count, 0) AS login_count,
    j.job_title,
    j.department,
    j.salary_range,
    j.job_location,
    st.stage_name
FROM public.interview_feedback f
JOIN public.interview_schedules s ON f.schedule_id = s.schedule_id
JOIN public.candidates c ON s.candidate_id = c.candidate_id
JOIN public.jobs j ON s.job_id = j.job_id
JOIN public.interview_stages st ON s.stage_id = st.stage_id
LEFT JOIN latest_education e ON c.candidate_id = e.candidate_id
LEFT JOIN login_counts l ON c.candidate_id = l.candidate_id
WHERE f.decision IS NOT NULL
"""


NUMERIC_FEATURES = ["expected_salary", "passing_year", "gpa", "login_count"]
CATEGORICAL_FEATURES = [
    "city",
    "state",
    "country",
    "degree",
    "university",
    "job_title",
    "department",
    "salary_range",
    "job_location",
    "stage_name",
]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def get_engine():
    required = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASS", "DB_PORT"]
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise EnvironmentError(
            "Missing required environment variables in config/.env: "
            + ", ".join(missing)
        )

    pg_url = (
        f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASS']}"
        f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    )
    return create_engine(pg_url)


def build_preprocessor():
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def make_classifier():
    return Pipeline(
        steps=[
            ("preprocess", build_preprocessor()),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=300,
                    min_samples_leaf=5,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def make_regressor():
    return Pipeline(
        steps=[
            ("preprocess", build_preprocessor()),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=300,
                    min_samples_leaf=5,
                    random_state=42,
                ),
            ),
        ]
    )


def load_training_data(engine):
    df = pd.read_sql(FEATURE_QUERY, engine)
    df["expected_salary"] = pd.to_numeric(df["expected_salary"], errors="coerce")
    df["passing_year"] = pd.to_numeric(df["passing_year"], errors="coerce")
    df["gpa"] = pd.to_numeric(df["gpa"], errors="coerce")
    df["login_count"] = pd.to_numeric(df["login_count"], errors="coerce").fillna(0)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["is_hire"] = (df["decision"] == "Hire").astype(int)
    return df


def feature_importance(model, top_n=25):
    preprocessor = model.named_steps["preprocess"]
    estimator = model.named_steps["model"]
    feature_names = preprocessor.get_feature_names_out()
    importances = estimator.feature_importances_

    rows = sorted(
        zip(feature_names, importances),
        key=lambda item: item[1],
        reverse=True,
    )[:top_n]
    return pd.DataFrame(rows, columns=["feature", "importance"])


def train_hire_model(df):
    X = df[FEATURE_COLUMNS]
    y = df["is_hire"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    model = make_classifier()
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "f1": round(float(f1_score(y_test, predictions)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "support": int(len(y_test)),
        "positive_rate": round(float(y.mean()), 4),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
        "classification_report": classification_report(
            y_test,
            predictions,
            target_names=["Not Hire", "Hire"],
            output_dict=True,
            zero_division=0,
        ),
    }
    return model, metrics, feature_importance(model)


def train_decision_model(df):
    X = df[FEATURE_COLUMNS]
    y = df["decision"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    model = make_classifier()
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "weighted_f1": round(float(f1_score(y_test, predictions, average="weighted")), 4),
        "support": int(len(y_test)),
        "classes": list(model.named_steps["model"].classes_),
        "confusion_matrix": confusion_matrix(
            y_test,
            predictions,
            labels=list(model.named_steps["model"].classes_),
        ).tolist(),
        "classification_report": classification_report(
            y_test,
            predictions,
            output_dict=True,
            zero_division=0,
        ),
    }
    return model, metrics, feature_importance(model)


def train_rating_model(df):
    rating_df = df.dropna(subset=["rating"]).copy()
    X = rating_df[FEATURE_COLUMNS]
    y = rating_df["rating"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
    )

    model = make_regressor()
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    metrics = {
        "mae": round(float(mean_absolute_error(y_test, predictions)), 4),
        "r2": round(float(r2_score(y_test, predictions)), 4),
        "support": int(len(y_test)),
        "rating_mean": round(float(y.mean()), 4),
    }
    return model, metrics, feature_importance(model)


def write_artifacts(models, metrics, importances):
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = ARTIFACT_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    for name, model in models.items():
        joblib.dump(model, run_dir / f"{name}.joblib")
        importances[name].to_csv(run_dir / f"{name}_feature_importance.csv", index=False)

    with open(run_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    latest_file = ARTIFACT_DIR / "latest_run.txt"
    latest_file.write_text(str(run_dir), encoding="utf-8")
    return run_id, run_dir


def write_db_insights(engine, run_id, metrics, importances):
    rows = []
    for model_name, importance_df in importances.items():
        metric_summary = metrics[model_name]
        for rank, row in importance_df.head(15).reset_index(drop=True).iterrows():
            rows.append(
                {
                    "run_id": run_id,
                    "model_name": model_name,
                    "feature_rank": rank + 1,
                    "feature": row["feature"],
                    "importance": float(row["importance"]),
                    "metric_summary": json.dumps(metric_summary),
                    "created_at": datetime.now(timezone.utc),
                }
            )

    insights_df = pd.DataFrame(rows)
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))
        insights_df.to_sql(
            "ml_feature_insights",
            conn,
            schema="analytics",
            if_exists="replace",
            index=False,
        )


def print_summary(run_dir, metrics, importances):
    print("\nML insights training complete")
    print("============================")
    print(f"Artifacts: {run_dir}")

    for model_name, model_metrics in metrics.items():
        print(f"\n{model_name}")
        for key, value in model_metrics.items():
            if key in {"classification_report", "confusion_matrix"}:
                continue
            print(f"  {key}: {value}")

        print("  top features:")
        for _, row in importances[model_name].head(5).iterrows():
            print(f"    {row['feature']}: {row['importance']:.4f}")


def run_training(skip_db_insights: bool = False):
    engine = get_engine()
    df = load_training_data(engine)
    if len(df) < 50:
        raise ValueError(f"Not enough labeled feedback rows to train models: {len(df)}")

    models = {}
    metrics = {}
    importances = {}

    models["hire_prediction"], metrics["hire_prediction"], importances["hire_prediction"] = (
        train_hire_model(df)
    )
    (
        models["decision_prediction"],
        metrics["decision_prediction"],
        importances["decision_prediction"],
    ) = train_decision_model(df)
    models["rating_prediction"], metrics["rating_prediction"], importances["rating_prediction"] = (
        train_rating_model(df)
    )

    run_id, run_dir = write_artifacts(models, metrics, importances)
    if not skip_db_insights:
        write_db_insights(engine, run_id, metrics, importances)

    print_summary(run_dir, metrics, importances)
    return run_id, run_dir


def main():
    parser = argparse.ArgumentParser(
        description="Train ML models and publish insight outputs for TalentFlow data."
    )
    parser.add_argument(
        "--skip-db-insights",
        action="store_true",
        help="Do not write analytics.ml_feature_insights.",
    )
    args = parser.parse_args()
    run_training(skip_db_insights=args.skip_db_insights)


if __name__ == "__main__":
    sys.exit(main())
