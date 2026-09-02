#!/usr/bin/env bash
# First-run backfill for the TANSTAAFL corpus. RUN THIS ON YOUR OWN MACHINE.
#
# NSE and BSE block datacentre IPs and most cloud sandboxes block them right back,
# so this cannot run from a hosted session. It is safe to interrupt and rerun at
# any point: gaps are computed from the manifest, never remembered, so it resumes
# from wherever it stopped.
#
#   ./bootstrap.sh                 # full backfill, prices from 2005
#   FROM=2015 ./bootstrap.sh       # shallower and much faster
#   DRY=1 ./bootstrap.sh           # fetches, but writes nothing — use it to check
#                                  # credentials and connectivity before committing
#                                  # to a multi-hour run
#
set -uo pipefail

FROM="${FROM:-2005}"
TO="${TO:-$(date +%Y)}"
ANN_FROM="${ANN_FROM:-2015}"          # announcements: NSE's archive thins out earlier
SLEEP="${SLEEP:-180}"                 # pause between year-slices; be a good citizen
DRY="${DRY:-}"
CLI="tanstaafl-ingest"
[ -n "$DRY" ] && CLI="tanstaafl-ingest --dry-run"

command -v tanstaafl-ingest >/dev/null || {
  echo "tanstaafl-ingest not on PATH. Run:  pip install -e '.[remote]'" >&2
  exit 1
}

log() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

# One slice per year. A single 5,000-day sweep from one IP invites a temporary ban,
# and a partial year is cheap to redo; a partial 20-year run is not.
slice_years() {
  local source=$1 first=$2
  for y in $(seq "$first" "$TO"); do
    log "$source $y"
    if ! $CLI fetch "$source" --start "$y-01-01" --end "$y-12-31"; then
      # Exit 2 is an unreachable source (blocked, rate-limited, cookie expired).
      # Stop rather than hammer: the gaps are recorded and the rerun resumes.
      echo "!! $source stalled at $y — fix the cause, then rerun this script." >&2
      return 1
    fi
    [ -z "$DRY" ] && sleep "$SLEEP"
  done
}

log "prices: NSE $FROM..$TO"
slice_years nse_bhavcopy "$FROM" || exit 1

log "announcements: NSE $ANN_FROM..$TO (+ attachments for weighty categories)"
for y in $(seq "$ANN_FROM" "$TO"); do
  $CLI fetch nse_announcements --start "$y-01-01" --end "$y-12-31" --attachments \
    || { echo "!! nse_announcements stalled at $y" >&2; break; }
  [ -z "$DRY" ] && sleep "$SLEEP"
done

# BSE is complementary, not redundant: some companies are BSE-only, and filers
# sometimes submit to one exchange first. For a veto-grade event like an auditor
# resignation, the earlier of the two dates is the one that matters.
log "announcements: BSE $ANN_FROM..$TO"
for y in $(seq "$ANN_FROM" "$TO"); do
  $CLI fetch bse_announcements --start "$y-01-01" --end "$y-12-31" \
    || { echo "!! bse_announcements stalled at $y" >&2; break; }
  [ -z "$DRY" ] && sleep "$SLEEP"
done

if [ -z "$DRY" ]; then
  log "integrity"
  tanstaafl-ingest verify || echo "!! corpus failed verification — do NOT run analysis" >&2

  log "remaining gaps"
  tanstaafl-ingest gaps nse_bhavcopy --start "$FROM-01-01"

  log "classification"
  tanstaafl-ingest classify

  cat <<'EOF'

Done. From here on, a daily catch-up is:

  tanstaafl-ingest fetch nse_bhavcopy      --start last
  tanstaafl-ingest fetch nse_announcements --start last --attachments

Both are no-ops when the corpus is current, so schedule them freely.
Watch the unclassified share in `classify` — a rise means exchange phrasing
drifted and the rules in classify.py need extending.
EOF
fi
