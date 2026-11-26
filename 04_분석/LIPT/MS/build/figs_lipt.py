# -*- coding: utf-8 -*-
# figs_lipt.py: figures for the LIPT manuscript.
#  Rules: colour; all panel letters the same size (48 pt, bold); north arrow 3x; no explanatory text inside figures; joins by district code only.
#  Panel letters = upper-case A, B. Sejong = not observed (light grey, no hatching).
#  Fig 1 (A) whole-period residual spatial RR (B) treatment SIR x suspicion SIR quadrants; Fig 2 model-wise RR of the 3 robust variables; Fig S1 (A) EHSA (B) hot/cold spots in two windows
import os, unicodedata, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from numbers_lipt import load, ROB, SHP, EDU, IMS, MPA
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.environ.get("LIPT_B", os.path.dirname(os.path.dirname(HERE))); RS = os.path.join(B, "results_std3")   # input directory from LIPT_B
NORESLAB = os.environ.get("LIPT_FIG2_RESLAB", "1") == "0"   # LIPT_FIG2_RESLAB=0: no value labels on the residents-denominator row of Fig. 2 (values in Table 2)
FIG = os.path.join(HERE, "figs"); OUTF = os.environ.get("LIPT_OUT") or os.path.join(os.path.dirname(HERE), "out", "Figures"); os.makedirs(FIG, exist_ok=True); os.makedirs(OUTF, exist_ok=True)
MM = 1 / 25.4; W = 174 * MM; DPI = 600; LW = 0.3; PANEL_LABEL_PT = 48
plt.rcParams.update({"font.family": "Arial", "font.size": 10, "axes.labelsize": 12, "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 10, "legend.title_fontsize": 10, "axes.linewidth": 0.6, "pdf.fonttype": 42})   # Print-scale axis titles 12 pt, ticks 10 pt (figures drawn at print width)
NFC = lambda s: unicodedata.normalize("NFC", str(s)).strip()
N = load()
GJ = os.path.join(FIG, "districts_5179.geojson")   # Export boundaries to GeoJSON (EPSG:5179) and draw from that file
if not os.path.exists(GJ): gpd.read_file(SHP).set_crs(epsg=5179, allow_override=True).to_file(GJ, driver="GeoJSON")
G = gpd.read_file(GJ).set_crs(epsg=5179, allow_override=True); G["cd"] = G.sigungu_cd.astype(str); G["sido"] = G.cd.str[:2]; SIDO = G.dissolve("sido")
XL = (G.total_bounds[0], G.total_bounds[2]); YL = (G.total_bounds[1], G.total_bounds[3])
rd = lambda f: pd.read_csv(os.path.join(RS, f), encoding="utf-8-sig", dtype={"sigungu_cd": str})
def letter(fig, ch, x, y):   # Constant size in figure coordinates
    fig.text(x, y, ch, fontsize=PANEL_LABEL_PT, fontweight="bold", va="top", ha="left")
from matplotlib.patches import Polygon as MPoly, Rectangle
def mapax(ax, fs=10):
    SIDO.boundary.plot(ax=ax, color="#404040", linewidth=0.45); ax.set_xlim(*XL); ax.set_ylim(*YL); ax.set_axis_off(); ax.set_aspect("equal")
    x0, x1 = XL; y0, y1 = YL; W_ = x1 - x0; H_ = y1 - y0
    # 0-50-100 km black-and-white scale bar and filled-triangle north arrow in the empty Yellow Sea area (clear of Jeju and islands)
    bx, by, bh = x0 + 0.02 * W_, y0 + 0.49 * H_, 0.012 * H_
    for i, c in enumerate(("black", "white")): ax.add_patch(Rectangle((bx + i * 50000, by), 50000, bh, facecolor=c, edgecolor="black", linewidth=0.6))
    for d in (0, 50000, 100000): ax.text(bx + d, by + bh + 0.008 * H_, f"{d // 1000}", ha="center", va="bottom", fontsize=fs)
    ax.text(bx + 50000, by - 0.008 * H_, "km", ha="center", va="top", fontsize=fs)
    ax_, ay = x0 + 0.06 * W_, y0 + 0.60 * H_; hw, hh = 0.022 * W_, 0.075 * H_
    ax.add_patch(MPoly([(ax_ - hw, ay), (ax_, ay + hh), (ax_ + hw, ay)], closed=True, facecolor="black", edgecolor="black", linewidth=0.5))
    ax.text(ax_, ay + hh + 0.012 * H_, "N", ha="center", va="bottom", fontsize=24, fontweight="bold")   # North arrow N 24 pt (at print width)
def save(fig, k):
    p = os.path.join(FIG, f"Fig{k}.png"); fig.savefig(p, dpi=DPI, facecolor="white"); plt.close(fig)
    im = Image.open(p).convert("RGB"); im.save(p, dpi=(DPI, DPI))
    if not str(k).startswith("S"): im.save(os.path.join(OUTF, f"Figure_{k}.tif"), dpi=(DPI, DPI), compression="tiff_lzw")
    return im.size

S6 = rd("S6_spatial_RR.csv"); S6 = S6[S6.observed]; assert len(S6) == 228
UNOBS = "#e6e6e6"
CD = dict(zip(S6.fbd_region.map(NFC), S6.sigungu_cd))   # Join only through the code table from the same pipeline output
GAP = pd.read_csv(os.path.join(RS, "S50_lipt_suspect_gap.csv"), encoding="utf-8-sig"); GAP["cd"] = GAP.fbd_region.map(NFC).map(CD); assert GAP.cd.notna().all() and len(GAP) == 228
QL = ["treated high / suspected low", "treated low / suspected high", "both high", "both low"]
assert GAP.quadrant.value_counts().to_dict() == N["gap"]["all_2011-24"]["quadrants"]

# Fig 1: 6 discrete classes (fixed breaks); No data in every map legend
BR = [0, 0.8, 0.9, 1, 1.1, 1.25, 99]; LB = ["<0.80", "0.80–0.89", "0.90–0.99", "1.00–1.09", "1.10–1.24", "≥1.25"]
PAL = ["#2166AC", "#67A9CF", "#D1E5F0", "#FDDBC7", "#EF8A62", "#B2182B"]
assert BR[0] < N["rr_min"] < BR[1] and BR[-2] < N["rr_max"] < 2
def nodata(): return Patch(facecolor=UNOBS, edgecolor="#777777", linewidth=LW, label="No data (1)")
MH = 4.6   # Map axis height (inches)
fh_ = 1.10 + MH + 0.55; fig = plt.figure(figsize=(W, fh_))
a0 = fig.add_axes([0.00, 1.10 / fh_, 0.49, MH / fh_]); a1 = fig.add_axes([0.51, 1.10 / fh_, 0.49, MH / fh_])
d = S6.set_index("sigungu_cd"); gg = G.copy(); gg["v"] = gg.cd.map(d.RR); gg["c"] = gg.cd.map(d["class"]); assert int(gg.v.isna().sum()) == 1
gg[gg.v.isna()].plot(ax=a0, color=UNOBS, edgecolor="#a0a0a0", linewidth=LW); gg = gg[gg.v.notna()]
gg.plot(ax=a0, column="v", cmap=ListedColormap(PAL), norm=BoundaryNorm(BR, len(PAL)), edgecolor="#a0a0a0", linewidth=LW); mapax(a0)
gg[gg.c == "coldspot"].boundary.plot(ax=a0, color="#08306B", linewidth=0.7, linestyle=(0, (2.0, 1.2))); gg[gg.c == "hotspot"].boundary.plot(ax=a0, color="black", linewidth=0.7)
h = [Patch(facecolor=c, edgecolor="#777777", linewidth=LW, label=l) for c, l in zip(PAL, LB)] + [Patch(facecolor="none", edgecolor="black", linewidth=0.9, label=f"Hot spot ({N['n_hot']})"), Patch(facecolor="none", edgecolor="#08306B", linewidth=0.9, linestyle="--", label=f"Cold spot ({N['n_cold']})"), nodata()]
a0.legend(handles=h, title="Residual spatial RR", loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=3, frameon=False, columnspacing=0.8, handlelength=1.3)
QP = {"treated high / suspected low": "#B2182B", "treated low / suspected high": "#2166AC", "both high": "#EF8A62", "both low": "#D1E5F0"}
QT = {"treated high / suspected low": "Treated >1, suspected ≤1", "treated low / suspected high": "Treated ≤1, suspected >1", "both high": "Both >1", "both low": "Both ≤1"}
g2 = G.copy(); g2["q"] = g2.cd.map(GAP.set_index("cd").quadrant); assert int(g2.q.isna().sum()) == 1
g2[g2.q.isna()].plot(ax=a1, color=UNOBS, edgecolor="#a0a0a0", linewidth=LW); g2 = g2[g2.q.notna()]
g2.plot(ax=a1, color=[QP[q] for q in g2.q], edgecolor="#a0a0a0", linewidth=LW); mapax(a1)
qc = g2.q.value_counts()
a1.legend(handles=[Patch(facecolor=QP[q], edgecolor="#777777", linewidth=LW, label=f"{QT[q]} ({qc[q]})") for q in QL] + [nodata()], title="Standardized ratios, 2011–2024", loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=2, frameon=False, columnspacing=0.8, handlelength=1.3)
letter(fig, "A", 0.005, 0.995); letter(fig, "B", 0.515, 0.995)
s1 = save(fig, 1)

# Fig 2: points, intervals and value labels only for the 5 sensitivity models; main model as a grey band (values only in Table 2); legend filled = credible, open = not credible
LAB = {EDU: "Tertiary\neducation", IMS: "Internal-medicine\nspecialists per\n100,000 residents", MPA: "Moderate-to-\nvigorous\nphysical activity"}
ORD = [EDU, IMS, MPA]; assert set(ORD) == set(ROB)
MOD = [("Knorr-Held type II (best fitting)", lambda v: N["s43"][("KH_typeII", v)], "#2166AC", "s"),
       ("Knorr-Held type IV", lambda v: N["s43"][("KH_typeIV", v)], "#B2182B", "D"),
       ("2011–2017 only", lambda v: N["win_irr"][(v, "W1_2011-17")], "#1b7837", "o"),
       ("2018–2024 only", lambda v: N["win_irr"][(v, "W2_2018-24")], "#E08214", "v"),
       ("Expected numbers from residents", lambda v: N["epop"][v], "#555555", "^")]
PM = lambda v: (N["main"][v]["IRR"], N["main"][v]["lo"], N["main"][v]["hi"])
lo_all = min(min(f(v)[1] for v in ORD for _, f, _, _ in MOD), min(PM(v)[1] for v in ORD)); hi_all = max(max(f(v)[2] for v in ORD for _, f, _, _ in MOD), max(PM(v)[2] for v in ORD))
fig, ax = plt.subplots(figsize=(W, 6.6)); fig.subplots_adjust(left=0.19, right=0.74, top=0.98, bottom=0.25)
off = np.linspace(-0.34, 0.34, len(MOD))
for i, v in enumerate(ORD):
    e0, l0, h0 = PM(v); ax.add_patch(Rectangle((l0, i - 0.44), h0 - l0, 0.88, facecolor="#e3e3e3", edgecolor="none", zorder=0)); ax.plot([e0, e0], [i - 0.44, i + 0.44], color="#9a9a9a", lw=0.8, zorder=1)
    for (lab, f, col, mk), o in zip(MOD, off):
        e, lo, hi, cr = f(v)[:4]; ax.plot([lo, hi], [i + o] * 2, color=col, lw=1.0, zorder=2)
        ax.plot(e, i + o, marker=mk, ms=5.5, mew=1.0, ls="none", color=col, markerfacecolor=(col if cr else "white"), zorder=3)
        if NORESLAB and lab == "Expected numbers from residents": continue   # Values only in the Residents column of Table 2
        ax.text(1.163, i + o, f"{e:.3f} ({lo:.3f}–{hi:.3f})", va="center", ha="left", fontsize=9, color=col, transform=ax.transData, clip_on=False)
ax.axvline(1, color="#404040", lw=0.6, ls=":"); ax.set_yticks(range(len(ORD))); ax.set_yticklabels([LAB[v] for v in ORD]); ax.invert_yaxis(); ax.set_ylim(len(ORD) - 0.5, -0.5)
xt = [0.94, 0.97, 1.00, 1.03, 1.06, 1.09, 1.12, 1.15]; assert xt[0] <= lo_all and hi_all <= xt[-1], (lo_all, hi_all)
ax.set_xlim(xt[0], xt[-1]); ax.set_xticks(xt); ax.set_xticklabels([f"{x:.2f}" for x in xt]); ax.minorticks_off()
ax.set_xlabel("Rate ratio per 1 SD (95% credible interval)"); ax.spines[["top", "right"]].set_visible(False)
hl = [Line2D([0], [0], color=c, marker=m, lw=1.0, ms=5.5, mew=1.0, label=l) for l, _, c, m in MOD]
hl += [Patch(facecolor="#e3e3e3", edgecolor="none", label="Principal model (Table 2)"), Line2D([0], [0], color="black", marker="o", ls="none", ms=5.5, label="Filled, CrI excludes 1"), Line2D([0], [0], color="black", marker="o", ls="none", ms=5.5, markerfacecolor="white", label="Open, CrI includes 1")]
ax.legend(handles=hl, loc="upper center", bbox_to_anchor=(0.62, -0.11), ncol=2, frameon=False, columnspacing=1.2)
s2 = save(fig, 2)

# Fig S1: canvas 159 mm = embedded 15.9 cm (no scaling, panel letters stay 48 pt); full-category legend; No data in both panels
WS = 159 * MM
EH = rd("S11_ehsa.csv")
CATS = [f"{a} {b}" for b in ("hot", "cold") for a in ("New", "Consecutive", "Intensifying", "Persistent", "Diminishing", "Sporadic", "Oscillating", "Historical")] + ["No pattern"]
EPAL = {"New hot": "#fdd0a2", "Consecutive hot": "#fdae6b", "Intensifying hot": "#a50f15", "Persistent hot": "#de2d26", "Diminishing hot": "#fc9272", "Sporadic hot": "#fee0d2", "Oscillating hot": "#d6a5c9", "Historical hot": "#bcbddc",
        "New cold": "#c6dbef", "Consecutive cold": "#9ecae1", "Intensifying cold": "#08519c", "Persistent cold": "#3182bd", "Diminishing cold": "#6baed6", "Sporadic cold": "#deebf7", "Oscillating cold": "#a1d99b", "Historical cold": "#c7e9c0", "No pattern": "#f7f7f7"}
WM = rd("S4b_window_spatialRR.csv"); WM = WM[WM["class"] != "unobserved"]
nh = WM[WM["class"] == "hotspot"].groupby("sigungu_cd").size(); nc = WM[WM["class"] == "coldspot"].groupby("sigungu_cd").size()
assert int((nh == 2).sum()) == N["hot_all_windows"] and int((nc == 2).sum()) == N["cold_all_windows"]
MS1 = 3.9; fhs = 2.75 + MS1 + 0.55
fig = plt.figure(figsize=(WS, fhs)); a0 = fig.add_axes([0.00, 2.75 / fhs, 0.49, MS1 / fhs]); a1 = fig.add_axes([0.51, 2.75 / fhs, 0.49, MS1 / fhs])
gg = G.copy(); gg["c"] = gg.cd.map(EH.set_index("sigungu_cd").EHSA); assert int(gg.c.isna().sum()) == 1
gg[gg.c.isna()].plot(ax=a0, color=UNOBS, edgecolor="#a0a0a0", linewidth=LW); gu = gg[gg.c.isna()].copy(); gg = gg[gg.c.notna()].copy()
gg.plot(ax=a0, color=[EPAL[c] for c in gg.c], edgecolor="#a0a0a0", linewidth=LW); mapax(a0, fs=9)
cnt = EH.EHSA.value_counts()
a0.legend(handles=[Patch(facecolor=EPAL[c], edgecolor="#777777", linewidth=LW, label=f"{c} ({int(cnt.get(c, 0))})") for c in CATS] + [nodata()], title="Category (districts)", loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=2, frameon=False, columnspacing=0.6, handlelength=1.1, fontsize=9, title_fontsize=9, labelspacing=0.35)
hh = gg.cd.map(nh).fillna(0).astype(int); cc = gg.cd.map(nc).fillna(0).astype(int)
gg["k"] = np.where((hh > 0) & (cc > 0), 9, hh - cc)
KP = {-2: "#2166AC", -1: "#92C5DE", 0: "#f7f7f7", 1: "#F4A582", 2: "#B2182B", 9: "#c2a5cf"}
KL = {-2: "Cold spot in both windows", -1: "Cold spot in one", 0: "Neither", 1: "Hot spot in one", 2: "Hot spot in both windows", 9: "Hot or cold by window"}
gu.plot(ax=a1, color=UNOBS, edgecolor="#a0a0a0", linewidth=LW)
gg.plot(ax=a1, color=[KP[k] for k in gg.k], edgecolor="#a0a0a0", linewidth=LW); mapax(a1, fs=9)
kc = gg.k.value_counts()
a1.legend(handles=[Patch(facecolor=KP[k], edgecolor="#777777", linewidth=LW, label=f"{KL[k]} ({int(kc.get(k, 0))})") for k in (2, 1, 0, -1, -2, 9)] + [nodata()], title="Windows 2011–2017 and 2018–2024", loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=1, frameon=False, handlelength=1.1, fontsize=9, title_fontsize=9, labelspacing=0.35)
letter(fig, "A", 0.005, 0.995); letter(fig, "B", 0.515, 0.995)
s3 = save(fig, "S1")
# Fig S2: observed standardized ratio and main-model fitted ratio maps (2011-2024, same fixed 6 classes)
E84 = pd.read_csv(os.path.join(B, "results_extra", "E084_map_values_SIR_obs_fitted.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str}); E84 = E84[E84.period == "2011-2024"].set_index("sigungu_cd"); assert len(E84) == 228
BR2 = [0, 0.8, 0.9, 1, 1.1, 1.25, 99]; assert E84.SIR_obs.min() > 0 and E84.SIR_obs.max() < 2
fhs2 = 0.95 + MS1 + 0.55; fig = plt.figure(figsize=(WS, fhs2))
for j, (col, ttl) in enumerate((("SIR_obs", "Observed ratio"), ("SIR_fitted", "Fitted ratio"))):
    ax = fig.add_axes([0.00 + 0.51 * j, 0.95 / fhs2, 0.49, MS1 / fhs2]); g3 = G.copy(); g3["v"] = g3.cd.map(E84[col]); assert int(g3.v.isna().sum()) == 1
    g3[g3.v.isna()].plot(ax=ax, color=UNOBS, edgecolor="#a0a0a0", linewidth=LW); g3 = g3[g3.v.notna()]
    g3.plot(ax=ax, column="v", cmap=ListedColormap(PAL), norm=BoundaryNorm(BR2, len(PAL)), edgecolor="#a0a0a0", linewidth=LW); mapax(ax, fs=9)
fig.legend(handles=[Patch(facecolor=c, edgecolor="#777777", linewidth=LW, label=l) for c, l in zip(PAL, LB)] + [nodata()], title="Standardized ratio, 2011–2024", loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=4, frameon=False, fontsize=9, title_fontsize=9, columnspacing=0.8, handlelength=1.2)
letter(fig, "A", 0.005, 0.995); letter(fig, "B", 0.515, 0.995)
s4 = save(fig, "S2")
for k, s in zip((1, 2, "S1", "S2"), (s1, s2, s3, s4)): print(f"Fig{k}: {s[0]}x{s[1]} px = {s[0]/DPI*25.4:.0f} x {s[1]/DPI*25.4:.0f} mm")
