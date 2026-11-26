#!/bin/bash
# rslot.sh - limit the number of concurrent single-threaded R jobs.
# Part of the analysis code for lifestyle-treated-dyslipidemia-korea (v1.0.2, MIT license). See README.md (Pipeline) for how to run.
N=${SK_RSLOTS:-9}; D="${RSLOT_DIR:-$HOME/.cache/sk_rslots}"; mkdir -p "$D"
while :; do
  for i in $(seq 1 "$N"); do
    if mkdir "$D/s$i" 2>/dev/null; then
      echo $$ > "$D/s$i/pid"; trap 'rm -rf "$D/s'$i'"' EXIT INT TERM
      nice -n 10 "$@"; exit $?
    fi
    p=$(cat "$D/s$i/pid" 2>/dev/null); [ -n "$p" ] && ! kill -0 "$p" 2>/dev/null && rm -rf "$D/s$i"
  done
  sleep 5
done
