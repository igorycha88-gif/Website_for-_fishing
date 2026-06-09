.PHONY: help build build-dev up down logs restart clean

help:
	@echo "Доступные команды:"
	@echo "  make build      - Собрать Docker образ"
	@echo "  make build-dev  - Собрать и запустить для разработки"
	@echo "  make up         - Запустить контейнеры"
	@echo "  make down       - Остановить контейнеры"
	@echo "  make logs       - Посмотреть логи"
	@echo "  make restart    - Перезапустить контейнеры"
	@echo "  make clean      - Очистить контейнеры и образы"

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
