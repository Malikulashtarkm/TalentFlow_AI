# TalentFlow AI - Professor Viva Questions and Answers

Student: Malikulashtar K Malampatiwalla  
BITS ID: 2024DA04133  
Project: TalentFlow AI - Enterprise Candidate Relationship Management and Predictive Intelligence Ecosystem

## 1. Project Overview

### Q1. What is TalentFlow AI?
TalentFlow AI is an end-to-end recruitment intelligence platform. It combines a Streamlit recruitment portal, Azure PostgreSQL operational database, Azure Blob/ADLS-style medallion lakehouse, Prefect orchestration, DuckDB Gold analytics, and Random Forest based ML insights. The main goal is to convert operational recruitment data into governed analytical assets and predictive intelligence.

### Q2. What problem does your project solve?
Recruitment data is usually fragmented across candidate profiles, schedules, feedback forms and reports. This makes it difficult to track candidate history, monitor funnel performance, and generate business insights. TalentFlow AI solves this by capturing recruitment workflows in PostgreSQL, moving data through Bronze/Silver/Gold lakehouse layers, and surfacing KPIs and ML feature insights in the admin dashboard.

### Q3. Why did you choose recruitment as the domain?
Recruitment is data intensive and naturally has multiple entities: candidates, jobs, interviewers, schedules, feedback, decisions and engagement logs. It is a good use case for demonstrating both operational transaction processing and analytical decision-making.

### Q4. What is the main contribution of your project?
The contribution is not only a recruitment portal. The main contribution is the complete data product pipeline: operational data capture, medallion lakehouse storage, PII-safe Silver processing, SCD Type 2 candidate history, Gold KPI generation, validation, and ML insight publishing.

### Q5. What has been completed at mid-term?
The completed scope includes Streamlit role-based portals, PostgreSQL schema, Bronze/Silver/Gold ELT pipelines, Azure storage outputs, Prefect scheduling, Gold KPI tables, ML artifacts, feature importance outputs, and validation checks. The pending/future scope is the conversational Text-to-SQL layer and production hardening.

## 2. Architecture

### Q6. Explain your architecture end-to-end.
User actions happen in the Streamlit portal and are stored in Azure PostgreSQL. Prefect runs the full ELT flow. Bronze extracts raw tables into versioned Parquet files. Silver encrypts PII and applies SCD Type 2 logic for candidates. Gold uses DuckDB to create business KPI datasets. The admin dashboard reads Gold KPIs and ML feature insights. ML training also creates joblib artifacts, metrics JSON, and feature-importance CSV files.

### Q7. Why did you separate the application database and analytical lakehouse?
PostgreSQL is best for transactional integrity and application queries. The lakehouse is better for historical storage, repeated ELT runs, analytics, and scalable Parquet datasets. Separating them prevents analytical workloads from disturbing operational workflows.

### Q8. Why not directly report from PostgreSQL?
Direct reporting from PostgreSQL is simpler but less scalable and less historical. It also mixes OLTP and analytical workloads. The medallion lakehouse preserves raw snapshots, secure transformed data, and business-ready Gold outputs.

### Q9. What are the main components of your system?
The components are Streamlit portal, PostgreSQL OLTP database, Bronze ingestion, Silver secure transformation, Gold analytics, Hive external table definitions, Prefect orchestration, ML training pipeline, validation scripts, and admin dashboard.

### Q10. What is the role of Streamlit?
Streamlit is the user interface layer. It supports candidate registration/profile update, admin scheduling and KPI views, and interviewer feedback submission. It is also the place where Gold KPIs and ML insights are demonstrated to users.

## 3. Database and ER Design

### Q11. What are the important tables in your database?
Important tables include `candidates`, `candidate_education`, `candidate_audit_log`, `login_logs`, `jobs`, `recruiters`, `interviewers`, `interview_stages`, `interview_schedules`, `interview_feedback`, `candidate_responses`, and `questions_bank`.

### Q12. Why did you normalize the PostgreSQL schema?
Normalization reduces redundancy and improves consistency. For example, candidate profile data, education, schedules and feedback are separated. This keeps relationships clear and prevents repeated or conflicting data.

### Q13. What constraints have you used?
The schema uses primary keys, foreign keys, unique constraints, not-null constraints and a check constraint. Example: `email` is unique in candidates/interviewers/recruiters, `candidate_id` and `job_id` are UUID primary keys, and feedback rating has `CHECK (rating >= 1 AND rating <= 5)`.

### Q14. How is candidate history captured in the operational layer?
The portal writes profile changes into `candidate_audit_log`, storing candidate_id, changed field, old value, new value and timestamp. This supports operational audit tracking.

### Q15. How is login activity captured?
When a candidate logs in successfully, a row is inserted into `login_logs`. This becomes an engagement signal for Gold analytics and ML features.

### Q16. How are interviews represented?
`interview_schedules` connects candidates, jobs, interviewers and stages. `interview_feedback` stores rating, comments and decision. This design supports both pipeline tracking and model training.

## 4. Medallion Lakehouse

### Q17. What is medallion architecture?
Medallion architecture organizes data into Bronze, Silver and Gold layers. Bronze stores raw data, Silver stores cleaned/secured/enriched data, and Gold stores business-ready datasets for analytics and ML.

### Q18. How did you implement Bronze?
Bronze uses Prefect tasks to read PostgreSQL tables using pandas and SQLAlchemy, convert them to Parquet, and upload them to the Azure `bronze` container. Each table gets a versioned run path and a `latest` copy.

### Q19. Which tables are extracted into Bronze?
The Bronze registry includes 12 tables: jobs, recruiters, interviewers, candidates, candidate_education, candidate_audit_log, interview_stages, questions_bank, interview_schedules, interview_feedback, candidate_responses and login_logs.

### Q20. What is the purpose of `run_datetime`?
`run_datetime` creates a shared runtime identifier for Bronze, Silver and Gold outputs. It allows every table produced in the same run to be traced together. Example path: `gold/job_hire_rate/run_datetime=YYYYMMDD_HHMMSS/job_hire_rate.parquet`.

### Q21. Why do you also maintain `latest` copies?
Versioned folders provide lineage and reproducibility. `latest` copies make downstream jobs simpler because they can read the most recent data without knowing the exact run timestamp.

### Q22. What happens in Silver?
Silver reads Bronze Parquet, encrypts PII columns, applies SCD Type 2 for candidates, copies non-PII tables forward, and writes secure Parquet outputs to the `silver` container.

### Q23. Which tables are treated as PII tables?
The PII tables are `candidates`, `recruiters`, `interviewers`, and `candidate_audit_log`. Candidate PII includes email, phone number, password and expected salary.

### Q24. What is SCD Type 2?
SCD Type 2 is a historical tracking method where changes create a new row version instead of overwriting the old row. The old row is closed with an end date and `is_current = false`, while the new row is active with `is_current = true`.

### Q25. How did you implement SCD Type 2?
In `elt_silver.py`, the candidate row is hashed using tracked columns. The pipeline compares the new hash with the current existing hash. If it changed, the previous current row is closed and a new row is inserted with `start_date`, `end_date`, `is_current`, and `row_hash`.

### Q26. Why is SCD2 useful in recruitment?
Recruitment decisions depend on historical candidate state. A candidate's city, salary expectation, education or profile can change. SCD2 allows point-in-time analysis instead of only seeing the latest profile.

### Q27. What happens in Gold?
Gold reads Silver Parquet data, decrypts salary where required for aggregate calculations, uses DuckDB to compute KPI datasets, writes Gold Parquet snapshots, and optionally publishes Gold tables to PostgreSQL analytics schema.

### Q28. What Gold datasets do you generate?
The Gold datasets are `city_talent_score`, `salary_benchmarks`, `candidate_engagement`, `interview_pipeline_funnel`, and `job_hire_rate`.

### Q29. Why is Gold lake-first?
The analytical source of truth is Parquet in the lake. PostgreSQL publishing is optional for dashboard caching. This avoids turning PostgreSQL into the warehouse and keeps Gold outputs reproducible in the lake.

## 5. Azure, Parquet, DuckDB and Hive Tables

### Q30. Why use Azure Blob/ADLS-style storage?
It provides cloud storage for structured lakehouse folders and Parquet outputs. The project uses separate containers for Bronze, Silver and Gold, making the data lifecycle clear.

### Q31. Why use Parquet?
Parquet is columnar, compact and efficient for analytical queries. It is well suited for lakehouse datasets and works directly with DuckDB and external table definitions.

### Q32. Why use DuckDB for Gold?
DuckDB can run analytical SQL directly over Parquet files with low overhead. It is lightweight and suitable for local/demo Gold aggregation without needing a full Spark cluster.

### Q33. What are Hive external tables used for?
`lakehouse/hive_external_tables.sql` defines external tables for Bronze, Silver and Gold datasets partitioned by `run_datetime`. This allows future query engines like Hive, Spark, Synapse or Databricks SQL to read the lakehouse data.

### Q34. What does `MSCK REPAIR TABLE` do?
It registers new partition folders in a Hive-compatible metastore. Since each pipeline run creates a new `run_datetime` partition, repair or explicit partition add commands are needed for query engines to discover new partitions.

## 6. Prefect and Orchestration

### Q35. Why use Prefect?
Prefect gives Python-native flow orchestration, task logs, states, deployments and scheduling. It helps demonstrate that the ELT is repeatable and observable, not just a manual script.

### Q36. What are your Prefect flows?
The flows are `Bronze-Ingestion-Flow`, `Silver-Secure-Flow`, `Gold-Analytical-Flow`, and the parent `TalentFlow-Full-ELT`.

### Q37. How does the full ELT flow work?
`full_elt_flow` creates a shared `run_datetime`, then calls `bronze_flow(run_datetime)`, `silver_flow(run_datetime)`, and `gold_flow(run_datetime, publish_postgres=...)`.

### Q38. How did you schedule the demo every 2 minutes?
There are two ways. Locally, `scripts/run_elt_scheduler.py --every-seconds 120 --publish-postgres` runs repeatedly. In Prefect Cloud, `scripts/serve_elt_prefect_cloud.py` serves a deployment named `talentflow-elt-every-2-min-demo` with `interval=120`.

### Q39. What can the examiner see in Prefect Cloud?
They can see deployment status, recurring flow runs, run duration, parameters, completed/failed states, tags, and child flows for Bronze, Silver and Gold.

## 7. Machine Learning

### Q40. What ML problem did you solve?
The project builds predictive intelligence from recruitment data. It trains models for hire prediction, decision prediction and rating prediction using candidate, job, education, interview and engagement features.

### Q41. What features are used for ML?
Numeric features are expected salary, passing year, GPA and login count. Categorical features include city, state, country, degree, university, job title, department, salary range, job location and stage name.

### Q42. Why use Random Forest?
Random Forest is a strong baseline for structured/tabular data. It handles nonlinear patterns, works with mixed features after preprocessing, and provides feature importance for explanation.

### Q43. What preprocessing is used?
The ML pipeline uses `ColumnTransformer`. Numeric features are imputed with median and scaled. Categorical features are imputed with most frequent value and one-hot encoded.

### Q44. What models are trained?
Three models are trained: `hire_prediction` classifier, `decision_prediction` classifier, and `rating_prediction` regressor. Artifacts are saved as joblib files.

### Q45. What were the current ML results?
The hire prediction model has accuracy 0.5021, F1 0.3958 and ROC-AUC 0.5016 on support 233. Decision prediction accuracy is 0.3433 with weighted F1 0.3404. Rating prediction MAE is 1.2278 and R2 is -0.0549.

### Q46. These ML results are modest. How will you defend them?
I will clearly say the mid-term goal was to establish an end-to-end ML workflow, not final model performance. The results show the baseline is working but needs stronger real data, better feature engineering, balancing, hyperparameter tuning, and model validation.

### Q47. What are the most important features?
For hire prediction, top features include expected salary, GPA, passing year, login count, state and interview stage. This makes sense because salary fit, education and engagement can influence hiring outcomes.

### Q48. Where are ML outputs stored?
The model artifacts are stored under `models/artifacts/<run_id>/`. Metrics are in `metrics.json`, feature importances are CSV files, and top insights are written to `analytics.ml_feature_insights` for the admin dashboard.

## 8. Validation and Testing

### Q49. How did you validate Gold analytics?
`scripts/validate_gold_analytics.py` checks whether analytics schema and expected columns exist, row counts are non-empty, values are within valid ranges, duplicate groups are absent, source-to-Gold totals reconcile, and hire-rate formula is correct.

### Q50. What reconciliation checks are performed?
The script compares source login counts to `candidate_engagement`, interview schedule counts to `interview_pipeline_funnel`, feedback counts to `job_hire_rate`, and source hire decisions to Gold hire counts.

### Q51. What tests exist in the project?
`tests/test_project_contracts.py` verifies important contracts: demo reset requires explicit flag, synthetic feedback has learnable signal, Gold validation covers expected tables, Silver tracks SCD2 hashes, lake layers write versioned paths, Gold PostgreSQL publish is optional, Hive external tables exist, and dashboard exposes Gold/ML outputs.

### Q52. How do you prevent accidental demo-data reset?
The project has a safety flag `ALLOW_DEMO_DATA_RESET`. The tests verify that the demo-data reset requires this explicit flag before truncating and regenerating data.

## 9. Security, Privacy and Limitations

### Q53. How do you handle PII?
Silver encrypts PII fields using Fernet encryption through `utils/crypto_utils.py`. Candidate email, phone number, password and expected salary are encrypted before being written to secure Silver outputs.

### Q54. Are passwords securely handled?
Currently the demo portal stores plaintext passwords in PostgreSQL and later encrypts them in the Silver layer. This is acceptable only for a mid-term demo. In production, passwords must be hashed with bcrypt/Argon2 at registration and never stored or decrypted.

### Q55. Why encrypt expected salary?
Expected salary is sensitive personal/compensation data. It is encrypted in Silver to reduce exposure. Gold decrypts it only for aggregate calculations like average salary benchmarks.

### Q56. What are the main limitations of the current project?
Main limitations are plaintext demo passwords, synthetic data, modest ML performance, no fully implemented Text-to-SQL agent yet, basic RBAC based on email domain, no CI/CD, and limited production monitoring.

### Q57. How would you improve security?
I would add password hashing, proper authentication provider, role-based access control, secret management through Azure Key Vault, stronger audit logging, and least-privilege access to storage and database.

## 10. Text-to-SQL and Future Scope

### Q58. What is the planned Text-to-SQL component?
The planned component will allow recruiters/admins to ask natural-language questions. The system will map the question to governed Gold table schema, generate SQL, validate it as read-only and safe, execute it, and return an explanation.

### Q59. Why did you keep Text-to-SQL as future work?
The project first needed a trusted data foundation. A Text-to-SQL interface without clean Gold tables can produce unreliable answers. The current phase establishes PostgreSQL, lakehouse, validation and Gold outputs first.

### Q60. How does Vaswani et al. relate to your project?
Vaswani et al.'s Transformer architecture is a foundation for modern LLMs. In TalentFlow AI, the future LLM layer will be used as an interface for natural-language analytics, while the trusted data source remains the Gold layer.

## 11. Design Defense Questions

### Q61. Why Kimball and Ross in your references?
Kimball and Ross are relevant because Gold datasets are designed as business-facing analytical outputs. The project thinks in terms of recruitment business processes such as hiring funnel, engagement, salary benchmark and hire rate.

### Q62. Is your project ELT or ETL?
It is closer to ELT. Data is extracted from PostgreSQL and loaded to Bronze first. Transformations happen afterward in Silver and Gold inside the lakehouse pipeline.

### Q63. Why not use Spark?
Spark is powerful for large distributed processing, but for this mid-term demo the data volume is manageable. DuckDB is simpler, lightweight and enough to demonstrate analytical SQL over Parquet.

### Q64. Why not use Delta Lake?
Delta Lake would provide ACID transactions and better metadata/version management. In this project, plain Parquet was chosen for simplicity and demonstration. Delta Lake is a strong future enhancement.

### Q65. Why use Azure PostgreSQL and Azure Blob together?
Azure PostgreSQL provides transactional relational storage for the application. Azure Blob/ADLS-style storage provides scalable file-based lakehouse storage for analytics and ML outputs.

### Q66. What makes your project different from a normal CRUD app?
A normal CRUD app only stores and displays operational records. TalentFlow AI adds data engineering layers, historical tracking, privacy processing, Gold analytics, orchestration, validation and ML insight generation.

### Q67. What would happen if a pipeline fails halfway?
Prefect will show the failed flow/task state and logs. Because outputs are written with run_datetime partitions, previous successful runs remain available. A failed run can be debugged without destroying older outputs.

### Q68. Why are Gold tables optionally pushed back to PostgreSQL?
The Streamlit dashboard can easily query PostgreSQL analytics schema. But the actual lakehouse source of truth remains Gold Parquet. PostgreSQL publish is a cache for dashboard convenience.

### Q69. How do you explain `candidate_engagement`?
It counts login events per candidate from `login_logs`. It indicates user activity and becomes both a dashboard KPI and an ML feature.

### Q70. How do you explain `job_hire_rate`?
It aggregates interview feedback by job title, counts total feedback, counts decisions where `decision = 'Hire'`, and calculates `hire_rate_pct = hire_count / total_feedback * 100`.

## 12. Demo Questions

### Q71. What should you show first in a live demo?
Start with the Streamlit portal: candidate registration/profile, admin schedule interview, interviewer feedback, and admin dashboard. Then show Prefect runs and Azure storage folders to prove data movement.

### Q72. How do you prove the pipeline is working?
Show Prefect completed runs, Azure Bronze/Silver/Gold folders, run_datetime partitions, Gold Parquet files, and admin dashboard KPI tables populated from analytics outputs.

### Q73. What command runs the full pipeline?
Use `python pipelines/run_elt.py --publish-postgres` if the dashboard should read updated Gold tables from PostgreSQL. Without `--publish-postgres`, Gold remains lake-first only.

### Q74. What command serves the 2-minute Prefect Cloud demo?
Run `python scripts/serve_elt_prefect_cloud.py` after logging into Prefect Cloud. It serves `TalentFlow-Full-ELT` as `talentflow-elt-every-2-min-demo` with interval 120 seconds.

### Q75. What should you say if dashboard data is not visible?
Say the dashboard reads PostgreSQL analytics cache. I need to run the Gold pipeline with `--publish-postgres` or train ML insights for `analytics.ml_feature_insights`.

## 13. Tough Questions and Best Answers

### Q76. Your model accuracy is low. Is the ML useful?
At this stage, the ML is useful as a workflow proof, not a final decision engine. It demonstrates feature extraction, preprocessing, training, evaluation, artifact storage and dashboard publishing. Improving predictive performance is future work.

### Q77. Why should recruiters trust your Gold KPIs?
Because Gold validation checks schema, row counts, null/range constraints, duplicates, reconciliation against source totals, and formula correctness. The KPIs are not just displayed; they are tested.

### Q78. Is encryption enough for privacy?
Encryption is one layer. A production system also needs access control, key management, audit logging, password hashing, masking, and least-privilege storage/database permissions.

### Q79. What is your biggest technical challenge so far?
The main challenge was making repeated ELT runs stable while preserving history and encrypting PII. Specific issues included encrypted strings being assigned into numeric columns and UUID values being read back from Parquet as bytes. These were handled by casting encryption targets to object and normalizing UUID business keys.

### Q80. What is the most important learning from this project?
The main learning is that AI features depend on trustworthy data engineering. Before building Text-to-SQL or ML predictions, the system needs clean operational schema, lineage, privacy handling, validated Gold datasets and reproducible orchestration.

## 14. Short Closing Answer

If asked to summarize the project in 30 seconds:

"TalentFlow AI is an end-to-end recruitment intelligence platform. It starts with a Streamlit portal backed by Azure PostgreSQL, moves operational recruitment data through Bronze, Silver and Gold lakehouse layers on Azure storage, protects PII and tracks candidate history using SCD Type 2, creates business KPIs using DuckDB, orchestrates the pipeline using Prefect, and publishes ML feature insights through Random Forest models. The mid-term work proves the data foundation, analytics and ML workflow; the remaining work is conversational Text-to-SQL, stronger ML evaluation and production hardening."

