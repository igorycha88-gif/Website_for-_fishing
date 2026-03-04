# Docker & Deployment

## Local Development (docker-compose.dev.yml)

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env with your values
nano .env

# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes
docker-compose -f docker-compose.dev.yml down -v
```

## Docker Swarm (docker-compose.yml)

```bash
# Initialize Swarm (if not already)
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml fishing

# List services
docker service ls

# View logs
docker service logs -f fishing_auth-service

# Scale service
docker service scale fishing_auth-service=4

# Update service
docker service update --image auth-service:new-version fishing_auth-service

# Remove stack
docker stack rm fishing
```

## Accessing Services

- **Frontend**: http://localhost
- **API Gateway (Traefik Dashboard)**: http://localhost:8080
- **Auth Service**: http://localhost/api/v1/auth
- **Places Service**: http://localhost/api/v1/places
- **Reports Service**: http://localhost/api/v1/reports
- **Booking Service**: http://localhost/api/v1/bookings
- **Shop Service**: http://localhost/api/v1/shop

## Database Access

```bash
# Connect to PostgreSQL
docker exec -it $(docker ps -q -f name=postgres) psql -U postgres -d fishing_db

# Backup database
docker exec $(docker ps -q -f name=postgres) pg_dump -U postgres fishing_db > backup.sql

# Restore database
docker exec -i $(docker ps -q -f name=postgres) psql -U postgres fishing_db < backup.sql
```

## Redis Access

```bash
# Connect to Redis
docker exec -it $(docker ps -q -f name=redis) redis-cli
```

## Environment Variables

Copy `.env.example` to `.env` and set the following variables:

- `POSTGRES_DB` - Database name
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password
- `SECRET_KEY` - JWT secret key (min 32 chars)
- `MAPBOX_API_KEY` - Mapbox API key for maps
- `CLOUDINARY_CLOUD_NAME` - Cloudinary cloud name
- `CLOUDINARY_API_KEY` - Cloudinary API key
- `CLOUDINARY_API_SECRET` - Cloudinary API secret
- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret
- `CORS_ORIGINS` - Comma-separated list of allowed CORS origins (e.g., https://fishmap.ru,https://api.fishmap.ru)

## Troubleshooting

### Service not starting
```bash
# Check logs
docker-compose -f docker-compose.dev.yml logs <service-name>

# Check service health
docker-compose -f docker-compose.dev.yml ps
```

### Database connection issues
```bash
# Check if postgres is running
docker ps | grep postgres

# Check postgres logs
docker logs <postgres-container-id>

# Test connection
docker exec -it <postgres-container-id> psql -U postgres -d fishing_db -c "SELECT 1"
```

### Redis connection issues
```bash
# Check if redis is running
docker ps | grep redis

# Test connection
docker exec -it <redis-container-id> redis-cli ping
```

### Rebuild services
```bash
# Rebuild and start
docker-compose -f docker-compose.dev.yml up -d --build <service-name>
```

## Production Deployment

For production:

1. Use separate `.env.production` file
2. Enable SSL/TLS with Let's Encrypt
3. Set up proper secrets management
4. Configure logging and monitoring
5. Set up backup strategy
6. Use dedicated database and redis servers

## Secrets Management (HashiCorp Vault)

### Development

Vault runs automatically in dev mode:

```bash
# Start with Vault
docker-compose -f docker-compose.dev.yml up -d

# Check Vault status
curl http://localhost:8200/v1/sys/health

# View initialization logs
docker logs $(docker ps -q -f name=vault-init)
```

### Production Setup

1. **Disable dev mode** in docker-compose.yml:
```yaml
vault:
  command: server  # Remove -dev flags
```

2. **Configure TLS**:
```yaml
vault:
  environment:
    VAULT_API_ADDR: https://vault.yourdomain.com:8200
```

3. **Initialize Vault**:
```bash
vault operator init -key-shares=5 -key-threshold=3
# Save unseal keys securely!
```

4. **Unseal Vault**:
```bash
vault operator unseal <key1>
vault operator unseal <key2>
vault operator unseal <key3>
```

### Enable Vault for Services

```bash
# Set in .env
USE_VAULT=true
VAULT_ADDR=http://vault:8200

# Get Role ID and Secret ID from vault-init logs
AUTH_VAULT_ROLE_ID=<from-logs>
AUTH_VAULT_SECRET_ID=<from-logs>
```

### Disable Vault (Fallback)

```bash
# In .env
USE_VAULT=false
# Services will use environment variables from .env
```

See [docs/SECRETS.md](docs/SECRETS.md) for complete documentation.
