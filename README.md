# Fishing Platform

Microservices-based platform for fishing enthusiasts with places catalog, reports, booking, and shop.

## Architecture

```
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                           Docker Development Stack                           │
 │                                                                             │
 │  ┌───────────────────────────────────────────────────────────────────────┐  │
 │  │                        Frontend (Next.js)                             │  │
 │  │  Port: 3000  │  │  Port: 3000  │
 │  │  - API Proxy via Next.js rewrites                                    │  │
 │  └───────────────────────────────────────────────────────────────────────┘  │
 │                                      │                                       │
 │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
 │  │ Auth Service │  │Places Service│  │Reports       │  │Booking       │  │
 │  │  (FastAPI)   │  │  (FastAPI)   │  │Service       │  │Service       │  │
 │  │  Port: 8001  │  │  Port: 8002  │  │(FastAPI)     │  │(FastAPI)     │  │
 │  │  ✅ Impl.    │  │  🚧 Plan.    │  │  Port: 8003  │  │  Port: 8004  │  │
 │  │              │  │              │  │  🚧 Plan.    │  │  🚧 Plan.    │  │
 │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
 │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
 │  │Shop Service  │  │ Email        │  │PostgreSQL    │  │Redis         │  │
 │  │  (FastAPI)   │  │Service       │  │   (DB)       │  │  (Cache)     │  │
 │  │  Port: 8005  │  │  (FastAPI)   │  │  Port: 5432  │  │  Port: 6379  │  │
 │  │  🚧 Plan.    │  │  Port: 8006  │  │              │  │              │  │
 │  │              │  │  ✅ Impl.    │  │              │  │              │  │
 │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
 │                                                                             │
 │  ✅ = Implemented | 🚧 = Planned/Placeholder                               │
 └─────────────────────────────────────────────────────────────────────────────┘
```

## Project Status

**Current Phase**: Early Development

### Completed Features ✅
- User registration with email verification
- User authentication (JWT)
- Password reset functionality
- User profile management
- Email service with SMTP integration
- Frontend pages for all major features
- Docker-based development environment

### In Progress 🚧
- Database schema design (complete in schema.sql, not yet fully used)
- Frontend UI components

### Planned Features 🔮
- Places service with map integration
- Reports service with image uploads
- Booking service with payment integration
- Shop service with e-commerce functionality
- Admin/moderator role management

## Tech Stack

### Frontend
- **Next.js 15** (App Router) - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS
- **Framer Motion** - Animations
- **Zustand** - State management

### Backend
- **FastAPI** - Python async web framework
- **PostgreSQL** - Relational database
- **Redis** - Caching & sessions
- **SQLAlchemy** - Async ORM
- **Pydantic** - Data validation
- **JWT** - Authentication tokens
- **Bcrypt** - Password hashing

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Development environment
- **Docker Swarm** - Production (planned)

### External Services
- **Mapbox GL JS** - Interactive maps (planned)
- **Stripe** - Payment processing (planned)
- **Cloudinary** - Image hosting (planned)
- **Yandex SMTP** - Email service

## Project Structure

```
.
├── services/
│   ├── auth-service/          # ✅ Auth service (port 8001)
│   ├── places-service/        # 🚧 Places service (port 8002)
│   ├── reports-service/       # 🚧 Reports service (port 8003)
│   ├── booking-service/       # 🚧 Booking service (port 8004)
│   ├── shop-service/          # 🚧 Shop service (port 8005)
│   ├── email-service/         # ✅ Email service (port 8006)
│   └── shared-utils/          # Shared code
├── frontend/                   # ✅ Next.js application (port 3000)
├── database/                   # Database schema
│   ├── schema.sql             # SQL schema definition
│   └── schema.md              # Schema documentation
├── docker-compose.yml         # Production config (planned)
├── docker-compose.dev.yml     # Development config
├── docker-compose.test.yml    # Testing config
├── docker-compose.elk.yml     # ELK stack (logging)
├── ARCHITECTURE.md            # Architecture documentation
├── DEPLOYMENT.md              # Deployment guide
├── MONITORING.md              # Monitoring setup
├── DOCKER.md                  # Docker guide
├── README.md                  # This file
└── .env.example               # Environment variables
```

## Implemented Features

### Auth Service (Port 8001)
- User registration with email verification
- User login with JWT tokens
- Password reset with email tokens
- User profile management
- Role-based access control (user/moderator/admin)

### Email Service (Port 8006)
- Email notifications via SMTP
- Verification code generation
- Email sending toggle for development
- **API Key authentication** for service-to-service calls (SEC-005)

### Frontend (Port 3000)
**Implemented Pages:**
- `/` - Home page
- `/login` - User login
- `/register` - User registration
- `/verify-email` - Email verification
- `/reset-password` - Password reset
- `/profile` - User profile (Profile, Settings tabs)
- `/map` - Interactive map
- `/resorts` - Fishing places listing
- `/shop` - Online shop
- `/stores` - Stores page
- `/forecast` - Weather forecast

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ (for local development)
- Node.js 20+ (for local development)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd fishing-platform

# Copy environment file
cp .env.example .env

# Edit .env with your values
nano .env
```

### Environment Variables

Required environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres_password@postgres:5432/fishing_db

# Redis
REDIS_URL=redis://redis:6379/0

# Docker Environment (for frontend)
DOCKER_ENV=false  # Set to 'true' when running in Docker, 'false' for local dev (npm run dev)

# Auth
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
SMTP_HOST=smtp.yandex.ru
SMTP_PORT=465
SMTP_USER=your-email@yandex.ru
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@yandex.ru
SMTP_FROM_NAME=FishMap
ENABLE_EMAIL_SENDING=false  # Set to true for production
EMAIL_CODE_EXPIRE_MINUTES=15
EMAIL_SERVICE_API_KEY=your-secure-api-key-min-32-chars  # API Key for Email Service (SEC-005)

# External Services (planned)
MAPBOX_API_KEY=your-mapbox-api-key
YANDEX_MAPS_API_KEY=your-yandex-maps-api-key
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret

# Logging
LOG_LEVEL=INFO
LOGSTASH_URL=http://logstash:5000
SERVICE_NAME=your-service-name
```

### Running with Docker

#### Important: Frontend Build-time Variables

Next.js requires `NEXT_PUBLIC_*` environment variables at **build time**, not runtime. These variables are embedded in the JavaScript bundle during `npm run build`.

**For Docker builds**, these variables must be passed via `build args`:

```yaml
# docker-compose.dev.yml
frontend:
  build:
    args:
      NEXT_PUBLIC_YANDEX_MAPS_API_KEY: ${YANDEX_MAPS_API_KEY}
      NEXT_PUBLIC_API_URL: http://localhost:3000
      NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: ${STRIPE_PUBLISHABLE_KEY}
```

**Required variables in `.env`:**
```bash
YANDEX_MAPS_API_KEY=your_yandex_maps_api_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key
```

**Note:** After changing these variables, you **must rebuild** the frontend image:
```bash
docker-compose -f docker-compose.dev.yml build frontend
docker-compose -f docker-compose.dev.yml up -d frontend
```

#### Development
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down

# Stop services and remove volumes
docker-compose -f docker-compose.dev.yml down -v
```

#### Local Development (npm run dev)
```bash
# Start backend services in Docker
docker-compose -f docker-compose.dev.yml up -d postgres redis auth-service email-service

# Start frontend locally
cd frontend
npm run dev
```

**Important**: When running frontend locally with `npm run dev`, set `DOCKER_ENV=false` in the environment. Docker mode uses `DOCKER_ENV=true` automatically.

#### With ELK Stack (Logging)
```bash
# Start services with logging
docker-compose -f docker-compose.dev.yml -f docker-compose.elk.yml up -d
```

### Accessing Services

#### Development Environment
- **Frontend**: http://localhost:3000
- **Auth Service**: http://localhost:8001
- **Places Service**: http://localhost:8002
- **Reports Service**: http://localhost:8003
- **Booking Service**: http://localhost:8004
- **Shop Service**: http://localhost:8005
- **Email Service**: http://localhost:8006
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

#### Health Checks
```bash
# Check service health
curl http://localhost:8001/health    # Auth
curl http://localhost:8002/health    # Places
curl http://localhost:8003/health    # Reports
curl http://localhost:8004/health    # Booking
curl http://localhost:8005/health    # Shop
curl http://localhost:8006/health    # Email
```

## API Documentation

### Auth Service (Port 8001)

#### Authentication Endpoints
```bash
# Register new user
POST /api/v1/auth/register
Body: { "email": "user@example.com", "username": "username", "password": "password123" }

# Verify email
POST /api/v1/auth/verify-email
Body: { "email": "user@example.com", "code": "123456" }

# Login
POST /api/v1/auth/login
Body: { "email": "user@example.com", "password": "password123" }
Response: { "success": true, "message": "...", "access_token": "..." }

# Request password reset
POST /api/v1/auth/reset-password/request
Body: { "email": "user@example.com" }

# Confirm password reset
POST /api/v1/auth/reset-password/confirm
Body: { "token": "...", "new_password": "newpassword123" }
```

#### User Endpoints
```bash
# Get current user
GET /api/v1/users/me
Headers: Authorization: Bearer <access_token>

# Update user profile
PUT /api/v1/users/me
Headers: Authorization: Bearer <access_token>
Body: { "first_name": "John", "last_name": "Doe", ... }

# Change password
PATCH /api/v1/users/me/password
Headers: Authorization: Bearer <access_token>
Body: { "current_password": "...", "new_password": "..." }
```

### Email Service (Port 8006)

**Note**: All endpoints require `X-API-Key` header for authentication (SEC-005).

```bash
# Send verification email
POST /api/v1/email/send
Headers: X-API-Key: <your-api-key>
Body: { "to_email": "user@example.com", "verification_code": "123456", "username": "username" }

# Generate verification code
POST /api/v1/email/generate-code
Headers: X-API-Key: <your-api-key>
Response: { "code": "123456" }
```

**Error Responses:**
- 401 Unauthorized: `{"detail": {"code": "API_KEY_REQUIRED", "message": "X-API-Key header is required"}}`
- 403 Forbidden: `{"detail": {"code": "INVALID_API_KEY", "message": "Invalid API key"}}`

## Database Schema

See [database/schema.md](database/schema.md) for complete documentation.

### Implemented Tables
- `users` - User accounts with roles
- `refresh_tokens` - JWT refresh tokens
- `email_verification_codes` - Email verification codes

### Planned Tables (defined in schema.sql)
- `places` - Fishing places
- `reports` - Fishing reports
- `bookings` - Booking records
- `booking_slots` - Available slots
- `products` - Shop products
- `categories` - Product categories
- `orders` - Shop orders
- `order_items` - Order items
- `ratings` - Ratings

## Development

### Local Development Setup

#### Backend Services
```bash
# Auth Service
cd services/auth-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Running Tests

#### Backend
```bash
# All services
cd services
pytest

# Specific service
pytest services/auth-service
```

#### Frontend
```bash
cd frontend
npm test
```

### Code Quality

#### Python
```bash
# Linting
ruff check .

# Formatting
ruff format .

# Type checking
mypy services/
```

#### Frontend
```bash
# Linting
npm run lint

# Type checking
npm run typecheck
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Quick Start
```bash
# Production (planned)
docker swarm init
docker stack deploy -c docker-compose.yml fishing

# Check status
docker stack ps fishing
```

## Monitoring

See [MONITORING.md](MONITORING.md) for monitoring setup.

### ELK Stack (Optional)
```bash
# Start with logging
docker-compose -f docker-compose.dev.yml -f docker-compose.elk.yml up -d

# Access Kibana
http://localhost:5601
```

## Troubleshooting

### Common Issues

#### Email Service Not Working
```bash
# Check email service logs
docker-compose -f docker-compose.dev.yml logs -f email-service

# Verify SMTP credentials in .env
# Set ENABLE_EMAIL_SENDING=false for development
```

#### Database Connection Issues
```bash
# Check database is running
docker-compose -f docker-compose.dev.yml ps postgres

# Check database logs
docker-compose -f docker-compose.dev.yml logs -f postgres

# Restart database
docker-compose -f docker-compose.dev.yml restart postgres
```

#### Port Conflicts
```bash
# Check what's using the ports
lsof -i :3000  # Frontend
lsof -i :8001  # Auth
lsof -i :5432  # PostgreSQL

# Stop conflicting services or change ports
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write tests
5. Run tests and linting
6. Submit pull request

### Development Workflow
1. Analyze requirements
2. Design API/architecture
3. Implement backend
4. Implement frontend
5. Write tests
6. Update documentation
7. Create pull request

### Commit Message Format
```
feat(service): add new feature
- Description of changes
- More details

Tests: X unit tests, Y integration tests
Closes #123
```

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [DOCKER.md](DOCKER.md) - Docker guide
- [MONITORING.md](MONITORING.md) - Monitoring setup
- [docs/SECRETS.md](docs/SECRETS.md) - Secrets management (HashiCorp Vault)
- [database/schema.md](database/schema.md) - Database schema

## Secrets Management

This project uses **HashiCorp Vault** for centralized secrets management.

### Quick Start

```bash
# Start services with Vault
docker-compose -f docker-compose.dev.yml up -d

# Vault runs in dev mode on port 8200
# Root token: dev-root-token
```

### Environment Variables for Vault

```bash
# Enable Vault integration
USE_VAULT=true

# Vault connection
VAULT_ADDR=http://vault:8200

# Service credentials (from vault-init output)
AUTH_VAULT_ROLE_ID=<role-id>
AUTH_VAULT_SECRET_ID=<secret-id>
```

### Fallback Mode

If Vault is unavailable, services use `.env` variables (set `USE_VAULT=false`).

See [docs/SECRETS.md](docs/SECRETS.md) for complete documentation.

## Roadmap

### Phase 1: Authentication ✅
- [x] User registration with email verification
- [x] Login/logout
- [x] Password reset
- [x] User profile management

### Phase 2: Places 🚧
- [ ] CRUD operations for places
- [ ] Map integration (Mapbox)
- [ ] Search and filtering
- [ ] Place images (Cloudinary)

### Phase 3: Reports 🔮
- [ ] Report creation
- [ ] Image upload
- [ ] Comments and ratings
- [ ] Fish species tracking

### Phase 4: Booking 🔮
- [ ] Booking system
- [ ] Availability management
- [ ] Stripe payment integration
- [ ] Calendar view

### Phase 5: Shop 🔮
- [ ] Product catalog
- [ ] Shopping cart
- [ ] Order management
- [ ] Stripe payment integration

### Future Improvements 🔮
- [ ] WebSocket notifications
- [ ] Mobile app (React Native)
- [ ] GraphQL API
- [ ] Message queue (RabbitMQ)
- [ ] Microservice databases
- [ ] Prometheus/Grafana monitoring

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review ARCHITECTURE.md for technical details

## Acknowledgments

Built with:
- Next.js 15
- FastAPI
- PostgreSQL
- Redis
- Docker
- Mapbox (planned)
- Stripe (planned)
- Cloudinary (planned)
