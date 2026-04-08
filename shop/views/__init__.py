from .auth import login_view, register_view, logout_view
from .product import product_list_view, product_detail_view, product_reviews_view
from .cart import cart_detail_view, cart_add_view, cart_remove_view
from .order import order_create_view, order_success_view, process_payment_view
from .profile import profile_view
from .notes import user_notes_view, create_note_view, update_note_view, delete_note_view
from .wishlist import (
    wishlists_view, wishlist_detail_view,
    create_wishlist_view, update_wishlist_view, delete_wishlist_view,
    add_to_wishlist_view, remove_from_wishlist_view,
)
from .reviews import (
    create_review_view, user_reviews_view,
    update_review_view, delete_review_view,
)
from .admin import admin_logs_view, cleanup_logs_view, statistics_view
from .analytics import analytics_view, export_report
from .misc import index_view
