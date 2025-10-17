from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from main.models import Product, Category
from cart.cart import Cart
from decimal import Decimal


class SimpleCartTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Тестовая категория", 
            slug="test-category"
        )
        self.product1 = Product.objects.create(
            name="Тестовый товар 1",
            slug="test-product-1",
            category=self.category,
            price=Decimal('100.00'),
            available=True
        )
        self.product2 = Product.objects.create(
            name="Тестовый товар 2",
            slug="test-product-2",
            category=self.category,
            price=Decimal('200.00'),
            discount=10,  
            available=True
        )
        
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(self.request)
        self.request.session.save()
        
        self.cart = Cart(self.request)
    
    def test_add_product(self):
        self.cart.add(self.product1)
        self.assertEqual(len(self.cart), 1)  
        self.cart.add(self.product2, quantity=2)
        self.assertEqual(len(self.cart), 3)  
    
    def test_remove_product(self):
        self.cart.add(self.product1)
        self.cart.remove(self.product1)
        self.assertEqual(len(self.cart), 0)  