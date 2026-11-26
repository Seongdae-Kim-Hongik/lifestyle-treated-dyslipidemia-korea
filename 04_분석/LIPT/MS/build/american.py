
import re
from british import STEMS, WORDS
REV = {v: k for k, v in WORDS.items() if v not in ("per cent", "analyses")}
REV.update({"per cent": "percent", "dyslipidaemia": "dyslipidemia", "dyslipidaemias": "dyslipidemias", "hypercholesterolaemia": "hypercholesterolemia",
            "programme": "program", "programmes": "programs", "towards": "toward", "standardised": "standardized", "ageing": "aging", "practise": "practice",
            "glycaemic": "glycemic", "anaemia": "anemia", "haemoglobin": "hemoglobin", "judgement": "judgment", "judgements": "judgments", "modelling": "modeling", "modelled": "modeled",
            "enrol": "enroll", "enrolment": "enrollment", "catalogue": "catalog", "analysed": "analyzed", "analyse": "analyze", "analysing": "analyzing", "neighbouring": "neighboring",
            "labelled": "labeled", "travelled": "traveled", "colour": "color", "colours": "colors", "grey": "gray", "centre": "center", "centres": "centers", "centred": "centered",
            "specialised": "specialized", "randomised": "randomized", "recognised": "recognized", "organised": "organized", "penalised": "penalized", "summarised": "summarized",
            "acknowledgements": "acknowledgments", "acknowledgement": "acknowledgment", "paediatric": "pediatric", "oedema": "edema", "favourable": "favorable", "behaviour": "behavior",
            "winsorise": "winsorize", "winsorised": "winsorized", "winsorising": "winsorizing", "winsorisation": "winsorization", "favouring": "favoring", "favours": "favors", "favour": "favor", "favoured": "favored"})
SSTEMS = [s[:-1] + "s" for s in STEMS]
def amer(t):
    if not t: return t
    t = t.replace("per cent", "percent")
    def stem(m):
        w = m.group(0); low = w.lower()
        if low.startswith(("analys", "advertis", "exercis", "supervis", "comprom", "surpris", "expertis", "advis", "revis", "promis", "rais", "premis", "precis", "concis", "devis", "dispos", "suppos", "compos", "propos", "impos", "expos", "purpos", "televis", "improvis", "franchis", "merchandis", "disguis", "chastis", "wis", "rise", "arise", "noise", "praise", "cruise", "bruise", "raise")):
            return w
        for s in SSTEMS:
            if low.startswith(s):
                r = s[:-1] + "z" + low[len(s):]
                return r[0].upper() + r[1:] if w[0].isupper() else r
        return w
    t = re.sub(r"\b[A-Za-z]*is(?:e|ed|es|ing|ation|ations|er|ers)\b", stem, t)
    def word(m):
        w = m.group(0); r = REV.get(w.lower())
        if r is None: return w
        return r[0].upper() + r[1:] if w[0].isupper() else r
    return re.sub(r"\b[A-Za-z]+\b", word, t)
if __name__ == "__main__":
    print(amer("Standardised ratios were modelled; dyslipidaemia programme centre neighbours behaviour; analysis analyses Analyses; standardisation penalised specialised; per cent; organisation; precise; exercise; raised; otherwise; promise; summarise; hypercholesterolaemia; ageing"))
