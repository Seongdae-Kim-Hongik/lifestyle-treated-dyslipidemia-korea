#!/bin/bash
# Full build: figures -> manuscript and title page -> supplement and STROBE -> cover letter -> sanitize (author metadata kept) -> PDF -> checks
set -e; cd "$(dirname "$0")"; O="${LIPT_OUT:-../out}"; S="${LIPT_SUFFIX:-}"; mkdir -p "$O"
SOFFICE="${SOFFICE:-$(command -v soffice)}"; LOPROF="$(mktemp -d "${TMPDIR:-/tmp}/lo_lipt_XXXXXX")"
LIPT_FIG2_RESLAB=0 python3 figs_lipt.py   # figures (no value labels on the residents-denominator row of Fig. 2) -> $O/Figure_1.tif, Figure_2.tif
python3 build_manuscript_lipt.py
python3 build_supplement_lipt.py
[ -f cover_letter_lipt.py ] && python3 cover_letter_lipt.py   # optional (not part of the public code)
F="Manuscript$S Title_Page$S Supplementary_Material$S STROBE_Checklist$S"; [ -f "$O/Cover_Letter$S.docx" ] && F="$F Cover_Letter$S"
for f in $F; do "$SOFFICE" --headless -env:UserInstallation=file://$LOPROF --convert-to pdf --outdir "$O" "$O/$f.docx" > /dev/null 2>&1; done
[ -f sanitize_textdiff_lipt.py ] && python3 sanitize_textdiff_lipt.py pre $(for f in $F; do echo $O/$f.docx; done)
python3 sanitize_docx.py --no-anon $(for f in $F; do echo $O/$f.docx; done) > /dev/null
[ -f sanitize_textdiff_lipt.py ] && python3 sanitize_textdiff_lipt.py post $(for f in $F; do echo $O/$f.docx; done)   # text before and after sanitizing must match
if [ -f check_manuscript_lipt.py ]; then python3 check_manuscript_lipt.py; fi
