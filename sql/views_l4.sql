CREATE OR REPLACE VIEW v_users_with_roles AS
SELECT 
   u.id,
   u.username,
   u.email,
   u.first_name,
   u.last_name,
   u.timezone,
   u.is_active,
   u.is_superuser,
   u.date_joined,
   r.name as role_name,
   r.description as role_description,
   ur.assigned_at as role_assigned_at
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
WHERE u.is_active = TRUE;

CREATE OR REPLACE VIEW v_products_catalog AS
SELECT 
   p.id,
   p.name,
   p.slug,
   p.description,
   p.price,
   p.discount,
   ROUND(p.price * (1 - p.discount), 2) as final_price,
   c.name as category_name,
   c.slug as category_slug,
   p.created_at,
   p.updated_at
FROM products p
JOIN categories c ON p.category_id = c.id;

CREATE OR REPLACE VIEW v_orders_details AS
SELECT 
   o.id as order_id,
   o.user_id,
   u.username,
   u.email as user_email,
   o.city,
   o.address,
   o.postal_code,
   o.created_at as order_date,
   o.paid,
   COUNT(oi.id) as items_count,
   SUM(oi.price * oi.quantity) as total_amount
FROM orders o
LEFT JOIN users u ON o.user_id = u.id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, o.user_id, u.username, u.email, o.city, o.address, o.postal_code, o.created_at, o.paid;

CREATE OR REPLACE VIEW v_wishlists_full AS
SELECT 
   w.id as wishlist_id,
   w.user_id,
   u.username,
   w.name as wishlist_name,
   w.description as wishlist_description,
   wi.id as wishlist_item_id,
   p.id as product_id,
   p.name as product_name,
   p.slug as product_slug,
   p.price,
   p.discount,
   ROUND(p.price * (1 - p.discount), 2) as final_price,
   c.name as category_name,
   wi.created_at as added_to_wishlist_at
FROM wishlists w
JOIN users u ON w.user_id = u.id
LEFT JOIN wishlist_items wi ON w.id = wi.wishlist_id
LEFT JOIN products p ON wi.product_id = p.id
LEFT JOIN categories c ON p.category_id = c.id;

CREATE OR REPLACE VIEW v_log_entries_full AS
SELECT 
   le.id,
   le.user_id,
   u.username,
   u.email as user_email,
   le.action,
   le.details,
   ls.code as status_code,
   ls.name as status_name,
   le.created_at
FROM log_entries le
LEFT JOIN users u ON le.user_id = u.id
LEFT JOIN log_statuses ls ON le.status_id = ls.id;