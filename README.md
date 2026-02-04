# Fishing Platform

Microservices-based platform for fishing enthusiasts with places catalog, reports, booking, and shop.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Docker Swarm Cluster                               │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        Traefik (API Gateway)                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Frontend    │  │ Auth Service │  │Places Service│  │Reports       │  │
│  │  (Next.js)   │  │  (FastAPI)   │  │  (FastAPI)   │  │Service       │  │
│  │  Port: 3000  │  │  Port: 8000  │  │  Port: 8001  │  │(FastAPI)     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │  Port: 8002  │  │
│                                                        └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Booking       │  │Shop Service  │  │PostgreSQL    │  │Redis         │  │
│  │Service       │  │  (FastAPI)   │  │   (DB)       │  │  (Cache)     │  │
│  │(FastAPI)     │  │  Port: 8004  │  │  Port: 5432  │  │  Port: 6379  │  │
│  │  Port: 8003  │  └──────────────┘  └──────────────┘  └──────────────┘  │
│  └──────────────┘                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Frontend
- **Next.js 15** (App Router) - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS
- **shadcn/ui** - Component library
- **Framer Motion** - Animations
- **Zustand** - State management

### Backend
- **FastAPI** - Python async web framework
- **PostgreSQL** - Relational database
- **Redis** - Caching & sessions
- **SQLAlchemy** - Async ORM
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **JWT** - Authentication tokens

### Infrastructure
- **Docker Swarm** - Container orchestration
- **Traefik** - Reverse proxy & load balancer
- **Docker** - Containerization

### External Services
- **Mapbox GL JS** - Interactive maps
- **Stripe** - Payment processing
- **Cloudinary** - Image hosting

## Project Structure

```
.
├── services/
│   ├── auth-service/          # Authentication & users
│   ├── places-service/        # Places catalog
│   ├── reports-service/       # Fishing reports
│   ├── booking-service/      # Booking system
│   ├── shop-service/          # E-commerce
│   └── shared-utils/          # Shared code
├── frontend/                   # Next.js application
├── database/                   # Database schema
├── docker-compose.yml         # Docker Swarm config
├── docker-compose.dev.yml     # Local development
└── .env.example               # Environment variables
```

## Features

### Auth Service
- User registration & authentication
- JWT access & refresh tokens
- Email verification
- Password reset
- Profile management

### Places Service
- Browse fishing places
- Search & filter by location
- View place details & reviews
- Interactive map
- Add new places

### Reports Service
- Share fishing reports
- Upload photos
- Rate places
- Comments & likes
- Fish species tracking

### Booking Service
- Reserve fishing spots
- Calendar view
- Payment processing
- Booking management
- Cancellation policy

### Shop Service
- Browse fishing equipment
- Product categories
- Shopping cart
- Secure checkout
- Order tracking

## Getting Started

### Prerequisites
- Docker & Docker Swarm
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

### Running with Docker

```bash
# For local development
docker-compose -f docker-compose.dev.yml up -d

# For Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.yml fishing
```

### Accessing Services
- Frontend: http://localhost
- Traefik Dashboard: http://localhost:8080
- API: http://localhost/api/v1/

## API Endpoints

### Auth Service
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update profile

### Places Service
- `GET /api/v1/places` - List places
- `GET /api/v1/places/:id` - Get place details
- `POST /api/v1/places` - Create place
- `PUT /api/v1/places/:id` - Update place
- `DELETE /api/v1/places/:id` - Delete place

### Reports Service
- `GET /api/v1/reports` - List reports
- `GET /api/v1/reports/:id` - Get report details
- `POST /api/v1/reports` - Create report
- `PUT /api/v1/reports/:id` - Update report
- `DELETE /api/v1/reports/:id` - Delete report

### Booking Service
- `GET /api/v1/bookings` - List bookings
- `GET /api/v1/bookings/:id` - Get booking details
- `POST /api/v1/bookings` - Create booking
- `PATCH /api/v1/bookings/:id/cancel` - Cancel booking
- `GET /api/v1/booking-slots` - Get available slots

### Shop Service
- `GET /api/v1/shop/products` - List products
- `GET /api/v1/shop/products/:id` - Get product
- `GET /api/v1/shop/categories` - List categories
- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders` - List user orders

## Database Schema

See [database/schema.md](database/schema.md) for complete documentation.

## Development

### Local Development Setup

```bash
# Backend services
cd services/auth-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend
pytest services/

# Frontend
npm test
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Contributing

1. Fork the repository
2. Create feature branch
3. Make your changes
4. Write tests
5. Submit pull request

## License

MIT License - see LICENSE file for details
