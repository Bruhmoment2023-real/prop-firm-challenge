"""Helpers to edit the v16 manuscript docx in place: insert paragraphs, tables and figures at anchors."""
import copy
from docx import Document
from docx.shared import Pt, Cm, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def find_par(doc, startswith, nth=0):
    k = 0
    for p in doc.paragraphs:
        if p.text.strip().startswith(startswith):
            if k == nth: return p
            k += 1
    raise KeyError(startswith)


def set_text(p, text):
    """Replace paragraph text keeping the first run's formatting."""
    runs = p.runs
    if not runs:
        p.add_run(text); return p
    runs[0].text = text
    for r in runs[1:]: r._r.getparent().remove(r._r)
    return p


def new_par_after(anchor_el, style, text="", doc=None):
    p = OxmlElement("w:p"); anchor_el.addnext(p)
    from docx.text.paragraph import Paragraph
    par = Paragraph(p, doc._body); par.style = doc.styles[style]
    if text: par.add_run(text)
    return par


class Inserter:
    """Sequentially inserts blocks after an anchor element."""
    def __init__(self, doc, anchor_par):
        self.doc = doc; self.el = anchor_par._p

    def par(self, style, text):
        p = new_par_after(self.el, style, text, self.doc); self.el = p._p; return p

    def body(self, text): return self.par("Normal (Web)", text)
    def h2(self, text): return self.par("Heading 2", text)
    def h3(self, text): return self.par("Heading 3", text)
    def cap(self, text): return self.par("cap", text)
    def note(self, text): return self.par("note", text)

    def picture(self, path, width_cm=15.5):
        p = new_par_after(self.el, "Normal", "", self.doc); self.el = p._p
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(path), width=Cm(width_cm)); return p

    def table(self, header, rows, widths_cm=None, size=8):
        t = self.doc.add_table(rows=1 + len(rows), cols=len(header))
        for j, h in enumerate(header): self._cell(t.rows[0].cells[j], str(h), True, size)
        for i, r in enumerate(rows):
            for j, v in enumerate(r): self._cell(t.rows[i + 1].cells[j], str(v), False, size)
        if widths_cm:
            for row in t.rows:
                for j, w in enumerate(widths_cm): row.cells[j].width = Cm(w)
        self._rules(t)
        self.el.addnext(t._tbl); self.el = t._tbl
        return t

    @staticmethod
    def _cell(cell, text, bold, size):
        p = cell.paragraphs[0]; r = p.add_run(text); r.bold = bold; r.font.size = Pt(size)
        p.paragraph_format.space_after = Pt(0); p.paragraph_format.space_before = Pt(0)

    @staticmethod
    def _rules(t):
        tbl = t._tbl; pr = tbl.tblPr
        b = OxmlElement("w:tblBorders")
        for edge in ("top", "bottom"):
            e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "8"); e.set(qn("w:color"), "000000"); b.append(e)
        pr.append(b)
        # rule under header
        for c in t.rows[0].cells:
            tcPr = c._tc.get_or_add_tcPr(); tb = OxmlElement("w:tcBorders"); e = OxmlElement("w:bottom")
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), "000000"); tb.append(e); tcPr.append(tb)


def delete_par(p):
    p._p.getparent().remove(p._p)
