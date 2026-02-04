# Architecture Documentation

## Overview

The Fishing Platform is a microservices-based application built with:
- **Frontend**: Next.js 15 (App Router)
- **Backend**: FastAPI (Python) microservices
- **Database**: PostgreSQL (single shared database)
- **Cache**: Redis
- **Infrastructure**: Docker Swarm with Traefik

## Microservices

### 1. Auth Service (Port 8000)
**Responsibilities:**
- User registration & authentication
- JWT token generation & validation
- User profile management
- Password reset
- Email verification

**API Routes:**
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout user
- `POST /api/v1/auth/verify-email` - Verify email
- `POST /api/v1/auth/reset-password` - Reset password
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update user profile
- `PATCH /api/v1/users/me/password` - Change password
- `DELETE /api/v1/users/me` - Delete account

**Database Tables:**
- `users`
- `refresh_tokens`

### 2. Places Service (Port 8001)
**Responsibilities:**
- Manage fishing places
- Search & filtering
- Geospatial queries
- Place ratings

**API Routes:**
- `GET /api/v1/places` - List places with filters
- `GET /api/v1/places/:id` - Get place details
- `POST /api/v1/places` - Create new place
- `PUT /api/v1/places/:id` - Update place
- `DELETE /api/v1/places/:id` - Delete place
- `GET /api/v1/places/nearby` - Find nearby places
- `GET /api/v1/places/:id/reviews` - Get place reviews

**Database Tables:**
- `places`
- `ratings` (read-only for ratings)

### 3. Reports Service (Port 8002)
**Responsibilities:**
- User reports & posts
- Image upload (Cloudinary)
- Comments & likes
- Fish species tracking

**API Routes:**
- `GET /api/v1/reports` - List reports
- `GET /api/v1/reports/:id` - Get report details
- `POST /api/v1/reports` - Create report
- `PUT /api/v1/reports/:id` - Update report
- `DELETE /api/v1/reports/:id` - Delete report
- `POST /api/v1/reports/:id/like` - Like report
- `DELETE /api/v1/reports/:id/like` - Unlike report
- `GET /api/v1/reports/:id/comments` - Get comments
- `POST /api/v1/reports/:id/comments` - Add comment

**Database Tables:**
- `reports`
- `ratings`

### 4. Booking Service (Port 8003)
**Responsibilities:**
- Booking management
- Availability slots
- Payment processing (Stripe)
- Booking cancellation

**API Routes:**
- `GET /api/v1/bookings` - List user bookings
- `GET /api/v1/bookings/:id` - Get booking details
- `POST /api/v1/bookings` - Create booking
- `PATCH /api/v1/bookings/:id/cancel` - Cancel booking
- `GET /api/v1/booking-slots` - Get available slots
- `POST /api/v1/booking-slots` - Create slot (for place owners)
- `DELETE /api/v1/booking-slots/:id` - Delete slot
- `POST /api/v1/bookings/:id/webhook` - Stripe webhook

**Database Tables:**
- `bookings`
- `booking_slots`

### 5. Shop Service (Port 8004)
**Responsibilities:**
- Product catalog
- Categories
- Shopping cart
- Order management
- Payment processing (Stripe)

**API Routes:**
- `GET /api/v1/shop/products` - List products
- `GET /api/v1/shop/products/:id` - Get product details
- `GET /api/v1/shop/categories` - List categories
- `GET /api/v1/orders` - List user orders
- `GET /api/v1/orders/:id` - Get order details
- `POST /api/v1/orders` - Create order
- `PATCH /api/v1/orders/:id/cancel` - Cancel order
- `POST /api/v1/orders/webhook` - Stripe webhook

**Database Tables:**
- `products`
- `categories`
- `orders`
- `order_items`

## Communication Patterns

### REST API
All microservices communicate via REST API over HTTP:
- Frontend → Services (via Traefik)
- Service → Service (via Traefik)
- External Webhooks → Services (via Traefik)

### Authentication Flow

```
1. User registers
   Frontend → Auth Service (/auth/register)
   → Creates user in DB
   → Returns success

2. User logs in
   Frontend → Auth Service (/auth/login)
   → Validates credentials
   → Returns access_token (JWT) + refresh_token

3. Frontend stores tokens
   - Access token in memory (30 min)
   - Refresh token in HTTP-only cookie (7 days)

4. Frontend makes authenticated request
   Frontend → Any Service
   Headers: Authorization: Bearer <access_token>
   → Service validates JWT
   → Returns data

5. Access token expires
   Frontend → Auth Service (/auth/refresh)
   Cookie: refresh_token
   → Returns new access_token
```

### Data Flow Example (Booking)

```
1. User views place
   Frontend → Places Service (/places/:id)
   → Returns place details

2. User checks availability
   Frontend → Booking Service (/booking-slots?place_id=X)
   → Returns available slots

3. User creates booking
   Frontend → Booking Service (/bookings)
   Headers: Authorization: Bearer <token>
   Body: { place_id, slot_id, people_count }
   → Creates pending booking
   → Returns Stripe client_secret

4. User pays
   Frontend → Stripe SDK
   → User completes payment

5. Stripe webhook
   Stripe → Booking Service (/bookings/webhook)
   → Updates booking to confirmed
   → Emails user

6. User views bookings
   Frontend → Booking Service (/bookings)
   → Returns user's bookings
```

## Database Design

### Shared Database Strategy
Single PostgreSQL database shared by all microservices:
- **Pros**: Simple transactions, data consistency, easier to develop
- **Cons**: Tight coupling, single point of failure

### Table Ownership

| Table | Owner Service | Shared By |
|-------|---------------|-----------|
| users | Auth | All |
| refresh_tokens | Auth | None |
| places | Places | All (read) |
| reports | Reports | All (read) |
| bookings | Booking | All (read) |
| booking_slots | Booking | None |
| products | Shop | All (read) |
| categories | Shop | All (read) |
| orders | Shop | All (read) |
| order_items | Shop | All (read) |
| ratings | Reports | Places (read) |

### Database Connection
All services connect to the same PostgreSQL instance:
```
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/fishing_db
```

## Caching Strategy

### Redis Use Cases

1. **Session Store** - Refresh tokens
   ```
   Key: refresh:{token}
   Value: {user_id, expires_at}
   TTL: 7 days
   ```

2. **API Response Caching**
   ```
   Key: api:{endpoint}:{params_hash}
   Value: {response_data}
   TTL: 5-60 minutes
   ```

3. **Rate Limiting**
   ```
   Key: ratelimit:{user_id}:{endpoint}
   Value: request_count
   TTL: 1 minute
   ```

4. **Place Search Cache**
   ```
   Key: search:places:{lat},{lng},{radius}
   Value: [place_ids]
   TTL: 1 hour
   ```

## Security

### Authentication
- JWT access tokens (30 min expiry)
- Refresh tokens (7 days expiry)
- HTTP-only cookies for refresh tokens
- Password hashing with bcrypt

### Authorization
- Role-based access control (RBAC)
- Resource ownership checks
- Admin endpoints

### Data Protection
- HTTPS in production
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy)
- XSS protection (React)

## Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Place with id 'abc' not found",
    "details": {}
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid input data |
| UNAUTHORIZED | 401 | Missing or invalid token |
| FORBIDDEN | 403 | Insufficient permissions |
| RESOURCE_NOT_FOUND | 404 | Resource doesn't exist |
| CONFLICT | 409 | Resource already exists |
| INTERNAL_ERROR | 500 | Server error |

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

### Health Checks
Each service exposes `/health` endpoint:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

## Scalability

### Horizontal Scaling
Each service can be scaled independently:
```bash
# Scale auth-service to 4 instances
docker service scale fishing_auth-service=4
```

### Load Balancing
Traefik distributes requests across service instances.

### Database Scaling
For production:
- Read replicas for reads
- Connection pooling
- Database sharding (if needed)

## Deployment Architecture

### Development
```
Local machine
├── docker-compose.dev.yml
├── Traefik (port 80, 8080)
├── PostgreSQL (port 5432)
├── Redis (port 6379)
└── Services (ports 8000-8004, 3000)
```

### Production
```
Docker Swarm Cluster
├── Manager nodes (3)
├── Worker nodes (5+)
├── Traefik (3 replicas)
├── PostgreSQL (with backup)
├── Redis (with persistence)
└── Services (2+ replicas each)
```

## Future Improvements

1. **Event-Driven Architecture** - Add message queue (RabbitMQ/Kafka)
2. **Database per Service** - Migrate to separate databases
3. **GraphQL** - Add GraphQL gateway
4. **Micro Frontends** - Split frontend into micro frontends
5. **CI/CD Pipeline** - Automated testing & deployment
6. **Monitoring** - Prometheus, Grafana, ELK stack
7. **Rate Limiting** - Per-user and per-IP limits
8. **WebSocket** - Real-time notifications
