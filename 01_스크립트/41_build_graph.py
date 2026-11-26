#!/usr/bin/env python3
# 41_build_graph.py - principal adjacency graph (INLA graph format) from the district boundary file.
# Part of the analysis code for lifestyle-treated-dyslipidemia-korea (v1.0.1, MIT license). See README.md (Pipeline) for how to run.
#  Rule (the same as the graph block of 81_fit_inla.R): queen contiguity, i.e. two districts are neighbours when their
#  boundaries are within sqrt(machine epsilon) of each other; a district with no neighbour (island) is then linked, both
#  ways, to the district with the nearest centroid. Districts are numbered in boundary-file order (229 districts, 593 links).
#  Input:  ST_SHP (default data/boundary/final.shp)
#  Output: argument 1, default graph_593.graph in the LIPT analysis folder (the file passed to 81 as ST_GRAPH and read by 99L3)
import os, sys
import numpy as np, geopandas as gpd
from shapely.geometry import box
from shapely.strtree import STRtree
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SHP = os.environ.get("ST_SHP", os.path.join(ROOT, "data", "boundary", "final.shp"))
OUTF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "04_분석", "LIPT", "graph_593.graph")
G = gpd.read_file(SHP); geoms = list(G.geometry); n = len(geoms); snap = np.sqrt(np.finfo(float).eps)
tree = STRtree(geoms); nb = [set() for _ in range(n)]
for i in range(n):
    for j in tree.query(box(*(np.asarray(geoms[i].bounds) + [-snap, -snap, snap, snap]))):
        j = int(j)
        if j > i and geoms[i].distance(geoms[j]) <= snap: nb[i].add(j); nb[j].add(i)
cen = np.array([[g.centroid.x, g.centroid.y] for g in geoms]); isl = [k for k in range(n) if not nb[k]]
for i in isl:
    d = np.hypot(*(cen - cen[i]).T); d[i] = np.inf; j = int(np.argmin(d)); nb[i].add(j); nb[j].add(i)
lines = [str(n)] + [" ".join(map(str, [i + 1, len(nb[i])] + sorted(k + 1 for k in nb[i]))) for i in range(n)]
os.makedirs(os.path.dirname(os.path.abspath(OUTF)), exist_ok=True)
open(OUTF, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(f"[41] {OUTF}: {n} districts, {sum(len(s) for s in nb) // 2} links, islands linked {[G.region[k] for k in isl]}")
