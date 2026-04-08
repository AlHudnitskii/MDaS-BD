from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views
from . import api_views


urlpatterns = [
    path('api/auth/login/', api_views.api_login, name='api_login'),
    path('api/auth/logout/', api_views.api_logout, name='api_logout'),
    path('api/auth/verify/', api_views.api_token_verify, name='api_token_verify'),
    path('api/cache/stats/', api_views.api_cache_stats, name='api_cache_stats'),
    path('api/cache/invalidate/', api_views.api_cache_invalidate, name='api_cache_invalidate'),

    path('', views.index_view, name='index'),

    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('profile/', views.profile_view, name='profile'),

    path('shop/', views.product_list_view, name='product_list'),
    path('shop/category/<slug:category_slug>/', views.product_list_view, name='product_list_by_category'),
    path('shop/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('product/<slug:slug>/reviews/', views.product_reviews_view, name='product_reviews'),

    path('cart/', views.cart_detail_view, name='cart_detail'),
    path('cart/add/<str:product_id>/', views.cart_add_view, name='cart_add'),
    path('cart/remove/<str:product_id>/', views.cart_remove_view, name='cart_remove'),

    path('orders/create/', views.order_create_view, name='order_create'),
    path('orders/success/<str:order_id>/', views.order_success_view, name='order_success'),
    path('orders/payment/<str:order_id>/', views.process_payment_view, name='process_payment'),

    path('statistics/', views.statistics_view, name='statistics'),
    path('admin/logs/', views.admin_logs_view, name='admin_logs'),
    path('admin/cleanup-logs/', views.cleanup_logs_view, name='cleanup_logs'),

    path('admin/analytics/', views.analytics_view, name='analytics'),
    path('admin/analytics/export/<str:report_type>/', views.export_report, name='export_report'),

    path('notes/', views.user_notes_view, name='user_notes'),
    path('notes/create/', views.create_note_view, name='create_note'),
    path('notes/update/<str:note_id>/', views.update_note_view, name='update_note'),
    path('notes/delete/<str:note_id>/', views.delete_note_view, name='delete_note'),

    path('wishlists/', views.wishlists_view, name='wishlists'),
    path('wishlists/create/', views.create_wishlist_view, name='create_wishlist'),
    path('wishlists/<str:wishlist_id>/', views.wishlist_detail_view, name='wishlist_detail'),
    path('wishlists/<str:wishlist_id>/update/', views.update_wishlist_view, name='update_wishlist'),
    path('wishlists/<str:wishlist_id>/delete/', views.delete_wishlist_view, name='delete_wishlist'),
    path('wishlists/<str:wishlist_id>/add/<str:product_id>/', views.add_to_wishlist_view, name='add_to_wishlist'),
    path('wishlists/items/<str:wishlist_item_id>/remove/', views.remove_from_wishlist_view, name='remove_from_wishlist'),

    path('reviews/create/<str:product_id>/', views.create_review_view, name='create_review'),
    path('reviews/my/', views.user_reviews_view, name='user_reviews'),
    path('reviews/update/<str:review_id>/', views.update_review_view, name='update_review'),
    path('reviews/delete/<str:review_id>/', views.delete_review_view, name='delete_review'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
