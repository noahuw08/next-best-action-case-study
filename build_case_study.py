"""Build the PDF and Markdown case study from the reviewed narrative JSON.

Run: python build_case_study.py
Requires ReportLab. No employer data or model artifacts are used.
"""

import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Flowable, Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "case-study.json").read_text())
OUT = ROOT / "next-best-action-case-study.pdf"
W, H = 595.28, 841.89
M = 44
CW = W - 2 * M
NAVY = colors.HexColor("#142B38")
TEAL = colors.HexColor("#087F7A")
PAPER = colors.HexColor("#FAF9F5")
MUTED = colors.HexColor("#52666C")
LINE = colors.HexColor("#D8E0DB")
TINT = colors.HexColor("#E7F2ED")


def register_fonts():
    locations = [
        (Path("/System/Library/Fonts/Supplemental"), "Arial.ttf", "Arial Bold.ttf"),
        (Path("/usr/share/fonts/truetype/dejavu"), "DejaVuSans.ttf", "DejaVuSans-Bold.ttf"),
    ]
    for folder, regular, bold in locations:
        if (folder / regular).exists() and (folder / bold).exists():
            pdfmetrics.registerFont(TTFont("Body", str(folder / regular)))
            pdfmetrics.registerFont(TTFont("BodyBold", str(folder / bold)))
            return "Body", "BodyBold"
    return "Helvetica", "Helvetica-Bold"


FONT, BOLD = register_fonts()


def style(size=10.4, leading=14.6, bold=False, color=NAVY):
    return ParagraphStyle(
        "body", fontName=BOLD if bold else FONT, fontSize=size,
        leading=leading, textColor=color, alignment=TA_LEFT,
        allowWidows=0, allowOrphans=0,
    )


class FlowDiagram(Flowable):
    def __init__(self, items, caption):
        super().__init__()
        self.items = items
        self.caption = Paragraph(escape(caption), style(8.5, 11.6, color=MUTED))

    def wrap(self, width, height):
        self.width = width
        _, ch = self.caption.wrap(width, height)
        self.ch = ch
        self.height = 36 + 10 + ch
        return self.width, self.height

    def draw(self):
        c = self.canv
        bw = (self.width - 15 * 3) / 4
        y = self.height - 36
        for i, text in enumerate(self.items):
            x = i * (bw + 15)
            c.setFillColor(TINT)
            c.roundRect(x, y, bw, 36, 6, fill=1, stroke=0)
            p = Paragraph(escape(text), style(8.5, 10.5, bold=True, color=TEAL))
            _, ph = p.wrap(bw - 14, 36)
            p.drawOn(c, x + 7, y + (36 - ph) / 2)
            if i < 3:
                c.setStrokeColor(TEAL)
                c.line(x + bw + 3, y + 18, x + bw + 12, y + 18)
                c.line(x + bw + 9, y + 21, x + bw + 12, y + 18)
                c.line(x + bw + 9, y + 15, x + bw + 12, y + 18)
        self.caption.drawOn(c, 0, 0)


class ResultChart(Flowable):
    def wrap(self, width, height):
        self.width, self.height = width, 116
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFont(BOLD, 10)
        c.setFillColor(NAVY)
        c.drawString(0, 103, "Precision@4  |  matched offline benchmark")
        bx, maxw = 105, self.width - 151
        for name, value, y, fill in [
            ("Random", 0.059, 69, colors.HexColor("#BFCBC5")),
            ("v2 LLM", 0.126, 43, colors.HexColor("#788C96")),
            ("v3 LightGBM", 0.186, 17, TEAL),
        ]:
            c.setFont(FONT, 9)
            c.setFillColor(NAVY)
            c.drawString(0, y + 5, name)
            c.setFillColor(fill)
            barw = maxw * value / 0.2
            c.roundRect(bx, y, barw, 17, 3, fill=1, stroke=0)
            c.setFillColor(NAVY)
            c.setFont(BOLD, 9)
            c.drawString(bx + barw + 8, y + 5, f"{value:.3f}")


def callout(block):
    label = Paragraph(escape(block["label"]), style(8, 10.8, bold=True, color=TEAL))
    txt = escape(block["text"])
    if block.get("link"):
        txt += '<br/><a href="' + escape(DATA["supplement"], {'"': '&quot;'}) + '">Open the supplementary Notion workspace</a>'
    table = Table([[label], [Paragraph(txt, style(9.4, 13))]], colWidths=[CW - 24])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TINT),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
    ]))
    return table


def make_blocks(page):
    result = []
    for block in page["blocks"]:
        kind = block["type"]
        if kind == "h":
            result.append((Paragraph(escape(block["text"]), style(11.4, 15.5, bold=True)), 5, 5))
        elif kind == "p":
            result.append((Paragraph(escape(block["text"]), style()), 0, 8))
        elif kind == "note":
            result.append((Paragraph(escape(block["text"]), style(8.25, 11.25, color=MUTED)), 3, 6))
        elif kind == "flow":
            result.append((FlowDiagram(block["items"], block["caption"]), 5, 8))
        elif kind == "chart":
            result.append((ResultChart(), 2, 9))
        elif kind == "callout":
            result.append((callout(block), 3, 8))
        elif kind == "table":
            rows = [[Paragraph(escape(s), style(8.5, 11.5, bold=True, color=colors.white)) for s in block["headers"]]]
            rows += [[Paragraph(escape(s), style(8.6, 11.7)) for s in row] for row in block["rows"]]
            table = Table(rows, colWidths=[CW * frac for frac in block["widths"]], hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F0F3EF"), PAPER]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            result.append((table, 2, 8))
        else:
            raise ValueError(f"Unknown block: {kind}")
    return result


def draw_page(c, page):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.rect(0, H - 9, W, 9, fill=1, stroke=0)
    c.setFont(BOLD, 8)
    c.setFillColor(MUTED)
    c.drawString(M, H - 36, "WEALTHSIMPLE  /  NEXT BEST ACTION v3")
    c.setFont(FONT, 8)
    c.drawRightString(W - M, H - 36, "NOAH  ·  APPLIED ML CASE STUDY")
    c.setStrokeColor(LINE)
    c.line(M, 42, W - M, 42)
    c.setFont(FONT, 8)
    c.drawString(M, 27, "From LLM ranking to a learned next-best-action system")
    c.drawRightString(W - M, 27, f"{page['number']} / 06")
    c.bookmarkPage(page["number"])
    c.addOutlineEntry(page["kicker"].title(), page["number"], level=0)
    c.setFillColor(TEAL)
    c.setFont(BOLD, 9)
    c.drawString(M, H - 64, page["number"] + "   " + page["kicker"])
    title = Paragraph(escape(page["title"]), style(25, 29, bold=True))
    _, th = title.wrap(CW, H)
    y = H - 77 - th
    title.drawOn(c, M, y)
    y -= 15
    blocks = make_blocks(page)
    heights = [(f, f.wrap(CW, H)[1], before, after) for f, before, after in blocks]
    total = sum(h + before + after for _, h, before, after in heights)
    available = y - 57
    if total > available:
        raise ValueError(f"Page {page['number']} overflows by {total - available:.1f} pt; edit content or spacing.")
    for f, h, before, after in heights:
        y -= before + h
        f.drawOn(c, M, y)
        y -= after
    print(f"Page {page['number']}: {total:.0f} pt used, {available - total:.0f} pt remaining")
    c.showPage()


def build_markdown():
    out = [f"# {DATA['title']}", DATA["subtitle"], f"**{DATA['author']} · {DATA['date']}**", DATA["summary"]]
    for page in DATA["pages"]:
        out += [f"## {page['number']} · {page['kicker'].title()}", f"### {page['title']}"]
        for block in page["blocks"]:
            kind = block["type"]
            if kind == "h":
                out.append("#### " + block["text"])
            elif kind == "p":
                out.append(block["text"])
            elif kind == "note":
                out.append("*" + block["text"] + "*")
            elif kind == "table":
                table = ["| " + " | ".join(block["headers"]) + " |", "| " + " | ".join("---" for _ in block["headers"]) + " |"]
                table += ["| " + " | ".join(row) + " |" for row in block["rows"]]
                out.append("\n".join(table))
            elif kind == "flow":
                out.append("**" + " → ".join(block["items"]) + "**\n\n" + block["caption"])
            elif kind == "callout":
                out.append("**" + block["label"].title() + "**\n\n" + block["text"])
                if block.get("link"):
                    out.append("[Open the supplementary Notion workspace](" + DATA["supplement"] + ")")
            elif kind == "chart":
                out.append("![Precision@4: v3 LightGBM 0.186, v2 LLM 0.126, random 0.059](assets/precision-at-4.svg)")
    (ROOT / "CASE_STUDY.md").write_text("\n\n".join(out) + "\n")


def build_svg():
    folder = ROOT / "assets"
    folder.mkdir(exist_ok=True)
    rows = []
    for label, value, y, color in [("Random", .059, 80, "#BFCBC5"), ("v2 LLM", .126, 132, "#788C96"), ("v3 LightGBM", .186, 184, "#087F7A")]:
        width = 430 * value / .2
        rows.append(f'<text x="24" y="{y+21}">{label}</text><rect x="160" y="{y}" width="{width:.1f}" height="30" rx="4" fill="{color}"/><text x="{170+width:.1f}" y="{y+21}" font-weight="700">{value:.3f}</text>')
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="700" height="255" viewBox="0 0 700 255" role="img" aria-labelledby="title desc"><title id="title">Matched offline benchmark: Precision at four</title><desc id="desc">Random 0.059. LLM 0.126. LightGBM 0.186, a 47.6 percent relative gain over the LLM.</desc><rect width="700" height="255" rx="12" fill="#FAF9F5"/><g font-family="Arial, sans-serif" font-size="17" fill="#142B38"><text x="24" y="40" font-size="21" font-weight="700">Precision@4 · matched offline benchmark</text>' + ''.join(rows) + '</g></svg>'
    (folder / "precision-at-4.svg").write_text(svg)


def main():
    c = canvas.Canvas(str(OUT), pagesize=(W, H), pageCompression=1)
    c.setTitle(DATA["title"])
    c.setAuthor(DATA["author"])
    c.setSubject(DATA["subtitle"])
    for page in DATA["pages"]:
        draw_page(c, page)
    c.save()
    build_markdown()
    build_svg()
    print(OUT)


if __name__ == "__main__":
    main()
