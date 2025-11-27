import json
import time

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .sql_manager import (
    SQLManager,
    ProductRepository,
    StatisticsRepository
)


@require_http_methods(["GET"])
def api_products_list(request):
    start_time = time.time()
    
    try:
        category_slug = request.GET.get('category')
        sort_by = request.GET.get('sort', 'name')
        limit = int(request.GET.get('limit', 50))
        
        products = ProductRepository.get_all_products(category_slug, sort_by)        
        products = products[:limit]
        
        execution_time = time.time() - start_time
        
        return JsonResponse({
            'success': True,
            'count': len(products),
            'products': products,
            'execution_time_ms': round(execution_time * 1000, 2)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_statistics(request):
    start_time = time.time()
    
    try:
        stats = StatisticsRepository.get_sales_statistics()
        top_products = ProductRepository.get_top_products(10)
        
        execution_time = time.time() - start_time
        
        return JsonResponse({
            'success': True,
            'sales': stats,
            'top_products': top_products,
            'execution_time_ms': round(execution_time * 1000, 2)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        
        
@require_http_methods(["GET"])
def api_health(request):
    start_time = time.time()
    
    try:
        with SQLManager() as db:
            db.cursor.execute("SELECT 1")
            db.cursor.fetchone()
        
        execution_time = time.time() - start_time
        
        return JsonResponse({
            'success': True,
            'status': 'healthy',
            'database': 'connected',
            'execution_time_ms': round(execution_time * 1000, 2)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_create_order(request):
    start_time = time.time()
    
    try:
        data = json.loads(request.body)
        
        user_id = data['user_id']
        first_name = data['first_name']
        last_name = data['last_name']
        email = data['email']
        city = data['city']
        address = data['address']
        postal_code = data['postal_code']
        items = data['items']
        apply_discount = data.get('apply_discount', False)
        
        with SQLManager() as db:
            items_json = json.dumps(items)
            
            db.cursor.execute("""
                SELECT create_one_order_with_items(
                    %s::uuid, %s, %s, %s, %s, %s, %s, %s::jsonb
                )
            """, (user_id, first_name, last_name, email, city, address, postal_code, items_json))
            
            db.connection.commit()
            
            db.cursor.execute("""
                SELECT id FROM orders 
                WHERE user_id = %s::uuid 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (user_id,))
            result = db.cursor.fetchone()
            order_id = str(result['id']) if result else None
            
            if apply_discount and order_id:
                savepoint = db.begin_nested()  
                
                try:
                    db.cursor.execute("""
                        UPDATE order_items
                        SET price = price * 0.9
                        WHERE order_id = %s::uuid
                    """, (order_id,))
                    
                    db.cursor.execute("""
                        SELECT SUM(price * quantity) as total
                        FROM order_items
                        WHERE order_id = %s::uuid
                    """, (order_id,))
                    new_total = db.cursor.fetchone()['total']
                    
                    if new_total < 10:  
                        db.rollback_to(savepoint)
                        discount_applied = False
                        discount_message = "Discount rejected: order total too low"
                    else:
                        db.release_savepoint(savepoint)
                        db.connection.commit()
                        discount_applied = True
                        discount_message = "10% discount applied"
                
                except Exception as e:
                    db.rollback_to(savepoint)
                    discount_applied = False
                    discount_message = f"Discount failed: {str(e)}"
            else:
                discount_applied = False
                discount_message = "No discount requested"
        
        execution_time = time.time() - start_time
        
        return JsonResponse({
            'success': True,
            'order_id': order_id,
            'discount_applied': discount_applied,
            'discount_message': discount_message,
            'execution_time_ms': round(execution_time * 1000, 2)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)