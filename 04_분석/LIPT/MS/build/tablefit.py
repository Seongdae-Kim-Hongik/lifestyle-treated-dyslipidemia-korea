# tablefit.py: tables stay portrait; per table, lower the font tier, give each column at least the measured width of its longest unbreakable token (PIL, Times New Roman), then distribute the remaining width.
import re
from PIL import ImageFont
F = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"; FB = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
CM_PER_PT = 2.54 / 72
def _w(text, pt, bold=False):
    f = ImageFont.truetype(FB if bold else F, size=100)
    return f.getlength(text) / 100 * pt * CM_PER_PT
def _plain(s): return re.sub(r"<[^>]+>", "", str(s)).replace("\u2060", "")   # Word joiner has zero width
def fit(header, rows, avail=15.9, tiers=(11, 10, 9, 8.5, 8, 7.5, 7, 6.5), pad=0.65):
    """Return (fs, widths_cm). need = longest token width x1.08 + pad (cell margins), pref = full cell string width. The first (label) column includes a 0.33 cm indent."""
    data = [r for r in rows if r and r[0] != "__H__"]
    ncol = len(header)
    for fs in tiers:
        need = []; pref = []
        for j in range(ncol):
            cells = [(_plain(header[j]), True)] + [(_plain(r[j]).strip(), False) for r in data if j < len(r)]
            toks = [(t, b) for c, b in cells for t in c.split(" ") if t]   # Split only at ordinary spaces (keep NBSP)
            n = max(_w(t, fs, b) for t, b in toks) * 1.08 + pad + (0.33 if j == 0 else 0)
            p = max(_w(c, fs, b) for c, b in cells) * 1.02 + pad + (0.33 if j == 0 else 0)
            for c, b in cells:   # Extra room for hyphenated tokens (e.g. "(A00-B99)") so they do not break at the hyphen
                for t in c.split(" "):
                    if "-" in t.strip("-"): n = max(n, _w(t, fs, b) * 1.12 + pad + 0.1)
            if any(re.search(r"\d-\d", c) for c, b in cells[1:]):   # Numeric-range hyphens are break points, so keep the whole cell on one line
                n = max(n, max(_w(c, fs, b) for c, b in cells[1:]) * 1.05 + pad)
            need.append(n); pref.append(max(p, n))
        if sum(need) <= avail:
            # Data rows on one line: remaining width goes first to the label column (0) so it fits on one line, the rest proportionally
            extra = avail - sum(need); g0 = min(extra, max(0, pref[0] - need[0])); need[0] += g0; extra -= g0
            want = [0] + [p - n for n, p in zip(need[1:], pref[1:])]; tw = sum(want)
            ws = [n + (extra * w / tw if tw > 0 else extra / ncol) for n, w in zip(need, want)]
            ws = [min(w, p) if sum(pref) <= avail else w for w, p in zip(ws, pref)]
            if sum(ws) < avail: ws[0] += avail - sum(ws)
            k = (avail - 0.02) / sum(ws); return fs, [w * k for w in ws]   # Keep the sum slightly below the page width (avoids engine redistribution)
    raise ValueError("Table does not fit the portrait width even at 6.5 pt; split the columns")
def ind_cells(doc):
    """Sub-row indent: two leading spaces in a cell -> w:ind left 187 twips."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    n = 0
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                for p in c.paragraphs:
                    rs = [r for r in p.runs if r.text]
                    if rs and rs[0].text.startswith("  "):
                        rs[0].text = rs[0].text.lstrip(" "); pPr = p._p.get_or_add_pPr()
                        ind = pPr.find(qn("w:ind"))
                        if ind is None: ind = OxmlElement("w:ind"); pPr.append(ind)
                        ind.set(qn("w:left"), "187"); n += 1
    return n
