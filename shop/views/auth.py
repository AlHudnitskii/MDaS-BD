from django.shortcuts import render, redirect
from django.contrib   import messages

from ..services.auth_service import AuthService


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'users/login.html')

        result = AuthService.login(
            username=username,
            password=password,
            ip=request.META.get('REMOTE_ADDR', ''),
        )

        if result.success:
            request.session['user_id'] = result.user_id
            request.session['username'] = result.username
            request.session['is_authenticated'] = True

            messages.success(request, f'Welcome back, {result.username}!')

            next_url = request.POST.get('next') or request.GET.get('next') or '/'
            response = redirect(next_url)

            response.set_cookie('access_token', result.access_token,
                                max_age=3600, httponly=True, samesite='Lax')
            response.set_cookie('refresh_token', result.refresh_token,
                                max_age=7*24*3600, httponly=True, samesite='Lax')
            return response

        messages.error(request, result.error)
        context = {'is_blocked': result.is_blocked, 'block_ttl': result.block_ttl}
        return render(request, 'users/login.html', context)
    return render(request, 'users/login.html')


def logout_view(request):
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    access_token = request.COOKIES.get('access_token')

    if user_id:
        AuthService.logout(user_id, username or '', access_token)

    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')

    response = redirect('/')
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'users/registration.html',
                          {'username': username, 'email': email,
                           'first_name': first_name, 'last_name': last_name})

        result = AuthService.register(username, email, password, first_name, last_name)

        if result['success']:
            user = result['user']
            request.session['user_id'] = str(user['id'])
            request.session['username'] = user['username']
            request.session['is_authenticated'] = True
            messages.success(request, 'Registration successful! Welcome!')
            return redirect('/')
        messages.error(request, result['error'])

    return render(request, 'users/registration.html')
