import argparse
import os
import sys
from dataclasses import dataclass
from decimal import Decimal

import psycopg2
from dotenv import load_dotenv


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, "config", ".env"))


EXPECTED_TABLES = {
    "city_talent_score": ["city", "candidate_count", "avg_salary"],
    "salary_benchmarks": ["degree", "avg_expected"],
    "candidate_engagement": ["candidate_id", "login_count"],
    "interview_pipeline_funnel": [
        "job_title",
        "stage_name",
        "status",
        "interview_count",
    ],
    "job_hire_rate": ["job_title", "total_feedback", "hire_count", "hire_rate_pct"],
}


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


def get_connection():
    required = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASS", "DB_PORT"]
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise EnvironmentError(
            "Missing required environment variables in config/.env: "
            + ", ".join(missing)
        )

    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        port=os.environ["DB_PORT"],
    )


def scalar(cur, sql, params=None):
    cur.execute(sql, params or ())
    row = cur.fetchone()
    return row[0] if row else None


def add_result(results, name, passed, details):
    results.append(CheckResult(name=name, passed=passed, details=details))


def check_schema(cur, results):
    schema_exists = scalar(
        cur,
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.schemata
            WHERE schema_name = 'analytics'
        )
        """,
    )
    add_result(
        results,
        "analytics schema exists",
        bool(schema_exists),
        "schema found" if schema_exists else "schema is missing",
    )

    for table_name, expected_columns in EXPECTED_TABLES.items():
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'analytics'
              AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table_name,),
        )
        actual_columns = [row[0] for row in cur.fetchall()]
        missing_columns = [
            column for column in expected_columns if column not in actual_columns
        ]
        add_result(
            results,
            f"analytics.{table_name} columns",
            not missing_columns,
            (
                f"columns present: {', '.join(expected_columns)}"
                if not missing_columns
                else f"missing columns: {', '.join(missing_columns)}"
            ),
        )


def check_row_counts(cur, results, allow_empty=False):
    for table_name in EXPECTED_TABLES:
        exists = scalar(
            cur,
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'analytics'
                  AND table_name = %s
            )
            """,
            (table_name,),
        )
        if not exists:
            add_result(
                results,
                f"analytics.{table_name} row count",
                False,
                "table is missing",
            )
            continue

        count = scalar(cur, f'SELECT COUNT(*) FROM analytics."{table_name}"')
        passed = allow_empty or count > 0
        add_result(
            results,
            f"analytics.{table_name} row count",
            passed,
            f"{count} rows",
        )


def check_nulls_and_ranges(cur, results):
    checks = [
        (
            "city_talent_score required values",
            """
            SELECT COUNT(*)
            FROM analytics.city_talent_score
            WHERE candidate_count IS NULL
               OR avg_salary IS NULL
               OR candidate_count < 0
               OR avg_salary < 0
            """,
        ),
        (
            "salary_benchmarks required values",
            """
            SELECT COUNT(*)
            FROM analytics.salary_benchmarks
            WHERE degree IS NULL
               OR avg_expected IS NULL
               OR avg_expected < 0
            """,
        ),
        (
            "candidate_engagement required values",
            """
            SELECT COUNT(*)
            FROM analytics.candidate_engagement
            WHERE candidate_id IS NULL
               OR login_count IS NULL
               OR login_count <= 0
            """,
        ),
        (
            "interview_pipeline_funnel required values",
            """
            SELECT COUNT(*)
            FROM analytics.interview_pipeline_funnel
            WHERE job_title IS NULL
               OR stage_name IS NULL
               OR status IS NULL
               OR interview_count IS NULL
               OR interview_count <= 0
            """,
        ),
        (
            "job_hire_rate required values",
            """
            SELECT COUNT(*)
            FROM analytics.job_hire_rate
            WHERE job_title IS NULL
               OR total_feedback IS NULL
               OR hire_count IS NULL
               OR hire_rate_pct IS NULL
               OR total_feedback <= 0
               OR hire_count < 0
               OR hire_count > total_feedback
               OR hire_rate_pct < 0
               OR hire_rate_pct > 100
            """,
        ),
    ]

    for name, sql in checks:
        failures = scalar(cur, sql)
        add_result(
            results,
            name,
            failures == 0,
            f"{failures} invalid rows",
        )

    duplicate_checks = [
        (
            "candidate_engagement duplicate candidates",
            """
            SELECT COUNT(*)
            FROM (
                SELECT candidate_id
                FROM analytics.candidate_engagement
                GROUP BY candidate_id
                HAVING COUNT(*) > 1
            ) duplicates
            """,
        ),
        (
            "job_hire_rate duplicate jobs",
            """
            SELECT COUNT(*)
            FROM (
                SELECT job_title
                FROM analytics.job_hire_rate
                GROUP BY job_title
                HAVING COUNT(*) > 1
            ) duplicates
            """,
        ),
        (
            "interview_pipeline_funnel duplicate groups",
            """
            SELECT COUNT(*)
            FROM (
                SELECT job_title, stage_name, status
                FROM analytics.interview_pipeline_funnel
                GROUP BY job_title, stage_name, status
                HAVING COUNT(*) > 1
            ) duplicates
            """,
        ),
    ]

    for name, sql in duplicate_checks:
        duplicates = scalar(cur, sql)
        add_result(results, name, duplicates == 0, f"{duplicates} duplicate groups")


def check_reconciliation(cur, results):
    engagement_source = scalar(
        cur,
        "SELECT COUNT(DISTINCT candidate_id) FROM public.login_logs",
    )
    engagement_gold = scalar(
        cur,
        "SELECT COUNT(*) FROM analytics.candidate_engagement",
    )
    add_result(
        results,
        "candidate_engagement candidate coverage",
        engagement_source == engagement_gold,
        f"source distinct candidates={engagement_source}, gold rows={engagement_gold}",
    )

    login_source = scalar(cur, "SELECT COUNT(*) FROM public.login_logs")
    login_gold = scalar(
        cur,
        "SELECT COALESCE(SUM(login_count), 0) FROM analytics.candidate_engagement",
    )
    add_result(
        results,
        "candidate_engagement login total",
        login_source == login_gold,
        f"source logins={login_source}, gold login_count sum={login_gold}",
    )

    funnel_source = scalar(
        cur,
        """
        SELECT COUNT(*)
        FROM public.interview_schedules s
        JOIN public.jobs j ON s.job_id = j.job_id
        JOIN public.interview_stages st ON s.stage_id = st.stage_id
        """,
    )
    funnel_gold = scalar(
        cur,
        """
        SELECT COALESCE(SUM(interview_count), 0)
        FROM analytics.interview_pipeline_funnel
        """,
    )
    add_result(
        results,
        "interview_pipeline_funnel total",
        funnel_source == funnel_gold,
        f"source schedules={funnel_source}, gold interview_count sum={funnel_gold}",
    )

    feedback_source = scalar(
        cur,
        """
        SELECT COUNT(*)
        FROM public.interview_feedback f
        JOIN public.interview_schedules s ON f.schedule_id = s.schedule_id
        JOIN public.jobs j ON s.job_id = j.job_id
        """,
    )
    feedback_gold = scalar(
        cur,
        "SELECT COALESCE(SUM(total_feedback), 0) FROM analytics.job_hire_rate",
    )
    add_result(
        results,
        "job_hire_rate feedback total",
        feedback_source == feedback_gold,
        f"source feedback={feedback_source}, gold total_feedback sum={feedback_gold}",
    )

    hires_source = scalar(
        cur,
        """
        SELECT COUNT(*)
        FROM public.interview_feedback f
        JOIN public.interview_schedules s ON f.schedule_id = s.schedule_id
        JOIN public.jobs j ON s.job_id = j.job_id
        WHERE f.decision = 'Hire'
        """,
    )
    hires_gold = scalar(
        cur,
        "SELECT COALESCE(SUM(hire_count), 0) FROM analytics.job_hire_rate",
    )
    add_result(
        results,
        "job_hire_rate hire total",
        hires_source == hires_gold,
        f"source hires={hires_source}, gold hire_count sum={hires_gold}",
    )


def check_rate_formula(cur, results):
    cur.execute(
        """
        SELECT job_title, total_feedback, hire_count, hire_rate_pct
        FROM analytics.job_hire_rate
        """
    )
    bad_rows = []
    for job_title, total_feedback, hire_count, hire_rate_pct in cur.fetchall():
        expected = Decimal("0.00")
        if total_feedback:
            expected = (Decimal(hire_count) * Decimal("100.0") / Decimal(total_feedback)).quantize(
                Decimal("0.01")
            )
        actual = Decimal(str(hire_rate_pct)).quantize(Decimal("0.01"))
        if actual != expected:
            bad_rows.append(f"{job_title}: expected {expected}, found {actual}")

    add_result(
        results,
        "job_hire_rate percentage formula",
        not bad_rows,
        "all rates match" if not bad_rows else "; ".join(bad_rows[:5]),
    )


def print_results(results):
    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed

    print("\nGold analytics validation")
    print("=" * 25)
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name} - {result.details}")

    print("\nSummary")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate analytics gold tables after running pipelines/elt_gold.py."
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow analytics tables to have zero rows.",
    )
    args = parser.parse_args()

    results = []
    with get_connection() as conn:
        with conn.cursor() as cur:
            check_schema(cur, results)
            check_row_counts(cur, results, allow_empty=args.allow_empty)
            check_nulls_and_ranges(cur, results)
            check_reconciliation(cur, results)
            check_rate_formula(cur, results)

    print_results(results)
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
