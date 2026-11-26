# -*- coding: utf-8 -*-
# docx_engine.py: docx engine for original-article manuscripts.
#  Times New Roman 11 pt, double spacing, continuous line numbers, page numbers; order = title page -> abstract/keywords -> sections -> references -> figure legends -> tables (one per page)
#  Markup: {{key1,key2}} = citation (numbered by first appearance, superscript), <i>…</i> italic, <sup>…</sup> superscript, <b>…</b> bold. Write P values as <i>P</i>.
import re, os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

FONT="Times New Roman"

class JKMS:
    def __init__(self,cite="sup"):
        self.cite=cite   # "sup" = superscript numbers, "bracket" = [1-3]
        self.doc=Document(); d=self.doc
        st=d.styles["Normal"]; st.font.name=FONT; st.font.size=Pt(12); st.element.rPr.rFonts.set(qn("w:eastAsia"),FONT)
        st.paragraph_format.space_after=Pt(0); st.paragraph_format.line_spacing_rule=WD_LINE_SPACING.DOUBLE
        for s in d.sections:
            s.page_width=Cm(21.0); s.page_height=Cm(29.7); s.top_margin=s.bottom_margin=s.left_margin=s.right_margin=Cm(2.54)
            # Continuous line numbers + page numbers
            sp=s._sectPr; ln=OxmlElement("w:lnNumType"); ln.set(qn("w:countBy"),"1"); ln.set(qn("w:restart"),"continuous"); ln.set(qn("w:distance"),"360"); sp.append(ln)
            fp=s.footer.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
            _sl=OxmlElement("w:suppressLineNumbers"); _pp=fp._p.get_or_add_pPr(); _ps=_pp.find(qn("w:pStyle")); _pp.insert(0 if _ps is None else 1,_sl)   # Footer paragraph of a line-numbered document
            for kind,txt in (("begin",None),("instr","PAGE"),("end",None)):
                r=fp.add_run(); r.font.size=Pt(10); r.font.name=FONT
                if kind=="instr": it=OxmlElement("w:instrText"); it.set(qn("xml:space"),"preserve"); it.text=txt; r._element.append(it)
                else: fc=OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"),kind); r._element.append(fc)
        self.cites=[]; self.refs={}; self.body_words=0; self.counting=False; self.tables=[]; self.legends=[]
    # ── Citation management ──
    def cite_num(self,key):
        if key not in self.cites: self.cites.append(key)
        return self.cites.index(key)+1
    # ── Markup parser -> runs ──
    def _emit(self,p,text,sz=12,bold=False,italic=False):
        tok=re.split(r"(\{\{.*?\}\}|<i>|</i>|<sup>|</sup>|<b>|</b>)",text)
        it=italic; sup=False; bo=bold
        for t in tok:
            if t=="" : continue
            if t=="<i>": it=True; continue
            if t=="</i>": it=italic; continue
            if t=="<sup>": sup=True; continue
            if t=="</sup>": sup=False; continue
            if t=="<b>": bo=True; continue
            if t=="</b>": bo=bold; continue
            if t.startswith("{{") and t.endswith("}}") and self.cite=="ay":   # Author-year: aylabel(key) -> (sort key, "Kim et al., 2020"); several citations sorted by year, joined by "; "
                keys=[k.strip() for k in t[2:-2].split(",") if k.strip()]
                for k in keys: self.cite_num(k)
                labs=sorted((self.aylabel(k) for k in keys), key=lambda x: x[0]); txt="("+"; ".join(l for _, l in labs)+")"
                r=p.add_run(txt); r.font.size=Pt(sz); r.font.name=FONT
                if self.counting: self.body_words+=len(txt.split())
                continue
            if t.startswith("{{") and t.endswith("}}"):
                keys=[k.strip() for k in t[2:-2].split(",") if k.strip()]; nums=sorted({self.cite_num(k) for k in keys})
                # Consecutive numbers as ranges (1-3), others separated by commas
                parts=[]; i=0
                while i<len(nums):
                    j=i
                    while j+1<len(nums) and nums[j+1]==nums[j]+1: j+=1
                    parts.append(f"{nums[i]}-{nums[j]}" if j-i>=2 else ("," if self.cite=="sup" else ", ").join(str(n) for n in nums[i:j+1])); i=j+1
                if self.cite=="bracket":
                    r=p.add_run("["+", ".join(parts)+"]"); r.font.size=Pt(sz); r.font.name=FONT
                    if self.counting: self.body_words+=1
                    continue
                r=p.add_run(",".join(parts)); r.font.superscript=True; r.font.size=Pt(sz); r.font.name=FONT; continue
            r=p.add_run(t); r.font.size=Pt(sz); r.font.name=FONT; r.bold=bo; r.italic=it; r.font.superscript=sup
            r._element.rPr.rFonts.set(qn("w:eastAsia"),FONT)
            if self.counting and not sup: self.body_words+=len(t.split())
    def para(self,text,sz=12,bold=False,italic=False,align="left",double=True,before=0,after=0,indent=False):
        p=self.doc.add_paragraph(); pf=p.paragraph_format; pf.space_before=Pt(before); pf.space_after=Pt(after)
        if getattr(self,"_pb",False): pf.page_break_before=True; self._pb=False
        pf.line_spacing_rule=WD_LINE_SPACING.DOUBLE if double else WD_LINE_SPACING.SINGLE
        p.alignment={"left":WD_ALIGN_PARAGRAPH.LEFT,"center":WD_ALIGN_PARAGRAPH.CENTER,"justify":WD_ALIGN_PARAGRAPH.JUSTIFY}[align]
        if indent: pf.first_line_indent=Cm(0.75)
        self._emit(p,text,sz,bold,italic); return p
    def head(self,text,level=1):
        # level1 = upper-case section heading, level2 = bold subheading, level3 = italic sub-subheading
        c=self.counting; self.counting=False
        if level==1: self.para(text,bold=True,before=16,after=0)   # Section headings 16 pt before
        elif level==4: self.para(text,bold=True,before=24,after=6)   # Back-matter declaration headings 24/6
        elif level==2: self.para(text,bold=True,before=6)
        else: self.para(text,italic=True,before=4)
        self.counting=c
    def page_break(self):
        # An empty paragraph plus a page break spills onto the next page when the previous page is full, leaving a blank page.
        # -> Put page_break_before on the following paragraph (heading or table title) instead.
        self._pb=True
    def new_page(self,orient="portrait"):
        """Start a table page: page break if the orientation is the same, otherwise a new section (line and page numbers kept)."""
        cur=self.doc.sections[-1]; cur_or="landscape" if cur.orientation==WD_ORIENT.LANDSCAPE else "portrait"
        if orient==cur_or: self.page_break(); return cur
        s=self.doc.add_section(WD_SECTION.NEW_PAGE)
        if orient=="landscape": s.orientation=WD_ORIENT.LANDSCAPE; s.page_width=Cm(29.7); s.page_height=Cm(21.0)
        else: s.orientation=WD_ORIENT.PORTRAIT; s.page_width=Cm(21.0); s.page_height=Cm(29.7)
        s.top_margin=s.bottom_margin=s.left_margin=s.right_margin=Cm(2.54)
        sp=s._sectPr
        if sp.find(qn("w:lnNumType")) is None:
            ln=OxmlElement("w:lnNumType"); ln.set(qn("w:countBy"),"1"); ln.set(qn("w:restart"),"continuous"); ln.set(qn("w:distance"),"360"); sp.append(ln)
        s.footer.is_linked_to_previous=True
        return s
    def landscape_section(self):
        """Start a landscape section for tables (line and page numbers kept). Later tables may use a 24.6 cm width."""
        s=self.doc.add_section(WD_SECTION.NEW_PAGE)
        s.orientation=WD_ORIENT.LANDSCAPE; s.page_width=Cm(29.7); s.page_height=Cm(21.0)
        s.top_margin=s.bottom_margin=s.left_margin=s.right_margin=Cm(2.54)
        sp=s._sectPr; ln=OxmlElement("w:lnNumType"); ln.set(qn("w:countBy"),"1"); ln.set(qn("w:restart"),"continuous"); ln.set(qn("w:distance"),"360"); sp.append(ln)
        s.footer.is_linked_to_previous=True   # Page numbers inherit the previous section footer (avoids duplicates)
        return s
    # ── Tables ──
    def table_fit(self,title,header,rows,footnote="",fs_max=11,**k):
        """Portrait table with font tier and longest-token column widths (tablefit)."""
        import tablefit
        sec=self.doc.sections[-1]; avail=(sec.page_width-sec.left_margin-sec.right_margin)/360000
        fs,ws=tablefit.fit(header,rows,avail=avail,tiers=tuple(t for t in (11,10,9,8.5,8) if t<=fs_max),pad=getattr(self,'fit_pad',0.65))   # Tables at least 8 pt; overflow raises ValueError -> adjust the columns
        return self.table(title,header,rows,ws,footnote,fs=fs,**k)
    def table(self,title,header,rows,widths_cm,footnote="",fs=11,center_cols=(),title_bold=True):
        """rows: list of lists; markup allowed in cell strings; a row whose first cell is '__H__' is a group label row (bold, merged)."""
        d=self.doc; tp=self.para(title,bold=title_bold,double=True,before=18,after=4); tp.paragraph_format.keep_with_next=True   # Table title 360 before / 80 after (twips)
        # Scale proportionally if wider than the current section text width (portrait 15.0 cm / landscape 23.7 cm with 30 mm margins)
        sec=d.sections[-1]; avail=(sec.page_width-sec.left_margin-sec.right_margin)/360000
        if sum(widths_cm)>avail:   # When scaling, reserve 44% for the first (label) column to limit wrapping; other columns keep their ratios
            rest=sum(widths_cm[1:]); first=max(widths_cm[0]*avail/sum(widths_cm),0.44*avail)
            widths_cm=[first]+[w*(avail-first)/rest for w in widths_cm[1:]]
        ncol=len(header); tbl=d.add_table(rows=1,cols=ncol); tbl.alignment=WD_TABLE_ALIGNMENT.CENTER; tbl.autofit=False
        def trflag(row,tag):
            trPr=row._tr.get_or_add_trPr()
            if trPr.find(qn(f"w:{tag}")) is None: trPr.append(OxmlElement(f"w:{tag}"))
        def keepnext(row):
            for c in row.cells:
                for pp in c.paragraphs: pp.paragraph_format.keep_with_next=True
        tblPr=tbl._tbl.tblPr
        # No vertical rules: top, below-header and bottom horizontal rules only
        borders=OxmlElement("w:tblBorders")
        for edge,val in (("top","single"),("bottom","single"),("insideH","nil"),("insideV","nil"),("left","nil"),("right","nil")):
            e=OxmlElement(f"w:{edge}"); e.set(qn("w:val"),val); e.set(qn("w:sz"),"6"); e.set(qn("w:space"),"0"); e.set(qn("w:color"),"000000"); borders.append(e)
        tblPr.append(borders)
        # LibreOffice ignores tcW alone -> fixed layout plus explicit gridCol widths
        lay=tblPr.find(qn("w:tblLayout"))   # Reuse the tblLayout already created by autofit=False (no duplicates)
        if lay is None: lay=OxmlElement("w:tblLayout"); tblPr.append(lay)
        lay.set(qn("w:type"),"fixed")
        for gc,w in zip(tbl._tbl.tblGrid.findall(qn("w:gridCol")),widths_cm): gc.set(qn("w:w"),str(int(w*567)))
        def cell(c,text,bold=False,align="left",fs=fs):
            # Double spacing = exactly 2x font size (11 pt -> 22 pt). WD_LINE_SPACING.DOUBLE uses font line height x2 (about 25 pt for TNR),
            # which makes tables sparse and splits Table 1 across pages. 11 pt double spacing is still met.
            c.text=""; p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(0); p.paragraph_format.space_before=Pt(0)
            p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.EXACTLY; p.paragraph_format.line_spacing=Pt(getattr(self,'cell_ls',2)*fs)
            p.alignment={"left":WD_ALIGN_PARAGRAPH.LEFT,"center":WD_ALIGN_PARAGRAPH.CENTER}[align]
            cc=self.counting; self.counting=False; self._emit(p,text,fs,bold); self.counting=cc
        hdr=tbl.rows[0]; trflag(hdr,"tblHeader"); trflag(hdr,"cantSplit")   # Repeat the header row on new pages
        for i,h in enumerate(header): cell(hdr.cells[i],h,bold=True,align="center" if i>0 else "left"); hdr.cells[i].width=Cm(widths_cm[i])
        # Rule below the header
        for c in hdr.cells:
            tcPr=c._tc.get_or_add_tcPr(); b=OxmlElement("w:tcBorders"); e=OxmlElement("w:bottom"); e.set(qn("w:val"),"single"); e.set(qn("w:sz"),"6"); e.set(qn("w:color"),"000000"); b.append(e); tcPr.append(b)
        last=None; made=[]
        for row in rows:
            if row and row[0]=="__H__" and made:   # Thin 170-twip spacer row at each group change
                sr=tbl.add_row(); trflag(sr,"cantSplit"); trPr=sr._tr.get_or_add_trPr(); th=OxmlElement("w:trHeight"); th.set(qn("w:val"),"170"); th.set(qn("w:hRule"),"exact"); trPr.append(th)
                sm=sr.cells[0].merge(sr.cells[ncol-1]); sp_=sm.paragraphs[0]; sp_.paragraph_format.space_after=Pt(0); sp_.paragraph_format.space_before=Pt(0)
                sp_.paragraph_format.line_spacing_rule=WD_LINE_SPACING.EXACTLY; sp_.paragraph_format.line_spacing=Pt(2); made.append((sr,True))
            r=tbl.add_row(); trflag(r,"cantSplit"); last=r; made.append((r,bool(row) and row[0]=="__H__"))
            if row and row[0]=="__H__":
                m=r.cells[0].merge(r.cells[ncol-1]); cell(m,row[1],bold=True); continue
            for i,v in enumerate(row):
                cell(r.cells[i],str(v),align="center" if (i in center_cols or (i>0 and "(" in str(v)) or i>0) else "left"); r.cells[i].width=Cm(widths_cm[i])
        # Keep a group (label + rows) together: keep_with_next until the last row, so a single row is not pushed to the next page
        for k,(r,is_h) in enumerate(made):
            nxt_is_h = k+1<len(made) and made[k+1][1]
            if k+1<len(made) and not nxt_is_h: keepnext(r)
        if footnote:
            if last is not None: keepnext(last)   # Keep footnotes from moving alone to the next page
            fp=self.para(footnote,sz=12,double=True,before=4,after=0); fp.paragraph_format.keep_together=True
            fp.paragraph_format.line_spacing_rule=WD_LINE_SPACING.EXACTLY; fp.paragraph_format.line_spacing=Pt(22)   # 22 pt, same as table cells
    # ── Save ──
    def no_black_squares(self):
        """No black squares in the Word margin (no keepNext, keepLines or pageBreakBefore). pageBreakBefore is replaced by a page-break run before the paragraph."""
        body=self.doc.element.body
        for pPr in body.iter(qn("w:pPr")):
            for tag in ("w:keepNext","w:keepLines"):
                for e in pPr.findall(qn(tag)): pPr.remove(e)
            for e in pPr.findall(qn("w:pageBreakBefore")):
                pPr.remove(e); p=pPr.getparent(); r=OxmlElement("w:r"); br=OxmlElement("w:br"); br.set(qn("w:type"),"page"); r.append(br); pPr.addnext(r)
        # U+2011 (missing from the font, shows as a box) -> Word non-breaking hyphen element <w:noBreakHyphen/>
        import copy
        for r in list(body.iter(qn("w:r"))):
            t=r.find(qn("w:t"))
            if t is None or t.text is None or "\u2011" not in t.text: continue
            parts=t.text.split("\u2011"); rPr=r.find(qn("w:rPr")); anchor=r
            for i,part in enumerate(parts):
                if i>0:
                    nr=OxmlElement("w:r")
                    if rPr is not None: nr.append(copy.deepcopy(rPr))
                    nr.append(OxmlElement("w:noBreakHyphen")); anchor.addnext(nr); anchor=nr
                if part:
                    nr=OxmlElement("w:r")
                    if rPr is not None: nr.append(copy.deepcopy(rPr))
                    nt=OxmlElement("w:t"); nt.text=part; nt.set("{http://www.w3.org/XML/1998/namespace}space","preserve"); nr.append(nt); anchor.addnext(nr); anchor=nr
            r.getparent().remove(r)
        st=self.doc.styles.element
        for tag in ("w:keepNext","w:keepLines","w:pageBreakBefore"):
            for e in list(st.iter(qn(tag))): e.getparent().remove(e)
    def save(self,path):
        import booktabs, tablefit; tablefit.ind_cells(self.doc); booktabs.fix(self.doc); self.no_black_squares(); self.doc.core_properties.author="Seongdae Kim"; self.doc.core_properties.last_modified_by="Seongdae Kim"; self.doc.core_properties.comments=""; self.doc.core_properties.title=getattr(self,"doc_title",""); self.doc.save(path)

def vancouver(ref):
    """ref dict: authors(list 'Surname AB'), title, journal(abbr), year, vol, issue, pages, doi, url, accessed, type('journal'|'web'|'code')"""
    if ref.get("type")=="web":
        return f"{ref['authors']}. {ref['title']}. {ref['url']}. {('Updated '+ref['updated']+'. ') if ref.get('updated') else ''}Accessed {ref['accessed']}."
    if ref.get("type")=="code":
        return f"{ref['authors']}. {ref['title']}. {ref.get('publisher','')}; {ref['year']}. {ref.get('url','')}"
    a=ref["authors"]; a=", ".join(a[:6])+(", et al" if len(a)>6 else "")
    vol=ref.get("vol",""); iss=f"({ref['issue']})" if ref.get("issue") else ""; pg=f":{ref['pages']}" if ref.get("pages") else ""
    return f"{a}. {ref['title']}. <i>{ref['journal']}</i> {ref['year']};{vol}{iss}{pg}."
