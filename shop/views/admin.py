from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator

from ..repositories.mongo_log import MongoLogRepository
from ..repositories.statistics import StatisticsRepository
from ..repositories.product import ProductRepository


def _require_admin(request):
    return request.session.get('username') == 'admin'


@require_http_methods(["GET"])
def admin_logs_view(request):
    if not _require_admin(request):
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('profile')

    action_type = request.GET.get('action_type', '')
    status = request.GET.get('status', '')
    user_filter = request.GET.get('user', '')
    days = request.GET.get('days', '7')

    logs = MongoLogRepository.get_filtered(
        action_type = action_type or None,
        status = status or None,
        user_id = user_filter or None,
        days = int(days) if days.isdigit() else 7,
    )
    stats = MongoLogRepository.get_statistics()
    action_types = MongoLogRepository.get_unique_action_types()

    page_obj = Paginator(logs, 50).get_page(request.GET.get('page', 1))

    return render(request, 'admin/logs.html', {
        'logs':  page_obj,
        'stats': stats,
        'action_types': action_types,
        'current_filters': {
            'action_type': action_type,
            'status': status,
            'user': user_filter,
            'days': days,
        },
    })


def cleanup_logs_view(request):
    user_id = request.session.get('user_id')
    days = int(request.POST.get('days', request.GET.get('days', 90)))

    try:
        deleted = MongoLogRepository.cleanup_old(days)
        MongoLogRepository.log_action(
            user_id, 'LOGS_CLEANUP', {'days': days, 'deleted': deleted}, 'SUCCESS',
        )
        messages.success(request, f'Deleted {deleted} logs older than {days} days.')
    except Exception as e:
        messages.error(request, f'Error: {e}')

    return redirect('admin_logs')


def statistics_view(request):
    try:
        stats = StatisticsRepository.get_sales_summary()
        top_products = ProductRepository.get_top(5)
        category_stats = StatisticsRepository.get_by_category()

        return render(request, 'main/info/statistics.html', {
            'total_sales': stats['total_sales'],
            'total_orders': stats['total_orders'],
            'avg_order': stats['avg_order'],
            'top_products': top_products,
            'category_stats': category_stats,
        })
    except Exception:
        messages.error(request, 'Error loading statistics.')
        return render(request, 'main/info/statistics.html', {})
