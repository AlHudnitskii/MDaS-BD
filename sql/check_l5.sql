-- Проверка триггеров обновления updated_at в таблицах products, orders, user_notes и product_reviews
BEGIN;

SELECT updated_at AS old_updated_at FROM products WHERE id = '550e8400-e29b-41d4-a716-446655440501'::uuid;
SELECT updated_at AS old_updated_at FROM orders WHERE id = '550e8400-e29b-41d4-a716-446655440701'::uuid;
SELECT updated_at AS old_updated_at FROM user_notes WHERE id = '550e8400-e29b-41d4-a716-446655440301'::uuid;
SELECT updated_at AS old_updated_at FROM product_reviews WHERE id = '550e8400-e29b-41d4-a716-446655440901'::uuid;

UPDATE products SET description = 'Updated description' WHERE id = '550e8400-e29b-41d4-a716-446655440501'::uuid;
SELECT id, updated_at AS new_updated_at FROM products WHERE id = '550e8400-e29b-41d4-a716-446655440501'::uuid;

UPDATE orders SET address = 'New Address' WHERE id = '550e8400-e29b-41d4-a716-446655440701'::uuid;
SELECT id, updated_at AS new_updated_at FROM orders WHERE id = '550e8400-e29b-41d4-a716-446655440701'::uuid;

UPDATE user_notes SET content = 'Updated note content' WHERE id = '550e8400-e29b-41d4-a716-446655440301'::uuid;
SELECT id, updated_at AS new_updated_at FROM user_notes WHERE id = '550e8400-e29b-41d4-a716-446655440301'::uuid;

UPDATE product_reviews SET comment = 'Updated review comment' WHERE id = '550e8400-e29b-41d4-a716-446655440901'::uuid;
SELECT id, updated_at AS new_updated_at FROM product_reviews WHERE id = '550e8400-e29b-41d4-a716-446655440901'::uuid;

ROLLBACK;

-- Проверка триггеров логирования изменений цен и скидок в таблице products
BEGIN;
UPDATE products SET price = 350.00 WHERE id = '550e8400-e29b-41d4-a716-446655440501'::uuid;
SELECT * FROM log_entries WHERE action = 'PRICE_CHANGED' ORDER BY timestamp DESC LIMIT 1;

UPDATE products SET discount = 0.15 WHERE id = '550e8400-e29b-41d4-a716-446655440502'::uuid;
SELECT * FROM log_entries WHERE action = 'PRICE_CHANGED' ORDER BY timestamp DESC LIMIT 1;

UPDATE products SET discount = 0.60 WHERE id = '550e8400-e29b-41d4-a716-446655440503'::uuid;
SELECT * FROM log_entries WHERE action = 'HIGH_DISCOUNT_ALERT' ORDER BY timestamp DESC LIMIT 1;

DO $$
BEGIN
   UPDATE products SET discount = 1.1 WHERE id = '550e8400-e29b-41d4-a716-446655440504'::uuid;
EXCEPTION WHEN others THEN
   RAISE NOTICE 'ОШИБКА: %', SQLERRM;
END
$$;

UPDATE products SET description = 'Only description change' WHERE id = '550e8400-e29b-41d4-a716-446655440505'::uuid;
SELECT * FROM log_entries WHERE action = 'PRICE_CHANGED' AND details->>'product_id' = '550e8400-e29b-41d4-a716-446655440505' LIMIT 1;

ROLLBACK;

-- Проверка процедуры очистки старых записей в log_entries
BEGIN;

INSERT INTO log_entries (id, action, status, timestamp) VALUES
('550e8400-e29b-41d4-a716-446655449901'::uuid, 'OLD_LOG_1', 'SUCCESS', NOW() - INTERVAL '101 days'),
('550e8400-e29b-41d4-a716-446655449902'::uuid, 'OLD_LOG_2', 'SUCCESS', NOW() - INTERVAL '101 days');

SELECT count(*) AS pre_cleanup_count FROM log_entries WHERE action LIKE 'OLD_LOG%';
CALL cleanup_old_logs(100);

SELECT count(*) AS post_cleanup_count FROM log_entries WHERE action LIKE 'OLD_LOG%';

ROLLBACK;

-- Проверка процедуры получения топ N продуктов по количеству заказов
BEGIN;

CALL get_top_products(5);
CALL get_top_products(1);

ROLLBACK;

-- Проверка процедуры обработки оплаты заказа
BEGIN;

CALL process_payment('550e8400-e29b-41d4-a716-446655440703'::uuid);
SELECT paid, updated_at > created_at AS updated FROM orders WHERE id = '550e8400-e29b-41d4-a716-446655440703'::uuid;

DO $$
BEGIN
    CALL process_payment('550e8400-e29b-41d4-a716-446655440703'::uuid);
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'ОШИБКА ОБРАБОТАНА: %', SQLERRM;
END
$$;

DO $$
BEGIN
    CALL process_payment('00000000-0000-0000-0000-000000000000'::uuid);
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'ОШИБКА ОБРАБОТАНА: %', SQLERRM;
END
$$;

ROLLBACK;

-- Получение всех заказов пользователя
BEGIN;
CALL get_user_orders('550e8400-e29b-41d4-a716-446655440001'::uuid);
ROLLBACK;