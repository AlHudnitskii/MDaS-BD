from django.shortcuts import render, redirect
from django.contrib import messages

from ..repositories.product import ProductRepository
from ..repositories.category import CategoryRepository
from ..repositories.review import ProductReviewRepository
from ..repositories.wishlist import WishlistRepository
from ..repositories.log import LogRepository


def product_list_view(request, category_slug=None):
    try:
        sort_by = request.GET.get('sort', 'name')
        search_query = request.GET.get('q')
        categories = CategoryRepository.get_all()
        current_cat = CategoryRepository.get_by_slug(category_slug) if category_slug else None

        products = (
            ProductRepository.search(search_query)
            if search_query
            else ProductRepository.get_all(category_slug, sort_by)
        )

        return render(request, 'main/product/list.html', {
            'products': products, 'categories': categories,
            'category': current_cat, 'sort_by': sort_by, 'query': search_query,
        })
    except Exception:
        messages.error(request, 'Error loading products.')
        return render(request, 'main/product/list.html', {'products': [], 'categories': []})


def product_detail_view(request, slug):
    try:
        product = ProductRepository.get_by_slug(slug)
        if not product:
            messages.error(request, 'Product not found.')
            return redirect('product_list')

        reviews = ProductReviewRepository.get_by_product(str(product['id']))
        avg_rating = ProductReviewRepository.get_avg_rating(str(product['id']))

        user_wishlists = []
        if request.session.get('is_authenticated'):
            user_wishlists = WishlistRepository.get_by_user(request.session['user_id'])

        return render(request, 'main/product/detail.html', {
            'product': product, 'reviews': reviews[:3],
            'avg_rating': avg_rating,
            'user_authenticated': request.session.get('is_authenticated', False),
            'user_wishlists': user_wishlists,
        })
    except Exception as e:
        messages.error(request, f'Error loading product: {e}')
        return redirect('product_list')


def product_reviews_view(request, slug):
    try:
        product = ProductRepository.get_by_slug(slug)
        if not product:
            return redirect('product_list')
        return render(request, 'main/product/reviews.html', {
            'product': product,
            'reviews': ProductReviewRepository.get_by_product(str(product['id'])),
            'avg_rating': ProductReviewRepository.get_avg_rating(str(product['id'])),
        })
    except Exception:
        messages.error(request, 'Error loading reviews.')
        return redirect('product_list')
