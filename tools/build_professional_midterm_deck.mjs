import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, Presentation, PresentationFile } from "file:///C:/Users/Acer/AppData/Local/Temp/codex-presentations/talentflow-template-follow/tmp/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const OUT = "D:/TalentFlow_AI/outputs/TalentFlow_AI_Professional_Mid_Term_With_Screenshots_2024DA04133.pptx";
const QA = "C:/Users/Acer/AppData/Local/Temp/codex-presentations/talentflow-professional-midterm/qa";
const ASSETS = "D:/TalentFlow_AI/report_assets";
const SHOTS = {
  prefectRuns: "C:/Users/Acer/OneDrive/Pictures/Screenshots/Screenshot 2026-06-19 230633.png",
  prefectDeployment: "C:/Users/Acer/OneDrive/Pictures/Screenshots/Screenshot 2026-06-19 230544.png",
  goldRuns: "C:/Users/Acer/OneDrive/Pictures/Screenshots/Screenshot 2026-06-19 230709.png",
  goldFile: "C:/Users/Acer/OneDrive/Pictures/Screenshots/Screenshot 2026-06-19 225707.png",
  goldFolders: "C:/Users/Acer/OneDrive/Pictures/Screenshots/Screenshot 2026-06-19 225655.png",
  silverFolders: "C:/Users/Acer/OneDrive/Pictures/Screenshots/Screenshot 2026-06-19 225540.png",
  bronzeFolders: "C:/Users/Acer/OneDrive/Pictures/Screenshots/Screenshot 2026-06-19 225530.png",
  containers: "C:/Users/Acer/OneDrive/Pictures/Screenshots/Screenshot 2026-06-19 225521.png",
  goldDashboard: "C:/Users/Acer/OneDrive/Pictures/Screenshots/Screenshot 2026-06-19 005239.png",
  adminPipeline: "C:/Users/Acer/OneDrive/Pictures/Screenshots/Screenshot 2026-06-19 005200.png",
  adminSchedule: "C:/Users/Acer/OneDrive/Pictures/Screenshots/Screenshot 2026-06-19 005128.png",
  interviewerFeedback: "C:/Users/Acer/OneDrive/Pictures/Screenshots/Screenshot 2026-06-19 004905.png",
  interviewerList: "C:/Users/Acer/OneDrive/Pictures/Screenshots/Screenshot 2026-06-19 004848.png",
  candidateDashboard: "C:/Users/Acer/OneDrive/Pictures/Screenshots/Screenshot 2026-06-19 003314.png",
  candidateRegister: "C:/Users/Acer/OneDrive/Pictures/Screenshots/Screenshot 2026-06-19 003158.png",
};

const W = 1280;
const H = 720;
const C = {
  bg: "#07111f",
  bg2: "#0a1728",
  panel: "#101d31",
  panel2: "#0d2035",
  line: "#1f3b56",
  cyan: "#25c7f7",
  green: "#25d689",
  amber: "#f6b84b",
  red: "#f06a6a",
  text: "#f5f7fb",
  muted: "#a9b8ca",
  dim: "#718095",
  white: "#ffffff",
};

async function writeBlob(filePath, blob) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function imageBytes(filePath) {
  const bytes = await fs.readFile(filePath);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function addBg(slide, eyebrow) {
  slide.background.fill = C.bg;
  slide.shapes.add({
    geometry: "rect",
    position: { left: 0, top: 0, width: W, height: H },
    fill: C.bg,
    line: { fill: C.bg, width: 0 },
  });
  slide.shapes.add({
    geometry: "rect",
    position: { left: 0, top: H - 7, width: W, height: 7 },
    fill: C.cyan,
    line: { fill: C.cyan, width: 0 },
  });
  slide.shapes.add({
    geometry: "rect",
    position: { left: W * 0.58, top: H - 7, width: W * 0.42, height: 7 },
    fill: C.green,
    line: { fill: C.green, width: 0 },
  });
  if (eyebrow) {
    text(slide, eyebrow.toUpperCase(), 845, 27, 370, 20, {
      size: 10,
      color: C.muted,
      bold: true,
      align: "right",
    });
  }
}

function text(slide, value, left, top, width, height, opt = {}) {
  const s = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  s.text = value;
  s.text.style = {
    fontSize: opt.size ?? 18,
    color: opt.color ?? C.text,
    bold: opt.bold ?? false,
    fontFace: opt.font ?? "Inter",
    alignment: opt.align ?? "left",
  };
  return s;
}

function title(slide, value, subtitle, eyebrow) {
  addBg(slide, eyebrow);
  text(slide, value, 60, 54, 890, 62, { size: 33, bold: true });
  slide.shapes.add({
    geometry: "rect",
    position: { left: 60, top: 117, width: 70, height: 3 },
    fill: C.cyan,
    line: { fill: C.cyan, width: 0 },
  });
  if (subtitle) text(slide, subtitle, 60, 130, 1010, 36, { size: 14, color: C.muted });
}

function card(slide, left, top, width, height, opt = {}) {
  return slide.shapes.add({
    geometry: "roundRect",
    position: { left, top, width, height },
    fill: opt.fill ?? C.panel,
    line: { style: "solid", fill: opt.line ?? C.line, width: 1 },
    borderRadius: "rounded-lg",
  });
}

function label(slide, value, left, top, color = C.cyan) {
  text(slide, value.toUpperCase(), left, top, 260, 20, { size: 10, color, bold: true });
}

function bullet(slide, items, left, top, width, lineH = 28, opt = {}) {
  items.forEach((item, i) => {
    text(slide, "•", left, top + i * lineH + 1, 14, 20, { size: opt.size ?? 15, color: opt.color ?? C.green, bold: true });
    text(slide, item, left + 22, top + i * lineH, width - 22, lineH + 8, { size: opt.size ?? 15, color: opt.textColor ?? C.text });
  });
}

function metric(slide, value, caption, left, top, width, color = C.cyan) {
  card(slide, left, top, width, 94, { fill: C.panel2, line: "#1d455c" });
  text(slide, value, left + 16, top + 16, width - 32, 34, { size: 30, bold: true, color });
  text(slide, caption, left + 16, top + 56, width - 32, 24, { size: 12, color: C.muted });
}

function miniTable(slide, rows, left, top, width, rowH = 38) {
  rows.forEach((r, i) => {
    const y = top + i * rowH;
    slide.shapes.add({
      geometry: "rect",
      position: { left, top: y, width, height: rowH },
      fill: i === 0 ? "#14324a" : (i % 2 ? "#0e1d31" : "#101f34"),
      line: { fill: "#223b58", width: 1 },
    });
    const colW = width / r.length;
    r.forEach((cell, j) => text(slide, cell, left + j * colW + 12, y + 9, colW - 18, rowH - 10, {
      size: i === 0 ? 12 : 11,
      bold: i === 0,
      color: i === 0 ? C.text : C.muted,
    }));
  });
}

async function addImage(slide, file, left, top, width, height, fit = "contain") {
  slide.images.add({
    blob: await imageBytes(file),
    contentType: "image/png",
    alt: path.basename(file),
    fit,
    position: { left, top, width, height },
    geometry: "roundRect",
    borderRadius: "rounded-lg",
  });
}

async function screenshotFrame(slide, file, left, top, width, height, caption, fit = "cover") {
  card(slide, left - 6, top - 6, width + 12, height + 42, { fill: "#081522", line: "#22415c" });
  await addImage(slide, file, left, top, width, height, fit);
  text(slide, caption, left + 4, top + height + 12, width - 8, 20, { size: 11.5, color: C.muted, align: "center" });
}

function architectureLine(slide, labels, y) {
  const x0 = 55;
  const gap = 11;
  const w = (1170 - gap * (labels.length - 1)) / labels.length;
  labels.forEach((l, i) => {
    const x = x0 + i * (w + gap);
    card(slide, x, y, w, 94, { fill: i === labels.length - 1 ? "#221b13" : C.panel2, line: i === labels.length - 1 ? "#ad6837" : "#21445f" });
    text(slide, l[0], x + 12, y + 12, w - 24, 21, { size: 13, bold: true, color: i === labels.length - 1 ? C.amber : C.cyan });
    text(slide, l[1], x + 12, y + 42, w - 24, 42, { size: 10.5, color: C.muted });
    if (i < labels.length - 1) text(slide, "→", x + w + 1, y + 38, 14, 24, { size: 17, color: C.muted, bold: true });
  });
}

function bars(slide, data, left, top, width, height, color = C.green) {
  const max = Math.max(...data.map((d) => d[1]));
  data.forEach((d, i) => {
    const y = top + i * (height / data.length);
    text(slide, d[0], left, y + 2, 170, 18, { size: 10.5, color: C.muted });
    slide.shapes.add({
      geometry: "rect",
      position: { left: left + 180, top: y + 6, width: (width - 230) * (d[1] / max), height: 10 },
      fill: color,
      line: { fill: color, width: 0 },
    });
    text(slide, String(d[1]), left + width - 42, y + 1, 42, 18, { size: 10, color: C.text, align: "right" });
  });
}

async function main() {
  const p = Presentation.create({ slideSize: { width: W, height: H } });

  let s = p.slides.add();
  addBg(s, "TalentFlow AI | Mid-Term Review");
  text(s, "TalentFlow AI", 60, 135, 780, 70, { size: 46, bold: true });
  text(s, "Enterprise Candidate Relationship Management and Predictive Intelligence Ecosystem", 62, 214, 980, 38, { size: 21, color: C.muted });
  text(s, "A detailed mid-term presentation covering system design, lakehouse engineering, validation, ML workflow, and future Text-to-SQL direction.", 62, 284, 915, 58, { size: 18, color: C.text });
  metric(s, "2024DA04133", "BITS ID", 60, 515, 250);
  metric(s, "Mid-Term", "Project evaluation stage", 330, 515, 250, C.green);
  metric(s, "Altimetrik", "Host organization", 600, 515, 250, C.amber);
  text(s, "Malikulashtar K Malampatiwalla", 60, 634, 520, 20, { size: 13, color: C.muted });

  s = p.slides.add();
  title(s, "Presentation Roadmap", "How the review is structured for the examiner: problem, architecture, implementation evidence, validation, and next work.", "Narrative");
  const roadmap = [
    ["1", "Why TalentFlow AI?", "Recruitment data fragmentation, loss of candidate history, and manual reporting bottlenecks."],
    ["2", "How the system is built", "Streamlit portals, PostgreSQL operational schema, Azure lakehouse, Prefect flows, DuckDB Gold analytics."],
    ["3", "What has been completed", "Frontend workflows, Bronze/Silver/Gold ELT, Gold KPI datasets, ML artifacts, validation scripts."],
    ["4", "What remains", "Text-to-SQL conversational interface, stronger model validation, production hardening and final dissertation polish."],
  ];
  roadmap.forEach((r, i) => {
    const x = 70 + (i % 2) * 575;
    const y = 190 + Math.floor(i / 2) * 185;
    card(s, x, y, 530, 128);
    text(s, r[0], x + 20, y + 22, 34, 34, { size: 24, bold: true, color: C.cyan, align: "center" });
    text(s, r[1], x + 70, y + 24, 420, 26, { size: 19, bold: true });
    text(s, r[2], x + 70, y + 60, 425, 45, { size: 14, color: C.muted });
  });

  s = p.slides.add();
  title(s, "Problem Definition and Motivation", "TalentFlow AI was designed around a practical recruitment-data problem: operational tools capture activity, but do not automatically create reliable analytical memory.", "Context");
  card(s, 60, 190, 350, 310);
  label(s, "Operational fragmentation", 88, 218, C.red);
  bullet(s, [
    "Candidate profile, interview schedule, feedback and engagement data are spread across workflow screens.",
    "Simple update-in-place systems overwrite the earlier state of a candidate.",
    "Recruiters need timeline-aware information, not just the current profile row.",
  ], 88, 258, 285, 58);
  card(s, 465, 190, 350, 310);
  label(s, "Analytics bottleneck", 493, 218, C.amber);
  bullet(s, [
    "Hiring-funnel, salary, engagement and city-level questions require manual SQL or exported reports.",
    "Operational databases are not designed as business-facing reporting products.",
    "Data quality and privacy must be handled before analytics are trusted.",
  ], 493, 258, 285, 58);
  card(s, 870, 190, 350, 310);
  label(s, "Project response", 898, 218, C.green);
  bullet(s, [
    "Separate OLTP work from lakehouse analytics.",
    "Preserve historical candidate versions through Silver SCD2 logic.",
    "Serve Gold KPIs and ML features to admin dashboards and future conversational analytics.",
  ], 898, 258, 285, 58);
  text(s, "Design implication: the project is not only a recruitment portal; it is a governed recruitment-data product.", 85, 560, 1080, 28, { size: 20, bold: true, color: C.cyan, align: "center" });

  s = p.slides.add();
  title(s, "Project Objectives and Scope", "The scope combines application workflows with data engineering and AI readiness, so the system demonstrates end-to-end recruitment intelligence.", "Objectives");
  const objRows = [
    ["Area", "Objective", "Implementation Evidence"],
    ["Operational CRM", "Candidate, interviewer and admin workflows", "Streamlit portal, profile updates, schedules, feedback"],
    ["Relational core", "Normalized recruitment source schema", "13 PostgreSQL tables with PK/FK/CHECK/UNIQUE constraints"],
    ["Lakehouse", "Bronze raw, Silver secure, Gold analytics", "Versioned Parquet outputs with latest copies"],
    ["Orchestration", "Repeatable ELT with observability", "Prefect full flow and 2-minute demo deployment"],
    ["Analytics", "Recruitment KPI datasets", "city_talent_score, salary_benchmarks, engagement, funnel, hire_rate"],
    ["Predictive AI", "ML-ready features and model artifacts", "Random Forest pipelines, metrics JSON, feature importance CSVs"],
  ];
  miniTable(s, objRows, 62, 180, 1156, 55);

  s = p.slides.add();
  title(s, "Current Implementation Modules", "The implementation is modular: user-facing actions are separated from storage, transformation, analytics, metadata and validation.", "System Modules");
  const modules = [
    ["Candidate Portal", "Registration, login, profile display/update, engagement logging"],
    ["Interviewer Portal", "Assigned interview view, structured rating, comments and decision"],
    ["Admin Portal", "Recruiter assignment, schedule control, KPI tabs and ML feature insights"],
    ["Operational DB", "PostgreSQL recruitment entities, constraints, audit and login logs"],
    ["Bronze Layer", "Raw source extraction to versioned Parquet paths and latest copies"],
    ["Silver Layer", "PII encryption, SCD2 candidate tracking, secure Parquet outputs"],
    ["Gold Layer", "DuckDB KPI aggregation and optional analytics schema publishing"],
    ["ML Layer", "Random Forest artifacts, metrics, feature importance and dashboard output"],
  ];
  modules.forEach((m, i) => {
    const x = 60 + (i % 2) * 590;
    const y = 170 + Math.floor(i / 2) * 96;
    card(s, x, y, 535, 70);
    text(s, m[0], x + 18, y + 14, 180, 22, { size: 15, bold: true, color: C.cyan });
    text(s, m[1], x + 210, y + 13, 295, 36, { size: 12.3, color: C.muted });
  });

  s = p.slides.add();
  title(s, "Visual Evidence: Candidate and Admin Workflows", "These screens show the user-facing Streamlit application that feeds the operational PostgreSQL source database.", "Application Evidence");
  await screenshotFrame(s, SHOTS.candidateRegister, 55, 150, 555, 300, "Candidate registration screen captures profile data and login credentials.", "cover");
  await screenshotFrame(s, SHOTS.candidateDashboard, 670, 150, 555, 300, "Candidate dashboard shows the profile fields that become operational source records.", "cover");
  card(s, 80, 515, 1120, 75, { fill: "#071421" });
  text(s, "Why this matters", 105, 536, 160, 22, { size: 15, bold: true, color: C.green });
  text(s, "The portal is not separate from the data platform: candidate registration, profile updates and login activity create the records later extracted into Bronze and transformed into engagement, salary and profile-history analytics.", 265, 532, 880, 34, { size: 13.5, color: C.muted });

  s = p.slides.add();
  title(s, "Visual Evidence: Interviewer and Admin Workflows", "The recruitment workflow is role based: admins schedule interviews and interviewers submit feedback that later becomes Gold and ML input.", "Application Evidence");
  await screenshotFrame(s, SHOTS.adminSchedule, 50, 145, 370, 240, "Admin scheduling creates interview_schedules records.", "cover");
  await screenshotFrame(s, SHOTS.adminPipeline, 455, 145, 370, 240, "Admin pipeline overview shows scheduled/completed stages.", "cover");
  await screenshotFrame(s, SHOTS.interviewerFeedback, 860, 145, 370, 240, "Interviewer feedback captures rating and hire/hold/reject decisions.", "cover");
  card(s, 75, 470, 1130, 110, { fill: "#071421" });
  label(s, "Data generated by these screens", 105, 492, C.cyan);
  bullet(s, [
    "interview_schedules links candidate_id, job_id, interviewer_id, stage_id, interview_date and status.",
    "interview_feedback stores rating, comments, decision and submitted_at.",
    "These records drive interview_pipeline_funnel, job_hire_rate and Random Forest model targets.",
  ], 105, 528, 1010, 24, { size: 13 });

  s = p.slides.add();
  title(s, "End-to-End Functional Architecture", "The implementation follows the flow captured in your mid-term report: operational capture, medallion ELT, Gold analytics, and ML outputs.", "Architecture");
  await addImage(s, path.join(ASSETS, "talentflow_architecture.png"), 60, 145, 1160, 245);
  architectureLine(s, [
    ["Streamlit", "Candidate, Interviewer, Admin and KPI screens"],
    ["PostgreSQL", "Normalized OLTP source and audit logs"],
    ["Bronze", "Raw extracts with versioned run folders"],
    ["Silver", "PII encryption and SCD2 history"],
    ["Gold", "DuckDB KPIs as Parquet"],
    ["ML", "Training artifacts and feature insights"],
  ], 455);
  text(s, "Reference alignment: medallion architecture improves quality progressively from raw to validated to business-ready data; Gold is optimized for analytics and ML consumption.", 68, 592, 1110, 34, { size: 13.5, color: C.muted });

  s = p.slides.add();
  title(s, "ER Diagram and Relational Design", "The OLTP database is normalized to protect operational integrity before data enters the lakehouse.", "Database Design");
  await addImage(s, path.join(ASSETS, "talentflow_er_diagram.png"), 55, 145, 710, 500);
  card(s, 810, 145, 405, 500);
  label(s, "Schema groups", 838, 172);
  bullet(s, [
    "Candidate core: candidates, education, login logs, audit log.",
    "Hiring and evaluation: jobs, stages, interviewers, schedules, feedback, responses.",
    "Administration: recruiters and reference tables.",
    "Integrity: UUID primary keys, foreign keys, unique emails and rating CHECK constraint.",
    "Analytical seed: login logs and feedback become ML features and Gold KPIs.",
  ], 838, 220, 335, 56);

  s = p.slides.add();
  title(s, "PostgreSQL Operational Layer", "PostgreSQL is used as the transactional source of truth; the lakehouse is not a replacement for the normalized application database.", "OLTP Layer");
  card(s, 60, 170, 360, 390);
  label(s, "Why PostgreSQL here?", 88, 198);
  bullet(s, [
    "Recruitment workflow needs row-level consistency and relational integrity.",
    "Foreign keys connect candidate, schedule, job, interviewer and feedback records.",
    "Constraints prevent invalid operational values before they reach analytics.",
    "The schema remains understandable for application queries and migrations.",
  ], 88, 240, 290, 58);
  card(s, 460, 170, 760, 390, { fill: "#071421" });
  label(s, "Representative schema choices", 492, 198, C.green);
  text(s, "candidates(candidate_id UUID PRIMARY KEY, email TEXT UNIQUE NOT NULL, expected_salary NUMERIC)\ninterview_schedules(schedule_id UUID PRIMARY KEY, candidate_id FK, job_id FK, interviewer_id FK, stage_id FK)\ninterview_feedback(feedback_id SERIAL PRIMARY KEY, schedule_id FK, rating INTEGER CHECK rating between 1 and 5)\nlogin_logs(log_id SERIAL PRIMARY KEY, candidate_id FK, login_timestamp)", 492, 240, 665, 180, { size: 16, color: "#d8ecff", font: "Fira Code" });
  text(s, "Reference used: PostgreSQL constraints documentation confirms CHECK, NOT NULL, UNIQUE, PRIMARY KEY and FOREIGN KEY controls for table integrity.", 492, 480, 660, 38, { size: 13, color: C.muted });

  s = p.slides.add();
  title(s, "Why Medallion Architecture?", "The project uses Bronze, Silver and Gold layers because each stage has a different responsibility and audience.", "Lakehouse Rationale");
  const medRows = [
    ["Layer", "TalentFlow implementation", "Reference-backed purpose"],
    ["Bronze", "Extract each PostgreSQL table to raw versioned Parquet plus latest copy", "Preserve source fidelity, enable reprocessing and audit"],
    ["Silver", "Encrypt PII, normalize UUIDs, apply row_hash and SCD2 current flag", "Clean, validate, deduplicate and enrich detailed data"],
    ["Gold", "Build business KPIs and ML feature tables using DuckDB", "Serve domain-specific analytics, dashboards and ML-ready datasets"],
  ];
  miniTable(s, medRows, 70, 174, 1140, 82);
  text(s, "Design comparison: direct OLTP reporting is simpler, but it mixes operational load with analytics, loses historical versions, and makes privacy controls harder to isolate.", 90, 548, 1080, 35, { size: 17, bold: true, color: C.amber, align: "center" });

  s = p.slides.add();
  title(s, "Visual Evidence: Azure Lakehouse Containers", "The Azure storage account shows the medallion layout implemented as separate private containers for Bronze, Silver and Gold.", "Azure Evidence");
  await screenshotFrame(s, SHOTS.containers, 60, 145, 550, 245, "Storage account containers: bronze, silver and gold.", "cover");
  await screenshotFrame(s, SHOTS.bronzeFolders, 670, 145, 550, 245, "Bronze container stores raw table folders from PostgreSQL extraction.", "cover");
  await screenshotFrame(s, SHOTS.silverFolders, 60, 450, 550, 170, "Silver container stores secure/transformed table folders, including *_secure outputs.", "cover");
  await screenshotFrame(s, SHOTS.goldFolders, 670, 450, 550, 170, "Gold container stores business-facing KPI dataset folders.", "cover");

  s = p.slides.add();
  title(s, "Visual Evidence: Gold Versioned Parquet Outputs", "Gold outputs are written as versioned Parquet snapshots and latest copies, which supports repeated demo runs and reproducibility.", "Gold Evidence");
  await screenshotFrame(s, SHOTS.goldRuns, 60, 150, 560, 290, "salary_benchmarks has multiple run_datetime folders plus latest.", "cover");
  await screenshotFrame(s, SHOTS.goldFile, 665, 150, 560, 290, "Inside a run folder, the Gold parquet file is stored as a block blob.", "cover");
  card(s, 90, 515, 1090, 74, { fill: "#071421" });
  text(s, "Presentation talking point", 118, 536, 205, 22, { size: 15, bold: true, color: C.green });
  text(s, "This proves that the Gold layer is lake-first: each KPI dataset is materialized to Azure storage with traceable runtime partitions, and PostgreSQL publishing is only an optional dashboard cache.", 325, 532, 790, 34, { size: 13.5, color: C.muted });

  s = p.slides.add();
  title(s, "Bronze Layer: Raw Ingestion and Runtime Lineage", "Bronze is intentionally close to the source. It captures raw extracts and ties every table to the same run identifier.", "Bronze");
  card(s, 60, 170, 540, 380);
  label(s, "Implementation", 88, 198);
  bullet(s, [
    "Prefect task reads each configured PostgreSQL table with pandas SQL extraction.",
    "Each table is written to Azure Blob Storage as Parquet.",
    "Every run writes a versioned path and a latest copy.",
    "Shared run_datetime links Bronze, Silver and Gold outputs from the same execution.",
  ], 88, 240, 455, 56);
  card(s, 650, 170, 570, 380, { fill: "#071421" });
  label(s, "Path contract", 682, 198, C.green);
  text(s, "bronze/<table_name>/run_datetime=YYYYMMDD_HHMMSS/*.parquet\nbronze/<table_name>/latest/<table_name>.parquet\n\nThe same run_datetime is passed into Silver and Gold, giving traceability when demo runs execute every 2 minutes.", 682, 240, 480, 170, { size: 16, color: "#d8ecff", font: "Fira Code" });
  text(s, "Azure Data Lake Storage is built on Blob Storage and supports hierarchical directory organization for data lake workloads.", 682, 458, 455, 42, { size: 13, color: C.muted });

  s = p.slides.add();
  title(s, "Silver Layer: PII Protection and SCD Type 2 History", "Silver is where TalentFlow AI becomes analytically trustworthy: sensitive data is protected and changed candidate profiles are versioned.", "Silver");
  card(s, 60, 160, 360, 410);
  label(s, "Privacy controls", 88, 188, C.green);
  bullet(s, [
    "PII columns are encrypted before secure Parquet output.",
    "Numeric salary fields are cast to object/string before ciphertext assignment.",
    "Gold decrypts only the salary value required for aggregate KPI calculation.",
  ], 88, 230, 290, 66);
  card(s, 460, 160, 360, 410);
  label(s, "SCD2 mechanism", 488, 188, C.cyan);
  bullet(s, [
    "candidate_id is normalized even when Parquet returns UUID bytes.",
    "row_hash detects changes across tracked attributes.",
    "Changed keys close previous rows with end_date and is_current = false.",
    "New versions start with current timestamp and is_current = true.",
  ], 488, 230, 290, 56);
  card(s, 860, 160, 360, 410);
  label(s, "Why it matters", 888, 188, C.amber);
  bullet(s, [
    "Recruitment analytics need the state of the candidate at the time of decisions.",
    "Historical profile movement supports longitudinal analysis.",
    "Kimball-style dimensional thinking values clear grain and time-variant history.",
  ], 888, 230, 290, 66);
  text(s, "Mid-term debugging outcome: the pipeline was fixed to handle encrypted strings in numeric columns and UUID byte decoding in SCD2 comparison.", 80, 612, 1090, 26, { size: 16, color: C.text, align: "center" });

  s = p.slides.add();
  title(s, "Gold Layer: Business-Facing Analytical Datasets", "Gold converts secure Silver data into purpose-built recruitment KPIs that can be consumed by dashboards, BI tools and ML workflows.", "Gold Analytics");
  const goldRows = [
    ["Gold dataset", "Business question answered", "Implementation"],
    ["city_talent_score", "Where is candidate density high and what is avg salary by city?", "COUNT + AVG expected salary"],
    ["salary_benchmarks", "How do expected salaries vary by degree?", "Join candidates with education"],
    ["candidate_engagement", "Which candidates are active?", "Count login_logs per candidate"],
    ["interview_pipeline_funnel", "How many interviews by role, stage and status?", "Join schedules, jobs and stages"],
    ["job_hire_rate", "Which roles convert feedback into hires?", "Hire count / total feedback percentage"],
  ];
  miniTable(s, goldRows, 60, 165, 1160, 64);
  text(s, "Reference alignment: Kimball/Ross dimensional modeling focuses on business processes, grain, dimensions and facts. Gold tables in this project are intentionally domain-specific and query-ready.", 80, 605, 1090, 36, { size: 14, color: C.muted, align: "center" });

  s = p.slides.add();
  title(s, "DuckDB Analytical SQL Over Parquet", "DuckDB is used as lightweight analytical compute for Gold aggregation without making PostgreSQL do warehouse-style work.", "Analytical Compute");
  card(s, 60, 170, 500, 370);
  label(s, "Why DuckDB?", 88, 198);
  bullet(s, [
    "Reads Parquet files directly from temporary Silver downloads.",
    "Uses SQL joins and group-by logic for KPI generation.",
    "Keeps Gold generation lake-first; PostgreSQL publish is optional for dashboard caching.",
    "Simple to run locally during demo and easy to reason about in code.",
  ], 88, 240, 415, 56);
  card(s, 610, 170, 610, 370, { fill: "#071421" });
  label(s, "Representative Gold query pattern", 642, 198, C.green);
  text(s, "SELECT j.job_title,\n       COUNT(*) AS total_feedback,\n       SUM(CASE WHEN f.decision = 'Hire' THEN 1 ELSE 0 END) AS hire_count,\n       ROUND(100.0 * hire_count / COUNT(*), 2) AS hire_rate_pct\nFROM feedback f\nJOIN schedules s ON f.schedule_id = s.schedule_id\nJOIN jobs j ON s.job_id = j.job_id\nGROUP BY j.job_title;", 642, 238, 520, 215, { size: 13.5, color: "#d8ecff", font: "Fira Code" });

  s = p.slides.add();
  title(s, "Prefect Orchestration and 2-Minute Demo Schedule", "The pipeline is orchestrated as a full Bronze -> Silver -> Gold flow, with an interval deployment for examiner demonstration.", "Orchestration");
  card(s, 60, 170, 355, 370);
  label(s, "Flow structure", 88, 198);
  bullet(s, [
    "TalentFlow-Full-ELT creates or accepts a shared run_datetime.",
    "bronze_flow, silver_flow and gold_flow run in order.",
    "publish_postgres flag optionally caches Gold tables in analytics schema.",
  ], 88, 240, 285, 64);
  card(s, 460, 170, 355, 370);
  label(s, "Cloud demo deployment", 488, 198, C.green);
  bullet(s, [
    "Deployment name: talentflow-elt-every-2-min-demo.",
    "Interval: 120 seconds.",
    "Tags: talentflow, demo, etl.",
    "Prefect Cloud shows flow runs, state, failures and logs.",
  ], 488, 240, 285, 56);
  card(s, 860, 170, 355, 370);
  label(s, "Reference fit", 888, 198, C.amber);
  bullet(s, [
    "Prefect flows are decorated Python functions.",
    "Flow run states are tracked for observability.",
    "Deployments allow schedules and remote interaction.",
  ], 888, 240, 285, 64);
  text(s, "Demo command used: python scripts/serve_elt_prefect_cloud.py", 270, 600, 740, 24, { size: 16, color: C.cyan, font: "Fira Code", align: "center" });

  s = p.slides.add();
  title(s, "Visual Evidence: Prefect Cloud Orchestration", "The Cloud UI screenshots prove that the full ELT was deployed on an interval schedule and that nested Bronze, Silver and Gold flows completed.", "Prefect Evidence");
  await screenshotFrame(s, SHOTS.prefectDeployment, 55, 145, 555, 330, "Deployment view: every 2 minutes schedule, ready status and recent successful runs.", "cover");
  await screenshotFrame(s, SHOTS.prefectRuns, 670, 145, 555, 330, "Runs view: TalentFlow-Full-ELT triggers Bronze, Silver and Gold child flows.", "cover");
  card(s, 90, 540, 1090, 58, { fill: "#071421" });
  text(s, "How to explain it", 118, 558, 170, 22, { size: 15, bold: true, color: C.green });
  text(s, "For the demo, the examiner can see recurring flow runs, completed states, duration, parameters and task-run counts instead of only trusting terminal output.", 292, 554, 800, 28, { size: 13.5, color: C.muted });

  s = p.slides.add();
  title(s, "Machine Learning Workflow and Current Results", "The current ML goal is not to claim a final high-performing model; it is to prove a complete, repeatable predictive-intelligence workflow.", "Predictive Intelligence");
  metric(s, "0.5021", "Hire prediction accuracy", 60, 165, 250, C.cyan);
  metric(s, "0.3958", "Hire prediction F1", 330, 165, 250, C.green);
  metric(s, "0.5016", "Hire prediction ROC-AUC", 600, 165, 250, C.amber);
  metric(s, "1.2278", "Rating prediction MAE", 870, 165, 250, C.red);
  card(s, 60, 300, 535, 275);
  label(s, "Pipeline design", 88, 328);
  bullet(s, [
    "Feature query joins feedback, schedules, candidates, jobs, stages, education and login counts.",
    "ColumnTransformer handles numeric and categorical features.",
    "Random Forest classifier/regressor artifacts are saved with joblib.",
    "Feature importance CSVs are published to analytics.ml_feature_insights.",
  ], 88, 370, 440, 44);
  card(s, 645, 300, 575, 275);
  label(s, "Top hire-model feature importances", 675, 328, C.green);
  bars(s, [
    ["expected_salary", 0.0893],
    ["gpa", 0.0871],
    ["passing_year", 0.0658],
    ["login_count", 0.0579],
    ["state_Maharashtra", 0.0442],
  ], 675, 370, 500, 145, C.green);

  s = p.slides.add();
  title(s, "Visual Evidence: Gold KPI Dashboard and ML Insights", "This screen closes the loop: source data becomes Gold KPIs and model feature insights visible to the admin user.", "Dashboard Evidence");
  await screenshotFrame(s, SHOTS.goldDashboard, 55, 145, 800, 430, "Admin dashboard showing Gold Layer KPIs and ML Feature Insights from analytics outputs.", "cover");
  card(s, 900, 145, 315, 430);
  label(s, "What this proves", 928, 174, C.green);
  bullet(s, [
    "Gold KPIs are available inside the product, not only in backend files.",
    "Hire-rate by job is calculated from interview feedback outcomes.",
    "Feature insights are published from Random Forest artifacts into analytics output.",
    "The dashboard connects application, lakehouse, SQL analytics and ML into one reviewable flow.",
  ], 928, 216, 250, 52, { size: 12.5 });

  s = p.slides.add();
  title(s, "Why Random Forest First?", "For the mid-term stage, Random Forest is a sensible baseline because TalentFlow features are mostly structured/tabular recruitment signals.", "ML Rationale");
  card(s, 60, 165, 355, 390);
  label(s, "Breiman 2001", 88, 193);
  bullet(s, [
    "Random Forest combines many tree predictors.",
    "Generalization depends on individual tree strength and correlation.",
    "Variable importance is part of the method family.",
  ], 88, 235, 285, 64);
  card(s, 460, 165, 355, 390);
  label(s, "scikit-learn implementation", 488, 193, C.green);
  bullet(s, [
    "Pipeline prevents leakage by applying preprocessing inside training flow.",
    "ColumnTransformer keeps numeric and categorical transformations explicit.",
    "Class weight balancing is used for hire classification.",
  ], 488, 235, 285, 64);
  card(s, 860, 165, 355, 390);
  label(s, "Interpretation", 888, 193, C.amber);
  bullet(s, [
    "Current metrics are modest and honestly reported.",
    "The achievement is an end-to-end ML path, not final model maturity.",
    "Next work: stronger features, balanced labels, model cards and drift checks.",
  ], 888, 235, 285, 64);

  s = p.slides.add();
  title(s, "Natural-Language Analytics Roadmap", "The LLM/Text-to-SQL component is planned after the data platform is stable, so natural-language answers can be grounded in trusted Gold tables.", "Conversational AI");
  architectureLine(s, [
    ["User", "Recruiter asks business question"],
    ["Schema Context", "Gold table names, columns and business definitions"],
    ["LLM", "Intent parsing and SQL draft"],
    ["Guardrail", "Validate tables, columns, filters and read-only query"],
    ["Execution", "Run against Gold/analytics layer"],
    ["Answer", "Return explanation and KPI result"],
  ], 190);
  card(s, 80, 380, 520, 185);
  label(s, "Why not LLM-first?", 108, 408, C.red);
  bullet(s, [
    "A language model without trusted data produces impressive but unreliable answers.",
    "Gold tables give the model a governed semantic surface.",
    "Read-only SQL validation reduces operational risk.",
  ], 108, 450, 430, 38);
  card(s, 680, 380, 520, 185);
  label(s, "Reference connection", 708, 408, C.cyan);
  bullet(s, [
    "Vaswani et al. introduced Transformer attention foundations used by modern LLMs.",
    "In this project, LLMs are an interface layer, not the system of record.",
    "The trustworthy layer remains PostgreSQL + lakehouse + Gold validation.",
  ], 708, 450, 430, 38);

  s = p.slides.add();
  title(s, "Testing, Validation and Quality Gates", "Testing was implemented as a project safety layer, especially for Gold analytics and lakehouse contracts.", "Validation");
  const checks = [
    ["Schema", "analytics schema exists; expected columns are present"],
    ["Rows", "Gold tables are created and row counts are non-empty unless explicitly allowed"],
    ["Nulls/ranges", "Candidate counts, salaries, login counts and hire rates are checked"],
    ["Duplicates", "Candidate, job and funnel duplicate groups are detected"],
    ["Reconciliation", "Gold totals are matched back to source login, schedule and feedback counts"],
    ["Formula", "hire_rate_pct is recalculated and compared to stored Gold output"],
  ];
  checks.forEach((c, i) => {
    const x = 60 + (i % 2) * 590;
    const y = 165 + Math.floor(i / 2) * 112;
    card(s, x, y, 535, 82);
    text(s, c[0], x + 18, y + 15, 165, 24, { size: 16, bold: true, color: C.green });
    text(s, c[1], x + 185, y + 14, 310, 40, { size: 12.5, color: C.muted });
  });
  text(s, "Validation script: scripts/validate_gold_analytics.py", 370, 610, 540, 24, { size: 15, color: C.cyan, font: "Fira Code", align: "center" });

  s = p.slides.add();
  title(s, "Current Status and Remaining Work", "This slide aligns with the mid-term report timeline while making the progress easy to explain verbally.", "Project Plan");
  const phases = [
    ["Completed", "Dissertation outline", "5 May - 10 May 2026"],
    ["Completed", "Frontend + ETL development", "12 May - 5 June 2026"],
    ["Completed", "Testing Phase 1", "6 June - 20 June 2026"],
    ["Pending", "Text-to-SQL framework", "21 June - 30 June 2026"],
    ["Pending", "Conversational AI testing", "1 July - 7 July 2026"],
    ["Pending", "Dissertation review/submission", "9 July - 18 August 2026"],
  ];
  phases.forEach((p, i) => {
    const x = 75 + i * 190;
    card(s, x, 230, 160, 220, { fill: p[0] === "Completed" ? "#0c2b2c" : "#231b12", line: p[0] === "Completed" ? "#1f7b6a" : "#8a6731" });
    text(s, p[0], x + 18, 255, 124, 22, { size: 12, bold: true, color: p[0] === "Completed" ? C.green : C.amber, align: "center" });
    text(s, p[1], x + 14, 305, 132, 55, { size: 15, bold: true, align: "center" });
    text(s, p[2], x + 14, 382, 132, 30, { size: 11, color: C.muted, align: "center" });
  });
  text(s, "Mid-term position: the data platform foundation is implemented; the final phase is intelligence, usability validation and production hardening.", 105, 535, 1040, 40, { size: 18, color: C.text, align: "center" });

  s = p.slides.add();
  title(s, "Reference-Backed Design Decisions", "Each major technical decision is connected to a recognized method, official documentation or foundational paper.", "References");
  const refRows = [
    ["Decision", "Reference basis", "How it appears in TalentFlow AI"],
    ["Dimensional/Gold thinking", "Kimball & Ross, The Data Warehouse Toolkit", "Gold KPIs have business grain and reporting purpose"],
    ["Bronze/Silver/Gold", "Databricks medallion architecture concepts", "Raw -> secure/versioned -> business-ready datasets"],
    ["Relational constraints", "PostgreSQL documentation", "PK/FK/UNIQUE/CHECK controls in DDL.sql"],
    ["Cloud lake storage", "Microsoft Azure Data Lake Storage docs", "Blob-backed hierarchical lake folders and Parquet"],
    ["Workflow orchestration", "Prefect documentation", "Flows, deployments, schedules and Cloud UI monitoring"],
    ["Parquet analytics", "DuckDB documentation", "SQL joins/aggregations over Parquet-backed Silver data"],
    ["Predictive model", "Breiman Random Forests; scikit-learn docs", "Random Forest pipelines and feature importances"],
    ["Future LLM layer", "Vaswani et al., Attention Is All You Need", "Transformer/LLM foundation for Text-to-SQL interface"],
  ];
  miniTable(s, refRows, 45, 145, 1190, 53);

  s = p.slides.add();
  title(s, "Bibliography and Web Sources", "These are the concrete references used to connect the implementation choices to accepted data-engineering and AI foundations.", "Source List");
  card(s, 55, 150, 560, 440);
  label(s, "Books, papers and official docs", 85, 178, C.green);
  bullet(s, [
    "Ralph Kimball and Margy Ross, The Data Warehouse Toolkit.",
    "Databricks Docs: What is the medallion lakehouse architecture?",
    "PostgreSQL Docs: Data Definition - Constraints.",
    "Microsoft Learn: Introduction to Azure Data Lake Storage.",
    "Prefect Docs: Flows, deployments and schedules.",
    "DuckDB Docs: Parquet data support and read_parquet usage.",
    "Breiman, L. Random Forests. Machine Learning 45, 5-32 (2001).",
    "scikit-learn User Guide: Pipeline, ColumnTransformer, ensemble methods.",
    "Vaswani et al. Attention Is All You Need. arXiv:1706.03762.",
  ], 85, 222, 460, 34, { size: 11.5 });
  card(s, 665, 150, 560, 440);
  label(s, "URLs used for cross-checking", 695, 178, C.cyan);
  text(s, "https://docs.databricks.com/aws/en/lakehouse/medallion\nhttps://www.postgresql.org/docs/current/ddl-constraints.html\nhttps://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-introduction\nhttps://docs.prefect.io/v3/concepts/flows\nhttps://duckdb.org/docs/stable/data/parquet/overview\nhttps://link.springer.com/article/10.1023/A:1010933404324\nhttps://scikit-learn.org/stable/modules/compose.html\nhttps://scikit-learn.org/stable/modules/ensemble.html\nhttps://arxiv.org/abs/1706.03762", 695, 224, 485, 285, { size: 12.8, color: "#d8ecff", font: "Fira Code" });
  text(s, "The implementation-specific evidence is from D:/report/2024da04133.pdf and D:/TalentFlow_AI project files.", 696, 528, 475, 30, { size: 12.5, color: C.muted });

  s = p.slides.add();
  title(s, "Conclusion and Examiner Talking Points", "The project demonstrates a complete mid-term foundation: operational recruitment workflows, lakehouse ETL, validation, and AI readiness.", "Conclusion");
  card(s, 70, 180, 520, 330);
  label(s, "What is strong now", 100, 210, C.green);
  bullet(s, [
    "End-to-end working application and ELT foundation.",
    "Clear data separation: OLTP for workflow, lakehouse for analytics.",
    "SCD2 and PII handling show data engineering maturity.",
    "Gold validation and ML artifacts provide defensible evidence.",
  ], 100, 252, 430, 48);
  card(s, 690, 180, 520, 330);
  label(s, "What will make it final-ready", 720, 210, C.amber);
  bullet(s, [
    "Real UI screenshots replacing report placeholders.",
    "Text-to-SQL guardrails and conversational testing.",
    "Better ML features, model evaluation and model-card documentation.",
    "Security hardening: password hashing, stronger RBAC and alerts.",
  ], 720, 252, 430, 48);
  text(s, "Thank you. Questions?", 410, 590, 460, 42, { size: 31, bold: true, align: "center" });

  await fs.mkdir(QA, { recursive: true });
  for (const [i, slide] of p.slides.items.entries()) {
    const stem = `slide-${String(i + 1).padStart(2, "0")}`;
    await writeBlob(path.join(QA, `${stem}.png`), await p.export({ slide, format: "png", scale: 1 }));
    await fs.writeFile(path.join(QA, `${stem}.layout.json`), await (await slide.export({ format: "layout" })).text(), "utf-8");
  }
  await writeBlob(path.join(QA, "montage.webp"), await p.export({ format: "webp", montage: true, scale: 1 }));
  const pptx = await PresentationFile.exportPptx(p);
  await pptx.save(OUT);
  console.log(OUT);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
