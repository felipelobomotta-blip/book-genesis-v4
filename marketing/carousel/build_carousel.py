"""Build Book Genesis 5 - Imagination Edition carousel assets.

Run from this folder's parent with Python 3.11 and ReportLab installed.
Outputs a six-page square PDF plus one PNG export per slide.
"""

from pathlib import Path
import subprocess

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
PDF = ASSETS / "book-genesis-5-imagination-edition-carousel.pdf"
PNG_PREFIX = ASSETS / "book-genesis-5-slide"

W = H = 1080
FOREST = "#09251e"
IVORY = "#f6f1e5"
COPPER = "#b46a36"
MOSS = "#496a57"


def set_fill(c: canvas.Canvas, color: str) -> None:
    c.setFillColor(color)


def draw_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font: str,
    size: float,
    leading: float,
    color: str,
) -> float:
    """Draw text with explicit width wrapping, returning the next baseline."""
    c.setFont(font, size)
    set_fill(c, color)
    words = text.split()
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if line and stringWidth(candidate, font, size) > max_width:
            c.drawString(x, y, line)
            y -= leading
            line = word
        else:
            line = candidate
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def eyebrow(c: canvas.Canvas, number: int, label: str) -> None:
    c.setStrokeColor(COPPER)
    c.setLineWidth(4)
    c.line(78, 965, 170, 965)
    c.setFont("Helvetica-Bold", 18)
    set_fill(c, IVORY)
    c.drawString(78, 930, label.upper())
    c.setFont("Helvetica", 17)
    set_fill(c, "#c7d2c7")
    c.drawRightString(1002, 930, f"0{number} / 06")


def footer(c: canvas.Canvas) -> None:
    c.setStrokeColor(MOSS)
    c.setLineWidth(1.5)
    c.line(78, 95, 1002, 95)
    c.setFont("Helvetica-Bold", 15)
    set_fill(c, IVORY)
    c.drawString(78, 62, "BOOK GENESIS 5")
    c.setFont("Helvetica", 15)
    set_fill(c, "#c7d2c7")
    c.drawRightString(1002, 62, "IMAGINATION EDITION")


def organic_shape(c: canvas.Canvas, mode: int) -> None:
    c.saveState()
    c.setLineWidth(3)
    c.setStrokeColor(COPPER)
    c.setFillColor(FOREST)
    if mode == 1:
        c.circle(841, 522, 182, stroke=1, fill=0)
        c.circle(841, 522, 106, stroke=1, fill=0)
        c.setFillColor(COPPER)
        c.circle(841, 522, 23, stroke=0, fill=1)
    elif mode == 2:
        c.roundRect(735, 420, 194, 260, 97, stroke=1, fill=0)
        c.line(695, 550, 969, 550)
        c.line(832, 372, 832, 727)
    elif mode == 3:
        c.circle(852, 540, 165, stroke=1, fill=0)
        c.setFillColor(COPPER)
        c.circle(852, 540, 14, stroke=0, fill=1)
        c.setStrokeColor("#c7d2c7")
        c.line(687, 540, 1017, 540)
        c.line(852, 375, 852, 705)
    elif mode == 4:
        c.setStrokeColor(COPPER)
        c.roundRect(716, 414, 274, 275, 30, stroke=1, fill=0)
        c.setFillColor(COPPER)
        c.roundRect(756, 454, 194, 195, 20, stroke=0, fill=1)
        c.setFillColor(FOREST)
        c.setFont("Times-Bold", 116)
        c.drawCentredString(853, 510, "!")
    elif mode == 5:
        c.setStrokeColor(COPPER)
        c.circle(852, 540, 168, stroke=1, fill=0)
        c.setFont("Helvetica-Bold", 86)
        set_fill(c, IVORY)
        c.drawCentredString(852, 568, "279")
        c.setFont("Helvetica-Bold", 18)
        set_fill(c, "#c7d2c7")
        c.drawCentredString(852, 516, "LOCAL TESTS")
    else:
        c.setStrokeColor(COPPER)
        c.roundRect(712, 435, 286, 214, 107, stroke=1, fill=0)
        c.setFillColor(COPPER)
        c.circle(855, 542, 35, stroke=0, fill=1)
        c.setFillColor(FOREST)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(855, 532, "+")
    c.restoreState()


def title(c: canvas.Canvas, first: str, second: str | None = None) -> float:
    c.setFont("Times-Bold", 76)
    set_fill(c, IVORY)
    y = 760
    for line in (first, second):
        if line:
            c.drawString(78, y, line)
            y -= 88
    return y


def build() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(PDF), pagesize=(W, H), pageCompression=1)
    c.setTitle("Book Genesis 5 - Imagination Edition")
    c.setAuthor("Book Genesis")
    c.setSubject("Six-slide English marketing carousel")

    slides = [
        ("BOOK GENESIS 5", "Imagination Edition", "Creativity is the starting point. The story is yours.", "A WRITING WORKFLOW", 1),
        ("An idea deserves", "more than one prompt.", "Turn a premise into a project you can inspect: brief, outline, chapters, feedback, audit, review, export.", "FROM IDEA TO PROJECT", 2),
        ("The draft is not", "the finish line.", "Keep attempts, reader feedback, and the canonical chapter on disk. Pause. Resume. Revise with context.", "THE WORK STAYS VISIBLE", 3),
        ("Reports are", "not approval.", "A manuscript audit can return MAJOR REWRITE and stop the workflow at awaiting_revision.", "THE AUDIT GATE", 4),
        ("Beta evidence,", "stated plainly.", "279 local regression tests. One 1,910-word smoke story. Model evaluation only. Human validation is still pending.", "WHAT WE KNOW", 5),
        ("Try one chapter.", None, "Report what breaks. Contribute what improves the craft.", "OPEN BETA", 6),
    ]

    for index, (first, second, body, label, shape) in enumerate(slides, start=1):
        c.setFillColor(FOREST)
        c.rect(0, 0, W, H, stroke=0, fill=1)
        eyebrow(c, index, label)
        y = title(c, first, second)
        y -= 50
        draw_wrapped(c, body, 82, y, 560, "Helvetica", 28, 41, "#c7d2c7")
        organic_shape(c, shape)
        if index == 6:
            c.setFont("Helvetica-Bold", 20)
            set_fill(c, COPPER)
            c.drawString(82, 245, "github.com/felipelobomotta-blip/book-genesis-v4")
        footer(c)
        c.showPage()
    c.save()

    subprocess.run(
        ["pdftoppm", "-png", "-r", "72", str(PDF), str(PNG_PREFIX)],
        check=True,
    )
    # Poppler emits -1 through -6; rename them into stable zero-padded names.
    for index in range(1, 7):
        source = ASSETS / f"book-genesis-5-slide-{index}.png"
        target = ASSETS / f"book-genesis-5-slide-{index:02d}.png"
        if source.exists():
            source.replace(target)


if __name__ == "__main__":
    build()
