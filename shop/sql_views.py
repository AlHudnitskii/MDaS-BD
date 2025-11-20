"""
Views для работы с БД через чистый SQL
Все запросы выполняются через SQLManager
"""
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods

from .sql_manager import (
    SQLManager,
    UserRepository,
    ProductRepository,
    CategoryRepository,
    OrderRepository,
    StatisticsRepository,
    LogRepository,
    UserNoteRepository,
    WishlistRepository,
    ProductReviewRepository,
    ProductImageRepository
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
            
            if user_data:
                # Проверяем пароль используя функцию PostgreSQL
                with SQLManager() as db:
                    check_query = """
                        SELECT (password = crypt(%s, password)) as is_valid
                        FROM users WHERE username = %s
                    """
                    result = db.execute_one(check_query, (password, username))
                    
                    if result and result['is_valid']:
                        # Сохраняем данные в сессии
                        request.session['user_id'] = str(user_data['id'])
                        request.session['username'] = user_data['username']
                        request.session['is_authenticated'] = True
                        
                        # Обновляем last_login
                        db.execute_update("""
                            UPDATE users SET last_login = NOW()
                            WHERE id = %s::uuid
                        """, (str(user_data['id']),))
                        
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

def profile_view(request):
    """Профиль пользователя с использованием SQL"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.warning(request, 'Please login to access your profile')
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
            logger.warning(f"Product not found with slug: {slug}")
            return redirect('product_list')
        
        # Получаем отзывы для этого товара
        try:
            reviews = ProductReviewRepository.get_product_reviews(str(product['id']))
            avg_rating = ProductReviewRepository.get_product_average_rating(str(product['id']))
        except Exception as e:
            logger.warning(f"Error loading reviews: {e}")
            reviews = []
            avg_rating = {'avg_rating': 0, 'reviews_count': 0}
        
        context = {
            'product': product,
            'reviews': reviews[:3],  # Показываем только 3 последних отзыва
            'avg_rating': avg_rating,
            'user_authenticated': request.session.get('is_authenticated', False)
        }
        
        logger.info(f"Product detail loaded: {product['name']}")
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

def cleanup_logs_view(request):
    """Очистка старых логов (процедура из ЛР5)"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.warning(request, 'Please login first')
        return redirect('login')
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


# ============= USER NOTES =============

def user_notes_view(request):
    """Просмотр и управление заметками"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.warning(request, 'Please login to access notes')
        return redirect('login')
    
    try:
        notes = UserNoteRepository.get_user_notes(user_id)
        context = {'notes': notes}
        return render(request, 'users/notes.html', context)
    except Exception as e:
        logger.error(f"Notes view error: {e}")
        messages.error(request, 'Error loading notes')
        return redirect('profile')


@require_http_methods(["POST"])
def create_note_view(request):
    """Создание заметки"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    title = request.POST.get('title')
    content = request.POST.get('content')
    
    try:
        UserNoteRepository.create_note(user_id, title, content)
        LogRepository.log_action(user_id, 'NOTE_CREATED', {'title': title}, 'SUCCESS')
        messages.success(request, 'Note created successfully')
    except Exception as e:
        logger.error(f"Create note error: {e}")
        messages.error(request, 'Error creating note')
    
    return redirect('user_notes')


@require_http_methods(["POST"])
def update_note_view(request, note_id):
    """Обновление заметки"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    title = request.POST.get('title')
    content = request.POST.get('content')
    
    try:
        # Проверяем права доступа
        note = UserNoteRepository.get_note_by_id(note_id)
        if note and str(note['user_id']) == user_id:
            UserNoteRepository.update_note(note_id, title, content)
            LogRepository.log_action(user_id, 'NOTE_UPDATED', {'note_id': note_id}, 'SUCCESS')
            messages.success(request, 'Note updated successfully')
        else:
            messages.error(request, 'Access denied')
    except Exception as e:
        logger.error(f"Update note error: {e}")
        messages.error(request, 'Error updating note')
    
    return redirect('user_notes')


@require_http_methods(["POST"])
def delete_note_view(request, note_id):
    """Удаление заметки"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    try:
        note = UserNoteRepository.get_note_by_id(note_id)
        if note and str(note['user_id']) == user_id:
            UserNoteRepository.delete_note(note_id)
            LogRepository.log_action(user_id, 'NOTE_DELETED', {'note_id': note_id}, 'SUCCESS')
            messages.success(request, 'Note deleted successfully')
        else:
            messages.error(request, 'Access denied')
    except Exception as e:
        logger.error(f"Delete note error: {e}")
        messages.error(request, 'Error deleting note')
    
    return redirect('user_notes')


# ============= WISHLISTS =============

def wishlists_view(request):
    """Просмотр wishlist пользователя"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.warning(request, 'Please login to access wishlists')
        return redirect('login')
    
    try:
        wishlists = WishlistRepository.get_user_wishlists(user_id)
        context = {'wishlists': wishlists}
        return render(request, 'users/wishlists.html', context)
    except Exception as e:
        logger.error(f"Wishlists view error: {e}")
        messages.error(request, 'Error loading wishlists')
        return redirect('profile')


def wishlist_detail_view(request, wishlist_id):
    """Детали конкретного wishlist"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    try:
        items = WishlistRepository.get_wishlist_items(wishlist_id)
        context = {'wishlist_id': wishlist_id, 'items': items}
        return render(request, 'users/wishlist_detail.html', context)
    except Exception as e:
        logger.error(f"Wishlist detail error: {e}")
        messages.error(request, 'Error loading wishlist')
        return redirect('wishlists')


@require_http_methods(["POST"])
def create_wishlist_view(request):
    """Создание wishlist"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    
    try:
        WishlistRepository.create_wishlist(user_id, name, description)
        LogRepository.log_action(user_id, 'WISHLIST_CREATED', {'name': name}, 'SUCCESS')
        messages.success(request, 'Wishlist created successfully')
    except Exception as e:
        logger.error(f"Create wishlist error: {e}")
        messages.error(request, 'Error creating wishlist')
    
    return redirect('wishlists')


@require_http_methods(["POST"])
def add_to_wishlist_view(request, wishlist_id, product_id):
    """Добавление товара в wishlist"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    try:
        WishlistRepository.add_to_wishlist(wishlist_id, product_id)
        LogRepository.log_action(user_id, 'PRODUCT_ADDED_TO_WISHLIST', 
                                {'wishlist_id': wishlist_id, 'product_id': product_id}, 'SUCCESS')
        messages.success(request, 'Product added to wishlist')
    except Exception as e:
        logger.error(f"Add to wishlist error: {e}")
        messages.error(request, 'Error adding to wishlist')
    
    return redirect('wishlist_detail', wishlist_id=wishlist_id)


@require_http_methods(["POST"])
def remove_from_wishlist_view(request, wishlist_item_id):
    """Удаление товара из wishlist"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    try:
        WishlistRepository.remove_from_wishlist(wishlist_item_id)
        LogRepository.log_action(user_id, 'PRODUCT_REMOVED_FROM_WISHLIST', 
                                {'item_id': wishlist_item_id}, 'SUCCESS')
        messages.success(request, 'Product removed from wishlist')
    except Exception as e:
        logger.error(f"Remove from wishlist error: {e}")
        messages.error(request, 'Error removing from wishlist')
    
    return redirect('wishlists')


# ============= PRODUCT REVIEWS =============

def product_reviews_view(request, slug):
    """Просмотр отзывов на товар"""
    try:
        product = ProductRepository.get_product_by_slug(slug)
        if not product:
            messages.error(request, 'Product not found')
            return redirect('product_list')
        
        reviews = ProductReviewRepository.get_product_reviews(str(product['id']))
        avg_rating = ProductReviewRepository.get_product_average_rating(str(product['id']))
        
        context = {
            'product': product,
            'reviews': reviews,
            'avg_rating': avg_rating
        }
        
        return render(request, 'main/product/reviews.html', context)
    except Exception as e:
        logger.error(f"Product reviews error: {e}")
        messages.error(request, 'Error loading reviews')
        return redirect('product_list')


@require_http_methods(["POST"])
def create_review_view(request, product_id):
    """Создание отзыва на товар"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.warning(request, 'Please login to leave a review')
        return redirect('login')
    
    rating = int(request.POST.get('rating'))
    comment = request.POST.get('comment')
    
    try:
        ProductReviewRepository.create_review(product_id, user_id, rating, comment)
        LogRepository.log_action(user_id, 'REVIEW_CREATED', 
                                {'product_id': product_id, 'rating': rating}, 'SUCCESS')
        messages.success(request, 'Review submitted successfully')
    except Exception as e:
        logger.error(f"Create review error: {e}")
        messages.error(request, 'Error submitting review. You may have already reviewed this product.')
    
    # Получаем slug товара для редиректа
    product = ProductRepository.get_product_by_slug(product_id)
    if product:
        return redirect('product_detail', slug=product['slug'])
    return redirect('product_list')


def user_reviews_view(request):
    """Просмотр отзывов пользователя"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    try:
        reviews = ProductReviewRepository.get_user_reviews(user_id)
        context = {'reviews': reviews}
        return render(request, 'users/reviews.html', context)
    except Exception as e:
        logger.error(f"User reviews error: {e}")
        messages.error(request, 'Error loading reviews')
        return redirect('profile')


@require_http_methods(["POST"])
def update_review_view(request, review_id):
    """Обновление отзыва"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    rating = int(request.POST.get('rating'))
    comment = request.POST.get('comment')
    
    try:
        ProductReviewRepository.update_review(review_id, rating, comment)
        LogRepository.log_action(user_id, 'REVIEW_UPDATED', {'review_id': review_id}, 'SUCCESS')
        messages.success(request, 'Review updated successfully')
    except Exception as e:
        logger.error(f"Update review error: {e}")
        messages.error(request, 'Error updating review')
    
    return redirect('user_reviews')


@require_http_methods(["POST"])
def delete_review_view(request, review_id):
    """Удаление отзыва"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    try:
        ProductReviewRepository.delete_review(review_id)
        LogRepository.log_action(user_id, 'REVIEW_DELETED', {'review_id': review_id}, 'SUCCESS')
        messages.success(request, 'Review deleted successfully')
    except Exception as e:
        logger.error(f"Delete review error: {e}")
        messages.error(request, 'Error deleting review')
    
    return redirect('user_reviews')