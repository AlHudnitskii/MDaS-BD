import os
import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.contrib import messages
from pathlib import Path
from django.core.paginator import Paginator
from django.conf import settings

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
)


# ============= АУТЕНТИФИКАЦИЯ =============

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Please provide both username and password')
            return render(request, 'users/login.html')
        
        try:
            user_data = UserRepository.get_user_by_username(username)
            
            if user_data:
                with SQLManager() as db:
                    check_query = """
                        SELECT (password = crypt(%s, password)) as is_valid
                        FROM users WHERE username = %s AND is_active = TRUE
                    """
                    result = db.execute_one(check_query, (password, username))
                    
                    if result and result['is_valid']:
                        request.session['user_id'] = str(user_data['id'])
                        request.session['username'] = user_data['username']
                        request.session['is_authenticated'] = True
                        
                        db.execute_update("""
                            UPDATE users SET last_login = NOW()
                            WHERE id = %s::uuid
                        """, (str(user_data['id']),))
                        
                        try:
                            LogRepository.log_action(
                                str(user_data['id']),
                                'USER_LOGIN',
                                {'ip': request.META.get('REMOTE_ADDR'), 'username': username},
                                'SUCCESS'
                            )
                        except Exception:
                            pass
                        
                        messages.success(request, f'Welcome back, {username}!')
                        
                        next_url = request.POST.get('next') or request.GET.get('next') or '/'
                        return redirect(next_url)
            
            messages.error(request, 'Invalid username or password')
            
        except Exception:
            messages.error(request, 'An error occurred during login. Please try again.')
    
    return render(request, 'users/login.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        errors = []
        if not username:
            errors.append('Username is required')
        if not email:
            errors.append('Email is required')
        if not password:
            errors.append('Password is required')
        if password != password2:
            errors.append('Passwords do not match')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters long')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'users/registration.html', {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name
            })
        
        try:
            with SQLManager() as db:
                check_query = """
                    SELECT id FROM users 
                    WHERE username = %s OR email = %s
                """
                existing = db.execute_one(check_query, (username, email))
                
                if existing:
                    messages.error(request, 'Username or email already exists')
                    return render(request, 'users/registration.html', {
                        'username': username,
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name
                    })
                
                create_query = """
                    INSERT INTO users (
                        username, password, email, first_name, last_name,
                        is_active, is_superuser, date_joined
                    )
                    VALUES (
                        %s, crypt(%s, gen_salt('bf')), %s, %s, %s,
                        TRUE, FALSE, NOW()
                    )
                    RETURNING id, username, email, first_name, last_name
                """
                user_data = db.execute_one(create_query, 
                    (username, password, email, first_name, last_name))
                
                if user_data:
                    request.session['user_id'] = str(user_data['id'])
                    request.session['username'] = user_data['username']
                    request.session['is_authenticated'] = True
                    
                    try:
                        LogRepository.log_action(
                            str(user_data['id']),
                            'USER_REGISTER',
                            {'username': username, 'email': email},
                            'SUCCESS'
                        )
                    except Exception:
                        pass
                    
                    messages.success(request, 'Registration successful! Welcome to SQL Shop!')
                    return redirect('/')
                else:
                    messages.error(request, 'Failed to create user')
                    
        except Exception as e:
            error_msg = str(e)
            if 'unique constraint' in error_msg.lower():
                messages.error(request, 'Username or email already exists')
            else:
                messages.error(request, 'Registration failed. Please try again.')
    
    return render(request, 'users/registration.html')


def logout_view(request):
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
        except Exception:
            pass
    
    request.session.flush()
    messages.success(request, 'You have been logged out successfully')
    return redirect('/')

# ============= ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ =============

def profile_view(request):
    user_id = request.session.get('user_id')

    if not user_id:
        messages.warning(request, 'Please login to access your profile')
        return redirect('login')

    try:
        user_data = UserRepository.get_user_by_username(request.session.get('username'))
        orders = OrderRepository.get_user_orders(user_id)

        if request.method == 'POST':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            username = request.POST.get('username')
            email = request.POST.get('email')
            image_file = request.FILES.get('image')

            relative_path = None

            if image_file:
                allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
                if image_file.content_type not in allowed_types:
                    messages.error(request, 'Invalid file type. Allowed: JPEG, PNG, GIF, WEBP')
                    return redirect('profile')

                if image_file.size > 5 * 1024 * 1024:
                    messages.error(request, 'File too large. Maximum size: 5MB')
                    return redirect('profile')

                ext = Path(image_file.name).suffix.lower()
                filename = f"{uuid.uuid4()}{ext}"  # 
                relative_path = f"users/{filename}"
                full_path = settings.MEDIA_ROOT / relative_path

                full_path.parent.mkdir(parents=True, exist_ok=True)

                with open(full_path, 'wb+') as destination:
                    for chunk in image_file.chunks():
                        destination.write(chunk)

                if user_data.get('image_url') and 'noimage' not in str(user_data['image_url']):
                    old_image_path = settings.MEDIA_ROOT / user_data['image_url']
                    if old_image_path.exists():
                        try:
                            os.remove(old_image_path)
                        except Exception:
                            pass

            update_kwargs = {
                'first_name': first_name,
                'last_name': last_name,
                'username': username,
                'email': email
            }
            
            if relative_path is not None:
                update_kwargs['image_url'] = relative_path

            UserRepository.update_user_profile(user_id, **update_kwargs)
            
            request.session['username'] = username
            request.session['user_id'] = user_id
            request.session['is_authenticated'] = True
        
            fields_updated = list(update_kwargs.keys())
            LogRepository.log_action(
                user_id,
                'PROFILE_UPDATE',
                {'fields_updated': fields_updated},
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
        messages.error(request, f'Error loading profile: {str(e)}')
        return redirect('product_list')


# ============= КАТАЛОГ ТОВАРОВ =============

def product_list_view(request, category_slug=None):
    try:
        sort_by = request.GET.get('sort', 'name')
        search_query = request.GET.get('q')
        
        categories = CategoryRepository.get_all_categories()
        current_category = None
        
        if category_slug:
            current_category = CategoryRepository.get_category_by_slug(category_slug)
        
        if search_query:
            products = ProductRepository.search_products(search_query)
        else:
            products = ProductRepository.get_all_products(category_slug, sort_by)
        
        context = {
            'products': products,
            'categories': categories,
            'category': current_category,
            'sort_by': sort_by,
            'query': search_query,
        }
        
        return render(request, 'main/product/list.html', context)
    
    except Exception:
        messages.error(request, 'Error loading products')
        return render(request, 'main/product/list.html', {'products': [], 'categories': []})


def product_detail_view(request, slug):
    try:
        product = ProductRepository.get_product_by_slug(slug)
        
        if not product:
            messages.error(request, 'Product not found')
            return redirect('product_list')
        
        try:
            reviews = ProductReviewRepository.get_product_reviews(str(product['id']))
            avg_rating = ProductReviewRepository.get_product_average_rating(str(product['id']))
        except Exception:
            reviews = []
            avg_rating = {'avg_rating': 0, 'reviews_count': 0}
        
        user_wishlists = []
        if request.session.get('is_authenticated'):
            try:
                user_id = request.session.get('user_id')
                user_wishlists = WishlistRepository.get_user_wishlists(user_id)
            except Exception as e:
                print(f"Error loading wishlists: {e}")
                pass
        
        context = {
            'product': product,
            'reviews': reviews[:3],
            'avg_rating': avg_rating,
            'user_authenticated': request.session.get('is_authenticated', False),
            'user_wishlists': user_wishlists  
        }
        
        return render(request, 'main/product/detail.html', context)
    
    except Exception as e:
        messages.error(request, f'Error loading product: {str(e)}')
        return redirect('product_list')


# ============= КОРЗИНА =============

def cart_detail_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    
    try:
        for product_id, item_data in cart.items():
            product = ProductRepository.get_product_by_slug(item_data.get('slug'))
            if product:
                quantity = item_data.get('quantity', 1)
                item_total = float(product['final_price']) * quantity
                total_price += item_total
                
                cart_items.append({
                    'product': product,
                    'product_id': product_id, 
                    'quantity': quantity,
                    'total': item_total
                })
        
        context = {
            'cart_items': cart_items,
            'total_price': total_price
        }
        
        return render(request, 'cart/detail.html', context)
    
    except Exception:
        messages.error(request, 'Error loading cart')
        return render(request, 'cart/detail.html', {'cart_items': [], 'total_price': 0})


@require_http_methods(["POST"])
def cart_add_view(request, product_id):
    try:
        product = ProductRepository.get_product_by_slug(request.POST.get('slug'))
        
        if not product:
            messages.error(request, 'Product not found')
            return redirect('product_list')
        
        cart = request.session.get('cart', {})
        quantity = int(request.POST.get('quantity', 1))
        
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
        
        return redirect('cart_detail')
    
    except Exception:
        messages.error(request, 'Error adding to cart')
        return redirect('product_list')


@require_http_methods(["POST"])
def cart_remove_view(request, product_id):
    cart = request.session.get('cart', {})
    
    if product_id in cart:
        del cart[product_id]
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, 'Item removed from cart')
    
    return redirect('cart_detail')


# ============= ОФОРМЛЕНИЕ ЗАКАЗА =============


def order_create_view(request):
    user_id = request.session.get('user_id')

    if not user_id:
        messages.warning(request, 'Please login to create an order')
        return redirect('login')

    cart = request.session.get('cart', {})

    if not cart:
        messages.warning(request, 'Your cart is empty')
        return redirect('cart_detail')

    product_ids = [pid for pid in cart.keys()]
    products = ProductRepository.get_products_by_ids(product_ids)

    cart_items = []
    total_price = 0

    for product in products:
        pid = str(product["id"])
        item_data = cart[pid]

        quantity = item_data["quantity"]
        price = item_data["price"]
        total = price * quantity

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "total_price": total
        })

        total_price += total

    if request.method == "POST":
        try:
            first_name = request.POST.get("first_name")
            last_name = request.POST.get("last_name")
            email = request.POST.get("email")
            city = request.POST.get("city")
            address = request.POST.get("address")
            postal_code = request.POST.get("postal_code")

            items = [
                {"product_id": str(item["product"]["id"]), "quantity": item["quantity"]}
                for item in cart_items
            ]


            order_id = OrderRepository.create_order_with_items(
                user_id, first_name, last_name, email,
                city, address, postal_code, items
            )

            if order_id:
                request.session["cart"] = {}
                request.session.modified = True
                
                LogRepository.log_action(
                    user_id,
                    'ORDER_CREATED',
                    {'order_id': order_id, 'items_count': len(items)},
                    'SUCCESS'
                )

                return redirect("order_success", order_id=order_id)

            messages.error(request, "Failed to create order")

        except Exception as e:
            messages.error(request, f"Error creating order: {e}")

    context = {
        "cart": cart_items,
        "total_price": total_price
    }

    return render(request, "orders/order/create.html", context)




def order_success_view(request, order_id):
    try:
        order = OrderRepository.get_order_details(order_id)
        context = {'order': order}
        return render(request, 'orders/order/created.html', context)
    except Exception:
        messages.error(request, 'Order not found')
        return redirect('product_list')


# ============= СТАТИСТИКА =============

def statistics_view(request):
    try:
        stats = StatisticsRepository.get_sales_statistics()
        top_products = ProductRepository.get_top_products(5)
        category_stats = StatisticsRepository.get_category_statistics()
        
        context = {
            'total_sales': stats['total_sales'],
            'total_orders': stats['total_orders'],
            'avg_order': stats['avg_order'],
            'top_products': top_products,
            'category_stats': category_stats
        }
        
        return render(request, 'main/info/statistics.html', context)
    
    except Exception:
        messages.error(request, 'Error loading statistics')
        return render(request, 'main/info/statistics.html', {})


# ============= АДМИНИСТРАТИВНЫЕ ФУНКЦИИ =============

def cleanup_logs_view(request):
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    
    days = 90
    if request.method == 'POST':
        days = int(request.POST.get('days', 90))
    else:
        days = int(request.GET.get('days', 90))
    
    try:
        deleted_count = LogRepository.cleanup_old_logs(days)
        
        if deleted_count > 0:
            LogRepository.log_action(
                user_id,
                'LOGS_CLEANUP',
                {
                    'days': days,
                    'deleted_count': deleted_count
                },
                'SUCCESS'
            )
            
            messages.success(request, f'Successfully cleaned up {deleted_count} log entries older than {days} days')
        else:
            messages.info(request, f'No logs found older than {days} days')
        
    except Exception as e:
        messages.error(request, f'Error cleaning up logs: {str(e)}')
    
    return redirect('admin_logs')


@require_http_methods(["GET"])
def admin_logs_view(request):
    username = request.session.get('username')
    
    if username != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('profile')
    
    try:
        action_type = request.GET.get('action_type', '')
        status = request.GET.get('status', '')
        user_filter = request.GET.get('user', '')
        days = request.GET.get('days', '7')
        
        logs = LogRepository.get_filtered_logs(
            action_type=action_type if action_type else None,
            status=status if status else None,
            user_filter=user_filter if user_filter else None,
            days=int(days) if days.isdigit() else 7
        )
        
        stats = LogRepository.get_logs_statistics()
        
        action_types = LogRepository.get_unique_action_types()
        
        paginator = Paginator(logs, 50)  
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context = {
            'logs': page_obj,
            'stats': stats,
            'action_types': action_types,
            'current_filters': {
                'action_type': action_type,
                'status': status,
                'user': user_filter,
                'days': days
            }
        }
        
        return render(request, 'admin/logs.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading logs: {str(e)}')
        return redirect('profile')

def process_payment_view(request, order_id):
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
    except Exception as e:
        messages.error(request, f'Error processing payment: {str(e)}')
    
    return redirect('profile')


# ============= ГЛАВНАЯ СТРАНИЦА =============

def index_view(request):
    try:
        popular_products = ProductRepository.get_top_products(4)
        context = {'products': popular_products}
        return render(request, 'main/index/index.html', context)
    except Exception:
        return render(request, 'main/index/index.html', {'products': []})


# ============= USER NOTES =============

def user_notes_view(request):
    user_id = request.session.get('user_id')
    
    if not user_id:
        messages.warning(request, 'Please login to access notes')
        return redirect('login')
    
    try:
        notes = UserNoteRepository.get_user_notes(user_id)
        context = {'notes': notes}
        return render(request, 'users/notes.html', context)
    except Exception:
        messages.error(request, 'Error loading notes')
        return redirect('profile')


@require_http_methods(["POST"])
def create_note_view(request):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    title = request.POST.get('title')
    content = request.POST.get('content')
    
    try:
        UserNoteRepository.create_note(user_id, title, content)
        LogRepository.log_action(user_id, 'NOTE_CREATED', {'title': title}, 'SUCCESS')
        messages.success(request, 'Note created successfully')
    except Exception:
        messages.error(request, 'Error creating note')
    
    return redirect('user_notes')


@require_http_methods(["POST"])
def update_note_view(request, note_id):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    title = request.POST.get('title')
    content = request.POST.get('content')
    
    try:
        note = UserNoteRepository.get_note_by_id(note_id)
        if note and str(note['user_id']) == user_id:
            UserNoteRepository.update_note(note_id, title, content)
            LogRepository.log_action(user_id, 'NOTE_UPDATED', {'note_id': note_id}, 'SUCCESS')
            messages.success(request, 'Note updated successfully')
        else:
            messages.error(request, 'Access denied')
    except Exception:
        messages.error(request, 'Error updating note')
    
    return redirect('user_notes')


@require_http_methods(["POST"])
def delete_note_view(request, note_id):
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
    except Exception:
        messages.error(request, 'Error deleting note')
    
    return redirect('user_notes')


# ============= WISHLISTS =============

@require_http_methods(["GET"])
def wishlists_view(request):
    user_id = request.session.get('user_id')
    username = request.session.get('username')

    if not user_id:
        messages.warning(request, 'Please login to access wishlists')
        return redirect('login')

    try:
        wishlists = WishlistRepository.get_user_wishlists(user_id)
        return render(request, 'users/wishlists.html', {
            'wishlists': wishlists,
            'user_authenticated': True,
            'username': username
        })
    except Exception as e:
        messages.error(request, f'Error loading wishlists: {str(e)}')
        return redirect('profile')


@require_http_methods(["GET"])
def wishlist_detail_view(request, wishlist_id):
    user_id = request.session.get('user_id')

    if not user_id:
        messages.warning(request, 'Please login first')
        return redirect('login')

    try:
        wishlist = WishlistRepository.get_wishlist(wishlist_id)
        
        if not wishlist:
            messages.error(request, 'Wishlist not found')
            return redirect('wishlists')

        if str(wishlist['user_id']) != user_id:
            messages.error(request, "Access denied")
            return redirect('wishlists')

        items = WishlistRepository.get_wishlist_items(wishlist_id)

        return render(request, 'users/wishlist_detail.html', {
            'wishlist': wishlist,
            'items': items,
            'user_authenticated': True
        })

    except Exception as e:
        messages.error(request, f'Error loading wishlist: {str(e)}')
        return redirect('wishlists')


@require_http_methods(["POST"])
def create_wishlist_view(request):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    
    if not name:
        messages.error(request, 'Wishlist name is required')
        return redirect('wishlists')
    
    try:
        WishlistRepository.create_wishlist(user_id, name, description)
        LogRepository.log_action(user_id, 'WISHLIST_CREATED', {'name': name}, 'SUCCESS')
        messages.success(request, f'Wishlist "{name}" created successfully')
    except Exception as e:
        messages.error(request, f'Error creating wishlist: {str(e)}')
    
    return redirect('wishlists')


@require_http_methods(["POST"])
def update_wishlist_view(request, wishlist_id):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('login')

    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()

    if not name:
        messages.error(request, 'Wishlist name is required')
        return redirect('wishlist_detail', wishlist_id=wishlist_id)

    try:
        wishlist = WishlistRepository.get_wishlist(wishlist_id)

        if not wishlist or str(wishlist['user_id']) != user_id:
            messages.error(request, 'Access denied')
            return redirect('wishlists')

        WishlistRepository.update_wishlist(wishlist_id, name, description)
        LogRepository.log_action(user_id, 'WISHLIST_UPDATED', 
                                {'wishlist_id': wishlist_id, 'name': name}, 'SUCCESS')
        messages.success(request, 'Wishlist updated successfully')

    except Exception as e:
        messages.error(request, f'Error updating wishlist: {str(e)}')

    return redirect('wishlist_detail', wishlist_id=wishlist_id)


@require_http_methods(["POST"])
def delete_wishlist_view(request, wishlist_id):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('login')

    try:
        wishlist = WishlistRepository.get_wishlist(wishlist_id)

        if not wishlist or str(wishlist['user_id']) != user_id:
            messages.error(request, 'Access denied')
            return redirect('wishlists')

        WishlistRepository.delete_wishlist(wishlist_id)
        LogRepository.log_action(user_id, 'WISHLIST_DELETED', 
                                {'wishlist_id': wishlist_id}, 'SUCCESS')
        messages.success(request, 'Wishlist deleted successfully')

    except Exception as e:
        messages.error(request, f'Error deleting wishlist: {str(e)}')

    return redirect('wishlists')


@require_http_methods(["POST"])
def add_to_wishlist_view(request, wishlist_id, product_id):
    user_id = request.session.get('user_id')

    if not user_id:
        messages.warning(request, 'Please login first')
        return redirect('login')

    try:
        wishlist = WishlistRepository.get_wishlist(wishlist_id)

        if not wishlist or str(wishlist['user_id']) != user_id:
            messages.error(request, 'Access denied')
            return redirect('wishlists')

        if WishlistRepository.check_product_in_wishlist(wishlist_id, product_id):
            messages.warning(request, 'This product is already in your wishlist')
        else:
            WishlistRepository.add_to_wishlist(wishlist_id, product_id)
            LogRepository.log_action(
                user_id,
                'PRODUCT_ADDED_TO_WISHLIST',
                {'wishlist_id': wishlist_id, 'product_id': product_id},
                'SUCCESS'
            )
            messages.success(request, 'Product added to wishlist')

    except Exception as e:
        messages.error(request, f'Error adding to wishlist: {str(e)}')

    return redirect(request.META.get('HTTP_REFERER', 'wishlists'))


@require_http_methods(["POST"])
def remove_from_wishlist_view(request, wishlist_item_id):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('login')

    try:
        item = WishlistRepository.get_item(wishlist_item_id)
        
        if not item:
            messages.error(request, 'Item not found')
            return redirect('wishlists')

        wishlist = WishlistRepository.get_wishlist(item['wishlist_id'])

        if str(wishlist['user_id']) != user_id:
            messages.error(request, 'Access denied')
            return redirect('wishlists')

        WishlistRepository.remove_from_wishlist(wishlist_item_id)

        LogRepository.log_action(
            user_id,
            'PRODUCT_REMOVED_FROM_WISHLIST',
            {'item_id': wishlist_item_id, 'product_id': str(item['product_id'])},
            'SUCCESS'
        )
        messages.success(request, 'Product removed from wishlist')

    except Exception as e:
        messages.error(request, f'Error removing from wishlist: {str(e)}')

    return redirect(request.META.get('HTTP_REFERER', 'wishlists'))


# ============= PRODUCT REVIEWS =============

def product_reviews_view(request, slug):
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
    except Exception:
        messages.error(request, 'Error loading reviews')
        return redirect('product_list')


@require_http_methods(["POST"])
def create_review_view(request, product_id):
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
    except Exception:
        messages.error(request, 'Error submitting review. You may have already reviewed this product.')
    
    product = ProductRepository.get_product_by_slug(product_id)
    if product:
        return redirect('product_detail', slug=product['slug'])
    return redirect('product_list')


def user_reviews_view(request):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    try:
        reviews = ProductReviewRepository.get_user_reviews(user_id)
        context = {'reviews': reviews}
        return render(request, 'users/reviews.html', context)
    except Exception:
        messages.error(request, 'Error loading reviews')
        return redirect('profile')


@require_http_methods(["POST"])
def update_review_view(request, review_id):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    rating = int(request.POST.get('rating'))
    comment = request.POST.get('comment')
    
    try:
        ProductReviewRepository.update_review(review_id, rating, comment)
        LogRepository.log_action(user_id, 'REVIEW_UPDATED', {'review_id': review_id}, 'SUCCESS')
        messages.success(request, 'Review updated successfully')
    except Exception:
        messages.error(request, 'Error updating review')
    
    return redirect('user_reviews')


@require_http_methods(["POST"])
def delete_review_view(request, review_id):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    try:
        ProductReviewRepository.delete_review(review_id)
        LogRepository.log_action(user_id, 'REVIEW_DELETED', {'review_id': review_id}, 'SUCCESS')
        messages.success(request, 'Review deleted successfully')
    except Exception:
        messages.error(request, 'Error deleting review')
    
    return redirect('user_reviews')