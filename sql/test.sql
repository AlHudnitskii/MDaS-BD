SELECT id, username, first_name, last_name, email, timezone
FROM "users" 
WHERE is_active = TRUE
ORDER BY date_joined DESC;



SELECT p.name as product_name, p.price, c.name as category_name
FROM "products" p
JOIN "categories" c ON p.category_id = c.id
ORDER BY c.name, p.name;

SELECT 
    name, 
    price, 
    discount, 
    ROUND(price * (1 - discount), 2) as final_price
FROM "products" 
WHERE discount > 0
ORDER BY discount DESC;

SELECT 
    c.name as category_name, 
    COUNT(p.id) as products_count
FROM "categories" c
LEFT JOIN "products" p ON c.id = p.category_id
GROUP BY c.id, c.name
ORDER BY products_count DESC;

SELECT 
    p.name, 
    AVG(pr.rating)::DECIMAL(3,2) as avg_rating, 
    COUNT(pr.id) as reviews_count
FROM "products" p
LEFT JOIN "product_reviews" pr ON p.id = pr.product_id
GROUP BY p.id, p.name
HAVING COUNT(pr.id) > 0
ORDER BY avg_rating DESC;

SELECT 
    p.name, 
    COUNT(oi.id) as times_ordered, 
    SUM(oi.quantity) as total_quantity
FROM "products" p
JOIN "order_items" oi ON p.id = oi.product_id
JOIN "orders" o ON oi.order_id = o.id
WHERE o.paid = TRUE
GROUP BY p.id, p.name
ORDER BY times_ordered DESC, total_quantity DESC
LIMIT 5;

SELECT 
    ls.name as status_name,
    COUNT(le.id) as entries_count,
    COUNT(DISTINCT le.user_id) as unique_users
FROM "log_statuses" ls
LEFT JOIN "log_entries" le ON ls.id = le.status_id
GROUP BY ls.id, ls.name
ORDER BY entries_count DESC;

INSERT INTO "wishlist_items" (wishlist_id, product_id, created_at, updated_at)
SELECT 
    '550e8400-e29b-41d4-a716-446655441001'::uuid,
    '550e8400-e29b-41d4-a716-446655440505'::uuid,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM "wishlist_items" 
    WHERE wishlist_id = '550e8400-e29b-41d4-a716-446655441001'::uuid 
    AND product_id = '550e8400-e29b-41d4-a716-446655440505'::uuid
);

UPDATE "products" 
SET 
    price = price * 0.9, 
    updated_at = NOW() 
WHERE category_id = '550e8400-e29b-41d4-a716-446655440402'::uuid;

DELETE FROM "wishlist_items" 
WHERE wishlist_id = '550e8400-e29b-41d4-a716-446655441001'::uuid 
AND product_id = '550e8400-e29b-41d4-a716-446655440505'::uuid;