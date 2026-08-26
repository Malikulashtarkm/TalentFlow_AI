from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT_DIR = Path(r"D:\TalentFlow_AI\outputs\generated_report_figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 2200, 1050
BG = (248, 250, 252)
INK = (24, 37, 52)
MUTED = (82, 96, 111)
BLUE = (31, 78, 121)
CYAN = (9, 165, 196)
GREEN = (31, 150, 105)
AMBER = (211, 143, 36)
ORANGE = (218, 104, 43)
RED = (190, 76, 70)
CARD = (255, 255, 255)
PANEL = (239, 246, 251)
LINE = (177, 194, 211)


def font(size, bold=False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def text_height(draw, text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[3] - box[1]


def wrap(draw, text, fnt, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textbbox((0, 0), test, font=fnt)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw, xy, text, fnt, fill, max_width, gap=8):
    x, y = xy
    for line in wrap(draw, text, fnt, max_width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += text_height(draw, line, fnt) + gap
    return y


def rounded(draw, box, fill=CARD, outline=LINE, radius=14, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(draw, start, end, color=BLUE, width=4):
    sx, sy = start
    ex, ey = end
    draw.line([start, end], fill=color, width=width)
    if abs(ex - sx) >= abs(ey - sy):
        if ex >= sx:
            pts = [(ex, ey), (ex - 15, ey - 8), (ex - 15, ey + 8)]
        else:
            pts = [(ex, ey), (ex + 15, ey - 8), (ex + 15, ey + 8)]
    else:
        if ey >= sy:
            pts = [(ex, ey), (ex - 8, ey - 15), (ex + 8, ey - 15)]
        else:
            pts = [(ex, ey), (ex - 8, ey + 15), (ex + 8, ey + 15)]
    draw.polygon(pts, fill=color)


def dashed_line(draw, start, end, color=GREEN, width=3, dash=16, gap=10):
    sx, sy = start
    ex, ey = end
    length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    if length == 0:
        return
    dx = (ex - sx) / length
    dy = (ey - sy) / length
    dist = 0
    while dist < length:
        seg_end = min(dist + dash, length)
        draw.line(
            [
                (sx + dx * dist, sy + dy * dist),
                (sx + dx * seg_end, sy + dy * seg_end),
            ],
            fill=color,
            width=width,
        )
        dist += dash + gap


def card(draw, box, title, body, color=BLUE, fill=CARD):
    x1, y1, x2, y2 = box
    rounded(draw, box, fill=fill, outline=LINE, radius=14, width=2)
    draw.rectangle((x1, y1, x2, y1 + 8), fill=color)
    draw.text((x1 + 18, y1 + 26), title, font=font(22, True), fill=BLUE if color != ORANGE else ORANGE)
    draw_wrapped(draw, (x1 + 18, y1 + 70), body, font(17), MUTED, x2 - x1 - 36, gap=7)


def build():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    d.text((80, 58), "TalentFlow AI - Final Architecture", font=font(42, True), fill=INK)
    d.text(
        (80, 112),
        "End-to-end recruitment portal, lakehouse ELT, ML insight publishing, and conversational analytics feedback loop.",
        font=font(24),
        fill=MUTED,
    )

    main = [
        ("Streamlit Portal", "Candidate, interviewer, admin, KPI, Ask Data and feedback screens", CYAN),
        ("Azure PostgreSQL", "OLTP recruitment database plus analytics cache and agent feedback tables", BLUE),
        ("Prefect ELT", "Full bronze, silver and gold flow; optional 2-minute demo scheduler", AMBER),
        ("Bronze Parquet", "Versioned raw extracts and latest copies in Azure Blob Storage", BLUE),
        ("Silver Secure", "PII encryption, typed cleaning and SCD Type 2 candidate history", GREEN),
        ("Gold Lake", "DuckDB business aggregations as versioned parquet gold tables", AMBER),
        ("Hive Tables", "External tables over bronze, silver and gold lake folders", BLUE),
        ("Admin BI", "Gold KPIs, feature insights, result tables, metrics and charts", CYAN),
    ]

    x0, y0 = 80, 225
    bw, bh, gap = 235, 155, 24
    boxes = []
    for idx, (title, body, color) in enumerate(main):
        x = x0 + idx * (bw + gap)
        box = (x, y0, x + bw, y0 + bh)
        boxes.append(box)
        card(d, box, title, body, color=color)

    for left, right in zip(boxes, boxes[1:]):
        arrow(d, (left[2] + 7, (left[1] + left[3]) // 2), (right[0] - 7, (right[1] + right[3]) // 2), color=BLUE)

    # Supporting platform capabilities
    d.text((80, 470), "Final Additions", font=font(30, True), fill=INK)

    lower = [
        (
            "ML Training",
            "Random Forest hire, decision and rating models; metrics, artifacts and feature importance outputs",
            ORANGE,
            (80, 540, 390, 720),
        ),
        (
            "Insight Publishing",
            "Feature importance and model summaries published into analytics.ml_feature_insights",
            ORANGE,
            (450, 540, 760, 720),
        ),
        (
            "Validation",
            "Gold reconciliation, null checks, row-count checks and contract tests before reporting",
            RED,
            (820, 540, 1130, 720),
        ),
        (
            "Feedback Memory",
            "Admin helpful flags and corrected SQL stored in analytics.agent_interactions for learning",
            GREEN,
            (1190, 540, 1500, 720),
        ),
        (
            "Ask Data Agent",
            "Safe Text-to-SQL using local semantic matching, optional Hugging Face model and SQL guardrails",
            CYAN,
            (1560, 540, 1870, 720),
        ),
    ]

    for title, body, color, box in lower:
        card(d, box, title, body, color=color, fill=(255, 255, 255))

    ml_box = lower[0][3]
    publish_box = lower[1][3]
    validation_box = lower[2][3]
    feedback_box = lower[3][3]
    agent_box = lower[4][3]

    arrow(d, (ml_box[2] + 8, 630), (publish_box[0] - 8, 630), color=ORANGE)
    arrow(d, (publish_box[0] + 155, publish_box[1] - 8), (boxes[1][0] + 115, boxes[1][3] + 8), color=ORANGE)
    arrow(d, (validation_box[0] + 155, validation_box[1] - 8), (boxes[5][0] + 115, boxes[5][3] + 8), color=RED)
    arrow(d, (boxes[7][0] + 115, boxes[7][3] + 8), (agent_box[0] + 155, agent_box[1] - 8), color=CYAN)
    arrow(d, (agent_box[0] - 8, 630), (feedback_box[2] + 8, 630), color=GREEN)
    dashed_line(d, (feedback_box[0] + 155, feedback_box[1] - 8), (agent_box[0] + 155, agent_box[1] - 8), color=GREEN, width=4)

    # Analytics cache path from lake to PostgreSQL/dashboard.
    cache_y = 825
    rounded(d, (80, cache_y, 1870, cache_y + 115), fill=PANEL, outline=(197, 214, 230), radius=16, width=2)
    d.text((110, cache_y + 28), "Optional Dashboard Cache", font=font(25, True), fill=BLUE)
    d.text(
        (110, cache_y + 68),
        "Gold parquet remains the analytical source of truth; --publish-postgres caches selected gold tables into PostgreSQL for the Streamlit dashboard.",
        font=font(19),
        fill=MUTED,
    )
    # Cross-cutting callout
    rounded(d, (1930, 540, 2120, 940), fill=(255, 251, 245), outline=(227, 202, 167), radius=16, width=2)
    d.rectangle((1930, 540, 2120, 548), fill=AMBER)
    d.text((1950, 575), "Controls", font=font(24, True), fill=BLUE)
    controls = [
        "Read-only SQL guardrails",
        "Sensitive-field blocking",
        "Versioned lake partitions",
        "Latest-copy serving",
        "Offline tests",
        "Gold validation",
    ]
    y = 620
    for item in controls:
        d.ellipse((1952, y + 7, 1962, y + 17), fill=AMBER)
        y = draw_wrapped(d, (1973, y), item, font(17), INK, 125, gap=5) + 12

    d.line((80, 995, 2120, 995), fill=CYAN, width=5)
    d.text((80, 1010), "Generated from the implemented TalentFlow AI final repository state.", font=font(17), fill=MUTED)

    out = OUT_DIR / "talentflow_final_architecture.png"
    im.save(out)
    print(out)


if __name__ == "__main__":
    build()
