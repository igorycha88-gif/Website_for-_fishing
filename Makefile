.PHONY: help dev dev-build dev-up dev-down dev-logs dev-restart
.PHONY: test test-down pytest
.PHONY: elk elk-up elk-down elk-logs
.PHONY: health status clean clean-all
.PHONY: build build-frontend build-auth build-email build-places build-reports build-booking build-shop
.PHONY: prod prod-deploy prod-rollback prod-logs prod-ps
.PHONY: secrets secrets-generate secrets-create secrets-remove secrets-list

COMPOSE_DEV = docker-compose -f docker-compose.dev.yml
COMPOSE_PROD = docker-compose -f docker-compose.yml
COMPOSE_ELK = docker-compose -f docker-compose.elk.yml
COMPOSE_TEST = docker-compose -f docker-compose.test.yml
COMPOSE_FRONTEND = docker-compose -f docker-compose.frontend.yml
STACK_NAME = fishmap

help:
	@echo "FishMap - Docker Commands"
	@echo ""
	@echo "=== Development ==="
	@echo "  make dev           - Build and start all services (development)"
	@echo "  make dev-build     - Build all services"
	@echo "  make dev-up        - Start all services"
	@echo "  make dev-down      - Stop all services"
	@echo "  make dev-logs      - Follow logs for all services"
	@echo "  make dev-logs S=auth-service  - Follow logs for specific service"
	@echo "  make dev-restart   - Restart all services"
	@echo ""
	@echo "=== Production (Docker Swarm) ==="
	@echo "  make prod-deploy   - Deploy to Docker Swarm"
	@echo "  make prod-logs     - View production logs"
	@echo "  make prod-ps       - List production services"
	@echo "  make prod-rollback - Rollback last deployment"
	@echo ""
	@echo "=== Secrets Management ==="
	@echo "  make secrets-generate - Generate secret files"
	@echo "  make secrets-create   - Create Docker Swarm secrets"
	@echo "  make secrets-remove   - Remove Docker Swarm secrets"
	@echo "  make secrets-list     - List all secrets"
	@echo ""
	@echo "=== Health & Status ==="
	@echo "  make health        - Check health of all services"
	@echo "  make status        - Show container status"
	@echo ""
	@echo "=== Testing ==="
	@echo "  make test          - Run integration tests"
	@echo "  make test-down     - Stop test environment"
	@echo "  make pytest        - Run pytest in auth-service container"
	@echo "  make pytest S=email-service    - Run pytest in specific service"
	@echo ""
	@echo "=== ELK Stack ==="
	@echo "  make elk           - Start ELK Stack (with dev)"
	@echo "  make elk-up        - Start ELK Stack only"
	@echo "  make elk-down      - Stop ELK Stack"
	@echo "  make elk-logs      - Follow ELK logs"
	@echo ""
	@echo "=== Build Individual Services ==="
	@echo "  make build         - Build frontend only"
	@echo "  make build-auth    - Build auth-service"
	@echo "  make build-email   - Build email-service"
	@echo "  make build-places  - Build places-service"
	@echo "  make build-reports - Build reports-service"
	@echo "  make build-booking - Build booking-service"
	@echo "  make build-shop    - Build shop-service"
	@echo ""
	@echo "=== Cleanup ==="
	@echo "  make clean         - Remove containers and volumes (dev)"
	@echo "  make clean-all     - Full cleanup including ELK and docker prune"
	@echo "  make clean-images  - Remove all project images"

dev: dev-build dev-up
	@echo "Development environment started. Run 'make health' to verify."

dev-build:
	$(COMPOSE_DEV) build

dev-up:
	$(COMPOSE_DEV) up -d

dev-down:
	$(COMPOSE_DEV) down

dev-logs:
ifdef S
	$(COMPOSE_DEV) logs -f $(S)
else
	$(COMPOSE_DEV) logs -f
endif

dev-restart:
	$(COMPOSE_DEV) restart

health:
	@echo "=== Infrastructure ==="
	@docker inspect website_for_fishing-postgres-1 --format='postgres: {{.State.Health.Status}}' 2>/dev/null || echo "postgres: not running"
	@docker inspect website_for_fishing-redis-1 --format='redis: {{.State.Health.Status}}' 2>/dev/null || echo "redis: not running"
	@echo ""
	@echo "=== Backend Services ==="
	@curl -s http://localhost:8001/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"auth-service: {d['status']}\")" 2>/dev/null || echo "auth-service: not responding"
	@curl -s http://localhost:8006/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"email-service: {d['status']}\")" 2>/dev/null || echo "email-service: not responding"
	@curl -s http://localhost:8002/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"places-service: {d['status']}\")" 2>/dev/null || echo "places-service: not responding"
	@curl -s http://localhost:8003/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"reports-service: {d['status']}\")" 2>/dev/null || echo "reports-service: not responding"
	@curl -s http://localhost:8004/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"booking-service: {d['status']}\")" 2>/dev/null || echo "booking-service: not responding"
	@curl -s http://localhost:8005/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"shop-service: {d['status']}\")" 2>/dev/null || echo "shop-service: not responding"
	@echo ""
	@echo "=== Frontend ==="
	@curl -s http://localhost:3000/api/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"frontend: {d.get('status', 'ok')}\")" 2>/dev/null || echo "frontend: not responding"

status:
	$(COMPOSE_DEV) ps

test:
	$(COMPOSE_TEST) up --build --abort-on-container-exit

test-down:
	$(COMPOSE_TEST) down

pytest:
ifdef S
	docker exec website_for_fishing-$(S)-1 pytest /app/tests -v --cov=app --cov-report=term-missing
else
	docker exec website_for_fishing-auth-service-1 pytest /app/tests -v --cov=app --cov-report=term-missing
endif

elk: dev elk-up
	@echo "ELK Stack started with development environment."
	@echo "Kibana: http://localhost:5601"
	@echo "Elasticsearch: http://localhost:9200"

elk-up:
	$(COMPOSE_ELK) up -d

elk-down:
	$(COMPOSE_ELK) down

elk-logs:
	$(COMPOSE_ELK) logs -f

build:
	$(COMPOSE_FRONTEND) build

build-frontend:
	$(COMPOSE_FRONTEND) build

build-auth:
	$(COMPOSE_DEV) build auth-service

build-email:
	$(COMPOSE_DEV) build email-service

build-places:
	$(COMPOSE_DEV) build places-service

build-reports:
	$(COMPOSE_DEV) build reports-service

build-booking:
	$(COMPOSE_DEV) build booking-service

build-shop:
	$(COMPOSE_DEV) build shop-service

clean:
	$(COMPOSE_DEV) down -v
	@echo "Development environment cleaned."

clean-all:
	$(COMPOSE_DEV) down -v --remove-orphans
	$(COMPOSE_ELK) down -v
	$(COMPOSE_TEST) down -v
	docker system prune -af --volumes
	@echo "Full cleanup completed."

clean-images:
	docker images | grep "website_for_fishing" | awk '{print $$3}' | xargs -r docker rmi -f
	@echo "Project images removed."

prod-deploy:
	@echo "Deploying to Docker Swarm..."
	docker stack deploy -c docker-compose.yml $(STACK_NAME)
	@echo "Deployment started. Check status with: make prod-ps"

prod-logs:
	docker service logs -f $(STACK_NAME)_auth-service

prod-ps:
	docker stack services $(STACK_NAME)

prod-rollback:
	docker service rollback $(STACK_NAME)_auth-service
	docker service rollback $(STACK_NAME)_frontend
	@echo "Rollback initiated."

secrets-generate:
	./scripts/secrets.sh --generate

secrets-create:
	./scripts/secrets.sh --create

secrets-remove:
	./scripts/secrets.sh --remove

secrets-list:
	./scripts/secrets.sh --list
