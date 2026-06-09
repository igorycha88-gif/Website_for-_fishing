-- Fishing Platform Database Schema
-- PostgreSQL 14+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABLES
-- ============================================

-- Users table (Auth Service)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Places table (Places Service)
CREATE TABLE places (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    address VARCHAR(500) NOT NULL,
    city VARCHAR(100),
    region VARCHAR(100),
    price_per_day DECIMAL(10, 2),
    max_people INTEGER,
    facilities JSONB,
    fish_types JSONB,
    images TEXT[],
    rating_avg DECIMAL(3, 2) DEFAULT 0,
    reviews_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Reports table (Reports Service)
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    place_id UUID REFERENCES places(id) ON DELETE SET NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    images TEXT[],
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    fish_caught JSONB,
    weather JSONB,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Booking slots table (Booking Service)
CREATE TABLE booking_slots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    place_id UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    is_available BOOLEAN DEFAULT true,
    price DECIMAL(10, 2),
    max_people INTEGER,
    UNIQUE(place_id, date)
);

-- Bookings table (Booking Service)
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    place_id UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
    booking_slot_id UUID REFERENCES booking_slots(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    people_count INTEGER NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'confirmed', 'cancelled', 'completed')),
    payment_intent_id VARCHAR(200),
    cancel_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Categories table (Shop Service)
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    slug VARCHAR(100) UNIQUE
);

-- Products table (Shop Service)
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER DEFAULT 0,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    images TEXT[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Orders table (Shop Service)
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total_price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')),
    payment_intent_id VARCHAR(200),
    shipping_address JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Order items table (Shop Service)
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

-- Refresh tokens table (Auth Service)
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Ratings table (Reports/Places Service)
CREATE TABLE ratings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    place_id UUID REFERENCES places(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================

-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- Places indexes
CREATE INDEX idx_places_location ON places(latitude, longitude);
CREATE INDEX idx_places_owner ON places(owner_id);
CREATE INDEX idx_places_active ON places(is_active);
CREATE INDEX idx_places_rating ON places(rating_avg DESC);

-- Reports indexes
CREATE INDEX idx_reports_user ON reports(user_id);
CREATE INDEX idx_reports_place ON reports(place_id);
CREATE INDEX idx_reports_created ON reports(created_at DESC);

-- Bookings indexes
CREATE INDEX idx_bookings_user ON bookings(user_id);
CREATE INDEX idx_bookings_place ON bookings(place_id);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_date ON bookings(date);

-- Booking slots indexes
CREATE INDEX idx_booking_slots_place_date ON booking_slots(place_id, date);
CREATE INDEX idx_booking_slots_available ON booking_slots(is_available);

-- Products indexes
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_products_title ON products USING gin(to_tsvector('english', title));

-- Orders indexes
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at DESC);

-- Order items indexes
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- Refresh tokens indexes
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);

-- Ratings indexes
CREATE INDEX idx_ratings_user ON ratings(user_id);
CREATE INDEX idx_ratings_report ON ratings(report_id);
CREATE INDEX idx_ratings_place ON ratings(place_id);

-- Categories indexes
CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_slug ON categories(slug);

-- JSONB indexes
CREATE INDEX idx_places_facilities ON places USING GIN(facilities);
CREATE INDEX idx_places_fish_types ON places USING GIN(fish_types);
CREATE INDEX idx_reports_fish_caught ON reports USING GIN(fish_caught);

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_places_updated_at BEFORE UPDATE ON places
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reports_updated_at BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bookings_updated_at BEFORE UPDATE ON bookings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update place rating average
CREATE OR REPLACE FUNCTION update_place_rating()
RETURNS TRIGGER AS $$
DECLARE
    avg_rating DECIMAL(3, 2);
    review_count INTEGER;
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        IF NEW.place_id IS NOT NULL THEN
            SELECT COALESCE(AVG(rating), 0), COUNT(*) INTO avg_rating, review_count
            FROM ratings
            WHERE place_id = NEW.place_id;

            UPDATE places
            SET rating_avg = avg_rating,
                reviews_count = review_count
            WHERE id = NEW.place_id;
        END IF;
    ELSIF TG_OP = 'DELETE' THEN
        IF OLD.place_id IS NOT NULL THEN
            SELECT COALESCE(AVG(rating), 0), COUNT(*) INTO avg_rating, review_count
            FROM ratings
            WHERE place_id = OLD.place_id;

            UPDATE places
            SET rating_avg = avg_rating,
                reviews_count = review_count
            WHERE id = OLD.place_id;
        END IF;
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger for ratings
CREATE TRIGGER trigger_update_place_rating
    AFTER INSERT OR UPDATE OR DELETE ON ratings
    FOR EACH ROW EXECUTE FUNCTION update_place_rating();

-- ============================================
-- SAMPLE DATA (Optional)
-- ============================================

-- Insert sample categories
INSERT INTO categories (name, description, slug) VALUES
('Удочки', 'Рыболовные удочки всех типов', 'udochki'),
('Катушки', 'Катушки для спиннинга и фидерной ловли', 'katushki'),
('Приманки', 'Воблеры, блесны, силикон', 'primanki'),
('Крючки', 'Крючки разных размеров и типов', 'kryuchki'),
('Одежда', 'Рыболовная одежда', 'odezhda');

-- ============================================
-- VIEWS
-- ============================================

-- View for place details with owner info
CREATE VIEW v_places_with_owner AS
SELECT
    p.*,
    u.username as owner_username,
    u.first_name as owner_first_name,
    u.last_name as owner_last_name,
    u.avatar_url as owner_avatar_url
FROM places p
JOIN users u ON p.owner_id = u.id;

-- View for booking details with place and user info
CREATE VIEW v_bookings_details AS
SELECT
    b.*,
    p.title as place_title,
    p.latitude as place_latitude,
    p.longitude as place_longitude,
    u.username as user_username,
    u.email as user_email
FROM bookings b
JOIN places p ON b.place_id = p.id
JOIN users u ON b.user_id = u.id;
