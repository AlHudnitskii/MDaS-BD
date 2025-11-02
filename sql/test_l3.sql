SELECT * FROM users WHERE is_active = TRUE;

SELECT first_name, username, email, date_joined 
FROM users 
WHERE first_name LIKE 'Jo%';

SELECT username, email, date_joined 
FROM users 
WHERE date_joined >= NOW() - INTERVAL '1 month';

SELECT name, description FROM roles;


SELECT role_id, COUNT(*) as user_count 
FROM user_roles 
GROUP BY role_id;


SELECT name, price, discount 
FROM products 
WHERE discount > 10;

SELECT name, price 
FROM products 
WHERE price > 100;

SELECT category_id, COUNT(*) as product_count 
FROM products 
GROUP BY category_id;

SELECT product_id, user_id, rating 
FROM product_reviews 
WHERE rating = 5;

SELECT product_id, ROUND(AVG(rating), 2) as avg_rating 
FROM product_reviews 
GROUP BY product_id;

SELECT action, COUNT(*) as action_count 
FROM log_entries 
GROUP BY action;