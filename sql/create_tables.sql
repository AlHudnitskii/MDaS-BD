CREATE TABLE IF NOT EXISTS "users" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(128) NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    image VARCHAR,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    date_joined TIMESTAMP WITH TIME ZONE NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    CONSTRAINT check_email_format CHECK (email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$')
);

CREATE TABLE IF NOT EXISTS "roles" (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE IF NOT EXISTS "user_roles" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "users"(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES "roles"(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL,
    assigned_by_id INTEGER REFERENCES "users"(id) ON DELETE SET NULL,
    CONSTRAINT user_role_unique UNIQUE (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS "user_notes" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "users"(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE IF NOT EXISTS "log_entries" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "users"(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    details jsonb,
    ip_address inet,
    status VARCHAR(10),
    "timestamp" TIMESTAMP WITH TIME ZONE NOT NULL,
    user_agent TEXT,
    CONSTRAINT check_status CHECK (status IN ('SUCCESS', 'FAILED', 'WARNING'))
);

CREATE TABLE IF NOT EXISTS "categories" (
    id SERIAL PRIMARY KEY,
    name VARCHAR(20) UNIQUE NOT NULL,
    slug VARCHAR(20) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS "products" (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES "categories"(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    slug VARCHAR(50) NOT NULL,
    image VARCHAR,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    available BOOLEAN NOT NULL,
    created TIMESTAMP WITH TIME ZONE NOT NULL,
    updated TIMESTAMP WITH TIME ZONE NOT NULL,
    discount DECIMAL(4,2) NOT NULL,
    CONSTRAINT check_price_positive CHECK (price >= 0),
    CONSTRAINT check_discount_non_negative CHECK (discount >= 0)
);

CREATE TABLE IF NOT EXISTS "product_images" (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES "products"(id) ON DELETE CASCADE,
    image VARCHAR,
    alt_text VARCHAR(255),
    is_main BOOLEAN,
    display_order INTEGER,
    created_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS "product_reviews" (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES "products"(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES "users"(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_verified BOOLEAN NOT NULL,
    CONSTRAINT check_rating_range CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT product_user_unique UNIQUE (product_id, user_id)
);

CREATE TABLE IF NOT EXISTS "orders" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "users"(id) ON DELETE SET NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(254) NOT NULL,
    city VARCHAR(100) NOT NULL,
    address VARCHAR(250) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    created TIMESTAMP WITH TIME ZONE NOT NULL,
    updated TIMESTAMP WITH TIME ZONE NOT NULL,
    paid BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS "order_items" (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES "orders"(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES "products"(id) ON DELETE CASCADE,
    price DECIMAL(10,2) NOT NULL,
    quantity INTEGER NOT NULL,
    CONSTRAINT check_quantity_positive CHECK (quantity > 0)
);

CREATE TABLE IF NOT EXISTS "wishlists" (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES "users"(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES "products"(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT user_product_unique UNIQUE (user_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_user_active_joined ON "users"(is_active, date_joined);
CREATE INDEX IF NOT EXISTS idx_log_entry_user_timestamp ON "log_entries"(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_log_entry_action_status ON "log_entries"(action, details);
CREATE INDEX IF NOT EXISTS idx_product_category_available ON "products"(category_id, created_at);
CREATE INDEX IF NOT EXISTS idx_product_price_discount ON "products"(price, discount);
CREATE INDEX IF NOT EXISTS idx_product_review_product_rating ON "product_reviews"(product_id, rating);
CREATE INDEX IF NOT EXISTS idx_order_user_created ON "orders"(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_order_paid_created ON "orders"(paid, created_at);
CREATE INDEX IF NOT EXISTS idx_order_item_order_id ON "order_items"(order_id);