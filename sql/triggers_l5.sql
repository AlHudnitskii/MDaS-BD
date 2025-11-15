#1 - Автоматическое изменение поля updated_at при изменении записи
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_products_update_timestamp
   BEFORE UPDATE ON products
   FOR EACH ROW 
   EXECUTE FUNCTION update_timestamp();

ALTER TRIGGER trg_products_update_timestamp
ON products RENAME TO trg_products_update_timestamp_new_name;

ALTER TABLE products DISABLE TRIGGER trg_products_update_timestamp;

ALTER TABLE products ENABLE TRIGGER trg_products_update_timestamp;

DROP TRIGGER trg_products_update_timestamp ON products;

SELECT event_object_table, trigger_name FROM information_schema.triggers;

CREATE TRIGGER trg_orders_update_timestamp
   BEFORE UPDATE ON orders
   FOR EACH ROW
   EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_user_notes_update_timestamp
   BEFORE UPDATE ON user_notes
   FOR EACH ROW
   EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_product_reviews_update_timestamp
   BEFORE UPDATE ON product_reviews
   FOR EACH ROW
   EXECUTE FUNCTION update_timestamp();

# 2 - Запись в log_entries все изменения цен и скидок
CREATE OR REPLACE FUNCTION log_price_changes()
RETURNS TRIGGER AS $$
BEGIN 
   IF (OLD.price != NEW.price OR OLD.discount != NEW.discount) THEN
      INSERT INTO log_entries (action, details, status, timestamp)
      VALUES (
         'PRICE_CHANGED',
         jsonb_build_object(
            'product_id', NEW.id,
            'product_name', NEW.name,
            'old_price', OLD.price,
            'new_price', NEW.price,
            'old_discount', OLD.discount,
            'new_discount', NEW.discount,
            'price_change', NEW.price - OLD.price,
            'discount_change', NEW.discount - OLD.discount
         ),
         'SUCCESS',
         NOW()
      );
   END IF;
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_product_price_changes
   AFTER UPDATE ON products
   FOR EACH ROW 
   EXECUTE FUNCTION log_price_changes();

#3 - Проверка доступности товара с available = FALSE
CREATE OR REPLACE FUNCTION check_product_availability()
RETURNS TRIGGER AS $$
DECLARE
   v_available BOOLEAN;
   v_product_name VARCHAR(50);
BEGIN
   SELECT available, name 
   INTO v_available, v_product_name
   FROM products
   WHERE id = NEW.product_id;

   IF NOT FOUND THEN 
      RAISE EXCEPTION 'Product with ID % does not exist', NEW.product_id;
   END IF;

   IF NOT v_available THEN 
      RAISE EXCEPTION 'Product "%" (ID: %) is not available for purchase',
         v_product_name, NEW.product_id;
   END IF;

   RETURN NEW;         
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_product_availability
   BEFORE INSERT ON order_items
   FOR EACH ROW 
   EXECUTE FUNCTION check_product_availability();

#4 - Проверка корректности скидки и логирование больших скидок (> 50%)
CREATE OR REPLACE FUNCTION validate_discount()
RETURNS TRIGGER AS $$
BEGIN
   IF NEW.discount < 0 OR NEW.discount > 1 THEN 
      RAISE EXCEPTION 'Discount must be between 0 and 1, got: %',
         NEW.discount;
   END IF;

   IF NEW.discount > 0.5 THEN 
      INSERT INTO log_entries (action, details, status, timestamp)
      VALUES (
         'HIGH_DISCOUNT_ALERT',
         jsonb_build_object(
            'product_id', NEW.id,
            'product_name', NEW.name,
            'discount', NEW.discount,
            'discount_percent', (NEW.discount * 100)
         ),
         'WARNING',
         NOW()

      );
   END IF;    

   RETURN NEW;     
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_product_discount
   BEFORE INSERT OR UPDATE ON products
   FOR EACH ROW
   EXECUTE FUNCTION validate_discount(); 

#5 - Логирует каждое добавление товара в заказ
CREATE OR REPLACE FUNCTION log_order_item_added()
RETURNS TRIGGER AS $$
DECLARE 
   v_product_name VARCHAR(50);
BEGIN 
   SELECT name INTO v_product_name
   FROM products
   WHERE id = NEW.product_id;

   INSERT INTO log_entries (action, details, status, timestamp)
   VALUES (
      'ORDER_ITEM_ADDED',
         jsonb_build_object(
            'order_id', NEW.order_id,
            'product_id', NEW.product_id,
            'product_name', v_product_name,
            'quantity', NEW.quantity,
            'price', NEW.price,
            'total', NEW.price * NEW.quantity
        ),
        'SUCCESS',
        NOW()
   );   
   
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;   

CREATE TRIGGER trg_log_order_item_added 
   AFTER INSERT ON order_items
   FOR EACH ROW 
   EXECUTE FUNCTION log_order_item_added();

#6 - Запрет на удаление закаков со статусом paid = TRUE   
CREATE OR REPLACE FUNCTION prevent_paid_order_deletion()
RETURNS TRIGGER AS $$
BEGIN
   IF OLD.paid = TRUE THEN
      RAISE EXCEPTION 'Cannot delete paid order (ID: %)', OLD.id;
   END IF;
   RETURN OLD;   
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_paid_order_deletion
   BEFORE DELETE ON orders 
   FOR EACH ROW
   EXECUTE FUNCTION prevent_paid_order_deletion();  

#7 - Логирование создания каждого нового заказа
CREATE OR REPLACE FUNCTION log_order_created()
RETURNS TRIGGER AS $$
BEGIN
   INSERT INTO log_entries (user_id, action, details, status, timestamp)
   VALUES (
      NEW.user_id,
      'ORDER_CREATED',
      jsonb_build_object(
         'order_id', NEW.id,
         'email', NEW.email,
         'city', NEW.city,
         'paid', NEW.paid
      ),
      'SUCCESS',
      NOW()
   );
    
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_order_created
   AFTER INSERT ON orders
   FOR EACH ROW
   EXECUTE FUNCTION log_order_created();
   
#8 - Логирование заказа в случае его оплаты
CREATE OR REPLACE FUNCTION log_payment_status_change()
RETURNS TRIGGER AS $$
BEGIN 
   IF OLD.paid != NEW.paid THEN
      INSERT INTO log_entries (user_id, action, details, status, timestamp)
      VALUES (
         NEW.user_id,
         CASE
            WHEN NEW.paid THEN 'ORDER_PAID'
            ELSE 'ORDER_UNPAID'
         END,
         jsonb_build_object(
            'order_id', NEW.id,
            'old_status', OLD.paid,
            'new_status', NEW.paid
         ),
         'SUCCESS',
         NOW() 
      );
   END IF; 
   RETURN NEW;  
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_payment_status
   AFTER UPDATE ON orders 
   FOR EACH ROW 
   EXECUTE FUNCTION log_payment_status_change();

#9 - Автоматическая установка created_at и updated_at
CREATE OR REPLACE FUNCTION set_timestamps()
RETURNS TRIGGER AS $$
BEGIN
   NEW.created_at = NOW();
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;   

CREATE TRIGGER trg_orders_set_timestamps
   BEFORE INSERT ON orders
   FOR EACH ROW
   EXECUTE FUNCTION set_timestamps();

CREATE TRIGGER trg_product_reviews_set_timestamps
   BEFORE INSERT ON product_reviews
   FOR EACH ROW
   EXECUTE FUNCTION set_timestamps();