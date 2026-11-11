import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const OUT = "D:/TalentFlow_AI/outputs/TalentFlow_AI_Final_Project_Presentation_2024DA04133.pptx";
const TMP = "D:/TalentFlow_AI/tmp_final_ppt/final_render";
const ASSET = "D:/TalentFlow_AI/tmp_final_ppt/template-inspect/assets/ppt/media";

const W = 1280;
const H = 720;
const C = {
  bg: "#07111f",
  panel: "#0d1b2d",
  panel2: "#10253a",
  line: "#1e3b55",
  text: "#e8f2ff",
  muted: "#9eb2c7",
  cyan: "#14c8ff",
  green: "#22d98f",
  amber: "#f7a52b",
  red: "#ff6b6b",
  white: "#ffffff",
};

const FONT = "Aptos";

async function writeBlob(file, blob) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  await fs.writeFile(file, new Uint8Array(await blob.arrayBuffer()));
}

async function readImage(name) {
  return fs.readFile(path.join(ASSET, name));
}

function line(fill = "none", width = 0) {
  return { style: "solid", fill, width };
}

function rect(slide, x, y, w, h, fill = C.panel, stroke = C.line) {
  return slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: line(stroke, 1),
    borderRadius: 8,
  });
}

function textbox(slide, text, x, y, w, h, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: line(),
  });
  shape.text = text;
  shape.text.style = {
    fontFace: FONT,
    fontSize: opts.size ?? 18,
    bold: opts.bold ?? false,
    color: opts.color ?? C.text,
    alignment: opts.align ?? "left",
  };
  return shape;
}

function chrome(slide, section, number) {
  slide.background.fill = C.bg;
  slide.shapes.add({ geometry: "rect", position: { left: 0, top: 713, width: 1280, height: 7 }, fill: C.cyan, line: line() });
  slide.shapes.add({ geometry: "rect", position: { left: 742, top: 713, width: 538, height: 7 }, fill: C.green, line: line() });
  textbox(slide, section.toUpperCase(), 845, 27, 370, 20, { size: 10, bold: true, color: C.muted, align: "right" });
  textbox(slide, `Slide ${number}`, 1168, 662, 52, 16, { size: 8, color: C.muted, align: "right" });
}

function heading(slide, section, title, subtitle, number) {
  chrome(slide, section, number);
  textbox(slide, title, 60, 54, 910, 62, { size: 31, bold: true });
  slide.shapes.add({ geometry: "rect", position: { left: 60, top: 117, width: 70, height: 3 }, fill: C.cyan, line: line() });
  if (subtitle) textbox(slide, subtitle, 60, 130, 1040, 38, { size: 14, color: C.muted });
}

function bulletList(slide, items, x, y, w, gap = 48, size = 17) {
  items.forEach((item, idx) => {
    const top = y + idx * gap;
    slide.shapes.add({ geometry: "ellipse", position: { left: x, top: top + 8, width: 8, height: 8 }, fill: idx % 2 ? C.green : C.cyan, line: line() });
    textbox(slide, item, x + 22, top, w - 22, gap - 2, { size, color: C.text });
  });
}

function card(slide, title, body, x, y, w, h, accent = C.cyan) {
  rect(slide, x, y, w, h, C.panel, C.line);
  slide.shapes.add({ geometry: "rect", position: { left: x, top: y, width: w, height: 4 }, fill: accent, line: line() });
  textbox(slide, title, x + 18, y + 20, w - 36, 28, { size: 16, bold: true, color: accent });
  textbox(slide, body, x + 18, y + 58, w - 36, h - 70, { size: 14, color: C.text });
}

async function addImage(slide, file, x, y, w, h, alt, fit = "contain") {
  slide.images.add({
    blob: await readImage(file),
    contentType: "image/png",
    alt,
    fit,
    position: { left: x, top: y, width: w, height: h },
    geometry: "roundRect",
    borderRadius: 6,
  });
}

function notes(slide, text) {
  slide.speakerNotes.textFrame.setText(text);
  slide.speakerNotes.setVisible(true);
}

function flowNode(slide, label, x, y, w, h, fill = C.panel, accent = C.cyan) {
  rect(slide, x, y, w, h, fill, C.line);
  textbox(slide, label, x + 12, y + 18, w - 24, h - 20, { size: 14, bold: true, color: accent, align: "center" });
}

function arrow(slide, x1, y1, x2, y2) {
  slide.shapes.add({
    geometry: "line",
    position: {
      left: Math.min(x1, x2),
      top: Math.min(y1, y2),
      width: Math.abs(x2 - x1),
      height: Math.abs(y2 - y1),
    },
    line: { style: "solid", fill: C.muted, width: 2, beginArrowType: "none", endArrowType: "triangle" },
  });
}

const p = Presentation.create({ slideSize: { width: W, height: H } });

// 1
{
  const s = p.slides.add();
  chrome(s, "Final Review", 1);
  textbox(s, "TalentFlow AI", 60, 135, 780, 74, { size: 43, bold: true });
  textbox(s, "Enterprise Candidate Relationship Management and Predictive Intelligence Ecosystem", 62, 215, 1000, 38, { size: 20, color: C.muted });
  textbox(s, "Final project presentation covering the implemented portal, PostgreSQL schema, Azure lakehouse, ML insights, validation, and NLP-based conversational analytics agent.", 62, 284, 960, 58, { size: 16, color: C.text });
  card(s, "2024DA04133", "BITS ID", 60, 515, 250, 94, C.cyan);
  card(s, "Final Submission", "WILP dissertation stage", 330, 515, 250, 94, C.green);
  card(s, "Altimetrik", "Host organization", 600, 515, 250, 94, C.amber);
  textbox(s, "Malikulashtar K Malampatiwalla", 60, 634, 520, 20, { size: 14, color: C.text });
  notes(s, "[Sources]\nLocal source deck used for styling: TalentFlow_AI_Professional_Mid_Term_With_Screenshots_2024DA04133.pptx\nFinal report: TalentFlow_AI_Final_Project_Report_2024DA04133.pdf");
}

// 2
{
  const s = p.slides.add();
  heading(s, "Narrative", "Final Presentation Roadmap", "The final review is structured to help the examiner see the problem, the implemented system, the intelligence layer, and the project evidence.", 2);
  const items = [
    ["1", "Why TalentFlow AI?", "Recruitment data fragmentation, historical profile loss, slow reporting, and privacy exposure."],
    ["2", "What was built", "Role-based portal, PostgreSQL schema, medallion ELT, Gold analytics, ML, and Ask Data."],
    ["3", "What is new after mid-term", "NLP semantic matcher, downloaded Hugging Face LLM mode, feedback memory, and SQL repair."],
    ["4", "How it is validated", "Gold reconciliation, contract tests, agent tests, ML metrics, and security controls."],
  ];
  items.forEach(([n, t, b], i) => {
    const x = i % 2 ? 645 : 70;
    const y = i < 2 ? 190 : 375;
    rect(s, x, y, 530, 128);
    textbox(s, n, x + 20, y + 22, 34, 34, { size: 20, bold: true, color: C.cyan, align: "center" });
    textbox(s, t, x + 70, y + 24, 420, 26, { size: 18, bold: true });
    textbox(s, b, x + 70, y + 60, 425, 48, { size: 14, color: C.muted });
  });
  notes(s, "[Sources]\nFinal report sections 1, 4, 8, 9 and 10.");
}

// 3
{
  const s = p.slides.add();
  heading(s, "Context", "The problem is not only hiring workflow, it is analytical trust", "TalentFlow AI converts operational recruitment events into secured, versioned, and explainable decision-support data.", 3);
  card(s, "Operational fragmentation", "Candidate profile, interview schedule, feedback, login, and education data often live in separate screens or spreadsheets.", 60, 200, 350, 270, C.cyan);
  card(s, "History loss", "Profile updates overwrite previous state unless audit and SCD2 logic capture change over time.", 465, 200, 350, 270, C.green);
  card(s, "Analytics bottleneck", "Hiring managers need KPIs and natural-language answers without waiting for manual SQL or exported reports.", 870, 200, 350, 270, C.amber);
  textbox(s, "Design implication: the project is a governed recruitment data product, not only a CRUD application.", 85, 560, 1080, 30, { size: 18, bold: true, color: C.cyan, align: "center" });
  notes(s, "[Sources]\nFinal report section 1: problem statement and objectives.");
}

// 4
{
  const s = p.slides.add();
  heading(s, "Objectives", "All core project objectives were completed", "The final build covers operational capture, engineering, analytics, intelligence, security, and validation.", 4);
  const rows = [
    ["Role-aware portal", "Candidate, admin, interviewer workflows", "Implemented"],
    ["Normalized database", "Recruitment entities with relationships", "Implemented"],
    ["Medallion ELT", "Bronze, Silver, Gold Parquet pipeline", "Implemented"],
    ["Privacy controls", "Fernet encryption and SCD2 history", "Implemented"],
    ["Predictive layer", "Random Forest models and feature insight publishing", "Implemented"],
    ["Conversational analytics", "NLP matcher, Hugging Face LLM, SQL repair, feedback memory", "Implemented"],
  ];
  rows.forEach((r, i) => {
    const y = 190 + i * 58;
    rect(s, 80, y, 1120, 46, i % 2 ? "#0a1728" : C.panel, C.line);
    textbox(s, r[0], 105, y + 13, 230, 22, { size: 15, bold: true, color: C.cyan });
    textbox(s, r[1], 360, y + 13, 620, 22, { size: 14, color: C.text });
    textbox(s, r[2], 1030, y + 13, 120, 22, { size: 14, bold: true, color: C.green, align: "center" });
  });
  notes(s, "[Sources]\nFinal report abstract, sections 3 and 8.");
}

// 5
{
  const s = p.slides.add();
  heading(s, "Architecture", "The final system separates workflow, lakehouse, analytics, and intelligence", "The architecture keeps operational transactions in PostgreSQL and moves analytical processing through governed lakehouse layers.", 5);
  await addImage(s, "image5.png", 55, 185, 760, 210, "Current architecture diagram from project deck");
  const layers = [
    "Streamlit portal captures candidate, admin, and interviewer activity.",
    "PostgreSQL stores normalized operational records.",
    "Bronze/Silver/Gold pipelines publish versioned Parquet outputs.",
    "DuckDB builds Gold metrics; dashboard and agent consume curated data.",
    "ML models and the Ask Data agent add predictive and conversational intelligence.",
  ];
  bulletList(s, layers, 865, 190, 350, 58, 14);
  textbox(s, "The system is intentionally modular: transactional concerns, analytical storage, model training, and natural-language querying are separated.", 85, 535, 1090, 40, { size: 16, color: C.cyan, align: "center" });
  notes(s, "[Sources]\nEmbedded architecture image from mid-term deck; final report section 4.");
}

// 6
{
  const s = p.slides.add();
  heading(s, "System Modules", "The implementation is broad but connected through one recruitment data model", "Each module contributes a specific business or engineering capability.", 6);
  const modules = [
    ["Candidate portal", "Registration, login, profile update, education and salary details"],
    ["Admin center", "Schedule interviews, inspect KPIs, view ML insights, run Ask Data"],
    ["Interviewer center", "Assigned interviews, rating, comments, hire/hold/reject decision"],
    ["Data lakehouse", "Bronze snapshots, Silver protection/history, Gold business datasets"],
    ["ML insights", "Hire, decision and rating models with feature importance"],
    ["Analytics agent", "Natural-language questions converted to safe read-only SQL"],
  ];
  modules.forEach(([t, b], i) => {
    const x = i % 2 ? 665 : 80;
    const y = 185 + Math.floor(i / 2) * 125;
    card(s, t, b, x, y, 500, 88, i % 3 === 0 ? C.cyan : i % 3 === 1 ? C.green : C.amber);
  });
  notes(s, "[Sources]\nProject source files: app/portal.py, pipelines, models/train_ml_insights.py, app/analytics_agent.py.");
}

// 7
{
  const s = p.slides.add();
  heading(s, "Visual Evidence", "The portal supports all three recruitment roles", "Screenshots show the implemented user-facing workflows rather than only design diagrams.", 7);
  await addImage(s, "image.png", 45, 185, 360, 150, "Candidate dashboard screenshot", "cover");
  await addImage(s, "image2.png", 460, 185, 360, 150, "Admin schedule screenshot", "cover");
  await addImage(s, "image4.png", 875, 185, 360, 150, "Interviewer feedback screenshot", "cover");
  await addImage(s, "image3.png", 260, 380, 760, 155, "Admin pipeline screenshot", "cover");
  textbox(s, "Candidate profile, admin scheduling, active pipeline review, and interviewer feedback form are all implemented in the Streamlit portal.", 85, 575, 1090, 34, { size: 16, color: C.cyan, align: "center" });
  notes(s, "[Sources]\nEmbedded screenshots from mid-term deck; final project app/portal.py.");
}

// 8
{
  const s = p.slides.add();
  heading(s, "Database Design", "The PostgreSQL schema is normalized around recruitment entities", "Clear relationships make both transactional workflow and analytics joins reliable.", 8);
  await addImage(s, "image6.png", 55, 178, 665, 420, "Entity relationship diagram");
  bulletList(s, [
    "Candidate identity, education, login, audit, jobs, interviewers, stages, schedules and feedback are separated.",
    "Schedules connect candidate, job, interviewer and stage.",
    "Feedback belongs to a scheduled interview and drives KPIs and ML labels.",
    "analytics.agent_interactions stores question, SQL, summaries, helpful flag and corrected SQL.",
  ], 780, 205, 390, 62, 15);
  notes(s, "[Sources]\nEmbedded ERD from mid-term deck; DDL.sql; final report section 5.");
}

// 9
{
  const s = p.slides.add();
  heading(s, "Data Engineering", "The medallion pipeline turns raw operations into governed analytics", "Bronze preserves snapshots, Silver protects and versions records, and Gold publishes business-ready KPIs.", 9);
  const x0 = 80, y = 275, w = 150, gap = 45;
  const labels = ["PostgreSQL", "Bronze", "Silver", "Gold", "Dashboard", "ML + Agent"];
  labels.forEach((l, i) => flowNode(s, l, x0 + i * (w + gap), y, w, 78, i === 5 ? "#332411" : C.panel, i === 5 ? C.amber : C.cyan));
  for (let i = 0; i < labels.length - 1; i++) arrow(s, x0 + i * (w + gap) + w, y + 39, x0 + (i + 1) * (w + gap), y + 39);
  card(s, "Bronze", "Raw snapshots with run_datetime lineage and latest copies.", 80, 445, 320, 110, C.cyan);
  card(s, "Silver", "PII encryption plus candidate history using SCD Type 2 logic.", 480, 445, 320, 110, C.green);
  card(s, "Gold", "DuckDB aggregates city, salary, engagement, funnel and hire-rate datasets.", 880, 445, 320, 110, C.amber);
  notes(s, "[Sources]\nFinal report section 7; pipelines/elt_bronze.py, pipelines/elt_silver.py, pipelines/elt_gold.py.");
}

// 10
{
  const s = p.slides.add();
  heading(s, "Lakehouse Evidence", "Azure Blob containers store versioned Parquet outputs", "The screenshots show Bronze, Silver, and Gold folders produced by the pipeline.", 10);
  await addImage(s, "image7.png", 50, 182, 350, 130, "Azure container root", "cover");
  await addImage(s, "image8.png", 465, 182, 350, 130, "Bronze folders", "cover");
  await addImage(s, "image9.png", 880, 182, 350, 130, "Silver folders", "cover");
  await addImage(s, "image10.png", 50, 370, 350, 130, "Gold folders", "cover");
  await addImage(s, "image11.png", 465, 370, 350, 130, "Gold versioned run", "cover");
  await addImage(s, "image12.png", 880, 370, 350, 130, "Latest output", "cover");
  textbox(s, "Evidence point: each layer has both run-level lineage and current analytical consumption paths.", 85, 555, 1090, 32, { size: 16, color: C.cyan, align: "center" });
  notes(s, "[Sources]\nEmbedded Azure screenshots from mid-term deck; final report section 7.");
}

// 11
{
  const s = p.slides.add();
  heading(s, "Gold Analytics", "Gold datasets convert recruitment activity into business questions", "The dashboard consumes curated tables instead of forcing managers to inspect raw transactional rows.", 11);
  const rows = [
    ["city_talent_score", "Which cities have stronger candidate pipelines?"],
    ["salary_benchmarks", "How do expected salaries vary by education?"],
    ["candidate_engagement", "Which candidates are active or inactive?"],
    ["interview_pipeline_funnel", "Where is the interview process slowing down?"],
    ["job_hire_rate", "Which jobs have better hire recommendation rates?"],
  ];
  rows.forEach((r, i) => {
    const y = 190 + i * 62;
    rect(s, 100, y, 1080, 48, i % 2 ? "#0a1728" : C.panel, C.line);
    textbox(s, r[0], 130, y + 14, 300, 22, { size: 15, bold: true, color: C.cyan });
    textbox(s, r[1], 480, y + 14, 610, 22, { size: 15, color: C.text });
  });
  notes(s, "[Sources]\nFinal report section 7.3; pipelines/elt_gold.py; scripts/validate_gold_analytics.py.");
}

// 12
{
  const s = p.slides.add();
  heading(s, "Dashboard Evidence", "Admins can view KPIs and ML feature insights in one place", "The dashboard joins lakehouse outputs, PostgreSQL cache tables, and model artifacts for business-facing consumption.", 12);
  await addImage(s, "image15.png", 55, 185, 780, 380, "Gold KPI dashboard and ML feature insights screenshot", "cover");
  card(s, "What it proves", "The final product is not limited to backend pipelines. It exposes analytics through a usable admin interface.", 875, 200, 300, 120, C.cyan);
  card(s, "Decision support", "Feature insight tables help explain model behavior without replacing human judgement.", 875, 360, 300, 120, C.green);
  notes(s, "[Sources]\nEmbedded dashboard screenshot from mid-term deck; final report section 8.1.");
}

// 13
{
  const s = p.slides.add();
  heading(s, "Predictive Intelligence", "The ML layer creates three decision-support models", "The models are treated as prototypes for insight and explanation, not automatic hiring decision makers.", 13);
  card(s, "hire_prediction", "Accuracy 0.7552\nF1 0.8427\nROC-AUC 0.8262\nSupport 241", 80, 210, 310, 210, C.cyan);
  card(s, "decision_prediction", "Accuracy 0.7884\nWeighted F1 0.8165\nClasses: Hire, Hold, Reject\nSupport 241", 485, 210, 310, 210, C.green);
  card(s, "rating_prediction", "MAE 0.3017\nR2 0.5309\nSupport 241\nMean rating 4.4995", 890, 210, 310, 210, C.amber);
  textbox(s, "Pipeline: joined recruitment features -> preprocessing -> Random Forest training -> artifacts -> analytics.ml_feature_insights -> dashboard.", 95, 515, 1090, 44, { size: 17, color: C.cyan, align: "center" });
  notes(s, "[Sources]\nmodels/artifacts/20260708_065754/metrics.json; final report section 8.1.");
}

// 14
{
  const s = p.slides.add();
  heading(s, "Model Interpretation", "Random Forest was chosen as a strong tabular baseline", "It supports mixed recruitment features and produces feature-importance signals that are easy to present to admins.", 14);
  bulletList(s, [
    "Handles numeric and categorical recruitment variables after preprocessing.",
    "Works well as a practical baseline for tabular decision-support problems.",
    "Publishes feature importance so admins can see influential signals.",
    "Limitations are acknowledged: demo data size, bias risk, and the need for fairness/drift checks before production.",
  ], 90, 205, 500, 70, 17);
  card(s, "Feature examples", "city, state, country, degree, university, expected salary, passing year, GPA, login count, job title, department, stage", 680, 210, 440, 220, C.green);
  card(s, "Human review remains mandatory", "Model outputs are advisory. Final hiring decisions must remain transparent, policy-compliant, and reviewed by people.", 680, 470, 440, 120, C.amber);
  notes(s, "[Sources]\nFinal report sections 8.1 and Appendix C; scikit-learn Random Forest documentation cited in the report.");
}

// 15
{
  const s = p.slides.add();
  heading(s, "New Final Aspect", "The Ask Data module adds a conversational analytics layer", "Admins can ask recruitment questions in natural language and receive safe SQL-backed answers with tables or charts.", 15);
  card(s, "Natural-language input", "Example: Which candidates have high ratings but were not hired?", 70, 230, 250, 110, C.cyan);
  card(s, "Agent plan", "The router chooses fast local NLP, Hugging Face local LLM, optional cloud AI, or fallback SQL.", 370, 230, 250, 110, C.green);
  card(s, "Safe execution", "SQL is sanitized, limited, executed read-only, and optionally repaired once in Hugging Face mode.", 670, 230, 250, 110, C.amber);
  card(s, "Learning loop", "Question, SQL, summary, helpful flag, and corrected SQL are stored for future reuse.", 970, 230, 250, 110, C.cyan);
  textbox(s, "This is a major improvement over the mid-term plan: Text-to-SQL is now implemented with local NLP and downloaded LLM support.", 85, 515, 1090, 44, { size: 18, bold: true, color: C.green, align: "center" });
  notes(s, "[Sources]\napp/analytics_agent.py, app/local_sql_model.py, app/huggingface_sql_agent.py, app/portal.py; final report section 8.2.");
}

// 16
{
  const s = p.slides.add();
  heading(s, "NLP + Hugging Face", "Fast local matching keeps demos responsive, while local LLM mode handles harder questions", "The system avoids depending only on paid cloud AI or slow model generation.", 16);
  flowNode(s, "Admin question", 80, 265, 150, 74, C.panel, C.cyan);
  flowNode(s, "Schema + learned examples", 280, 265, 190, 74, C.panel, C.green);
  flowNode(s, "Fast local NLP matcher", 520, 220, 190, 74, C.panel, C.cyan);
  flowNode(s, "Downloaded Hugging Face LLM", 520, 350, 220, 74, "#332411", C.amber);
  flowNode(s, "Sanitized PostgreSQL SELECT", 790, 265, 210, 74, C.panel, C.green);
  flowNode(s, "Answer + visualization", 1050, 265, 160, 74, C.panel, C.cyan);
  arrow(s, 230, 302, 280, 302);
  arrow(s, 470, 302, 520, 257);
  arrow(s, 470, 302, 520, 387);
  arrow(s, 710, 257, 790, 302);
  arrow(s, 740, 387, 790, 302);
  arrow(s, 1000, 302, 1050, 302);
  bulletList(s, [
    "LOCAL_AGENT_SPEED_MODE defaults to fast local SQL before slow LLM generation.",
    "LOCAL_ALLOW_SLOW_LLM enables slower Hugging Face fallback when local confidence is low.",
    "Default local model: Qwen/Qwen2.5-Coder-1.5B-Instruct through Transformers text-generation pipeline.",
  ], 105, 505, 1020, 36, 15);
  notes(s, "[Sources]\napp/analytics_agent.py and app/huggingface_sql_agent.py; Hugging Face Transformers/Qwen references cited in final report.");
}

// 17
{
  const s = p.slides.add();
  heading(s, "Agent Safety", "The assistant is designed to be useful without being dangerous", "Generated SQL is never trusted directly; the same sanitizer protects pasted SQL, local NLP SQL, cloud SQL, and Hugging Face SQL.", 17);
  const safety = [
    ["Read-only", "Only SELECT or WITH queries are allowed."],
    ["Single statement", "Multiple semicolon-separated statements are rejected."],
    ["Blocked mutations", "INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, COPY, GRANT and REVOKE are blocked."],
    ["Sensitive fields", "Password and secret fields are not allowed in assistant output."],
    ["Bounded output", "A LIMIT is added when missing to reduce accidental large scans."],
    ["Feedback memory", "Useful answers and corrected SQL teach future examples."],
  ];
  safety.forEach(([t, b], i) => card(s, t, b, i % 3 * 380 + 80, 190 + Math.floor(i / 3) * 180, 320, 120, i % 2 ? C.green : C.cyan));
  notes(s, "[Sources]\napp/analytics_assistant.py, app/analytics_agent.py; final report section 8.2.4.");
}

// 18
{
  const s = p.slides.add();
  heading(s, "Agent Demonstration", "The question bank is aligned with real recruitment decisions", "These questions are ready to use during viva or project demonstration.", 18);
  const qs = [
    "Give me a hiring summary with the main KPIs.",
    "Which cities have the strongest candidate pipeline?",
    "Which candidates have high ratings but were not hired?",
    "Which jobs have the best hire rate and enough feedback?",
    "Which interviewers have the highest pending feedback workload?",
    "Which degrees are associated with better ratings?",
    "Which active candidates have not logged in recently?",
    "What are the top ML feature insights and what should I do next?",
  ];
  qs.forEach((q, i) => {
    const x = i % 2 ? 650 : 80;
    const y = 185 + Math.floor(i / 2) * 88;
    rect(s, x, y, 520, 58, C.panel, C.line);
    textbox(s, q, x + 20, y + 15, 480, 26, { size: 15, color: C.text });
  });
  notes(s, "[Sources]\napp/portal.py example_questions; outputs/TalentFlow_AI_Agent_Question_Bank.md.");
}

// 19
{
  const s = p.slides.add();
  heading(s, "Testing", "Validation covers schema, data quality, contracts, and the new agent", "The final project includes tests for both the data product and the conversational analytics layer.", 19);
  const tests = [
    ["Gold validation", "Row counts, nulls, duplicates, ranges, formulas, reconciliation"],
    ["Project contracts", "SCD2, versioned lake paths, Hive tables, dashboard exposure"],
    ["Agent tests", "Local matching, Hugging Face prompt parsing, response extraction, fallback narration"],
    ["Latest result", "10 targeted agent tests passed after the final update"],
  ];
  tests.forEach(([t, b], i) => card(s, t, b, i % 2 ? 650 : 80, 200 + Math.floor(i / 2) * 180, 500, 120, i === 3 ? C.green : C.cyan));
  textbox(s, "Verification command result: 10 passed across huggingface_sql_agent, analytics_agent, and local_sql_model tests.", 85, 570, 1090, 30, { size: 16, color: C.green, align: "center" });
  notes(s, "[Sources]\ntests/test_huggingface_sql_agent.py, tests/test_analytics_agent.py, tests/test_local_sql_model.py; local verification run on 2026-07-27.");
}

// 20
{
  const s = p.slides.add();
  heading(s, "Security", "Privacy and governance are built into the pipeline and assistant", "The project handles sensitive data carefully at the analytics boundary and prevents unsafe assistant operations.", 20);
  bulletList(s, [
    "Fernet encryption protects selected PII before Silver publication.",
    "SCD Type 2 candidate history preserves changes instead of overwriting analytical memory.",
    "Read-only SQL guardrails reduce risk in the conversational agent.",
    "run_datetime lake paths provide lineage and reproducibility.",
    "Production recommendations include Key Vault, formal RBAC, password hashing, CI, monitoring, model cards, fairness checks, and drift monitoring.",
  ], 95, 190, 1020, 68, 17);
  notes(s, "[Sources]\nutils/crypto_utils.py, pipelines/elt_silver.py, app/analytics_assistant.py; final report section 10.");
}

// 21
{
  const s = p.slides.add();
  heading(s, "Results", "The final outcome is a working recruitment intelligence foundation", "The project demonstrates end-to-end data engineering plus data science, not isolated scripts.", 21);
  const outcomes = [
    ["Operational workflows", "Registration, profile update, scheduling, feedback"],
    ["Lakehouse pipeline", "Bronze, Silver, Gold, Azure Parquet, external table readiness"],
    ["Analytics products", "Gold KPIs, dashboard, validation, reconciliation"],
    ["Predictive intelligence", "ML models, feature importance, decision-support framing"],
    ["Conversational analytics", "NLP matcher, Hugging Face LLM, SQL safety, feedback memory"],
  ];
  outcomes.forEach(([t, b], i) => card(s, t, b, 80 + (i % 3) * 380, i < 3 ? 200 : 400, 320, 125, i % 2 ? C.green : C.cyan));
  notes(s, "[Sources]\nFinal report conclusion and appendices; local project implementation.");
}

// 22
{
  const s = p.slides.add();
  heading(s, "Limitations", "The project is strong as a prototype, with clear production next steps", "Acknowledging limits improves credibility and shows engineering maturity.", 22);
  card(s, "Current limitations", "Demo-oriented data size\nEmail-domain role checks\nPrototype ML evaluation\nLocal LLM can be slow on CPU\nNo production CI/CD yet", 95, 210, 460, 260, C.amber);
  card(s, "Recommended hardening", "Identity provider and RBAC\nAzure Key Vault\nArgon2/bcrypt passwords\nDeployment automation\nMonitoring, fairness and drift checks", 725, 210, 460, 260, C.green);
  textbox(s, "Positioning: the submitted system is a complete academic project and a realistic foundation for productionization.", 85, 550, 1090, 32, { size: 17, color: C.cyan, align: "center" });
  notes(s, "[Sources]\nFinal report sections 10 and 11.");
}

// 23
{
  const s = p.slides.add();
  heading(s, "Viva Talking Points", "Use these points to explain the project confidently", "The answers connect implementation choices to business and engineering value.", 23);
  card(s, "Why medallion?", "It separates raw capture, protected history, and trusted business metrics.", 70, 200, 350, 130, C.cyan);
  card(s, "Why DuckDB?", "It can query Parquet directly and works well for lake-first Gold aggregation.", 465, 200, 350, 130, C.green);
  card(s, "Why Random Forest?", "It is a strong tabular baseline and gives feature-importance outputs.", 860, 200, 350, 130, C.amber);
  card(s, "Why local NLP + LLM?", "The local matcher keeps common questions fast; Hugging Face mode handles harder Text-to-SQL without paid cloud AI.", 70, 390, 540, 150, C.cyan);
  card(s, "What is the main contribution?", "An integrated recruitment data product combining OLTP workflows, lakehouse engineering, privacy, ML, and conversational analytics.", 670, 390, 540, 150, C.green);
  notes(s, "[Sources]\nFinal report sections 4, 7, 8, 9 and 11.");
}

// 24
{
  const s = p.slides.add();
  chrome(s, "Closing", 24);
  textbox(s, "Conclusion", 60, 90, 780, 70, { size: 42, bold: true });
  textbox(s, "TalentFlow AI successfully demonstrates a complete recruitment intelligence data product: operational workflows, governed lakehouse pipelines, validated analytics, machine-learning insights, and an NLP-based analytics agent.", 62, 180, 980, 86, { size: 21, color: C.text });
  card(s, "Best examiner takeaway", "This project combines data engineering, data science, privacy, validation, and practical business usability in one coherent system.", 80, 350, 520, 150, C.green);
  card(s, "Thank you", "Questions and discussion", 680, 350, 420, 150, C.cyan);
  textbox(s, "Malikulashtar K Malampatiwalla | 2024DA04133", 60, 635, 560, 20, { size: 14, color: C.muted });
  notes(s, "[Sources]\nFinal report conclusion.");
}

await fs.mkdir(TMP, { recursive: true });
for (const [i, slide] of p.slides.items.entries()) {
  const stem = `slide-${String(i + 1).padStart(2, "0")}`;
  await writeBlob(path.join(TMP, `${stem}.png`), await p.export({ slide, format: "png", scale: 1 }));
  await fs.writeFile(path.join(TMP, `${stem}.layout.json`), await (await slide.export({ format: "layout" })).text());
}
await writeBlob(path.join(TMP, "montage.webp"), await p.export({ format: "webp", montage: true, scale: 1 }));
const pptx = await PresentationFile.exportPptx(p);
await pptx.save(OUT);
console.log(OUT);
