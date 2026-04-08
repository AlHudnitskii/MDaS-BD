import json

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse

from ..repositories.mongo_analytics import MongoAnalyticsRepository


def _require_admin(request):
    return request.session.get('username') == 'admin'


def analytics_view(request):
    if not _require_admin(request):
        messages.error(request, 'Access denied.')
        return redirect('profile')

    period = request.GET.get('period', 'day')

    try:
        context = {
            'period': period,
            'activity': MongoAnalyticsRepository.activity_by_period(period),
            'top_users': MongoAnalyticsRepository.top_active_users(),
            'operations': MongoAnalyticsRepository.operations_distribution(),
            'time_series': MongoAnalyticsRepository.time_series(),
            'anomalies': MongoAnalyticsRepository.detect_anomalies(),
        }
    except Exception as e:
        messages.error(request, f'Analytics error: {e}')
        context = {'period': period, 'activity': [], 'top_users': [],
                   'operations': {}, 'time_series': [], 'anomalies': []}

    return render(request, 'admin/analytics.html', context)


def export_report(request, report_type):
    if not _require_admin(request):
        return HttpResponse('Access denied', status=403)

    fmt = request.GET.get('format', 'json')
    period = request.GET.get('period', 'day')

    if fmt == 'csv':
        content = MongoAnalyticsRepository.export_csv(report_type, period=period)
        response = HttpResponse(content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{report_type}.csv"'
    else:
        content = MongoAnalyticsRepository.export_json(report_type, period=period)
        response = HttpResponse(content, content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{report_type}.json"'

    return response
