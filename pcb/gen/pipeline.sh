#!/bin/bash
# build -> DSN -> Freerouting 1.9 (xvfb) -> SES import + GND pour -> DRC
set -e
cd "$(dirname "$0")"
B="$(cd .. && pwd)/robo-garage/robo-garage"
"${PY:-python3}" build.py >/dev/null
"${PY:-python3}" -c "import route; route.export_dsn('$B.kicad_pcb', '$B.dsn')"
rm -f "$B.ses"
# -oit 1: stop the optimizer once a pass gains < 1 % (one run looped for > 20 min); if it still times out (FR_TIMEOUT,
# default 900 s), route again without the optimizer (-mt 0) so a session file always exists
timeout --foreground "${FR_TIMEOUT:-900}" xvfb-run -a java -jar ../tools/freerouting-1.9.0.jar \
    -de "$B.dsn" -do "$B.ses" -mp "${PASSES:-40}" -mt 1 -oit 1 < /dev/null > "$B.fr.log" 2>&1 || true
if [ ! -s "$B.ses" ]; then
    echo "optimizer timed out -> routing without optimization"
    timeout --foreground "${FR_TIMEOUT:-900}" xvfb-run -a java -jar ../tools/freerouting-1.9.0.jar \
        -de "$B.dsn" -do "$B.ses" -mp "${PASSES:-40}" -mt 0 < /dev/null > "$B.fr.log" 2>&1 || true
fi
grep -a -E "Auto-routing was completed|optimization was completed|Saving" "$B.fr.log" | sed 's/.*INFO  //' | tail -3
"${PY:-python3}" finish.py 2>&1 | grep -v "memory leak" | tail -2
