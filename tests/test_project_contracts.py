from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_demo_data_reset_requires_explicit_flag():
    source = read_text("generate_production_data.py")

    assert "ALLOW_DEMO_DATA_RESET" in source
    assert "require_demo_reset_enabled()" in source
    assert "TRUNCATE TABLE" in source


def test_synthetic_feedback_has_learnable_signal():
    source = read_text("generate_production_data.py")

    assert "def interview_signal" in source
    assert "profile[\"gpa\"]" in source
    assert "profile[\"login_count\"]" in source
    assert "profile[\"expected_salary\"]" in source
    assert "decision = \"Hire\"" in source


def test_gold_validation_covers_expected_tables():
    source = read_text("scripts/validate_gold_analytics.py")

    for table_name in [
        "city_talent_score",
        "salary_benchmarks",
        "candidate_engagement",
        "interview_pipeline_funnel",
        "job_hire_rate",
    ]:
        assert table_name in source

    assert "check_reconciliation" in source
    assert "check_rate_formula" in source


def test_silver_candidate_layer_tracks_scd2_hashes():
    source = read_text("pipelines/elt_silver.py")

    assert "row_hash" in source
    assert "_apply_scd2_snapshot" in source
    assert "is_current" in source
    assert "end_date" in source


def test_lake_layers_write_versioned_runtime_paths():
    helper = read_text("pipelines/run_context.py")
    bronze = read_text("pipelines/elt_bronze.py")
    silver = read_text("pipelines/elt_silver.py")
    gold = read_text("pipelines/elt_gold.py")

    assert "run_datetime=" in helper
    assert "table_name" in helper
    assert "versioned_blob" in bronze
    assert "versioned_blob" in silver
    assert "versioned_blob" in gold
    assert "latest_blob" in bronze
    assert "latest_blob" in silver
    assert "latest_blob" in gold


def test_gold_postgres_publish_is_optional():
    gold = read_text("pipelines/elt_gold.py")
    runner = read_text("pipelines/run_elt.py")

    assert "publish_postgres: bool = False" in gold
    assert "--publish-postgres" in gold
    assert "--publish-postgres" in runner
    assert "Skipping PostgreSQL publish" in gold


def test_hive_external_tables_exist_for_lakehouse_layers():
    source = read_text("lakehouse/hive_external_tables.sql")

    assert "CREATE DATABASE IF NOT EXISTS talentflow_bronze" in source
    assert "CREATE DATABASE IF NOT EXISTS talentflow_silver" in source
    assert "CREATE DATABASE IF NOT EXISTS talentflow_gold" in source
    assert "PARTITIONED BY (run_datetime STRING)" in source
    assert "LOCATION '${LAKE_ROOT}/bronze/candidates'" in source
    assert "LOCATION '${LAKE_ROOT}/silver/candidates_secure'" in source
    assert "LOCATION '${LAKE_ROOT}/gold/job_hire_rate'" in source


def test_admin_dashboard_exposes_gold_and_ml_insights():
    source = read_text("app/portal.py")

    assert "Gold Layer KPIs" in source
    assert "analytics.job_hire_rate" in source
    assert "analytics.ml_feature_insights" in source


def test_admin_dashboard_exposes_conversational_data_assistant():
    portal = read_text("app/portal.py")
    assistant = read_text("app/analytics_assistant.py")
    agent = read_text("app/analytics_agent.py")
    local_model = read_text("app/local_sql_model.py")
    hf_agent = read_text("app/huggingface_sql_agent.py")

    assert "Ask Data" in portal
    assert "LOCAL_AGENT_ONLY" in portal
    assert "LOCAL_LLM_PROVIDER" in portal
    assert "generate_agent_plan" in portal
    assert "generate_result_narrative" in portal
    assert "repair_agent_plan" in portal
    assert "record_agent_interaction" in portal
    assert "update_agent_feedback" in portal
    assert "render_assistant_result" in portal
    assert "st.bar_chart" in portal
    assert "st.line_chart" in portal
    assert "analytics.agent_interactions" in agent
    assert "OPENAI_API_KEY" in agent
    assert "retrieve_agent_examples" in agent
    assert "generate_local_sql_plan" in agent
    assert "generate_huggingface_sql_plan" in agent
    assert "repair_huggingface_sql" in agent
    assert "pipeline" in hf_agent
    assert "LOCAL_HF_MODEL" in hf_agent
    assert "LOCAL_SQL_USE_CASES" in local_model
    assert "High-rated candidates not hired" in local_model
    assert "candidate_audit_log" in assistant
    assert "interview_feedback" in assistant
    assert "analytics.ml_feature_insights" in assistant
    assert "Only SELECT/WITH queries are allowed" in assistant


def test_admin_dashboard_exposes_genai_hiring_copilot():
    portal = read_text("app/portal.py")
    copilot = read_text("app/genai_hiring_copilot.py")
    orchestrator = read_text("app/genai_agent_orchestrator.py")
    ddl = read_text("DDL.sql")
    readme = read_text("README.md")

    assert "GenAI Copilot" in portal
    assert "GenAI agent studio" in portal
    assert "run_genai_agent_team" in portal
    assert "build_copilot_pack" in portal
    assert "analytics.genai_copilot_outputs" in copilot
    assert "analytics.genai_agent_runs" in copilot
    assert "redact_sensitive_text" in copilot
    assert "AgentMessage" in orchestrator
    assert "risk_agent" in orchestrator
    assert "analytics_agent" in orchestrator
    assert "human review" in copilot
    assert "analytics.genai_copilot_outputs" in ddl
    assert "analytics.genai_agent_runs" in ddl
    assert "GenAI hiring copilot" in readme


def test_readme_documents_demo_flow_and_architecture():
    source = read_text("README.md")

    assert "Architecture" in source
    assert "Run The Platform" in source
    assert "Demo Flow" in source
    assert "Production Readiness Roadmap" in source


def test_agent_memory_and_join_indexes_are_declared():
    source = read_text("DDL.sql")

    assert "analytics.agent_interactions" in source
    assert "idx_agent_interactions_feedback" in source
    assert "idx_interview_schedules_candidate_id" in source
    assert "idx_interview_feedback_schedule_id" in source
    assert "idx_login_logs_candidate_timestamp" in source


def test_deploy_schema_uses_ddl_and_remains_non_destructive():
    source = read_text("deploy_schema.py")

    assert "DDL.sql" in source
    assert "read_schema_sql()" in source
    assert "DROP " not in source.upper()
    assert "TRUNCATE " not in source.upper()
    assert "DELETE " not in source.upper()
