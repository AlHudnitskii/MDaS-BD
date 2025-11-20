from django.urls import path

from . import sql_views

urlpatterns = [
    path('', sql_views.index_view, name='index'),
    
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
    
    path('notes/', sql_views.user_notes_view, name='user_notes'),
    path('notes/create/', sql_views.create_note_view, name='create_note'),
    path('notes/update/<str:note_id>/', sql_views.update_note_view, name='update_note'),
    path('notes/delete/<str:note_id>/', sql_views.delete_note_view, name='delete_note'),
    
    path('wishlists/', sql_views.wishlists_view, name='wishlists'),
    path('wishlists/<str:wishlist_id>/', sql_views.wishlist_detail_view, name='wishlist_detail'),
    path('wishlists/create/', sql_views.create_wishlist_view, name='create_wishlist'),
    path('wishlists/<str:wishlist_id>/add/<str:product_id>/', sql_views.add_to_wishlist_view, name='add_to_wishlist'),
    path('wishlists/remove/<str:wishlist_item_id>/', sql_views.remove_from_wishlist_view, name='remove_from_wishlist'),
    
    path('product/<slug:slug>/reviews/', sql_views.product_reviews_view, name='product_reviews'),
    path('reviews/create/<str:product_id>/', sql_views.create_review_view, name='create_review'),
    path('reviews/my/', sql_views.user_reviews_view, name='user_reviews'),
    path('reviews/update/<str:review_id>/', sql_views.update_review_view, name='update_review'),
    path('reviews/delete/<str:review_id>/', sql_views.delete_review_view, name='delete_review'),
]