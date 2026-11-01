#!/bin/bash
# build -> DSN -> Freerouting 1.9 (xvfb) -> SES import + GND pour -> DRC
set -e
cd "$(dirname "$0")"
B="$(cd .. && pwd)/robo-garage/robo-garage"
${PY:-python3} build.py >/dev/null
${PY:-python3} -c "import route; route.export_dsn('$B.kicad_pcb', '$B.dsn')"
rm -f $B.ses
timeout --foreground ${FR_TIMEOUT:-500} xvfb-run -a java -jar ../tools/freerouting-1.9.0.jar -de $B.dsn -do $B.ses -mp ${PASSES:-40} -mt 1 < /dev/null > $B.fr.log 2>&1 || true
grep -a -E "Auto-routing was completed|optimization was completed|Saving" $B.fr.log | sed 's/.*INFO  //' | tail -3
${PY:-python3} finish.py 2>&1 | grep -v "memory leak" | tail -2
