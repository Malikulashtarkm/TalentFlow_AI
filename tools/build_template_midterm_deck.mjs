import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "file:///C:/Users/Acer/AppData/Local/Temp/codex-presentations/talentflow-template-follow/tmp/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const TMP_DIR = "C:/Users/Acer/AppData/Local/Temp/codex-presentations/talentflow-template-follow/tmp";
const TEMPLATE_PPTX = "C:/Users/Acer/AppData/Local/Temp/codex-presentations/talentflow-template-follow/tmp/template-starter.pptx";
const FINAL_PPTX = "D:/TalentFlow_AI/outputs/TalentFlow_AI_Mid_Term_Template_Aligned_2024DA04133.pptx";
const QA_DIR = path.join(TMP_DIR, "qa-final");

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

const slideText = [
  [
    "TALENTFLOW AI | MID-TERM REVIEW",
    "TalentFlow AI: Mid-Term Project Review",
    "Recruitment intelligence platform combining Streamlit portals, PostgreSQL OLTP, Azure lakehouse ETL, Gold KPIs, and predictive AI foundations.",
    "STUDENT NAME:\nMalikulashtar K Malampatiwalla\nBITS ID:\n2024DA04133",
    "Academic Program\nM.Tech in Data Science & Data Engineering\nBITS Pilani",
    "Project Stage\nMid-Term Evaluation\nFrontEnd + ETL Proof of Concept",
    "Host Organization\nAltimetrik Pvt Ltd\nBangalore, India",
  ],
  [
    "TALENTFLOW AI | CONTEXT & PROBLEM DEFINITION",
    'The Business Problem (The "Why")',
    'Presenter Notes: "The project is not only a portal. It solves fragmented recruitment data by preserving candidate history, preparing trusted analytics, and reducing dependency on manually written SQL reports."',
    "The Gap",
    "Recruitment data sits across candidate screens, interview feedback, admin actions, and reports. Important history is lost when systems only keep the latest record.",
    "The Bottleneck",
    "Useful questions such as funnel movement, skill demand, and candidate quality require SQL knowledge or manual exports, slowing decision cycles.",
    "The Need",
    "A governed lakehouse that separates raw, refined, and business-ready data, then exposes KPIs and future natural-language analytics to recruiters.",
  ],
  [
    "TALENTFLOW AI | STRATEGIC OBJECTIVES",
    "Project Objectives",
    'Presenter Notes: "The objectives separate operational reliability from analytical scale: PostgreSQL runs the app, while the lakehouse preserves history and powers reporting and AI."',
    "Engineering Objectives",
    "Intelligence Objectives",
    "Build role-based Streamlit portals backed by a normalized PostgreSQL schema for candidate, interviewer, admin, and feedback workflows.",
    "Implement Bronze, Silver, and Gold lakehouse layers on Azure storage with repeatable Parquet snapshots and SCD Type 2 history.",
    "Use Prefect Cloud for scheduled orchestration and visibility, with DuckDB for analytical SQL over Parquet datasets.",
    "Create Gold KPIs and a Random Forest baseline for candidate outcome intelligence and feature-importance explanation.",
    "Prepare the foundation for a Text-to-SQL conversational layer so non-technical users can ask recruitment questions naturally.",
  ],
  [
    "TALENTFLOW AI | CURRENT ARCHITECTURE",
    "Current System Architecture",
    'Presenter Notes: "The architecture follows a medallion pattern: Bronze captures source snapshots, Silver secures and versions records, Gold serves KPIs and ML features."',
    "Streamlit + OLTP",
    "Candidate, interviewer, and admin screens write operational records to Azure PostgreSQL.",
    "Prefect Cloud",
    "Schedules the ELT every few minutes during demo and monitors each Bronze, Silver, and Gold run.",
    "Bronze Parquet",
    "Stores raw source extracts and latest copies for traceable ingestion from PostgreSQL.",
    "Silver Secure",
    "Applies PII encryption, row hashing, SCD Type 2 versioning, and current-record flags.",
    "Gold + BI",
    "Publishes recruitment KPIs, funnel metrics, and feature tables for dashboards and ML.",
    "AI Layer",
    "Uses Gold features for ML training now, with Text-to-SQL planned as the final interaction layer.",
  ],
  [
    "TALENTFLOW AI | CORE DIMENSIONAL MODELING",
    "Data Engineering Deep Dive (SCD Type 2)",
    'Presenter Notes: "SCD Type 2 matters because recruitment decisions depend on the timeline of changes, not just the final value. This follows dimensional modeling guidance from Kimball and Ross."',
    "The Challenge",
    "Track profile, stage, salary, and feedback changes without deleting the earlier state that explains the candidate journey.",
    "The Solution",
    "Silver creates new active versions when row_hash changes, closes old rows with end_date, and keeps is_current for fast reporting.",
    "Key Database Enablers",
    "Business Key: Candidate IDs connect operational records to historical versions across pipeline runs.",
    "Effective Dates: start_date and end_date preserve point-in-time validity for every version.",
    "Privacy Controls: encrypted PII columns are isolated before serving analytics-ready Gold data.",
  ],
  [
    "TALENTFLOW AI | REFERENCE-BACKED DESIGN",
    "Modern Data Stack: Why This Stack?",
    "Orchestration",
    "Prefect Cloud",
    "Compute",
    "DuckDB",
    "Storage",
    "Azure ADLS Gen2",
    "Compared with manual scripts, Prefect gives scheduled runs, task visibility, retries, and Cloud UI evidence.",
    "The 2-minute demo schedule proves repeated ELT loads without manually starting every step.",
    "Compared with querying only OLTP, DuckDB reads Parquet directly and keeps analytics separate from app traffic.",
    "This supports Kimball-style business marts while keeping transformation logic lightweight and reproducible.",
    "Compared with flat local files, Azure storage supports cloud-scale lakehouse folders and versioned Parquet.",
    "Bronze/Silver/Gold design aligns with medallion architecture and Azure data lake patterns.",
    "→",
    "→",
    "→",
    "→",
    "→",
    "→",
  ],
  [
    "TALENTFLOW AI | AI ENGINEERING LAYER",
    "AI & Predictive Intelligence",
    "Conversational Analytics (Planned)",
    "The Text-to-SQL layer will translate recruiter questions into governed SQL over Gold tables, using LLM foundations from Transformer research.",
    "Predictive Engine",
    "Goal: estimate recruitment outcome signals such as candidate conversion, decision probability, or quality indicators.",
    "Features: engagement activity, role fit, salary gap, experience band, feedback ratings, and funnel-stage behaviour.",
    "Current baseline: Random Forest via scikit-learn because it is robust, interpretable, and suitable for tabular data.",
    'Recruiter asks: "Which candidates are strongest for this role?"',
    "LLM interprets intent, entities, and filters.",
    "Text-to-SQL agent generates a controlled SQL query.",
    "Gold tables return auditable results and explanation-ready KPIs.",
  ],
  [
    "TALENTFLOW AI | PORTAL ENVIRONMENTS",
    "Role-Based Product Ecosystem",
    'Presenter Notes: "The application layer is deliberately role-based. Each portal creates operational events that later become analytical signals in the lakehouse."',
    "Candidate Portal",
    "Supports registration, profile capture, login behaviour, and candidate-side interaction data.",
    "Interviewer Portal",
    "Captures interview schedules, structured feedback, ratings, and decision-support inputs.",
    "Admin Center",
    "Manages users, recruitment operations, dashboards, and visibility into ETL and Gold KPIs.",
    "Governance",
    "Separates PII, applies encrypted Silver processing, and prepares for stronger RBAC and audit controls.",
  ],
  [
    "TALENTFLOW AI | MID-TERM PROGRESS",
    "Current Progress (Proof of Concept)",
    "Abstract and outline report completed and submitted.",
    "Streamlit frontend screens completed for Candidate, Interviewer, and Admin roles.",
    "Azure PostgreSQL schema and sample recruitment data successfully loaded.",
    "Bronze, Silver, and Gold ETL pipeline implemented with scheduled Prefect runs.",
    "Testing Phase 1 completed for frontend and ETL; pipeline failures debugged and refreshed.",
    "600+",
    "Simulated Candidate Records",
    "Used to demonstrate operational screens, recurring ELT loads, Gold KPIs, and ML feature readiness.",
  ],
  [
    "TALENTFLOW AI | TIMELINE & FUTURE SCOPE",
    "Roadmap & Future Work",
    'Presenter Notes: "The mid-term milestone proves the app and ETL foundation. The remaining work moves from reliable data movement toward conversational intelligence and final validation."',
    "Phase 3",
    "Text-to-SQL framework: define safe prompts, schema context, SQL validation, and response formatting.",
    "Phase 4",
    "Conversational AI testing: check query correctness, guardrails, latency, and recruiter usability.",
    "Phase 5",
    "Final dissertation review: consolidate screenshots, ER diagram, architecture, metrics, and testing evidence.",
    "Production Readiness",
    "Improve password security, RBAC hardening, pipeline alerts, model tracking, and monitoring dashboards.",
  ],
  [
    "TALENTFLOW AI | DEFENDING PROJECT THESIS",
    "Conclusion & Q&A",
    'Presenter Notes: "Thank you. I am now open to your questions."',
    "TalentFlow AI demonstrates how a recruitment application can evolve into a governed analytics and AI ecosystem.",
    "The design is defensible: PostgreSQL for transactional integrity, medallion lakehouse for trusted analytics, Prefect for orchestration, DuckDB for Parquet SQL, and ML/LLM layers for decision intelligence.",
    "Questions?",
    "Thank you for your attention.",
  ],
];

async function main() {
  await fs.mkdir(QA_DIR, { recursive: true });
  const presentation = await PresentationFile.importPptx(await FileBlob.load(TEMPLATE_PPTX));

  for (let slideIndex = 0; slideIndex < slideText.length; slideIndex += 1) {
    const slide = presentation.slides.items[slideIndex];
    const editable = slide.shapes.items.filter((shape) => shape.text && String(shape.text).trim());
    if (editable.length !== slideText[slideIndex].length) {
      console.warn(`Slide ${slideIndex + 1}: expected ${slideText[slideIndex].length} text boxes, found ${editable.length}`);
    }

    for (let i = 0; i < Math.min(editable.length, slideText[slideIndex].length); i += 1) {
      editable[i].text = slideText[slideIndex][i];
    }

    const stem = `slide-${String(slideIndex + 1).padStart(2, "0")}`;
    await writeBlob(path.join(QA_DIR, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 1 }));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(QA_DIR, `${stem}.layout.json`), await layout.text(), "utf-8");
  }

  await writeBlob(
    path.join(QA_DIR, "final-montage.webp"),
    await presentation.export({ format: "webp", montage: true, scale: 1 }),
  );

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(FINAL_PPTX);
  console.log(FINAL_PPTX);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
