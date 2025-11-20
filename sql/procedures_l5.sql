-- 1 - Создание заказа с добавлением товаров одной транзакцией
CREATE OR REPLACE FUNCTION create_one_order_with_items(
    p_user_id UUID,
    p_first_name VARCHAR(50),
    p_last_name VARCHAR(50),
    p_email VARCHAR(254),
    p_city VARCHAR(100),
    p_address VARCHAR(250),
    p_postal_code VARCHAR(20),
    p_items JSONB 
)
RETURNS UUID 
LANGUAGE plpgsql AS $$ 
DECLARE 
    v_order_id UUID;
    v_item JSONB;
    v_product_price DECIMAL(10,2);
    v_available BOOLEAN;
    v_product_name VARCHAR(50);
    v_total_amount DECIMAL(10,2) := 0;
BEGIN
    -- Вставка заказа (включая fix: first_name, last_name, email)
    INSERT INTO orders (
        user_id, first_name, last_name, email,
        city, address, postal_code, 
        created_at, updated_at, paid
    )
    VALUES (
        p_user_id, p_first_name, p_last_name, p_email,
        p_city, p_address, p_postal_code,
        NOW(), NOW(), FALSE
    )
    RETURNING id INTO v_order_id;

    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
    LOOP 
      -- ... (логика обработки order_items) ...
      
      SELECT price, available, name 
      INTO v_product_price, v_available, v_product_name
      FROM products
      WHERE id = (v_item ->>'product_id')::UUID;

      IF NOT FOUND THEN
          RAISE EXCEPTION 'Product with ID % not found', v_item->>'product_id';
      END IF;

      IF NOT v_available THEN 
          RAISE EXCEPTION 'Product "%" is not available', v_product_name;
      END IF;

      INSERT INTO order_items (order_id, product_id, price, quantity)
      VALUES (
          v_order_id,
          (v_item->>'product_id')::UUID,
          v_product_price,
          (v_item->>'quantity')::INTEGER
      );

      v_total_amount := v_total_amount + (v_product_price * (v_item->>'quantity')::INTEGER);
    END LOOP;

    RAISE NOTICE 'Order % created successfully with % items. Total: $%:',
        v_order_id, jsonb_array_length(p_items), v_total_amount;
    
    -- !!! ДОБАВЛЕН ИСПРАВЛЕНИЕ: ВОЗВРАТ ID !!!
    RETURN v_order_id; 
END;
$$;

-- 2 - Очистка старых логов
CREATE OR REPLACE PROCEDURE cleanup_old_logs(
   p_days_to_keep INTEGER DEFAULT 90
) 
LANGUAGE plpgsql AS $$
DECLARE 
   v_deleted_count INTEGER;
   v_cutoff_date TIMESTAMP WITH TIME ZONE;
BEGIN
   BEGIN;
   v_cutoff_date := NOW() - (p_days_to_keep || ' days')::INTERVAL;

   DELETE FROM log_entries
   WHERE timestamp < v_cutoff_date;

   GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

   RAISE NOTICE 'Deleted % log entries older than % days (before %)',
        v_deleted_count, p_days_to_keep, v_cutoff_date::DATE;
   COMMIT;     
END;
$$;   

-- 3 - Получение самых продаваемых товаров
CREATE OR REPLACE PROCEDURE get_top_products(
   p_limit INTEGER DEFAULT 10
)
LANGUAGE plpgsql AS $$
DECLARE
   v_product RECORD;
   v_counter INTEGER := 0;
BEGIN
   FOR v_product IN
      SELECT 
         p.id,
         p.name,
         p.price,
         p.discount,
         COUNT(DISTINCT oi.order_id) as order_count,
         SUM(oi.quantity) as total_sold,
         SUM(oi.price * oi.quantity) as revenue
      FROM products p
      LEFT JOIN order_items oi ON p.id = oi.product_id
      LEFT JOIN orders o ON oi.order_id = o.id AND o.paid = TRUE
      WHERE p.available = TRUE
      GROUP BY p.id, p.name, p.price, p.discount
      ORDER BY total_sold DESC NULLS LAST, revenue DESC NULLS LAST
      LIMIT p_limit
   LOOP
      v_counter := v_counter + 1;
         RAISE NOTICE '%. % | Price: $% | Sold: % | Revenue: $%',
            v_counter,
            v_product.name,
            v_product.price,
            COALESCE(v_product.total_sold, 0),
            ROUND(COALESCE(v_product.revenue, 0), 2);
   END LOOP;
END;
$$;

-- 4 - Обработка заказа как оплаченного
CREATE OR REPLACE PROCEDURE process_payment(
   p_order_id UUID,
   p_user_id UUID DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
   v_order_exists BOOLEAN;
   v_already_paid BOOLEAN;
   v_total_amount DECIMAL(10,2);
   v_items_count INTEGER;
BEGIN
   SELECT paid INTO v_already_paid
   FROM orders
   WHERE id = p_order_id;
    
   IF NOT FOUND THEN
      RAISE EXCEPTION 'Order with ID % not found', p_order_id;
   END IF;
    
   IF v_already_paid THEN
      RAISE EXCEPTION 'Order % is already paid', p_order_id;
   END IF;
    
   SELECT 
      SUM(price * quantity * (1 - COALESCE(p.discount, 0))),
      COUNT(*)
   INTO v_total_amount, v_items_count
   FROM order_items oi
   LEFT JOIN products p ON oi.product_id = p.id
   WHERE oi.order_id = p_order_id;
    
   IF v_items_count = 0 THEN
      RAISE EXCEPTION 'Cannot process payment for empty order %', p_order_id;
   END IF;
    
   UPDATE orders
   SET paid = TRUE, updated_at = NOW()
   WHERE id = p_order_id;
    
   RAISE NOTICE 'Payment processed for order %. Amount: $%. Items: %', 
      p_order_id, ROUND(v_total_amount, 2), v_items_count;    
END;
$$;

-- 5 - Деактивация пользователей без активности
CREATE OR REPLACE PROCEDURE deactivate_inactive_users(
   p_days_inactive INTEGER DEFAULT 365
)
LANGUAGE plpgsql AS $$
DECLARE
   v_deactivated_count INTEGER;
   v_cutoff_date TIMESTAMP WITH TIME ZONE;
BEGIN
   v_cutoff_date := NOW() - (p_days_inactive || ' days')::INTERVAL;
    
   UPDATE users
   SET is_active = FALSE
   WHERE is_active = TRUE
      AND (last_login < v_cutoff_date OR last_login IS NULL)
      AND date_joined < v_cutoff_date
      AND is_superuser = FALSE;
    
   GET DIAGNOSTICS v_deactivated_count = ROW_COUNT;
    
   INSERT INTO log_entries (action, details, status, timestamp)
   VALUES (
      'USERS_DEACTIVATED',
      jsonb_build_object(
         'count', v_deactivated_count,
         'days_inactive', p_days_inactive,
         'cutoff_date', v_cutoff_date
      ),
      'SUCCESS',
      NOW()
   );
    
   RAISE NOTICE 'Deactivated % users inactive for more than % days',
      v_deactivated_count, p_days_inactive;
END;
$$;

-- 6 - Получение всех заказов пользователя с подробностями
CREATE OR REPLACE PROCEDURE get_user_orders(
   p_user_id UUID
)
LANGUAGE plpgsql AS $$
DECLARE
   v_username VARCHAR(150);
   v_order RECORD;
   v_item RECORD;
   v_order_total DECIMAL(10,2);
BEGIN
   SELECT username INTO v_username
   FROM users
   WHERE id = p_user_id;
    
   IF NOT FOUND THEN
      RAISE EXCEPTION 'User with ID % not found', p_user_id;
   END IF;
    
   RAISE NOTICE 'Orders for user: % (ID: %)', v_username, p_user_id;
   
   FOR v_order IN
      SELECT 
         id,
         first_name,
         last_name,
         email,
         city,
         address,
         postal_code,
         created_at,
         paid
      FROM orders
      WHERE user_id = p_user_id
      ORDER BY created_at DESC
   LOOP
      RAISE NOTICE '';
      RAISE NOTICE 'Order #%', v_order.id;
      RAISE NOTICE 'Date: % | Status: %', 
         v_order.created_at::DATE, 
         CASE 
            WHEN v_order.paid THEN 'PAID' 
            ELSE 'UNPAID' 
         END;
      RAISE NOTICE 'Delivery: %, %, %', v_order.city, v_order.address, v_order.postal_code;
      RAISE NOTICE 'Items:';
        
      v_order_total := 0;
        
      FOR v_item IN
         SELECT 
            p.name,
            oi.quantity,
            oi.price,
            p.discount,
            oi.price * oi.quantity * (1 - COALESCE(p.discount, 0)) as item_total
         FROM order_items oi
         JOIN products p ON oi.product_id = p.id
         WHERE oi.order_id = v_order.id
      LOOP
         RAISE NOTICE '  - % x% @ $% (discount: %) = $%',
            v_item.name,
            v_item.quantity,
            v_item.price,
            COALESCE(ROUND(v_item.discount * 100, 0), 0),
            ROUND(v_item.item_total, 2);
         v_order_total := v_order_total + v_item.item_total;
      END LOOP;
        
      RAISE NOTICE 'Order Total: $%', ROUND(v_order_total, 2);
   END LOOP;
END;
$$;