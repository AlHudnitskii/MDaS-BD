from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from ..repositories.review import ProductReviewRepository
from ..repositories.product import ProductRepository
from ..repositories.mongo_log import MongoLogRepository


@require_http_methods(["POST"])
def create_review_view(request, product_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    rating = int(request.POST.get('rating', 5))
    comment = request.POST.get('comment', '').strip()

    try:
        ProductReviewRepository.create(product_id, user_id, rating, comment)
        MongoLogRepository.log_action(
            user_id, 'REVIEW_CREATED',
            {'product_id': product_id, 'rating': rating}, 'SUCCESS',
        )
        messages.success(request, 'Review submitted.')
    except Exception:
        messages.error(request, 'Error submitting review. You may have already reviewed this product.')

    product = ProductRepository.get_by_slug(product_id)
    if product:
        return redirect('product_detail', slug=product['slug'])
    return redirect('product_list')


def user_reviews_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    return render(request, 'users/reviews.html', {'reviews': ProductReviewRepository.get_by_user(user_id)})


@require_http_methods(["POST"])
def update_review_view(request, review_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    ProductReviewRepository.update(review_id, int(request.POST.get('rating', 5)), request.POST.get('comment', '').strip())
    MongoLogRepository.log_action(user_id, 'REVIEW_UPDATED', {'review_id': review_id}, 'SUCCESS')
    messages.success(request, 'Review updated.')
    return redirect('user_reviews')


@require_http_methods(["POST"])
def delete_review_view(request, review_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    ProductReviewRepository.delete(review_id)
    MongoLogRepository.log_action(user_id, 'REVIEW_DELETED', {'review_id': review_id}, 'SUCCESS')
    messages.success(request, 'Review deleted.')
    return redirect('user_reviews')
