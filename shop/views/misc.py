from django.shortcuts import render
from ..repositories.product import ProductRepository


def index_view(request):
    try:
        products = ProductRepository.get_top(4)
    except Exception:
        products = []
    return render(request, 'main/index/index.html', {'products': products})
