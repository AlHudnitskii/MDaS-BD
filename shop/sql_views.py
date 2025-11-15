"""
Views для работы с БД через чистый SQL
Все запросы выполняются через SQLManager
"""
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import check_password, make_password

from .sql_manager import (
    UserRepository,
    ProductRepository,
    CategoryRepository,
    OrderRepository,
    StatisticsRepository,
    LogRepository
)

logger = logging.getLogger(__name__)


# ============= АУТЕНТИФИКАЦИЯ =============

def login_view(request):
    """Вход пользователя через SQL"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            # Получаем пользователя через SQL
            user_data = UserRepository.get_user_by_username(username)
            
            if user_data and check_password(password, user_data['password']):
                # Сохраняем данные в сессии
                request.session['user_id'] = str(user_data['id'])
                request.session['username'] = user_data['username']
                request.session['is_authenticated'] = True
                
                # Логируем вход
                LogRepository.log_action(
                    str(user_data['id']),
                    'USER_LOGIN',
                    {'ip': request.META.get('REMOTE_ADDR'), 'username': username},
                    'SUCCESS'
                )
                
                logger.info(f"User {username} logged in successfully")
                messages.success(request, f'Welcome, {username}!')
                return redirect('product_list')
            else:
                messages.error(request, 'Invalid username or password')
                logger.warning(f"Failed login attempt for username: {username}")
        except Exception as e:
            logger.error(f"Login error: {e}")
            messages.error(request, 'An error occurred during login')
    
    return render(request, 'users/login.html')


def register_view(request):
    """Регистрация пользователя через SQL"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'users/registration.html')
        
        try:
            # Создаем пользователя через SQL
            user_data = UserRepository.create_user(
                username, email, password, first_name, last_name
            )
            
            if user_data:
                # Автоматический вход
                request.session['user_id'] = str(user_data['id'])
                request.session['username'] = user_data['username']
                request.session['is_authenticated'] = True
                
                # Логируем регистрацию
                LogRepository.log_action(
                    str(user_data['id']),
                    'USER_REGISTER',
                    {'username': username, 'email': email},
                    'SUCCESS'
                )
                
                logger.info(f"New user registered: {username}")
                messages.success(request, 'Registration successful!')
                return redirect('product_list')
        except Exception as e:
            logger.error(f"Registration error: {e}")
            messages.error(request, f'Registration failed: {str(e)}')
    
    return render(request, 'users/registration.html')


def logout_view(request):
    """Выход пользователя"""
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    
    if user_id:
        try:
            LogRepository.log_action(
                user_id,
                'USER_LOGOUT',
                {'username': username},
                'SUCCESS'
            )
        except Exception as e:
            logger.error(f"Logout logging error: {e}")
    
    request.session.flush()
    messages.success(request, 'You have been logged out')
    return redirect('product_list')


# ============= ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ =============

@login_required
def profile_view(request):
    """Профиль пользователя с использованием SQL"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    try:
        # Получаем данные пользователя
        user_data = UserRepository.get_user_by_username(request.session.get('username'))
        
        # Получаем заказы пользователя
        orders = OrderRepository.get_user_orders(user_id)
        
        if request.method == 'POST':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            
            # Обновляем профиль через SQL
            UserRepository.update_user_profile(user_id, first_name, last_name, email)
            
            LogRepository.log_action(
                user_id,
                'PROFILE_UPDATE',
                {'fields_updated': ['first_name', 'last_name', 'email']},
                'SUCCESS'
            )
            
            messages.success(request, 'Profile updated successfully')
            return redirect('profile')
        
        context = {
            'user': user_data,
            'orders': orders
        }
        
        return render(request, 'users/profile.html', context)
    
    except Exception as e:
        logger.error(f"Profile view error: {e}")
        messages.error(request, 'Error loading profile')
        return redirect('product_list')


# ============= КАТАЛОГ ТОВАРОВ =============

def product_list_view(request, category_slug=None):
    """Список товаров через SQL"""
    try:
        sort_by = request.GET.get('sort', 'name')
        search_query = request.GET.get('q')
        
        # Получаем категории
        categories = CategoryRepository.get_all_categories()
        current_category = None
        
        if category_slug:
            current_category = CategoryRepository.get_category_by_slug(category_slug)
        
        # Получаем товары
        if search_query:
            products = ProductRepository.search_products(search_query)
            logger.info(f"Search query: '{search_query}', found {len(products)} products")
        else:
            products = ProductRepository.get_all_products(category_slug, sort_by)
        
        context = {
            'products': products,
            'categories': categories,
            'category': current_category,
            'sort_by': sort_by,
            'query': search_query
        }
        
        return render(request, 'main/product/list.html', context)
    
    except Exception as e:
        logger.error(f"Product list error: {e}")
        messages.error(request, 'Error loading products')
        return render(request, 'main/product/list.html', {'products': [], 'categories': []})


def product_detail_view(request, slug):
    """Детали товара через SQL"""
    try:
        product = ProductRepository.get_product_by_slug(slug)
        
        if not product:
            messages.error(request, 'Product not found')
            return redirect('product_list')
        
        context = {'product': product}
        return render(request, 'main/product/detail.html', context)
    
    except Exception as e:
        logger.error(f"Product detail error: {e}")
        messages.error(request, 'Error loading product')
        return redirect('product_list')


# ============= КОРЗИНА =============

def cart_detail_view(request):
    """Просмотр корзины"""
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    
    try:
        for product_id, item_data in cart.items():
            # Получаем актуальные данные товара из БД
            product = ProductRepository.get_product_by_slug(item_data.get('slug'))
            if product:
                quantity = item_data.get('quantity', 1)
                item_total = float(product['final_price']) * quantity
                total_price += item_total
                
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'total': item_total
                })
        
        context = {
            'cart_items': cart_items,
            'total_price': total_price
        }
        
        return render(request, 'cart/detail.html', context)
    
    except Exception as e:
        logger.error(f"Cart view error: {e}")
        messages.error(request, 'Error loading cart')
        return render(request, 'cart/detail.html', {'cart_items': [], 'total_price': 0})


@require_http_methods(["POST"])
def cart_add_view(request, product_id):
    """Добавление товара в корзину"""
    try:
        # Получаем товар из БД через SQL
        product = ProductRepository.get_product_by_slug(request.POST.get('slug'))
        
        if not product:
            messages.error(request, 'Product not found')
            return redirect('product_list')
        
        cart = request.session.get('cart', {})
        quantity = int(request.POST.get('quantity', 1))
        
        # Добавляем/обновляем товар в корзине
        if product_id in cart:
            cart[product_id]['quantity'] += quantity
        else:
            cart[product_id] = {
                'slug': product['slug'],
                'name': product['name'],
                'price': float(product['final_price']),
                'quantity': quantity
            }
        
        request.session['cart'] = cart
        request.session.modified = True
        
        messages.success(request, f"{product['name']} added to cart")
        logger.info(f"Product {product['name']} added to cart")
        
        return redirect('cart_detail')
    
    except Exception as e:
        logger.error(f"Cart add error: {e}")
        messages.error(request, 'Error adding to cart')
        return redirect('product_list')


@require_http_methods(["POST"])
def cart_remove_view(request, product_id):
    """Удаление товара из корзины"""
    cart = request.session.get('cart', {})
    
    if product_id in cart:
        del cart[product_id]
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, 'Item removed from cart')
    
    return redirect('cart_detail')


# ============= ОФОРМЛЕНИЕ ЗАКАЗА =============

def order_create_view(request):
    """Создание заказа через SQL (с использованием процедуры из ЛР5)"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.warning(request, 'Please login to create an order')
        return redirect('login')
    
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.warning(request, 'Your cart is empty')
        return redirect('cart_detail')
    
    if request.method == 'POST':
        try:
            # Получаем данные формы
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            city = request.POST.get('city')
            address = request.POST.get('address')
            postal_code = request.POST.get('postal_code')
            
            # Подготавливаем товары для процедуры
            items = []
            for product_id, item_data in cart.items():
                items.append({
                    'product_id': product_id,
                    'quantity': item_data['quantity']
                })
            
            # Создаем заказ через процедуру SQL
            order_id = OrderRepository.create_order_with_items(
                user_id, first_name, last_name, email,
                city, address, postal_code, items
            )
            
            if order_id:
                # Очищаем корзину
                request.session['cart'] = {}
                request.session.modified = True
                
                # Логируем создание заказа
                LogRepository.log_action(
                    user_id,
                    'ORDER_CREATED',
                    {'order_id': order_id, 'items_count': len(items)},
                    'SUCCESS'
                )
                
                logger.info(f"Order {order_id} created successfully")
                messages.success(request, f'Order #{order_id} created successfully!')
                return redirect('order_success', order_id=order_id)
            else:
                messages.error(request, 'Failed to create order')
        
        except Exception as e:
            logger.error(f"Order creation error: {e}")
            messages.error(request, f'Error creating order: {str(e)}')
    
    # Рассчитываем итоговую сумму
    total_price = sum(item['price'] * item['quantity'] for item in cart.values())
    
    context = {
        'cart': cart,
        'total_price': total_price
    }
    
    return render(request, 'orders/order/create.html', context)


def order_success_view(request, order_id):
    """Страница успешного создания заказа"""
    try:
        order = OrderRepository.get_order_details(order_id)
        context = {'order': order}
        return render(request, 'orders/order/created.html', context)
    except Exception as e:
        logger.error(f"Order success view error: {e}")
        messages.error(request, 'Order not found')
        return redirect('product_list')


# ============= СТАТИСТИКА =============

def statistics_view(request):
    """Статистика продаж через SQL (из ЛР4)"""
    try:
        # Получаем общую статистику
        stats = StatisticsRepository.get_sales_statistics()
        
        # Получаем топ товары
        top_products = ProductRepository.get_top_products(5)
        
        # Получаем статистику по категориям
        category_stats = StatisticsRepository.get_category_statistics()
        
        context = {
            'total_sales': stats['total_sales'],
            'total_orders': stats['total_orders'],
            'avg_order': stats['avg_order'],
            'top_products': top_products,
            'category_stats': category_stats
        }
        
        return render(request, 'main/info/statistics.html', context)
    
    except Exception as e:
        logger.error(f"Statistics view error: {e}")
        messages.error(request, 'Error loading statistics')
        return render(request, 'main/info/statistics.html', {})


# ============= ИНФОРМАЦИОННЫЕ СТРАНИЦЫ =============

def about_view(request):
    """Страница 'О нас'"""
    return render(request, 'main/info/about.html')


def contacts_view(request):
    """Страница контактов"""
    return render(request, 'main/info/contacts.html')


# ============= АДМИНИСТРАТИВНЫЕ ФУНКЦИИ =============

@login_required
def cleanup_logs_view(request):
    """Очистка старых логов (процедура из ЛР5)"""
    user_id = request.session.get('user_id')
    
    if request.method == 'POST':
        days = int(request.POST.get('days', 90))
        
        try:
            LogRepository.cleanup_old_logs(days)
            
            LogRepository.log_action(
                user_id,
                'LOGS_CLEANUP',
                {'days': days},
                'SUCCESS'
            )
            
            messages.success(request, f'Logs older than {days} days have been cleaned up')
        except Exception as e:
            logger.error(f"Log cleanup error: {e}")
            messages.error(request, 'Error cleaning up logs')
    
    return redirect('profile')


@login_required
def process_payment_view(request, order_id):
    """Обработка оплаты заказа (процедура из ЛР5)"""
    user_id = request.session.get('user_id')
    
    try:
        OrderRepository.process_payment(order_id)
        
        LogRepository.log_action(
            user_id,
            'ORDER_PAID',
            {'order_id': order_id},
            'SUCCESS'
        )
        
        messages.success(request, f'Payment processed for order #{order_id}')
        logger.info(f"Payment processed for order {order_id}")
    except Exception as e:
        logger.error(f"Payment processing error: {e}")
        messages.error(request, f'Error processing payment: {str(e)}')
    
    return redirect('profile')


# ============= API ДЛЯ AJAX-ЗАПРОСОВ =============

def api_product_search(request):
    """API для поиска товаров"""
    query = request.GET.get('q', '')
    
    if len(query) < 3:
        return JsonResponse({'products': []})
    
    try:
        products = ProductRepository.search_products(query)
        return JsonResponse({'products': products})
    except Exception as e:
        logger.error(f"API search error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def api_category_products(request, category_slug):
    """API для получения товаров категории"""
    try:
        products = ProductRepository.get_all_products(category_slug)
        return JsonResponse({'products': products})
    except Exception as e:
        logger.error(f"API category products error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# ============= ГЛАВНАЯ СТРАНИЦА =============

def index_view(request):
    """Главная страница с популярными товарами"""
    try:
        # Получаем топ товары через SQL
        popular_products = ProductRepository.get_top_products(4)
        context = {'products': popular_products}
        return render(request, 'main/index/index.html', context)
    except Exception as e:
        logger.error(f"Index view error: {e}")
        return render(request, 'main/index/index.html', {'products': []})