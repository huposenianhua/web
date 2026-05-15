#!/bin/bash
BASE_URL="http://localhost:80"
LOG_DIR="/var/www/html/woody/res/debug"
LOG_FILE="$LOG_DIR/cron_fetch.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

fetch_page() {
    local page="$1"
    local url="${BASE_URL}${page}"
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 120 "$url")
    if [ "$http_code" = "200" ]; then
        log "OK  $page (HTTP $http_code)"
    else
        log "ERR $page (HTTP $http_code)"
    fi
}

log "=== Starting afternoon fetch ==="

fetch_page "/woody/res/lofcn.php"
sleep 30
fetch_page "/woody/res/overnightcn.php"
sleep 30
fetch_page "/woody/res/chinafuturecn.php"
sleep 60
fetch_page "/woody/res/qdiicn.php"
sleep 60
fetch_page "/woody/res/qdiimixcn.php"
sleep 60
fetch_page "/woody/res/qdiihkcn.php"
sleep 60
fetch_page "/woody/res/qdiijpcn.php"
sleep 60
fetch_page "/woody/res/qdiieucn.php"

log "=== Afternoon fetch completed ==="
