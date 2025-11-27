INSERT INTO "users" (id, username, password, email, first_name, last_name, is_active, image_url, timezone, is_superuser, date_joined) VALUES
('550e8400-e29b-41d4-a716-446655440001'::uuid, 'admin', 'admin', 'admin@example.com', 'Admin', 'User', TRUE,  'users/admin.jpg', 'UTC', TRUE, NOW()),
('550e8400-e29b-41d4-a716-446655440002'::uuid, 'john_doe', 'john_doe', 'john@example.com', 'John', 'Doe', TRUE,  'users/john.jpg', 'America/New_York', FALSE, NOW()),
('550e8400-e29b-41d4-a716-446655440003'::uuid, 'jane_smith', 'jane_smith', 'jane@example.com', 'Jane', 'Smith', TRUE,  'users/jane.jpg', 'Europe/London', FALSE, NOW()),
('550e8400-e29b-41d4-a716-446655440004'::uuid, 'bob_wilson', 'bob_wilson', 'bob@example.com', 'Bob', 'Wilson', TRUE,  'users/bob.jpg', 'Asia/Tokyo', FALSE, NOW()),
('550e8400-e29b-41d4-a716-446655440005'::uuid, 'alice_brown', 'alice_brown', 'alice@example.com', 'Alice', 'Brown', FALSE, 'users/alice.jpg', 'Australia/Sydney', FALSE, NOW());

INSERT INTO "roles" (id, name, description, created_at) VALUES
('550e8400-e29b-41d4-a716-446655440101'::uuid, 'Customer', 'Regular customer with basic permissions', NOW()),
('550e8400-e29b-41d4-a716-446655440102'::uuid, 'Premium Customer', 'Premium customer with extended permissions', NOW()),
('550e8400-e29b-41d4-a716-446655440103'::uuid, 'Manager', 'Store manager with administrative permissions', NOW()),
('550e8400-e29b-41d4-a716-446655440104'::uuid, 'Support', 'Customer support representative', NOW());

INSERT INTO "user_roles" (id, user_id, role_id, assigned_at, assigned_by_id) VALUES
('550e8400-e29b-41d4-a716-446655440201'::uuid, '550e8400-e29b-41d4-a716-446655440001'::uuid, '550e8400-e29b-41d4-a716-446655440103'::uuid, NOW(), NULL),
('550e8400-e29b-41d4-a716-446655440202'::uuid, '550e8400-e29b-41d4-a716-446655440002'::uuid, '550e8400-e29b-41d4-a716-446655440102'::uuid, NOW(), '550e8400-e29b-41d4-a716-446655440001'::uuid),
('550e8400-e29b-41d4-a716-446655440203'::uuid, '550e8400-e29b-41d4-a716-446655440003'::uuid, '550e8400-e29b-41d4-a716-446655440101'::uuid, NOW(), '550e8400-e29b-41d4-a716-446655440001'::uuid),
('550e8400-e29b-41d4-a716-446655440204'::uuid, '550e8400-e29b-41d4-a716-446655440004'::uuid, '550e8400-e29b-41d4-a716-446655440104'::uuid, NOW(), '550e8400-e29b-41d4-a716-446655440001'::uuid),
('550e8400-e29b-41d4-a716-446655440205'::uuid, '550e8400-e29b-41d4-a716-446655440005'::uuid, '550e8400-e29b-41d4-a716-446655440102'::uuid, NOW(), '550e8400-e29b-41d4-a716-446655440001'::uuid);

INSERT INTO "user_notes" (id, user_id, title, content, created_at, updated_at) VALUES
('550e8400-e29b-41d4-a716-446655440301'::uuid, '550e8400-e29b-41d4-a716-446655440001'::uuid, 'Shopping List', 'Need to buy new headphones and keyboard', NOW(), NOW()),
('550e8400-e29b-41d4-a716-446655440302'::uuid, '550e8400-e29b-41d4-a716-446655440002'::uuid, 'Wishlist Items', 'Looking for gaming accessories', NOW(), NOW()),
('550e8400-e29b-41d4-a716-446655440303'::uuid, '550e8400-e29b-41d4-a716-446655440003'::uuid, 'Product Ideas', 'Suggestions for new product categories', NOW(), NOW());

INSERT INTO log_entries (id, user_id, action, details, status, timestamp) VALUES
('550e8400-e29b-41d4-a716-446655440351'::uuid, '550e8400-e29b-41d4-a716-446655440001'::uuid, 'LOGIN', '{"ip": "192.168.1.1", "user_agent": "Mozilla/5.0"}'::jsonb, 'SUCCESS', NOW() - INTERVAL '1 hour'),
('550e8400-e29b-41d4-a716-446655440352'::uuid, '550e8400-e29b-41d4-a716-446655440002'::uuid, 'ORDER_CREATED', '{"order_id": 1, "total": 459.98}'::jsonb, 'SUCCESS', NOW() - INTERVAL '5 days'),
('550e8400-e29b-41d4-a716-446655440353'::uuid, '550e8400-e29b-41d4-a716-446655440003'::uuid, 'ORDER_CREATED', '{"order_id": 2, "total": 129.97}'::jsonb, 'SUCCESS', NOW() - INTERVAL '3 days'),
('550e8400-e29b-41d4-a716-446655440354'::uuid, '550e8400-e29b-41d4-a716-446655440004'::uuid, 'LOGIN_FAILED', '{"ip": "192.168.1.100", "reason": "invalid_password"}'::jsonb, 'FAILED', NOW() - INTERVAL '2 hours'),
('550e8400-e29b-41d4-a716-446655440355'::uuid, '550e8400-e29b-41d4-a716-446655440002'::uuid, 'REVIEW_POSTED', '{"product_id": 1, "rating": 5}'::jsonb, 'SUCCESS', NOW() - INTERVAL '3 days');

INSERT INTO "categories" (id, name, slug) VALUES
('550e8400-e29b-41d4-a716-446655440401'::uuid, 'Electronics', 'electronics'),
('550e8400-e29b-41d4-a716-446655440402'::uuid, 'Gaming', 'gaming'),
('550e8400-e29b-41d4-a716-446655440403'::uuid, 'Accessories', 'accessories'),
('550e8400-e29b-41d4-a716-446655440404'::uuid, 'Audio', 'audio'),
('550e8400-e29b-41d4-a716-446655440405'::uuid, 'Computing', 'computing');

INSERT INTO "products" (id, category_id, name, slug, description, price, available, created_at, updated_at, discount) VALUES
('550e8400-e29b-41d4-a716-446655440501'::uuid, '550e8400-e29b-41d4-a716-446655440404'::uuid, 'Wireless Headphones', 'wireless-headphones', 'High-quality wireless headphones with noise cancellation', 299.99, TRUE, NOW(), NOW(), 0.10),
('550e8400-e29b-41d4-a716-446655440502'::uuid, '550e8400-e29b-41d4-a716-446655440402'::uuid, 'Gaming Keyboard', 'gaming-keyboard', 'Mechanical gaming keyboard with RGB lighting', 159.99, TRUE, NOW(), NOW(), 0.05),
('550e8400-e29b-41d4-a716-446655440503'::uuid, '550e8400-e29b-41d4-a716-446655440402'::uuid, 'Gaming Mouse', 'gaming-mouse', 'Professional gaming mouse with precision sensor', 79.99, TRUE, NOW(), NOW(), 0.00),
('550e8400-e29b-41d4-a716-446655440504'::uuid, '550e8400-e29b-41d4-a716-446655440403'::uuid, 'Phone Case', 'phone-case', 'Protective phone case with premium materials', 24.99, FALSE, NOW(), NOW(), 0.15),
('550e8400-e29b-41d4-a716-446655440505'::uuid, '550e8400-e29b-41d4-a716-446655440401'::uuid, 'Tablet', 'tablet-10inch', '10-inch tablet with high-resolution display', 449.99, TRUE, NOW(), NOW(), 0.20),
('550e8400-e29b-41d4-a716-446655440506'::uuid, '550e8400-e29b-41d4-a716-446655440404'::uuid, 'Bluetooth Speaker', 'bluetooth-speaker', 'Portable Bluetooth speaker with rich sound', 89.99, TRUE, NOW(), NOW(), 0.08),
('550e8400-e29b-41d4-a716-446655440507'::uuid, '550e8400-e29b-41d4-a716-446655440405'::uuid, 'External HDD', 'external-hdd-1tb', '1TB external hard drive for backup', 69.99, TRUE, NOW(), NOW(), 0.00);

INSERT INTO "product_images" (id, product_id, image_url, description, is_main, created_at) VALUES
('550e8400-e29b-41d4-a716-446655440601'::uuid, '550e8400-e29b-41d4-a716-446655440501'::uuid, 'products/headphones_main.jpg', 'Wireless headphones main view', TRUE, NOW()),
('550e8400-e29b-41d4-a716-446655440602'::uuid, '550e8400-e29b-41d4-a716-446655440501'::uuid, 'products/headphones_side.jpg', 'Wireless headphones side view', FALSE, NOW()),
('550e8400-e29b-41d4-a716-446655440603'::uuid, '550e8400-e29b-41d4-a716-446655440502'::uuid, 'products/keyboard_main.jpg', 'Gaming keyboard main view', TRUE, NOW()),
('550e8400-e29b-41d4-a716-446655440604'::uuid, '550e8400-e29b-41d4-a716-446655440503'::uuid, 'products/mouse_main.jpg', 'Gaming mouse main view', TRUE, NOW()),
('550e8400-e29b-41d4-a716-446655440605'::uuid, '550e8400-e29b-41d4-a716-446655440504'::uuid, 'products/case_main.jpg', 'Phone case main view', TRUE, NOW());

INSERT INTO "orders" (id, user_id, first_name, last_name, email, city, address, postal_code, created_at, updated_at, paid) VALUES 
('550e8400-e29b-41d4-a716-446655440701'::uuid, '550e8400-e29b-41d4-a716-446655440001'::uuid, 'Admin', 'User', 'admin@example.com', 'New York', '123 Main St, Apt 4B', '10001', NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days', TRUE), 
('550e8400-e29b-41d4-a716-446655440702'::uuid, '550e8400-e29b-41d4-a716-446655440002'::uuid, 'John', 'Doe', 'john@example.com', 'London', '456 Queen St', 'SW1A 1AA', NOW() - INTERVAL '3 days', NOW() - INTERVAL '2 days', TRUE), 
('550e8400-e29b-41d4-a716-446655440703'::uuid, '550e8401-e29b-41d4-a716-446655440003'::uuid, 'Jane', 'Smith', 'jane@example.com', 'Tokyo', '789 Shibuya District', '150-0002', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day', FALSE);

INSERT INTO "order_items" (id, order_id, product_id, price, quantity) VALUES
('550e8400-e29b-41d4-a716-446655440801'::uuid, '550e8400-e29b-41d4-a716-446655440701'::uuid, '550e8400-e29b-41d4-a716-446655440501'::uuid, 299.99, 1),
('550e8400-e29b-41d4-a716-446655440802'::uuid, '550e8400-e29b-41d4-a716-446655440701'::uuid, '550e8400-e29b-41d4-a716-446655440502'::uuid, 159.99, 1),
('550e8400-e29b-41d4-a716-446655440803'::uuid, '550e8400-e29b-41d4-a716-446655440702'::uuid, '550e8400-e29b-41d4-a716-446655440503'::uuid, 79.99, 1),
('550e8400-e29b-41d4-a716-446655440804'::uuid, '550e8400-e29b-41d4-a716-446655440702'::uuid, '550e8400-e29b-41d4-a716-446655440504'::uuid, 24.99, 2),
('550e8400-e29b-41d4-a716-446655440805'::uuid, '550e8400-e29b-41d4-a716-446655440703'::uuid, '550e8400-e29b-41d4-a716-446655440506'::uuid, 89.99, 1),
('550e8400-e29b-41d4-a716-446655440806'::uuid, '550e8400-e29b-41d4-a716-446655440703'::uuid, '550e8400-e29b-41d4-a716-446655440507'::uuid, 69.99, 1);

INSERT INTO "product_reviews" (id, product_id, user_id, rating, comment, created_at, updated_at, is_verified) VALUES
('550e8400-e29b-41d4-a716-446655440901'::uuid, '550e8400-e29b-41d4-a716-446655440501'::uuid, '550e8400-e29b-41d4-a716-446655440002'::uuid, 5, 'Excellent headphones! Great sound quality and comfortable to wear.', NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days', TRUE),
('550e8400-e29b-41d4-a716-446655440902'::uuid, '550e8400-e29b-41d4-a716-446655440502'::uuid, '550e8400-e29b-41d4-a716-446655440002'::uuid, 4, 'Good keyboard, but a bit loud for office use.', NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days', TRUE),
('550e8400-e29b-41d4-a716-446655440903'::uuid, '550e8400-e29b-41d4-a716-446655440503'::uuid, '550e8400-e29b-41d4-a716-446655440003'::uuid, 5, 'Perfect gaming mouse, very responsive and accurate.', NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days', TRUE),
('550e8400-e29b-41d4-a716-446655440904'::uuid, '550e8400-e29b-41d4-a716-446655440504'::uuid, '550e8400-e29b-41d4-a716-446655440003'::uuid, 3, 'Phone case is okay, but not as durable as expected.', NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days', TRUE),
('550e8400-e29b-41d4-a716-446655440905'::uuid, '550e8400-e29b-41d4-a716-446655440506'::uuid, '550e8400-e29b-41d4-a716-446655440004'::uuid, 4, 'Good sound quality for the price.', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day', FALSE);

INSERT INTO "wishlists" (id, user_id, name, description, created_at, updated_at) VALUES
('550e8400-e29b-41d4-a716-446655441001'::uuid, '550e8400-e29b-41d4-a716-446655440002'::uuid, 'Gaming Setup', 'Items for my gaming room', NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days'),
('550e8400-e29b-41d4-a716-446655441002'::uuid, '550e8400-e29b-41d4-a716-446655440003'::uuid, 'Tech Wishlist', 'Latest technology items I want', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),
('550e8400-e29b-41d4-a716-446655441003'::uuid, '550e8400-e29b-41d4-a716-446655440004'::uuid, 'Audio Equipment', 'Sound equipment for music production', NOW(), NOW());

INSERT INTO "wishlist_items" (id, wishlist_id, product_id, created_at, updated_at) VALUES
('550e8400-e29b-41d4-a716-446655441101'::uuid, '550e8400-e29b-41d4-a716-446655441001'::uuid, '550e8400-e29b-41d4-a716-446655440505'::uuid, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days'),
('550e8400-e29b-41d4-a716-446655441102'::uuid, '550e8400-e29b-41d4-a716-446655441002'::uuid, '550e8400-e29b-41d4-a716-446655440507'::uuid, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),
('550e8400-e29b-41d4-a716-446655441103'::uuid, '550e8400-e29b-41d4-a716-446655441003'::uuid, '550e8400-e29b-41d4-a716-446655440501'::uuid, NOW(), NOW()),
('550e8400-e29b-41d4-a716-446655441104'::uuid, '550e8400-e29b-41d4-a716-446655441003'::uuid, '550e8400-e29b-41d4-a716-446655440502'::uuid, NOW(), NOW());


UPDATE users SET password = hash_password('admin') WHERE username = 'admin';
UPDATE users SET password = hash_password('john123') WHERE username = 'john_doe';
UPDATE users SET password = hash_password('jane123') WHERE username = 'jane_smith';
UPDATE users SET password = hash_password('bob123') WHERE username = 'bob_wilson';
UPDATE users SET password = hash_password('alice123') WHERE username = 'alice_brown';
