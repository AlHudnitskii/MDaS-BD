from django.urls import path

from . import sql_views


urlpatterns = [
    path('', sql_views.index_view, name='main'),
    
    path('login/', sql_views.login_view, name='login'),
    path('register/', sql_views.register_view, name='register'),
    path('logout/', sql_views.logout_view, name='logout'),
    path('profile/', sql_views.profile_view, name='profile'),
    
    path('shop/', sql_views.product_list_view, name='product_list'),
    path('shop/category/<slug:category_slug>/', sql_views.product_list_view, name='product_list_by_category'),
    path('shop/<slug:slug>/', sql_views.product_detail_view, name='product_detail'),
    
    path('cart/', sql_views.cart_detail_view, name='cart_detail'),
    path('cart/add/<str:product_id>/', sql_views.cart_add_view, name='cart_add'),
    path('cart/remove/<str:product_id>/', sql_views.cart_remove_view, name='cart_remove'),
    
    path('orders/create/', sql_views.order_create_view, name='order_create'),
    path('orders/success/<str:order_id>/', sql_views.order_success_view, name='order_success'),
    path('orders/payment/<str:order_id>/', sql_views.process_payment_view, name='process_payment'),
    
    path('statistics/', sql_views.statistics_view, name='statistics'),
    
    path('admin/cleanup-logs/', sql_views.cleanup_logs_view, name='cleanup_logs'),
    
    path('api/search/', sql_views.api_product_search, name='api_search'),
    path('api/category/<slug:category_slug>/', sql_views.api_category_products, name='api_category_products'),
]