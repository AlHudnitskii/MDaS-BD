CREATE TABLE IF NOT EXISTS "user" (
    id serial PRIMARY KEY,
    username varchar(150) UNIQUE NOT NULL,
    password varchar(128) NOT NULL,
    email varchar(254) UNIQUE NOT NULL,
    first_name varchar(150),
    last_name varchar(150),
    is_active boolean NOT NULL DEFAULT true,
    image varchar,
    is_staff boolean NOT NULL DEFAULT false,
    is_superuser boolean NOT NULL DEFAULT false,
    date_joined timestamp with time zone NOT NULL,
    last_login timestamp with time zone
);

CREATE TABLE IF NOT EXISTS "role" (
    id serial PRIMARY KEY,
    name varchar(100) UNIQUE NOT NULL,
    description text,
    created_at timestamp with time zone NOT NULL
);

CREATE TABLE IF NOT EXISTS "user_role" (
    id serial PRIMARY KEY,
    user_id integer NOT NULL,
    role_id integer NOT NULL,
    assigned_at timestamp with time zone NOT NULL,
    assigned_by_id integer,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES "role"(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by_id) REFERENCES "user"(id) ON DELETE SET NULL,
    UNIQUE (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS "user_note" (
    id serial PRIMARY KEY,
    user_id integer NOT NULL,
    title varchar(200) NOT NULL,
    content text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "user_timezone" (
    id serial PRIMARY KEY,
    user_id integer UNIQUE NOT NULL,
    timezone varchar(32) NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "log_entry" (
    id serial PRIMARY KEY,
    user_id integer,
    action varchar(50) NOT NULL,
    details jsonb,
    ip_address inet,
    status varchar(10),
    "timestamp" timestamp with time zone NOT NULL,
    user_agent text,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS "category" (
    id serial PRIMARY KEY,
    name varchar(20) UNIQUE NOT NULL,
    slug varchar(20) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS "product" (
    id serial PRIMARY KEY,
    category_id integer NOT NULL,
    name varchar(50) NOT NULL,
    slug varchar(50) NOT NULL,
    image varchar,
    description text,
    price decimal(10,2) NOT NULL,
    available boolean NOT NULL,
    created timestamp with time zone NOT NULL,
    updated timestamp with time zone NOT NULL,
    discount decimal(4,2) NOT NULL,
    FOREIGN KEY (category_id) REFERENCES "category"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "product_image" (
    id serial PRIMARY KEY,
    product_id integer NOT NULL,
    image varchar,
    alt_text varchar(255),
    is_main boolean,
    display_order integer,
    created_at timestamp with time zone,
    FOREIGN KEY (product_id) REFERENCES "product"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS"product_review" (
    id serial PRIMARY KEY,
    product_id integer NOT NULL,
    user_id integer NOT NULL,
    rating integer NOT NULL,
    comment text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    is_verified boolean NOT NULL,
    FOREIGN KEY (product_id) REFERENCES "product"(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    UNIQUE (product_id, user_id)
);

CREATE TABLE IF NOT EXISTS "order" (
    id serial PRIMARY KEY,
    user_id integer,
    first_name varchar(50) NOT NULL,
    last_name varchar(50) NOT NULL,
    email varchar(254) NOT NULL,
    city varchar(100) NOT NULL,
    address varchar(250) NOT NULL,
    postal_code varchar(20) NOT NULL,
    created timestamp with time zone NOT NULL,
    updated timestamp with time zone NOT NULL,
    paid boolean NOT NULL,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS "order_item" (
    id serial PRIMARY KEY,
    order_id integer NOT NULL,
    product_id integer NOT NULL,
    price decimal(10,2) NOT NULL,
    quantity integer NOT NULL,
    FOREIGN KEY (order_id) REFERENCES "order"(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES "product"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "wishlist" (
    id serial PRIMARY KEY,
    user_id integer NOT NULL,
    product_id integer NOT NULL,
    added_at timestamp with time zone NOT NULL,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES "product"(id) ON DELETE CASCADE,
    UNIQUE (user_id, product_id)
);