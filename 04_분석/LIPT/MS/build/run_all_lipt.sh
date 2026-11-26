#!/bin/bash

set -e; cd "$(dirname "$0")"; O=../out_ang; mkdir -p $O
python3 figs_lipt.py
cp -X ../out/Figures/Figure_1.tif $O/Figure_1.tif; cp -X ../out/Figures/Figure_2.tif $O/Figure_2.tif
python3 build_manuscript_lipt.py
python3 build_supplement_lipt.py
python3 cover_ang_lipt.py
F="Manuscript_LIPT_ANG Title_Page_LIPT_ANG Supplementary_Material_LIPT_ANG Cover_Letter_LIPT_ANG STROBE_Checklist_LIPT_ANG"
for f in $F; do /opt/homebrew/bin/soffice --headless -env:UserInstallation=file:///tmp/lo_lipt_ang_all --convert-to pdf --outdir $O $O/$f.docx > /dev/null 2>&1; done
python3 sanitize_docx.py --no-anon $(for f in $F; do echo $O/$f.docx; done) > /dev/null
python3 check_ang_lipt.py
