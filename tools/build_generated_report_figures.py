from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT_DIR = Path(r"D:\TalentFlow_AI\outputs\generated_report_figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BG = (248, 250, 252)
INK = (25, 35, 48)
MUTED = (83, 96, 112)
BLUE = (31, 78, 121)
CYAN = (9, 165, 196)
GREEN = (31, 160, 113)
YELLOW = (211, 143, 36)
RED = (190, 76, 70)
CARD = (255, 255, 255)
LINE = (194, 204, 216)


def font(size, bold=False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def rounded(draw, box, fill=CARD, outline=LINE, radius=16, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def wrap_text(draw, text, fnt, max_width):
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


def draw_textbox(draw, xy, text, fnt, fill=INK, max_width=None, line_gap=8):
    x, y = xy
    if max_width is None:
        draw.text((x, y), text, font=fnt, fill=fill)
        return y + draw.textbbox((x, y), text, font=fnt)[3] - y
    for line in wrap_text(draw, text, fnt, max_width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def arrow(draw, start, end, color=BLUE):
    draw.line([start, end], fill=color, width=4)
    ex, ey = end
    sx, sy = start
    if ex >= sx:
        pts = [(ex, ey), (ex - 14, ey - 8), (ex - 14, ey + 8)]
    else:
        pts = [(ex, ey), (ex + 14, ey - 8), (ex + 14, ey + 8)]
    draw.polygon(pts, fill=color)


def build_ml_results():
    im = Image.new("RGB", (1400, 900), BG)
    d = ImageDraw.Draw(im)
    d.text((70, 58), "Final Machine-Learning Results", font=font(42, True), fill=BLUE)
    d.text(
        (70, 112),
        "Random Forest models are positioned as decision-support prototypes on demo-oriented recruitment data.",
        font=font(24),
        fill=MUTED,
    )

    cards = [
        ("Hire Prediction", "Accuracy 0.7552", "F1 0.8427 | ROC-AUC 0.8262", "Support: 241", GREEN),
        ("Decision Prediction", "Accuracy 0.7884", "Weighted F1 0.8165", "Classes: Hire, Hold, Reject", CYAN),
        ("Rating Prediction", "MAE 0.3017", "R2 0.5309", "Support: 241", YELLOW),
    ]
    x = 70
    for title, metric1, metric2, note, color in cards:
        rounded(d, (x, 190, x + 390, 390), fill=CARD, outline=(213, 222, 232), radius=18)
        d.rectangle((x, 190, x + 390, 200), fill=color)
        d.text((x + 28, 225), title, font=font(25, True), fill=INK)
        d.text((x + 28, 272), metric1, font=font(31, True), fill=color)
        d.text((x + 28, 318), metric2, font=font(22), fill=INK)
        d.text((x + 28, 354), note, font=font(19), fill=MUTED)
        x += 430

    rounded(d, (70, 445, 660, 735), fill=(239, 247, 252), outline=(185, 212, 231), radius=18)
    d.text((100, 490), "Interpretation", font=font(28, True), fill=BLUE)
    notes = [
        "End-to-end ML training, artifact saving and feature-importance publishing are functional.",
        "Hire and decision models show usable prototype performance on the available demo dataset.",
        "Production use requires real data, model cards, fairness checks and drift monitoring.",
    ]
    y = 525
    for note in notes:
        d.ellipse((100, y + 8, 110, y + 18), fill=GREEN)
        y = draw_textbox(d, (125, y), note, font(20), fill=INK, max_width=485, line_gap=6) + 14

    rounded(d, (735, 445, 1330, 735), fill=(249, 244, 236), outline=(226, 206, 171), radius=18)
    d.text((765, 490), "Why It Matters", font=font(28, True), fill=BLUE)
    notes = [
        "The dashboard can explain which features influenced model decisions.",
        "The models are framed as recruiter decision support, not automated hiring authority.",
        "Metrics are backed by the latest model artifact metrics.json.",
    ]
    y = 525
    for note in notes:
        d.ellipse((765, y + 8, 775, y + 18), fill=YELLOW)
        y = draw_textbox(d, (790, y), note, font(20), fill=INK, max_width=490, line_gap=6) + 14

    d.line((70, 820, 1330, 820), fill=CYAN, width=6)
    d.text((70, 840), "Generated for the final report from the latest TalentFlow AI model metrics.", font=font(18), fill=MUTED)
    im.save(OUT_DIR / "ml_final_results.png")


def build_agent_flow():
    im = Image.new("RGB", (1400, 820), BG)
    d = ImageDraw.Draw(im)
    d.text((70, 58), "Ask Data Conversational Analytics Flow", font=font(42, True), fill=BLUE)
    d.text(
        (70, 112),
        "The assistant combines deterministic matching, optional local LLM generation, SQL safety and feedback memory.",
        font=font(24),
        fill=MUTED,
    )

    boxes = [
        ("Admin Question", "Natural-language question or pasted SQL", (70, 225, 285, 370), CYAN),
        ("Schema Context", "public + analytics metadata excluding password fields", (335, 225, 550, 370), GREEN),
        ("Router", "fast local matcher first; optional Hugging Face fallback", (600, 225, 815, 370), YELLOW),
        ("SQL Guardrail", "SELECT/WITH only, one statement, no sensitive columns", (865, 225, 1080, 370), RED),
        ("Result View", "table, metric, bar chart or line chart in Streamlit", (1130, 225, 1345, 370), BLUE),
    ]
    for title, body, box, color in boxes:
        rounded(d, box, fill=CARD, outline=(205, 214, 225), radius=18)
        x1, y1, x2, y2 = box
        d.rectangle((x1, y1, x2, y1 + 10), fill=color)
        d.text((x1 + 20, y1 + 30), title, font=font(24, True), fill=INK)
        draw_textbox(d, (x1 + 20, y1 + 72), body, font(18), fill=MUTED, max_width=x2 - x1 - 40, line_gap=6)

    for i in range(len(boxes) - 1):
        x2 = boxes[i][2][2]
        y = (boxes[i][2][1] + boxes[i][2][3]) // 2
        x1_next = boxes[i + 1][2][0]
        arrow(d, (x2 + 8, y), (x1_next - 8, y), color=BLUE)

    lower = [
        ("SQL Repair", "If generated SQL fails, the local LLM gets the error and returns one corrected safe query.", (220, 500, 625, 650), CYAN),
        ("Feedback Memory", "Helpful flags and corrected SQL are stored in analytics.agent_interactions for reuse.", (775, 500, 1180, 650), GREEN),
    ]
    for title, body, box, color in lower:
        rounded(d, box, fill=(245, 249, 252), outline=(195, 210, 222), radius=18)
        x1, y1, x2, y2 = box
        d.text((x1 + 24, y1 + 28), title, font=font(26, True), fill=BLUE)
        draw_textbox(d, (x1 + 24, y1 + 72), body, font(19), fill=INK, max_width=x2 - x1 - 48, line_gap=6)

    arrow(d, (972, 380), (972, 495), color=RED)
    arrow(d, (830, 650), (760, 650), color=GREEN)
    arrow(d, (760, 650), (705, 370), color=GREEN)
    d.line((70, 752, 1330, 752), fill=CYAN, width=6)
    d.text((70, 770), "Generated for the final report where no finished Ask Data screenshot existed in the mid-term assets.", font=font(18), fill=MUTED)
    im.save(OUT_DIR / "ask_data_agent_flow.png")


if __name__ == "__main__":
    build_ml_results()
    build_agent_flow()
    print(OUT_DIR / "ml_final_results.png")
    print(OUT_DIR / "ask_data_agent_flow.png")
