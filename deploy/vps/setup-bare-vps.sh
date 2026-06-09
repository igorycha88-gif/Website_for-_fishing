#!/bin/bash
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

FISHMAP_DIR="/opt/fishmap"
COMPOSE_FILE="docker-compose.vps.yml"
ENV_FILE=".env.vps"
VPS_IP="5.35.102.219"

log()  { echo -e "${GREEN}[FishMap]${NC} $1"; }
warn() { echo -e "${YELLOW}[FishMap]${NC} $1"; }
err()  { echo -e "${RED}[FishMap]${NC} $1"; exit 1; }

install_docker() {
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        log "Docker already installed"
        return 0
    fi

    log "Installing Docker..."
    apt-get update -qq
    apt-get install -y -qq ca-certificates curl gnupg lsb-release

    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list

    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    systemctl enable docker
    systemctl start docker

    log "Docker installed successfully"
}

install_nginx() {
    if command -v nginx >/dev/null 2>&1; then
        log "Nginx already installed"
        return 0
    fi

    log "Installing Nginx..."
    apt-get update -qq
    apt-get install -y -qq nginx
    systemctl enable nginx
    systemctl start nginx
    log "Nginx installed"
}

configure_nginx() {
    log "Configuring Nginx for FishMap (IP: $VPS_IP)..."

    cp "$FISHMAP_DIR/deploy/vps/nginx-ip.conf" /etc/nginx/sites-available/fishmap
    rm -f /etc/nginx/sites-enabled/fishmap
    ln -sf /etc/nginx/sites-available/fishmap /etc/nginx/sites-enabled/fishmap

    rm -f /etc/nginx/sites-enabled/default

    nginx -t && log "Nginx config valid" || err "Nginx config error"
    systemctl reload nginx
    log "Nginx configured"
}

setup_firewall() {
    log "Configuring firewall..."
    if command -v ufw >/dev/null 2>&1; then
        ufw --force enable
        ufw allow 22/tcp
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 3080/tcp
        ufw reload
        log "Firewall configured (ufw)"
    elif command -v iptables >/dev/null 2>&1; then
        iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || iptables -A INPUT -p tcp --dport 80 -j ACCEPT
        iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || iptables -A INPUT -p tcp --dport 443 -j ACCEPT
        iptables -C INPUT -p tcp --dport 3080 -j ACCEPT 2>/dev/null || iptables -A INPUT -p tcp --dport 3080 -j ACCEPT
        log "Firewall configured (iptables)"
    else
        warn "No firewall tool found, skipping"
    fi
}

build_and_start() {
    cd "$FISHMAP_DIR"

    log "Building FishMap containers (5-10 min)..."
    docker compose -f "$COMPOSE_FILE" build 2>&1 | tail -20

    log "Starting FishMap services..."
    docker compose -f "$COMPOSE_FILE" up -d

    log "Waiting for healthchecks (up to 180s)..."
    local elapsed=0
    while [ $elapsed -lt 180 ]; do
        local all_healthy=true
        local services=(postgres redis auth-service email-service forecast-service frontend)

        for svc in "${services[@]}"; do
            local status
            status=$(docker compose -f "$COMPOSE_FILE" ps "$svc" --format json 2>/dev/null | python3 -c "
import sys, json
for line in sys.stdin:
    d = json.loads(line)
    print(d.get('Health', d.get('Status', 'unknown')))
" 2>/dev/null || echo "unknown")

            if [ "$status" != "healthy" ]; then
                all_healthy=false
                printf "  %ds: %s = %s\n" "$elapsed" "$svc" "$status"
            fi
        done

        if [ "$all_healthy" = true ]; then
            log "All services healthy!"
            return 0
        fi

        sleep 10
        elapsed=$((elapsed + 10))
    done

    warn "Timeout waiting for healthchecks. Showing status:"
    docker compose -f "$COMPOSE_FILE" ps
}

verify_deployment() {
    echo ""
    echo "========================================="
    echo -e "${GREEN} FishMap Deployment Status${NC}"
    echo "========================================="

    docker compose -f "$COMISHMAP_DIR/$COMPOSE_FILE" ps 2>/dev/null || \
    docker compose -f "$FISHMAP_DIR/$COMPOSE_FILE" ps 2>/dev/null || true

    echo ""
    echo "=== Health Checks ==="
    for url in "http://127.0.0.1:3080/api/health"; do
        local resp
        resp=$(curl -sf "$url" 2>/dev/null && echo " OK" || echo " FAIL")
        echo "  $url -> $resp"
    done

    echo ""
    echo "=== Memory Usage ==="
    docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}" 2>/dev/null | head -20

    echo ""
    echo "========================================="
    log "  Site available at: http://$VPS_IP"
    log "  (and http://$VPS_IP:3080 directly)"
    log "========================================="
}

case "${1:-deploy}" in
    setup)
        install_docker
        install_nginx
        configure_nginx
        setup_firewall
        log "VPS setup complete. Now run: $0 deploy"
        ;;
    deploy)
        cd "$FISHMAP_DIR"
        [ -f "$ENV_FILE" ] || err ".env.vps not found"
        build_and_start
        configure_nginx
        verify_deployment
        ;;
    update)
        cd "$FISHMAP_DIR"
        docker compose -f "$COMPOSE_FILE" build
        docker compose -f "$COMPOSE_FILE" up -d --force-recreate
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
        verify_deployment
        ;;
    *)
        echo "Usage: $0 {setup|deploy|update|stop|logs [svc]|health}"
        exit 1
        ;;
esac
