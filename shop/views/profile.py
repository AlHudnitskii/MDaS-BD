import os
import uuid
from pathlib import Path

from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings

from ..repositories.user import UserRepository
from ..repositories.order import OrderRepository
from ..repositories.mongo_log import MongoLogRepository


def profile_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.warning(request, 'Please login to access your profile.')
        return redirect('login')

    try:
        user = UserRepository.get_user_by_username(request.session.get('username'))
        orders = OrderRepository.get_user_orders(user_id)

        if request.method == 'POST':
            image_file = request.FILES.get('image')
            relative_path = None

            if image_file:
                allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
                if image_file.content_type not in allowed:
                    messages.error(request, 'Invalid file type.')
                    return redirect('profile')
                if image_file.size > 5 * 1024 * 1024:
                    messages.error(request, 'File too large (max 5 MB).')
                    return redirect('profile')

                ext = Path(image_file.name).suffix.lower()
                filename = f"{uuid.uuid4()}{ext}"
                relative_path = f"users/{filename}"
                full_path = settings.MEDIA_ROOT / relative_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                with open(full_path, 'wb+') as f:
                    for chunk in image_file.chunks():
                        f.write(chunk)

                if user.get('image_url') and 'noimage' not in str(user['image_url']):
                    old = settings.MEDIA_ROOT / user['image_url']
                    if old.exists():
                        try:
                            os.remove(old)
                        except Exception:
                            pass

            update_kwargs = {
                'first_name': request.POST.get('first_name'),
                'last_name': request.POST.get('last_name'),
                'email': request.POST.get('email'),
                'username': request.POST.get('username'),
            }
            if relative_path:
                update_kwargs['image_url'] = relative_path

            UserRepository.update_profile(user_id, **update_kwargs)
            request.session['username'] = update_kwargs['username']

            MongoLogRepository.log_action(
                user_id, 'PROFILE_UPDATE',
                {'fields': list(update_kwargs.keys())}, 'SUCCESS',
            )
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')

        return render(request, 'users/profile.html', {'user': user, 'orders': orders})

    except Exception as e:
        MongoLogRepository.log_error(
            error_type='PROFILE_VIEW_ERROR',
            message=str(e),
            user_id=user_id,
            request_path='/profile/',
        )
        messages.error(request, f'Error loading profile: {e}')
        return redirect('product_list')
