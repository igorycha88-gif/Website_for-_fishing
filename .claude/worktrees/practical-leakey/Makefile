.PHONY: help build build-dev up down logs restart clean test-backend test-e2e test-all test-clean db-test-start db-test-stop

help:
	@echo "Доступные команды:"
	@echo "  make build      - Собрать Docker образ"
	@echo "  make build-dev  - Собрать и запустить для разработки"
	@echo "  make up         - Запустить контейнеры"
	@echo "  make down       - Остановить контейнеры"
	@echo "  make logs       - Посмотреть логи"
	@echo "  make restart    - Перезапустить контейнеры"
	@echo "  make clean      - Очистить контейнеры и образы"
	@echo "  make db-test-start       - Запустить тестовую базу данных"
	@echo "  make db-test-stop        - Остановить тестовую базу данных"
	@echo "  make test-backend        - Запустить backend тесты"
	@echo "  make test-e2e            - Запустить E2E тесты (Playwright)"
	@echo "  make test-e2e-ui         - Запустить E2E тесты с UI"
	@echo "  make test-e2e-debug      - Запустить E2E тесты в режиме debug"
	@echo "  make test-all            - Запустить все тесты"
	@echo "  make test-clean          - Очистить тестовые артефакты"

build:
	docker-compose -f docker-compose.frontend.yml build

build-dev:
	docker-compose -f docker-compose.frontend.yml up --build

up:
	docker-compose -f docker-compose.frontend.yml up -d

down:
	docker-compose -f docker-compose.frontend.yml down

logs:
	docker-compose -f docker-compose.frontend.yml logs -f frontend

restart:
	docker-compose -f docker-compose.frontend.yml restart

clean:
	docker-compose -f docker-compose.frontend.yml down -v
	docker system prune -f

db-test-start:
	@echo "Запуск тестовой базы данных..."
	docker-compose -f docker-compose.test.yml up -d
	@echo "Ожидание запуска базы данных..."
	sleep 5
	@echo "Тестовая база данных запущена на порту 5433"

db-test-stop:
	@echo "Остановка тестовой базы данных..."
	docker-compose -f docker-compose.test.yml down -v
	@echo "Тестовая база данных остановлена"

test-backend:
	@echo "Запуск backend тестов..."
	@cd services/auth-service && pytest tests/ -v --cov=app --cov-report=html || true
	@cd services/places-service && pytest tests/ -v --cov=app --cov-report=html || true
	@cd services/email-service && pytest tests/ -v --cov=app --cov-report=html || true

test-e2e:
	@echo "Запуск E2E тестов..."
	@cd frontend && npm run test:e2e

test-e2e-ui:
	@echo "Запуск E2E тестов с UI..."
	@cd frontend && npm run test:e2e:ui

test-e2e-debug:
	@echo "Запуск E2E тестов в режиме debug..."
	@cd frontend && npm run test:e2e:debug

test-e2e-report:
	@echo "Открытие отчета E2E тестов..."
	@cd frontend && npm run test:e2e:report

test-all: db-test-start test-backend test-e2e db-test-stop
	@echo "Все тесты выполнены!"

test-clean:
	@echo "Очистка тестовых артефактов..."
	@rm -rf frontend/test-results/
	@rm -rf frontend/playwright-report/
	@rm -rf frontend/e2e/.auth/
	@rm -rf services/*/htmlcov/
	@rm -rf services/*/.pytest_cache/
	@rm -rf services/*/.coverage
	@echo "Тестовые артефакты очищены"
