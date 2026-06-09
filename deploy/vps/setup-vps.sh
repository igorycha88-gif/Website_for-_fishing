#!/bin/bash
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

FISHMAP_DIR="/opt/fishmap"
SMARTTRAFFIC_DIR="/opt/smarttraffic"
COMPOSE_FILE="docker-compose.vps.yml"
ENV_FILE=".env.vps"

log()  { echo -e "${GREEN}[FishMap]${NC} $1"; }
warn() { echo -e "${YELLOW}[FishMap]${NC} $1"; }
err()  { echo -e "${RED}[FishMap]${NC} $1"; exit 1; }

check_prerequisites() {
    log "Checking prerequisites..."
    command -v docker >/dev/null 2>&1 || err "Docker not installed"
    docker compose version >/dev/null 2>&1 || err "Docker Compose not installed"
    [ -f "$ENV_FILE" ] || err ".env.vps not found. Copy .env.vps.example and fill in values."
    log "Prerequisites OK"
}

source_env() {
    set -a
    source "$FISHMAP_DIR/$ENV_FILE"
    set +a
}

configure_smarttraffic_nginx() {
    log "Configuring SmartTraffic nginx for FishMap..."

    [ -d "$SMARTTRAFFIC_DIR" ] || err "SmartTraffic not found at $SMARTTRAFFIC_DIR"

    source_env
    local DOMAIN="${FISHMAP_DOMAIN:-yourdomain.ru}"

    local SRC_CONF="$FISHMAP_DIR/deploy/vps/nginx-fishmap.conf"
    local TARGET_DIR="$SMARTTRAFFIC_DIR/deploy/server-ru/nginx/conf.d"
    mkdir -p "$TARGET_DIR"

    sed "s/FISHMAP_DOMAIN/$DOMAIN/g" "$SRC_CONF" > "$TARGET_DIR/fishmap.conf"
    log "Nginx config written (domain: $DOMAIN)"

    local OVERRIDE="$SMARTTRAFFIC_DIR/docker-compose.override.yml"

    if [ ! -f "$OVERRIDE" ]; then
        cat > "$OVERRIDE" << 'EOF'
services:
  nginx:
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - ./deploy/server-ru/nginx/conf.d/fishmap.conf:/etc/nginx/conf.d/fishmap.conf:ro
EOF
        log "Created new docker-compose.override.yml"
    else
        if ! grep -q "host.docker.internal" "$OVERRIDE"; then
            echo '      - "host.docker.internal:host-gateway"' >> "$OVERRIDE"
            log "Added host.docker.internal to override"
        fi

        if ! grep -q "fishmap.conf" "$OVERRIDE"; then
            echo '      - ./deploy/server-ru/nginx/conf.d/fishmap.conf:/etc/nginx/conf.d/fishmap.conf:ro' >> "$OVERRIDE"
            log "Added fishmap.conf volume to override"
        fi
    fi
}

build_and_start() {
    log "Building FishMap containers (this may take 5-10 min)..."
    docker compose -f "$COMPOSE_FILE" build 2>&1 | tail -10

    log "Starting FishMap services..."
    docker compose -f "$COMPOSE_FILE" up -d

    log "Waiting for healthchecks (up to 120s)..."
    local elapsed=0
    while [ $elapsed -lt 120 ]; do
        local unhealthy
        unhealthy=$(docker compose -f "$COMPOSE_FILE" ps --format json 2>/dev/null \
            | python3 -c "
import sys, json
for line in sys.stdin:
    d = json.loads(line)
    h = d.get('Health', 'unknown')
    if h != 'healthy':
        print(d.get('Service','?'), h)
" 2>/dev/null || echo "checking...")

        if [ -z "$unhealthy" ]; then
            log "All services healthy!"
            return 0
        fi
        sleep 5
        elapsed=$((elapsed + 5))
        printf "  %ds: %s\n" "$elapsed" "$unhealthy"
    done
    warn "Timeout. Check: docker compose -f $COMPOSE_FILE ps"
}

restart_smarttraffic_nginx() {
    log "Restarting SmartTraffic nginx..."
    docker compose -f "$SMARTTRAFFIC_DIR/docker-compose.yml" \
        -f "$SMARTTRAFFIC_DIR/docker-compose.override.yml" \
        up -d --force-recreate nginx
    sleep 3
    docker exec smarttraffic-nginx nginx -t 2>&1 && log "Nginx config valid" || err "Nginx config error"
}

verify_deployment() {
    echo ""
    echo "=== FishMap Services ==="
    docker compose -f "$COMPOSE_FILE" ps 2>/dev/null || true

    echo ""
    echo "=== Health Checks ==="
    for svc in auth-service email-service forecast-service; do
        docker compose -f "$COMPOSE_FILE" exec -T "$svc" \
            python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())" 2>/dev/null \
            && echo "  -> $svc OK" || warn "$svc: not responding"
    done
    curl -sf http://127.0.0.1:3080/api/health 2>/dev/null && echo " -> frontend OK" || warn "frontend: not responding"

    echo ""
    echo "=== Memory Usage ==="
    docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}" 2>/dev/null | head -20

    echo ""
    source_env
    if [ "${FISHMAP_DOMAIN:-}" != "yourdomain.ru" ] && [ -n "${FISHMAP_DOMAIN:-}" ]; then
        log "Site: http://$FISHMAP_DOMAIN"
    else
        log "Site: http://127.0.0.1:3080 (no domain configured)"
    fi

    echo ""
    log "========================================="
    log "  FishMap deployment complete!"
    log "========================================="
}

case "${1:-deploy}" in
    deploy)
        check_prerequisites
        cd "$FISHMAP_DIR"
        configure_smarttraffic_nginx
        build_and_start
        restart_smarttraffic_nginx
        verify_deployment
        ;;
    update)
        cd "$FISHMAP_DIR"
        docker compose -f "$COMPOSE_FILE" build
        docker compose -f "$COMPOSE_FILE" up -d --force-recreate
        restart_smarttraffic_nginx
        verify_deployment
        ;;
    stop)
        cd "$FISHMAP_DIR"
        docker compose -f "$COMPOSE_FILE" down
        log "FishMap stopped"
        ;;
    logs)
        cd "$FISHMAP_DIR"
        docker compose -f "$COMPOSE_FILE" logs --tail=50 "${2:-}"
        ;;
    health)
        cd "$FISHMAP_DIR"
        verify_deployment
        ;;
    *)
        echo "Usage: $0 {deploy|update|stop|logs [svc]|health}"
        exit 1
        ;;
esac
