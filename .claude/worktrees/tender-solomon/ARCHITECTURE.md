# Architecture Documentation

## Overview

The Fishing Platform is a microservices-based application built with:
- **Frontend**: Next.js 15 (App Router)
- **Backend**: FastAPI (Python) microservices
- **Database**: PostgreSQL (single shared database)
- **Cache**: Redis
- **Infrastructure**: Docker with docker-compose (development), Docker Swarm (production planned)

**Current Status**: Early development phase. Only Auth Service and Email Service are fully implemented. Other services are placeholders.

## Microservices Architecture

### Port Configuration

| Service | Container Port | Host Port (Dev) | Status |
|---------|---------------|-----------------|--------|
| Auth | 8000 | 8001 | ✅ Implemented |
| Places | 8001 | 8002 | 🚧 Placeholder |
| Reports | 8002 | 8003 | 🚧 Placeholder |
| Booking | 8003 | 8004 | 🚧 Placeholder |
| Shop | 8004 | 8005 | 🚧 Placeholder |
| Email | 8005 | 8006 | ✅ Implemented |
| Frontend | 3000 | 3000 | ✅ Implemented |

## Service Details

### 1. Auth Service (Host: 8001, Container: 8000) ✅
**Status**: Fully Implemented

**Responsibilities:**
- User registration & authentication
- JWT token generation & validation
- User profile management
- Password reset
- Email verification
- Role-based access control (user/moderator/admin)

**Implemented API Routes:**
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/verify-email` - Verify email with code
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/reset-password/request` - Request password reset
- `POST /api/v1/auth/reset-password/confirm` - Confirm password reset
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update user profile
- `PATCH /api/v1/users/me/password` - Change password

**Database Tables:**
- `users` - User accounts with role field (user/moderator/admin)
- `refresh_tokens` - Refresh tokens for JWT
- `email_verification_codes` - Email verification codes

**Health Check:**
- `GET /health` - Service health status

**Features:**
- Email verification via Email Service
- Password reset with token
- Bcrypt password hashing
- JWT access tokens
- Structured logging with Logstash integration

### 2. Places Service (Host: 8002, Container: 8001) 🚧
**Status**: Placeholder (Not Implemented)

**Planned Responsibilities:**
- Manage fishing places
- Search & filtering
- Geospatial queries
- Place ratings

**Health Check:**
- `GET /health` - Service health status

**Planned API Routes:**
- `GET /api/v1/places` - List places with filters
- `GET /api/v1/places/:id` - Get place details
- `POST /api/v1/places` - Create new place
- `PUT /api/v1/places/:id` - Update place
- `DELETE /api/v1/places/:id` - Delete place

### 3. Reports Service (Host: 8003, Container: 8002) 🚧
**Status**: Placeholder (Not Implemented)

**Planned Responsibilities:**
- User reports & posts
- Image upload (Cloudinary)
- Comments & likes
- Fish species tracking

**Health Check:**
- `GET /health` - Service health status

**Planned API Routes:**
- `GET /api/v1/reports` - List reports
- `GET /api/v1/reports/:id` - Get report details
- `POST /api/v1/reports` - Create report

### 4. Booking Service (Host: 8004, Container: 8003) 🚧
**Status**: Placeholder (Not Implemented)

**Planned Responsibilities:**
- Booking management
- Availability slots
- Payment processing (Stripe)
- Booking cancellation

**Health Check:**
- `GET /health` - Service health status

**Planned API Routes:**
- `GET /api/v1/bookings` - List user bookings
- `POST /api/v1/bookings` - Create booking
- `GET /api/v1/booking-slots` - Get available slots

### 5. Shop Service (Host: 8005, Container: 8004) 🚧
**Status**: Placeholder (Not Implemented)

**Planned Responsibilities:**
- Product catalog
- Categories
- Shopping cart
- Order management
- Payment processing (Stripe)

**Health Check:**
- `GET /health` - Service health status

**Planned API Routes:**
- `GET /api/v1/shop/products` - List products
- `POST /api/v1/orders` - Create order

### 6. Email Service (Host: 8006, Container: 8005) ✅
**Status**: Fully Implemented

**Responsibilities:**
- Email notifications
- Verification code generation
- SMTP integration with fallback

**Implemented API Routes:**
- `POST /api/v1/email/send` - Send verification email
- `POST /api/v1/email/generate-code` - Generate verification code

**Health Check:**
- `GET /health` - Service health status
- `GET /` - Service root endpoint

**Features:**
- SMTP integration (Yandex)
- Email sending toggle (development mode)
- Structured logging with Logstash integration
- Async email sending

## Frontend Structure

### Next.js 15 App Router (Port 3000) ✅

**Implemented Pages:**
- `/` - Home page
- `/login` - User login
- `/register` - User registration
- `/verify-email` - Email verification
- `/reset-password` - Password reset
- `/profile` - User profile (with tabs: Profile, Settings)
- `/map` - Interactive map
- `/resorts` - Fishing places/resorts listing
- `/shop` - Online shop
- `/stores` - Stores page
- `/forecast` - Weather forecast

**State Management:**
- Zustand stores (useAuthStore for authentication)

**API Proxying:**
Next.js rewrites configured in `next.config.js`:
```
/api/v1/auth/* -> http://host.docker.internal:8001/api/v1/auth/*
/api/v1/users/* -> http://host.docker.internal:8001/api/v1/users/*
/api/v1/places/* -> http://host.docker.internal:8002/api/v1/places/*
/api/v1/reports/* -> http://host.docker.internal:8003/api/v1/reports/*
/api/v1/booking/* -> http://host.docker.internal:8004/api/v1/booking/*
/api/v1/shop/* -> http://host.docker.internal:8005/api/v1/shop/*
/api/v1/email/* -> http://host.docker.internal:8006/api/v1/email/*
```

## Database Design

### Shared Database Strategy
Single PostgreSQL database shared by all microservices:
- **Pros**: Simple transactions, data consistency, easier to develop
- **Cons**: Tight coupling, single point of failure

### Cross-Service Data References

**Strategy**: FK constraints at database level only, not at ORM level

**Rationale**:
- Microservices independence: Each service can operate without importing models from other services
- Referential integrity: PostgreSQL FK constraints ensure data consistency
- Validation: User existence validated via JWT token, not DB lookup

**Affected tables**:
- `places.owner_id` → references `users.id` (DB-level FK only)
- `favorite_places.user_id` → references `users.id` (DB-level FK only)

### Implemented Tables
- `users` - User accounts (email, username, password_hash, role, etc.)
- `refresh_tokens` - JWT refresh tokens
- `email_verification_codes` - Email verification codes

### Planned Tables (in schema.sql, not yet used)
- `places` - Fishing places
- `reports` - Fishing reports
- `bookings` - Booking records
- `booking_slots` - Available booking slots
- `products` - Shop products
- `categories` - Product categories
- `orders` - Shop orders
- `order_items` - Order line items
- `ratings` - Ratings for places and reports

### User Model Fields
```python
id: UUID (primary key)
email: VARCHAR(255) UNIQUE
username: VARCHAR(100) UNIQUE
password_hash: VARCHAR(255)
first_name: VARCHAR(100)
last_name: VARCHAR(100)
phone: VARCHAR(20)
avatar_url: VARCHAR(500)
is_active: BOOLEAN (default true)
is_verified: BOOLEAN (default false)
role: VARCHAR(20) (default 'user')  # user, moderator, admin
created_at: TIMESTAMP
updated_at: TIMESTAMP
```

## Authentication Flow

### Registration Flow
```
1. User submits registration form
   Frontend → Auth Service (/api/v1/auth/register)
   → Creates user in DB
   → Generates verification code
   → Sends verification email via Email Service

2. User receives email with verification code

3. User verifies email
   Frontend → Auth Service (/api/v1/auth/verify-email)
   → Validates code
   → Updates user.is_verified = true
   → Returns JWT access token

4. Frontend stores access token in memory
```

### Login Flow
```
1. User submits login credentials
   Frontend → Auth Service (/api/v1/auth/login)
   → Validates email and password
   → Checks is_verified status
   → Returns JWT access token

2. Frontend stores access token in memory

3. Frontend includes Authorization header for authenticated requests
   Authorization: Bearer <access_token>
```

### Password Reset Flow
```
1. User requests password reset
   Frontend → Auth Service (/api/v1/auth/reset-password/request)
   → Generates reset token (JWT, 1 hour expiry)
   → Returns success message

2. User receives reset link with token

3. User submits new password
   Frontend → Auth Service (/api/v1/auth/reset-password/confirm)
   → Validates token
   → Updates password
```

## Caching Strategy (Redis)

### Current Usage
- Planned for:
  - Session store for refresh tokens
  - API response caching
  - Rate limiting

### Planned Use Cases
```python
# Session Store
Key: refresh:{token}
Value: {user_id, expires_at}
TTL: 7 days

# API Response Caching
Key: api:{endpoint}:{params_hash}
Value: {response_data}
TTL: 5-60 minutes

# Rate Limiting
Key: ratelimit:{user_id}:{endpoint}
Value: request_count
TTL: 1 minute
```

## Security

### Authentication
- JWT access tokens (no expiry configured currently, typically 30 min)
- Bcrypt password hashing
- Email verification required
- Password reset with temporary tokens

### Authorization
- Role-based access control (RBAC): user, moderator, admin
- Role field in User model and JWT tokens

### Data Protection
- HTTPS in production (planned)
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy)
- XSS protection (React escaping)

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message",
    "details": {}
  }
}
```

### Implemented Error Codes
- `EMAIL_ALREADY_EXISTS` - Email already registered
- `USERNAME_ALREADY_EXISTS` - Username already taken
- `INVALID_OR_EXPIRED_CODE` - Invalid or expired verification code
- `INVALID_CREDENTIALS` - Invalid email or password
- `EMAIL_NOT_VERIFIED` - Email not verified
- `USER_NOT_FOUND` - User not found
- `EMAIL_SEND_FAILED` - Failed to send email

## Monitoring & Logging

### Structured Logging
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "service": "auth-service",
  "message": "User logged in",
  "user_id": "abc-123",
  "ip": "192.168.1.1"
}
```

### ELK Stack Integration
- **Elasticsearch**: Log storage
- **Logstash**: Log processing (port 5000)
- **Kibana**: Log visualization (planned)

### Health Checks
All services expose `/health` endpoint:
```json
{
  "status": "healthy",
  "service": "auth-service",
  "version": "1.0.0"
}
```

## Deployment Architecture

### Development
```
Local machine
├── docker-compose.dev.yml
├── PostgreSQL (port 5432)
├── Redis (port 6379)
├── Services (ports 8001-8006)
└── Frontend (port 3000)
```

### Production (Planned)
```
Docker Swarm Cluster
├── Traefik (reverse proxy)
├── PostgreSQL (with backup)
├── Redis (with persistence)
└── Services (2+ replicas each)
```

## Future Improvements

1. **Places Service** - Implement CRUD operations, map integration
2. **Reports Service** - Implement report creation, image upload
3. **Booking Service** - Implement booking system, Stripe integration
4. **Shop Service** - Implement e-commerce functionality
5. **Event-Driven Architecture** - Add message queue (RabbitMQ/Kafka)
6. **Database per Service** - Migrate to separate databases
7. **API Gateway** - GraphQL Gateway or centralized routing
8. **Monitoring** - Prometheus, Grafana
9. **WebSocket** - Real-time notifications
10. **Rate Limiting** - Per-user and per-IP limits

## Development Roadmap

### Phase 1: Authentication (✅ Complete)
- User registration with email verification
- Login/logout
- Password reset
- User profile management

### Phase 2: Places Service (🚧 In Progress)
- CRUD operations for places
- Map integration (Mapbox)
- Search and filtering

### Phase 3: Reports Service (Planned)
- Report creation and management
- Image upload (Cloudinary)
- Comments and ratings

### Phase 4: Booking Service (Planned)
- Booking system
- Availability management
- Stripe payment integration

### Phase 5: Shop Service (Planned)
- Product catalog
- Shopping cart
- Order management
- Stripe payment integration

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ (for local development)
- Node.js 20+ (for local development)

### Running the Application
```bash
# Development
docker-compose -f docker-compose.dev.yml up -d

# Access services
Frontend: http://localhost:3000
Auth Service: http://localhost:8001
Places Service: http://localhost:8002
Reports Service: http://localhost:8003
Booking Service: http://localhost:8004
Shop Service: http://localhost:8005
Email Service: http://localhost:8006
```

### Testing Auth Service
```bash
# Register
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"test","password":"password123"}'

# Login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Get current user (requires token)
curl -X GET http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```
