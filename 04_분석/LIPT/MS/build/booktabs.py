# booktabs.py: just before saving, normalizes every table to a strict three-rule layout
#  top rule sz6 + rule below the header row sz4 + rule below the last row sz6 (cell level); no vertical rules, row rules, shading or table style;
#  fixed layout; table width = usable width of its section (gridCol scaled proportionally; tcW respects gridSpan).
#  Prevents tables being exported with the 'Table Grid' style (grid lines).
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def _border(parent, edge, val, sz):
    e = parent.find(qn(f"w:{edge}"))
    if e is None:
        e = OxmlElement(f"w:{edge}"); parent.append(e)
    e.set(qn("w:val"), val); e.set(qn("w:sz"), str(sz)); e.set(qn("w:space"), "0"); e.set(qn("w:color"), "000000")

def _usable_twips(doc):
    """Return the usable width (twips) of the section holding each table, in body order."""
    body = doc.element.body; out = []; pending = []
    secs = iter(doc.sections); sec = next(secs)
    for el in body.iterchildren():
        if el.tag == qn("w:tbl"):
            pending.append(el)
        elif el.tag == qn("w:p") and el.find(qn("w:pPr")) is not None and el.find(qn("w:pPr")).find(qn("w:sectPr")) is not None:
            w = int((sec.page_width - sec.left_margin - sec.right_margin) / 635)
            out += [(t, w) for t in pending]; pending = []; sec = next(secs, sec)
    last = doc.sections[-1]
    out += [(t, int((last.page_width - last.left_margin - last.right_margin) / 635)) for t in pending]
    return out

def fix(doc):
    n = 0
    for tbl, avail in _usable_twips(doc):
        tblPr = tbl.find(qn("w:tblPr"))
        st = tblPr.find(qn("w:tblStyle"))
        if st is not None: tblPr.remove(st)
        b = tblPr.find(qn("w:tblBorders"))
        if b is None:
            b = OxmlElement("w:tblBorders"); tblPr.append(b)
        for edge, val, sz in (("top", "single", 6), ("left", "nil", 0), ("bottom", "single", 6), ("right", "nil", 0), ("insideH", "nil", 0), ("insideV", "nil", 0)):
            _border(b, edge, val, sz)
        lay = tblPr.find(qn("w:tblLayout"))
        if lay is None:
            lay = OxmlElement("w:tblLayout"); tblPr.append(lay)
        lay.set(qn("w:type"), "fixed")
        # Width: gridCol proportions -> section usable width
        gcs = tbl.find(qn("w:tblGrid")).findall(qn("w:gridCol"))
        ws = [int(g.get(qn("w:w")) or 0) for g in gcs]
        if sum(ws) <= 0: ws = [1] * len(gcs)
        k = avail / sum(ws); ws = [int(w * k) for w in ws]; ws[0] += avail - sum(ws)
        for g, w in zip(gcs, ws): g.set(qn("w:w"), str(w))
        tw = tblPr.find(qn("w:tblW"))
        if tw is None:
            tw = OxmlElement("w:tblW"); tblPr.append(tw)
        tw.set(qn("w:w"), str(avail)); tw.set(qn("w:type"), "dxa")
        rows = tbl.findall(qn("w:tr"))
        hdr_idx = [i for i, r in enumerate(rows) if r.find(qn("w:trPr")) is not None and r.find(qn("w:trPr")).find(qn("w:tblHeader")) is not None]
        hlast = hdr_idx[-1] if hdr_idx and hdr_idx == list(range(len(hdr_idx))) else 0
        # Footnote row: if the last row is one cell spanning all columns and the row before has several cells, it is a footnote row -> bottom rule under the previous row, no rules on the footnote row, no rule under the table
        def _ntc(r): return len(r.findall(qn("w:tc")))
        foot = len(rows) >= 3 and _ntc(rows[-1]) == 1 and _ntc(rows[-2]) > 1
        lastdata = len(rows) - 2 if foot else len(rows) - 1
        if foot: _border(b, "bottom", "nil", 0)
        for i, r in enumerate(rows):
            col = 0
            for tc in r.findall(qn("w:tc")):
                tcPr = tc.find(qn("w:tcPr"))
                if tcPr is None:
                    tcPr = OxmlElement("w:tcPr"); tc.insert(0, tcPr)
                span = tcPr.find(qn("w:gridSpan")); sp = int(span.get(qn("w:val"))) if span is not None else 1
                tcw = tcPr.find(qn("w:tcW"))
                if tcw is None:
                    tcw = OxmlElement("w:tcW"); tcPr.insert(0, tcw)
                tcw.set(qn("w:w"), str(sum(ws[col:col + sp]))); tcw.set(qn("w:type"), "dxa"); col += sp
                for s in tcPr.findall(qn("w:shd")): tcPr.remove(s)
                old = tcPr.find(qn("w:tcBorders"))
                if old is not None: tcPr.remove(old)
                cb = OxmlElement("w:tcBorders")
                if i == 0: _border(cb, "top", "single", 6)
                _border(cb, "left", "nil", 0)
                if i == hlast: _border(cb, "bottom", "single", 4)
                elif i == lastdata: _border(cb, "bottom", "single", 6)
                else: _border(cb, "bottom", "nil", 0)
                _border(cb, "right", "nil", 0)
                # tcBorders after tcW/gridSpan and before shd/vAlign (schema order)
                anchor = next(x for x in (tcPr.find(qn("w:vMerge")), span, tcw) if x is not None)
                anchor.addnext(cb)
        for s in tbl.iter(qn("w:shd")): s.getparent().remove(s)
        # Single tblLayout, 40-twip left/right cell margins, tblPr children in schema order
        lays = tblPr.findall(qn("w:tblLayout"))
        for x in lays[1:]: tblPr.remove(x)
        cm = tblPr.find(qn("w:tblCellMar"))
        if cm is None: cm = OxmlElement("w:tblCellMar"); tblPr.append(cm)
        for edge in ("left", "right"):
            e = cm.find(qn(f"w:{edge}"))
            if e is None: e = OxmlElement(f"w:{edge}"); cm.append(e)
            e.set(qn("w:w"), "40"); e.set(qn("w:type"), "dxa")
        ORDER = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption", "tblDescription"]
        kids = list(tblPr); rank = {qn(f"w:{t}"): i for i, t in enumerate(ORDER)}
        for k_ in kids: tblPr.remove(k_)
        for k_ in sorted(kids, key=lambda e: rank.get(e.tag, 99)): tblPr.append(k_)
        n += 1
    return n
