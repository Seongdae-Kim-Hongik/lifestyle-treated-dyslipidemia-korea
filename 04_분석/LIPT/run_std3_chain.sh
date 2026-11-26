#!/bin/bash
# run_std3_chain.sh - full model chain for the principal version (std3).
# Part of the analysis code for lifestyle-treated-dyslipidemia-korea (v1.0.0, MIT license). See README.md (Pipeline) for how to run.
set -x
S="${ST_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"; cd "$S"; RS="$S/01_스크립트/rslot.sh"; RC="${ST_FBDZIP_CORRECTED:?set ST_FBDZIP_CORRECTED}"
T=LIPT; GR="$S/04_분석/$T/graph_593.graph"; D=261111; NW=3; NMV=200
q(){ while [ "$(jobs -rp | wc -l)" -ge 3 ]; do sleep 10; done; }
ST_FBDZIP="$RC" python3 01_스크립트/99L2_build_Estd3_lipt.py || exit 1
python3 01_스크립트/99c_extra_canonical_pool_lipt.py || exit 1
ST_VER=std3 python3 01_스크립트/80_build_disease_panel_v.py $T || exit 1
python3 ../논문_마스터자료/00_분석전_데이터게이트/data_gate.py 04_분석/$T/panel_${T}_std3.csv --region fbd_region > 04_분석/$T/data_gate_${T}_std3_$D.txt 2>&1
echo "GATE rc=$?"
( for V in s577 s2 s8; do ST_VER=$V python3 01_스크립트/80_build_disease_panel_v.py $T && (cd 01_스크립트 && ST_VER=$V ST_THREADS=1 ST_MV_N=2 ST_GRAPH=$([ $V = s577 ] || echo "$GR") $RS Rscript 81_fit_inla.R $T); done > 04_분석/$T/run_sens3.log 2>&1 ) &
export ST_VER=std3 ST_THREADS=1 ST_GRAPH="$GR"
(cd 01_스크립트 && ST_MV_STOP=1 $RS Rscript 81_fit_inla.R $T) > 04_분석/$T/run_std3_81a.log 2>&1 || exit 1
STEP=$(( (NMV + NW - 1) / NW ))
for k in $(seq 0 $((NW-1))); do a=$(( k*STEP+1 )); b=$(( (k+1)*STEP )); [ $b -gt $NMV ] && b=$NMV; (cd 01_스크립트 && ST_MV_RANGE=$a-$b $RS Rscript 81_fit_inla.R $T) > 04_분석/$T/run_std3_81_mv_$a.log 2>&1 & sleep 20; done
wait
(cd 01_스크립트 && $RS Rscript 81_fit_inla.R $T) > 04_분석/$T/run_std3_81b.log 2>&1 || exit 1
python3 01_스크립트/82_core_report.py $T $D > 04_분석/$T/run_std3_82.log 2>&1
python3 01_스크립트/83_check_report.py $T $D >> 04_분석/$T/run_std3_82.log 2>&1
echo "CHAIN done"
python3 01_스크립트/87_window_grid.py $T std3; (cd 01_스크립트 && TAG=$T ST_VER=std3 $RS Rscript 85_window_maps.R $T std3); python3 01_스크립트/86_yearly_maps_ehsa.py $T std3
python3 01_스크립트/88g_sens_prep.py $T std3 INFECT,GCA || exit 1
cd 01_스크립트; export TAG=$T NCO=INFECT,GCA
L=../04_분석/$T
for G in 1 2 3 4 5 6; do q; GROUP=$G $RS Rscript 88g_sens_suite.R > $L/run_std3_88g_$G.log 2>&1 & sleep 5; done
q; $RS Rscript 88h_ppc_varpart.R > $L/run_std3_88h.log 2>&1 &
for G in nb struct review kh; do q; $RS Rscript 88k_struct_kh.R $G > $L/run_std3_88k_$G.log 2>&1 & sleep 5; done
wait
cd ..; TAG=$T ST_VER=std3 python3 01_스크립트/89g_sens_combine.py $T std3 > 04_분석/$T/run_std3_89g.log 2>&1
echo "ALL rc=$?"; grep -l "FAILED" 04_분석/$T/run_std3_88*.log; true
