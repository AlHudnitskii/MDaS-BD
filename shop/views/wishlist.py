from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from ..repositories.wishlist import WishlistRepository
from ..repositories.log import LogRepository


def _get_user_id(request):
    return request.session.get('user_id')


def _owns_wishlist(wishlist, user_id: str) -> bool:
    return wishlist and str(wishlist['user_id']) == user_id


def wishlists_view(request):
    user_id = _get_user_id(request)
    if not user_id:
        return redirect('login')

    return render(request, 'users/wishlists.html', {
        'wishlists': WishlistRepository.get_by_user(user_id),
        'user_authenticated': True,
        'username': request.session.get('username'),
    })


@require_http_methods(["GET"])
def wishlist_detail_view(request, wishlist_id):
    user_id  = _get_user_id(request)
    if not user_id:
        return redirect('login')

    wishlist = WishlistRepository.get_by_id(wishlist_id)
    if not _owns_wishlist(wishlist, user_id):
        messages.error(request, 'Access denied.')
        return redirect('wishlists')

    return render(request, 'users/wishlist_detail.html', {
        'wishlist': wishlist,
        'items': WishlistRepository.get_items(wishlist_id),
        'user_authenticated': True,
    })


@require_http_methods(["POST"])
def create_wishlist_view(request):
    user_id = _get_user_id(request)
    if not user_id:
        return redirect('login')

    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, 'Wishlist name is required.')
        return redirect('wishlists')

    WishlistRepository.create(user_id, name, request.POST.get('description', '').strip())
    LogRepository.log_action(user_id, 'WISHLIST_CREATED', {'name': name}, 'SUCCESS')
    messages.success(request, f'Wishlist "{name}" created.')
    return redirect('wishlists')


@require_http_methods(["POST"])
def update_wishlist_view(request, wishlist_id):
    user_id  = _get_user_id(request)
    if not user_id:
        return redirect('login')

    wishlist = WishlistRepository.get_by_id(wishlist_id)
    if not _owns_wishlist(wishlist, user_id):
        messages.error(request, 'Access denied.')
        return redirect('wishlists')

    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, 'Name is required.')
        return redirect('wishlist_detail', wishlist_id=wishlist_id)

    WishlistRepository.update(wishlist_id, name, request.POST.get('description', '').strip())
    LogRepository.log_action(user_id, 'WISHLIST_UPDATED', {'wishlist_id': wishlist_id}, 'SUCCESS')
    messages.success(request, 'Wishlist updated.')
    return redirect('wishlist_detail', wishlist_id=wishlist_id)


@require_http_methods(["POST"])
def delete_wishlist_view(request, wishlist_id):
    user_id  = _get_user_id(request)
    if not user_id:
        return redirect('login')

    wishlist = WishlistRepository.get_by_id(wishlist_id)
    if not _owns_wishlist(wishlist, user_id):
        messages.error(request, 'Access denied.')
        return redirect('wishlists')

    WishlistRepository.delete(wishlist_id)
    LogRepository.log_action(user_id, 'WISHLIST_DELETED', {'wishlist_id': wishlist_id}, 'SUCCESS')
    messages.success(request, 'Wishlist deleted.')
    return redirect('wishlists')


@require_http_methods(["POST"])
def add_to_wishlist_view(request, wishlist_id, product_id):
    user_id  = _get_user_id(request)
    if not user_id:
        return redirect('login')

    wishlist = WishlistRepository.get_by_id(wishlist_id)
    if not _owns_wishlist(wishlist, user_id):
        messages.error(request, 'Access denied.')
        return redirect('wishlists')

    if WishlistRepository.item_exists(wishlist_id, product_id):
        messages.warning(request, 'Already in wishlist.')
    else:
        WishlistRepository.add_item(wishlist_id, product_id)
        LogRepository.log_action(
            user_id, 'PRODUCT_ADDED_TO_WISHLIST',
            {'wishlist_id': wishlist_id, 'product_id': product_id}, 'SUCCESS'
        )
        messages.success(request, 'Added to wishlist.')

    return redirect(request.META.get('HTTP_REFERER', 'wishlists'))


@require_http_methods(["POST"])
def remove_from_wishlist_view(request, wishlist_item_id):
    user_id = _get_user_id(request)
    if not user_id:
        return redirect('login')

    item = WishlistRepository.get_item_by_id(wishlist_item_id)
    wishlist = WishlistRepository.get_by_id(item['wishlist_id']) if item else None

    if not _owns_wishlist(wishlist, user_id):
        messages.error(request, 'Access denied.')
        return redirect('wishlists')

    WishlistRepository.remove_item(wishlist_item_id)
    LogRepository.log_action(
        user_id, 'PRODUCT_REMOVED_FROM_WISHLIST',
        {'item_id': wishlist_item_id}, 'SUCCESS'
    )
    messages.success(request, 'Removed from wishlist.')
    return redirect(request.META.get('HTTP_REFERER', 'wishlists'))
