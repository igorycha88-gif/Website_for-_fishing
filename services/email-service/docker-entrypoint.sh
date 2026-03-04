#!/bin/sh
set -e

echo "Starting $0..."

DB_HOST=${DATABASE_URL:-postgres}
if [ "$DB_HOST" = "postgres" ]; then
    echo "Waiting for PostgreSQL..."
    while ! nc -z postgres 5432; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 1
    done
    echo "PostgreSQL is up!"
fi

REDIS_HOST=${REDIS_URL:-redis}
if [ "$REDIS_HOST" = "redis" ]; then
    echo "Waiting for Redis..."
    while ! nc -z redis 6379; do
        echo "Redis is unavailable - sleeping"
        sleep 1
    done
    echo "Redis is up!"
fi

exec "$@"
