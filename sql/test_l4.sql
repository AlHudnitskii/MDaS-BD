-- Active: 1760707665025@@127.0.0.1@5432@bdshop
#1a - Запрос с несколькими условиями

SELECT DISTINCT
   u.id,
   u.username,
   u.email,
   u.first_name,
   u.last_name,
   r.name AS role_name
FROM users AS u
INNER JOIN user_roles AS ur ON u.id = ur.user_id
INNER JOIN roles AS r ON ur.role_id = r.id
INNER JOIN orders AS o ON u.id = o.user_id
WHERE u.is_active = TRUE
   AND r.name = 'Premium Customer'
   AND o.paid = TRUE
   AND o.created_at >= CURRENT_DATE - INTERVAL '30 days';

#1b - Запрос с вложенной конструкцией (подзапрос)

SELECT 
   p.id,
   p.name,
   c.name AS category_name,
   p.price,
   p.discount,
   ROUND(p.price * (1 - p.discount), 2),
   ROUND((SELECT AVG(price)
      FROM products
      WHERE category_id = p.category_id), 2) AS avg_category_price
FROM products AS p
INNER JOIN categories AS c ON p.category_id = c.id
WHERE price > (
   SELECT AVG(price)
   FROM products p2
   WHERE p2.category_id = p.category_id
)   
ORDER BY c.name ASC, p.price DESC; 

#1c - Детальная информация о продуктах и пользователях

SELECT 
   o.id AS order_id,
   o.created_at AS order_date,
   u.username,
   u.email,
   o.city,
   o.address,
   p.name AS product_name,
   c.name AS category_name,
   oi.quantity,
   oi.price AS item_price,
   (oi.price * oi.quantity) AS item_total,
   CASE 
      WHEN o.paid = TRUE THEN 'Paid'
      ELSE 'Not paid'
   END AS payment_status
FROM orders as o 
LEFT JOIN users AS u ON o.user_id = u.id
INNER JOIN order_items AS oi ON o.id = oi.order_id
INNER JOIN products AS p ON oi.product_id = p.id
INNER JOIN categories AS c ON p.category_id = c.id
WHERE o.created_at >= CURRENT_DATE - INTERVAL '1 month'
ORDER BY o.created_at DESC, o.id ASC;        

--- Продукты в определенном ценовом диапозоне и с определенными словами в названии

SELECT 
   p.id,
   p.name,
   c.name AS category,
   p.price,
   p.discount,
   (p.price * (1 - p.discount)) AS final_price,
   p.description
FROM products AS p
INNER JOIN categories AS c ON p.category_id = c.id
WHERE (price BETWEEN 50 AND 300)
   AND (p.name ILIKE '%gaming%' OR p.description ILIKE '%gaming%')
   AND p.discount > 0
ORDER BY final_price DESC;   

#2a - INNER JOIN - Все продукты с их категориями

SELECT 
   p.id,
   p.name AS product_name,
   c.name AS category_name,
   p.price,
   p.discount,
   ROUND((p.price * (1 - p.discount)), 2) as final_price
FROM products AS p
INNER JOIN categories AS c ON p.category_id = c.id
ORDER BY c.name ASC, p.name ASC 
LIMIT 5

#2b - LEFT OUTER JOIN -- Пользователи, что НЕ оставляли отзывы

SELECT 
   u.id,
   u.username,
   u.email,
   u.date_joined,
   COUNT(o.id) as orders_count
FROM users u
LEFT JOIN product_reviews pr ON u.id = pr.user_id
LEFT JOIN orders o ON u.id = o.user_id
WHERE pr.id IS NULL  
GROUP BY u.id, u.username, u.email, u.date_joined
ORDER BY orders_count DESC;

#2с - FULL OUTER JOIN - Все пользователи и все их роли

SELECT 
   u.id AS user_id,
   u.username,
   u.email,
   r.id AS role_id,
   r.name AS role_name,
   CASE 
      WHEN u.id IS NULL THEN 'Role is not assigned'
      WHEN r.id IS NULL THEN 'User without role'
      ELSE 'Active assignment'
   END AS status
FROM users AS u 
FULL OUTER JOIN user_roles AS ur ON u.id = ur.user_id
FULL OUTER JOIN roles AS r ON ur.role_id = r.id
ORDER BY u.username

#2d - CROSS JOIN - Комбанация пользователей и категорий 

SELECT  
   u.id as user_id,
   u.username,
   c.id as category_id,
   c.name as category_name
FROM users AS u
CROSS JOIN categories AS c 
WHERE u.is_active = TRUE
ORDER BY u.username ASC

#2e - SELF JOIN - Пользователи с несколькими ролями

SELECT 
   u.username,
   u.email,
   r1.name as role1,
   r2.name as role2,
   ur1.assigned_at as role1_assigned,
   ur2.assigned_at as role2_assigned
FROM user_roles ur1
INNER JOIN user_roles ur2 ON ur1.user_id = ur2.user_id AND ur1.role_id < ur2.role_id
INNER JOIN users u ON ur1.user_id = u.id
INNER JOIN roles r1 ON ur1.role_id = r1.id
INNER JOIN roles r2 ON ur2.role_id = r2.id
ORDER BY u.username;

#3a - GROUP BY - Количество пользователей по ролям

SELECT 
    r.name as role_name,
    COUNT(ur.user_id) as user_count
FROM user_roles ur
JOIN roles r ON ur.role_id = r.id
GROUP BY r.name
ORDER BY user_count DESC;

#3b - PARTITION - Скользящие средние цены продуктов по категориям

SELECT 
   name,
   category_id,
   price,
   ROUND(AVG(price) OVER (PARTITION BY category_id ORDER BY created_at), 2) as moving_avg_price,
   ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY price DESC) as price_rank
FROM products

#3c - HAVING - Категории с дорогими продуктами

SELECT 
   c.name AS category_name,
   ROUND(AVG(p.price), 2) AS avg_price
FROM categories AS c 
INNER JOIN products AS p ON p.category_id = c.id
GROUP BY c.id, c.name 
HAVING AVG(p.price) > 100

#3d - UNION - Заказы + отзывы

SELECT 
   u.id AS user_id,
   u.username,
   'order' AS activity_type,
   o.created_at AS activity_date,
   CONCAT('Order #', o.id) AS description
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.created_at >= NOW() - INTERVAL '30 days'

UNION

SELECT 
   u.id AS user_id,
   u.username,
   'review' AS activity_type,
   pr.created_at AS activity_date,
   CONCAT('Review for product #', pr.product_id) AS description
FROM users u
INNER JOIN product_reviews pr ON u.id = pr.user_id
WHERE pr.created_at >= NOW() - INTERVAL '30 days'

ORDER BY activity_date DESC;

#4a - EXISTS - Пользователи с оплаченными товарами

SELECT 
   u.id,
   u.username
FROM users AS u
WHERE EXISTS (
   SELECT 1
   FROM orders AS o
   WHERE o.user_id = u.id
      AND o.paid = TRUE
)
ORDER BY u.username;

#4b - INSERT INTO SELECT - Как пример, что пришел в голову - такой таблицы нет, но пример показательный 

INSERT INTO orders_archive (
   id, user_id, first_name, last_name, email, 
   city, address, postal_code, created_at, updated_at, paid, archive_reason
)
SELECT 
   id, user_id, first_name, last_name, email,
   city, address, postal_code, created_at, updated_at, paid,
   'Заказ старше 6 месяцев'
FROM orders
WHERE created_at < CURRENT_DATE - INTERVAL '6 months'
   AND paid = TRUE
   AND NOT EXISTS (
      SELECT 1 FROM orders_archive WHERE orders_archive.id = orders.id
  );

#4c - CASE - Все пользователи и все их роли

SELECT 
   u.id AS user_id,
   u.username,
   u.email,
   r.id AS role_id,
   r.name AS role_name,
   CASE 
      WHEN u.id IS NULL THEN 'Role is not assigned'
      WHEN r.id IS NULL THEN 'User without role'
      ELSE 'Active assignment'
   END AS status
FROM users AS u 
FULL OUTER JOIN user_roles AS ur ON u.id = ur.user_id
FULL OUTER JOIN roles AS r ON ur.role_id = r.id
ORDER BY u.username

#4d - EXPLAIN

EXPLAIN (ANALYZE, BUFFERS)
SELECT 
    r.name as role_name,
    COUNT(ur.user_id) as user_count
FROM user_roles ur
JOIN roles r ON ur.role_id = r.id
GROUP BY r.name
ORDER BY user_count DESC;